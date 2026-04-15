#!/usr/bin/env python3
"""MDPM local kanban board server.

Zero dependencies beyond the Python stdlib. Reads task files from ./tasks/
and serves them as JSON alongside a single-page kanban board.

Usage:
    python3 serve.py [--port 8765] [--root .] [--host 127.0.0.1]

The server exposes:
    GET /               -> board.html
    GET /api/tasks      -> JSON array of tasks (all statuses)
    GET /api/roadmap    -> current ROADMAP.md (plain text)
    GET /healthz        -> "ok"
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from datetime import date, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


STATUS_DIRS = ("inbox", "backlog", "active", "done")


# ---------------------------------------------------------------------------
# Minimal YAML frontmatter parser (avoids PyYAML dependency).
# Supports scalars, lists (inline `[a, b]` or null), booleans, and simple strings.
# ---------------------------------------------------------------------------

FM_BOUNDARY = re.compile(r"^---\s*$", re.MULTILINE)
LIST_INLINE = re.compile(r"^\[(.*)\]$")


def _coerce(value: str):
    value = value.strip()
    if value == "" or value.lower() == "null" or value.lower() == "~":
        return None
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    m = LIST_INLINE.match(value)
    if m:
        inner = m.group(1).strip()
        if not inner:
            return []
        return [_coerce(part) for part in _split_top_level(inner, ",")]
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1]
    return value


def _split_top_level(s: str, sep: str) -> list[str]:
    """Split on sep while respecting brackets/quotes (simple single-level)."""
    out, buf, depth, quote = [], [], 0, None
    for ch in s:
        if quote:
            buf.append(ch)
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
            buf.append(ch)
        elif ch in "[{(":
            depth += 1
            buf.append(ch)
        elif ch in "]})":
            depth -= 1
            buf.append(ch)
        elif ch == sep and depth == 0:
            out.append("".join(buf).strip())
            buf = []
        else:
            buf.append(ch)
    if buf:
        out.append("".join(buf).strip())
    return out


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Return (frontmatter_dict, body_text). Frontmatter is empty dict if absent."""
    if not text.startswith("---"):
        return {}, text
    # Find the closing ---
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text
    end = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end = i
            break
    if end is None:
        return {}, text
    fm_block = "\n".join(lines[1:end])
    body = "\n".join(lines[end + 1 :])
    data: dict = {}
    current_key = None
    for raw in fm_block.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        # nested keys not supported — keep it simple; task schema is flat.
        if ":" in raw and not raw.lstrip().startswith("-"):
            key, _, val = raw.partition(":")
            key = key.strip()
            data[key] = _coerce(val)
            current_key = key
        elif raw.lstrip().startswith("-") and current_key is not None:
            # block-style list
            val = _coerce(raw.lstrip()[1:].strip())
            existing = data.get(current_key)
            if not isinstance(existing, list):
                data[current_key] = []
            data[current_key].append(val)
    return data, body


# ---------------------------------------------------------------------------
# Task loading
# ---------------------------------------------------------------------------


AC_CHECKED = re.compile(r"^\s*-\s*\[x\]", re.IGNORECASE | re.MULTILINE)
AC_UNCHECKED = re.compile(r"^\s*-\s*\[ \]", re.MULTILINE)
SECTION = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)


def extract_section(body: str, name: str) -> str:
    """Grab the content of a '## Name' section. Returns empty string if absent."""
    matches = list(SECTION.finditer(body))
    for i, m in enumerate(matches):
        if m.group(1).strip().lower() == name.lower():
            start = m.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
            return body[start:end].strip()
    return ""


def load_task(path: Path, status_dir: str) -> dict | None:
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as exc:
        print(f"[mdpm] failed reading {path}: {exc}", file=sys.stderr)
        return None
    fm, body = parse_frontmatter(text)
    ac_section = extract_section(body, "Acceptance Criteria")
    done_count = len(AC_CHECKED.findall(ac_section))
    todo_count = len(AC_UNCHECKED.findall(ac_section))
    total = done_count + todo_count
    objective = extract_section(body, "Objective")
    worklog = extract_section(body, "Work Log")
    notes = extract_section(body, "Notes")
    latest_log = ""
    for line in reversed(worklog.splitlines()):
        if line.strip().startswith("-"):
            latest_log = line.strip().lstrip("- ").strip()
            break

    today = date.today().isoformat()
    due = fm.get("due")
    overdue = bool(due and isinstance(due, str) and due < today and status_dir != "done")

    return {
        "id": fm.get("id"),
        "title": fm.get("title") or path.stem.replace("-", " ").title(),
        "priority": fm.get("priority") or "medium",
        "status_dir": status_dir,
        "status_field": fm.get("status"),
        "created": fm.get("created"),
        "updated": fm.get("updated"),
        "due": due,
        "overdue": overdue,
        "tags": fm.get("tags") or [],
        "depends_on": fm.get("depends_on") or [],
        "assigned_to": fm.get("assigned_to"),
        "wrike_id": fm.get("wrike_id"),
        "jira_id": fm.get("jira_id"),
        "jira_project": fm.get("jira_project"),
        "objective": objective,
        "notes": notes,
        "acceptance": {
            "done": done_count,
            "total": total,
        },
        "latest_log": latest_log,
        "filename": path.name,
        "path": str(path),
    }


def load_all_tasks(root: Path) -> list[dict]:
    tasks: list[dict] = []
    base = root / "tasks"
    if not base.exists():
        return tasks
    for status in STATUS_DIRS:
        sdir = base / status
        if not sdir.is_dir():
            continue
        for path in sorted(sdir.glob("*.md")):
            t = load_task(path, status)
            if t:
                tasks.append(t)
    return tasks


# ---------------------------------------------------------------------------
# HTTP handler
# ---------------------------------------------------------------------------


class BoardHandler(BaseHTTPRequestHandler):
    server_version = "mdpm-board/0.1"
    project_root: Path = Path(".")
    board_html: Path = Path("board.html")

    def log_message(self, fmt: str, *args):  # quieter logs
        sys.stderr.write(
            "[%s] %s\n" % (time.strftime("%H:%M:%S"), fmt % args)
        )

    def _send(self, status: int, body: bytes, content_type: str, cache: bool = False):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        if not cache:
            self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self) -> bytes:
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0:
            return b""
        return self.rfile.read(length)

    def _resolve_task_path(self, raw: str) -> Path | None:
        """Resolve a path like /api/task/backlog/PRJ-001-title.md to an absolute file.

        Returns None if the path escapes tasks/ or targets a non-.md file or
        a status directory outside STATUS_DIRS.
        """
        # Strip /api/task/ prefix
        rel = raw[len("/api/task/"):]
        rel = rel.strip("/")
        parts = rel.split("/")
        if len(parts) != 2:
            return None
        status, filename = parts
        if status not in STATUS_DIRS and status != "archive":
            return None
        if not filename.endswith(".md") or "/" in filename or ".." in filename:
            return None
        candidate = (self.project_root / "tasks" / status / filename).resolve()
        try:
            candidate.relative_to((self.project_root / "tasks").resolve())
        except ValueError:
            return None
        return candidate

    def do_GET(self):  # noqa: N802
        url = urlparse(self.path)
        path = url.path

        if path in ("/", "/index.html"):
            try:
                html = self.board_html.read_bytes()
            except FileNotFoundError:
                self._send(500, b"board.html not found", "text/plain")
                return
            self._send(200, html, "text/html; charset=utf-8")
            return

        if path == "/healthz":
            self._send(200, b"ok", "text/plain")
            return

        if path == "/api/tasks":
            tasks = load_all_tasks(self.project_root)
            payload = json.dumps(
                {"tasks": tasks, "generated_at": datetime.now().isoformat()},
                indent=2,
                default=str,
            ).encode("utf-8")
            self._send(200, payload, "application/json")
            return

        if path == "/api/roadmap":
            roadmap = self.project_root / "docs" / "ROADMAP.md"
            if roadmap.exists():
                self._send(200, roadmap.read_bytes(), "text/plain; charset=utf-8")
            else:
                self._send(404, b"ROADMAP.md not found", "text/plain")
            return

        if path.startswith("/api/task/"):
            file_path = self._resolve_task_path(path)
            if file_path is None or not file_path.exists():
                self._send(404, b"task not found", "text/plain")
                return
            content = file_path.read_text(encoding="utf-8")
            mtime = file_path.stat().st_mtime
            payload = json.dumps(
                {"path": str(file_path.relative_to(self.project_root)), "content": content, "mtime": mtime}
            ).encode("utf-8")
            self._send(200, payload, "application/json")
            return

        self._send(404, b"not found", "text/plain")

    def do_POST(self):  # noqa: N802
        url = urlparse(self.path)
        path = url.path

        if path.startswith("/api/task/"):
            file_path = self._resolve_task_path(path)
            if file_path is None or not file_path.exists():
                self._send(404, b"task not found", "text/plain")
                return
            try:
                payload = json.loads(self._read_body().decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                self._send(400, f"invalid json: {exc}".encode("utf-8"), "text/plain")
                return
            new_content = payload.get("content")
            expected_mtime = payload.get("mtime")
            if not isinstance(new_content, str):
                self._send(400, b"content must be a string", "text/plain")
                return

            # Conflict detection: reject if the file changed on disk since the client loaded it.
            current_mtime = file_path.stat().st_mtime
            if expected_mtime is not None and abs(current_mtime - float(expected_mtime)) > 1e-6:
                body = json.dumps({
                    "error": "conflict",
                    "message": "file changed on disk since you opened it",
                    "current_content": file_path.read_text(encoding="utf-8"),
                    "current_mtime": current_mtime,
                }).encode("utf-8")
                self._send(409, body, "application/json")
                return

            # Lightweight validation: frontmatter must still parse.
            if not new_content.startswith("---\n"):
                self._send(400, b"missing YAML frontmatter (must start with '---\\n')", "text/plain")
                return
            fm, _body = parse_frontmatter(new_content)
            if not fm:
                self._send(400, b"frontmatter failed to parse", "text/plain")
                return

            # Atomic write: write to temp, fsync, rename.
            tmp = file_path.with_suffix(file_path.suffix + ".tmp")
            try:
                tmp.write_text(new_content, encoding="utf-8")
                os.replace(tmp, file_path)
            except OSError as exc:
                self._send(500, f"write failed: {exc}".encode("utf-8"), "text/plain")
                return

            new_mtime = file_path.stat().st_mtime
            body = json.dumps({"ok": True, "mtime": new_mtime}).encode("utf-8")
            self._send(200, body, "application/json")
            return

        self._send(404, b"not found", "text/plain")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def _find_free_port(host: str, start: int, max_attempts: int = 20) -> int:
    """Find the first free TCP port at or above `start` on `host`.

    Raises OSError if no port is available in the attempted range.
    """
    import socket as _socket

    for candidate in range(start, start + max_attempts):
        with _socket.socket(_socket.AF_INET, _socket.SOCK_STREAM) as probe:
            probe.setsockopt(_socket.SOL_SOCKET, _socket.SO_REUSEADDR, 1)
            try:
                probe.bind((host, candidate))
            except OSError:
                continue
            return candidate
    raise OSError(
        f"No free port found in range {start}..{start + max_attempts - 1} on {host}"
    )


def main(argv: list[str]) -> int:
    here = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description="MDPM kanban board server")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument(
        "--root",
        default=None,
        help="Project root containing tasks/ and docs/. Defaults to CWD, falling back to the parent of this script.",
    )
    parser.add_argument(
        "--strict-port",
        action="store_true",
        help="Fail instead of auto-picking the next free port if --port is in use.",
    )
    args = parser.parse_args(argv)

    if args.root:
        project_root = Path(args.root).resolve()
    else:
        cwd = Path.cwd()
        if (cwd / "tasks").exists():
            project_root = cwd
        elif (here.parent / "tasks").exists():
            project_root = here.parent
        else:
            project_root = cwd

    BoardHandler.project_root = project_root
    BoardHandler.board_html = here / "board.html"

    # Resolve the port: try the requested one, then walk forward if busy.
    port = args.port
    try:
        server = ThreadingHTTPServer((args.host, port), BoardHandler)
    except OSError as exc:
        if args.strict_port:
            print(f"[mdpm] port {port} is busy: {exc}", file=sys.stderr)
            return 1
        try:
            port = _find_free_port(args.host, args.port + 1)
        except OSError as find_exc:
            print(f"[mdpm] port {args.port} is busy and {find_exc}", file=sys.stderr)
            return 1
        print(
            f"[mdpm] port {args.port} was busy; using {port} instead "
            f"(pass --strict-port to fail instead)"
        )
        server = ThreadingHTTPServer((args.host, port), BoardHandler)

    print(f"[mdpm] serving board from {project_root} at http://{args.host}:{port}")
    print("[mdpm] ctrl+c to quit")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print()
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
