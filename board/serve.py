#!/usr/bin/env python3
"""MDPM local kanban board server.

Zero dependencies beyond the Python stdlib. Reads task files from ./tasks/
and serves them as JSON alongside a single-page kanban board.

Usage:
    python3 serve.py [--port 8765] [--root .] [--host 127.0.0.1]

The server exposes:
    GET  /                                   -> board.html
    GET  /api/tasks                          -> JSON array of tasks (all statuses)
    GET  /api/roadmap                        -> current ROADMAP.md (plain text)
    GET  /healthz                            -> "ok"
    GET  /api/task/<status>/<filename>       -> raw markdown + mtime
    POST /api/task/<status>/<filename>       -> write raw markdown (mtime-checked)

Task parsing, loading, and filename conventions live in lib/mdpm_core.py so
this server and the bin/mdpm CLI share the same model.
"""

from __future__ import annotations

import argparse
import json
import os
import socket
import sys
import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "lib"))

import mdpm_core as core  # noqa: E402


# ---------------------------------------------------------------------------
# HTTP handler
# ---------------------------------------------------------------------------


class BoardHandler(BaseHTTPRequestHandler):
    server_version = "mdpm-board/0.4"
    project_root: Path = Path(".")
    board_html: Path = Path("board.html")

    def log_message(self, fmt: str, *args):  # quieter logs
        sys.stderr.write("[%s] %s\n" % (time.strftime("%H:%M:%S"), fmt % args))

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
        """Resolve /api/task/<status>/<filename>.md to an absolute path or None."""
        rel = raw[len("/api/task/"):].strip("/")
        parts = rel.split("/")
        if len(parts) != 2:
            return None
        status, filename = parts
        if status not in core.ALL_STATUS_DIRS:
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
        path = urlparse(self.path).path

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
            tasks = core.load_all_tasks(self.project_root)
            # Strip the frontmatter/body heavy fields for the wire format
            wire = []
            for t in tasks:
                item = {k: v for k, v in t.items() if k not in ("frontmatter", "body")}
                wire.append(item)
            payload = json.dumps(
                {"tasks": wire, "generated_at": datetime.now().isoformat()},
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
            payload = json.dumps({
                "path": str(file_path.relative_to(self.project_root)),
                "content": content,
                "mtime": mtime,
            }).encode("utf-8")
            self._send(200, payload, "application/json")
            return

        self._send(404, b"not found", "text/plain")

    def do_POST(self):  # noqa: N802
        path = urlparse(self.path).path

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

            if not new_content.startswith("---\n"):
                self._send(400, b"missing YAML frontmatter (must start with '---\\n')", "text/plain")
                return
            fm, _body = core.parse_frontmatter(new_content)
            if not fm:
                self._send(400, b"frontmatter failed to parse", "text/plain")
                return

            try:
                core.atomic_write_text(file_path, new_content)
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
    for candidate in range(start, start + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                probe.bind((host, candidate))
            except OSError:
                continue
            return candidate
    raise OSError(f"No free port in range {start}..{start + max_attempts - 1} on {host}")


def main(argv: list[str]) -> int:
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
        elif (HERE.parent / "tasks").exists():
            project_root = HERE.parent
        else:
            project_root = cwd

    BoardHandler.project_root = project_root
    BoardHandler.board_html = HERE / "board.html"

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
    sys.exit(main(sys.argv[1:]))
