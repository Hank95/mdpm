"""MDPM core — shared task loading, parsing, and file operations.

Used by both `bin/mdpm` (CLI) and `board/serve.py` (kanban server). Keep this
module dependency-free (Python stdlib only) to match the plugin's zero-deps
design.
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

STATUS_DIRS = ("inbox", "backlog", "active", "done")
ALL_STATUS_DIRS = STATUS_DIRS + ("archive",)

# Canonical order for frontmatter keys when we rewrite a task file. Keys not
# in this list are appended in their original order.
TASK_FIELD_ORDER = [
    "id",
    "title",
    "priority",
    "status",
    "created",
    "updated",
    "due",
    "tags",
    "depends_on",
    "assigned_to",
    "wrike_id",
    "jira_id",
    "jira_project",
]

# Sections recognized in task bodies.
SECTION_RE = re.compile(r"^##\s+(.+?)\s*$")


# ---------------------------------------------------------------------------
# Error types
# ---------------------------------------------------------------------------


class MdpmError(Exception):
    """Base error with an associated exit code (maps to bin/mdpm's contract)."""

    exit_code = 1


class NotFoundError(MdpmError):
    exit_code = 2


class AmbiguousRefError(MdpmError):
    exit_code = 2

    def __init__(self, message: str, candidates: list[dict]):
        super().__init__(message)
        self.candidates = candidates


class ValidationError(MdpmError):
    exit_code = 3


class PreconditionError(MdpmError):
    exit_code = 4


class ConflictError(MdpmError):
    exit_code = 5


# ---------------------------------------------------------------------------
# Project root discovery
# ---------------------------------------------------------------------------


def find_project_root(start: Path | None = None) -> Path:
    """Walk upward from `start` (or CWD) until a directory containing `tasks/`
    is found. Returns that directory. Raises NotFoundError if none found.
    """
    here = (start or Path.cwd()).resolve()
    for candidate in [here, *here.parents]:
        if (candidate / "tasks").is_dir():
            return candidate
    raise NotFoundError(
        f"no MDPM project (tasks/ directory) found at or above {here}"
    )


def find_mdpm_project(start: Path | None = None) -> Path | None:
    """Walk upward from `start` (or CWD) to a directory that has opted in to
    MDPM via `.mdpm/config.json`. Stricter than `find_project_root`: used
    where a bare `tasks/` folder in an unrelated repo must not count.
    """
    here = (start or Path.cwd()).resolve()
    for candidate in [here, *here.parents]:
        if (candidate / ".mdpm" / "config.json").is_file():
            return candidate
    return None


# ---------------------------------------------------------------------------
# Frontmatter parsing
# ---------------------------------------------------------------------------
#
# MDPM reads a deliberately small subset of YAML: `key: value` scalars, inline
# `[a, b]` lists, `- item` block lists, quoted strings, `#` comments, and
# `|` / `>` block scalars. Anything it rewrites goes through
# `merge_frontmatter`, which leaves every line it was not asked to change
# byte-identical — so YAML outside this subset survives a round trip even
# though MDPM cannot interpret it.


LIST_INLINE = re.compile(r"^\[(.*)\]$")
_BLOCK_SCALAR = re.compile(r"^[|>][+-]?$")
_DOUBLE_QUOTE_ESCAPES = {"n": "\n", "t": "\t", '"': '"', "\\": "\\"}


def _strip_comment(value: str) -> str:
    """Drop a trailing ` # comment`. A `#` only starts a comment at the start
    of the value or after whitespace, and never inside quotes."""
    quote = None
    i = 0
    while i < len(value):
        ch = value[i]
        if quote:
            if ch == "\\" and quote == '"':
                i += 1
            elif ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
        elif ch == "#" and (i == 0 or value[i - 1] in " \t"):
            return value[:i]
        i += 1
    return value


def _unquote_double(inner: str) -> str:
    out = []
    i = 0
    while i < len(inner):
        ch = inner[i]
        if ch == "\\" and i + 1 < len(inner):
            nxt = inner[i + 1]
            out.append(_DOUBLE_QUOTE_ESCAPES.get(nxt, "\\" + nxt))
            i += 2
        else:
            out.append(ch)
            i += 1
    return "".join(out)


def _coerce(value: str) -> Any:
    value = _strip_comment(value).strip()
    if value == "" or value.lower() in ("null", "~"):
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
    if len(value) >= 2 and value[0] == value[-1] == '"':
        return _unquote_double(value[1:-1])
    if len(value) >= 2 and value[0] == value[-1] == "'":
        return value[1:-1].replace("''", "'")
    return value


def _split_top_level(s: str, sep: str) -> list[str]:
    """Split on sep while respecting brackets/quotes (shallow)."""
    out, buf, depth, quote = [], [], 0, None
    i = 0
    while i < len(s):
        ch = s[i]
        if quote:
            buf.append(ch)
            if ch == "\\" and quote == '"' and i + 1 < len(s):
                buf.append(s[i + 1])
                i += 1
            elif ch == quote:
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
        i += 1
    if buf:
        out.append("".join(buf).strip())
    return out


def _split_document(text: str) -> tuple[list[str] | None, str]:
    """Return (frontmatter_lines, body). frontmatter_lines is None when the
    text has no well-formed `---` ... `---` block."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, text
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return lines[1:i], "\n".join(lines[i + 1 :])
    return None, text


def _is_key_line(line: str) -> bool:
    return bool(line) and line[0] not in " \t#-" and ":" in line


def _split_segments(fm_lines: list[str]) -> list[tuple[str | None, list[str]]]:
    """Group frontmatter lines into (key, lines) segments. A segment is a
    `key:` line plus the continuation lines under it; lines that belong to no
    key (leading comments, blanks) get key None."""
    segments: list[tuple[str | None, list[str]]] = []
    for line in fm_lines:
        if _is_key_line(line):
            segments.append((line.partition(":")[0].strip(), [line]))
        elif segments and not line.startswith("#"):
            segments[-1][1].append(line)
        else:
            segments.append((None, [line]))
    return segments


def _block_scalar(style: str, lines: list[str]) -> str:
    while lines and not lines[-1].strip():
        lines = lines[:-1]
    indent = min((len(ln) - len(ln.lstrip()) for ln in lines if ln.strip()), default=0)
    lines = [ln[indent:] if ln.strip() else "" for ln in lines]
    if style.startswith("|"):
        return "\n".join(lines)
    # Folded: single newlines become spaces, blank lines become newlines.
    paragraphs, current = [], []
    for ln in lines:
        if ln:
            current.append(ln.strip())
        else:
            paragraphs.append(" ".join(current))
            current = []
    paragraphs.append(" ".join(current))
    return "\n".join(paragraphs)


def _segment_value(lines: list[str]) -> Any:
    head = lines[0].partition(":")[2]
    rest = lines[1:]
    marker = _strip_comment(head).strip()
    if _BLOCK_SCALAR.match(marker):
        return _block_scalar(marker, rest)
    items = [ln.lstrip()[1:] for ln in rest if ln.lstrip().startswith("-")]
    if marker == "" and items:
        return [_coerce(item) for item in items]
    return _coerce(head)


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Return (frontmatter_dict, body_text). Frontmatter is empty dict if absent."""
    fm_lines, body = _split_document(text)
    if fm_lines is None:
        return {}, text
    data: dict = {}
    for key, lines in _split_segments(fm_lines):
        if key is not None:
            data[key] = _segment_value(lines)
    return data, body


# ---------------------------------------------------------------------------
# Frontmatter rendering
# ---------------------------------------------------------------------------


_NEEDS_QUOTES = set(":#{}[],&*!|>'\"%@`\n\t")
_RESERVED_WORDS = ("", "null", "~", "true", "false")


def _render_value(v: Any) -> str:
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, list):
        if not v:
            return "[]"
        return "[" + ", ".join(_render_value(x) for x in v) + "]"
    if isinstance(v, (int, float)):
        return str(v)
    s = str(v)
    # Quote anything the parser would otherwise read back as something else.
    if _NEEDS_QUOTES & set(s) or s != s.strip() or s.lower() in _RESERVED_WORDS:
        escaped = (
            s.replace("\\", "\\\\")
            .replace('"', '\\"')
            .replace("\n", "\\n")
            .replace("\t", "\\t")
        )
        return f'"{escaped}"'
    return s


def _ordered_keys(fm: dict) -> list[str]:
    """Keys in TASK_FIELD_ORDER first; unknown keys follow in insertion order."""
    known = [k for k in TASK_FIELD_ORDER if k in fm]
    return known + [k for k in fm if k not in known]


def render_frontmatter(fm: dict) -> str:
    """Render a frontmatter dict to a fresh `---\\n...\\n---\\n` block."""
    lines = ["---"]
    lines += [f"{key}: {_render_value(fm[key])}" for key in _ordered_keys(fm)]
    lines.append("---")
    return "\n".join(lines) + "\n"


def merge_frontmatter(original_text: str, fm: dict) -> str:
    """Render `fm` as a frontmatter block, reusing the lines of
    `original_text`'s frontmatter wherever a field's value is unchanged.

    Unchanged fields keep their exact original lines (comments, block lists,
    block scalars, spacing). Changed fields are re-rendered on one line. Fields
    absent from `fm` are dropped; fields new to `fm` are appended.
    """
    fm_lines, _ = _split_document(original_text)
    if fm_lines is None:
        return render_frontmatter(fm)
    out = ["---"]
    written = set()
    for key, lines in _split_segments(fm_lines):
        if key is None:
            out += lines
        elif key in fm:
            written.add(key)
            if _segment_value(lines) == fm[key]:
                out += lines
            else:
                out.append(f"{key}: {_render_value(fm[key])}")
    out += [f"{key}: {_render_value(fm[key])}" for key in _ordered_keys(fm) if key not in written]
    out.append("---")
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------------------
# Section utilities
# ---------------------------------------------------------------------------


_FENCE = re.compile(r"^\s{0,3}(`{3,}|~{3,})")


def _section_headers(body: str) -> list[tuple[str, int, int]]:
    """Return (name, header_start, header_end) for each `## Name` heading,
    skipping lines inside fenced code blocks."""
    headers = []
    fence = None
    pos = 0
    for line in body.splitlines(keepends=True):
        m = _FENCE.match(line)
        if m:
            marker = m.group(1)[0]
            if fence is None:
                fence = marker
            elif fence == marker:
                fence = None
        elif fence is None:
            h = SECTION_RE.match(line.rstrip("\r\n"))
            if h:
                headers.append((h.group(1).strip(), pos, pos + len(line.rstrip("\r\n"))))
        pos += len(line)
    return headers


def _section_span(body: str, name: str) -> tuple[int, int] | None:
    """Return (content_start, content_end) of the first `## name` section."""
    headers = _section_headers(body)
    for i, (title, _start, end) in enumerate(headers):
        if title.lower() == name.lower():
            next_start = headers[i + 1][1] if i + 1 < len(headers) else len(body)
            return end, next_start
    return None


def extract_section(body: str, name: str) -> str:
    """Return the content of a '## Name' section. Empty string if absent."""
    span = _section_span(body, name)
    return body[span[0] : span[1]].strip() if span else ""


def replace_section(body: str, name: str, new_content: str) -> str:
    """Replace a '## Name' section's content (everything from after the header
    up to the next '## ' or EOF). Appends the section at EOF if absent.
    """
    span = _section_span(body, name)
    if span:
        tail = body[span[1] :].lstrip()
        section = body[: span[0]] + "\n" + new_content.rstrip() + "\n"
        return section + ("\n" + tail if tail else "")
    # Section not found — append
    if body and not body.endswith("\n"):
        body += "\n"
    sep = "\n" if body and not body.endswith("\n\n") else ""
    return body + sep + f"## {name}\n{new_content.rstrip()}\n"


def append_worklog(body: str, entry: str, when: str | None = None) -> str:
    """Append a dated entry to the ## Work Log section. Creates the section
    if missing. `entry` should not include the leading '- ' or date.
    """
    when = when or date.today().isoformat()
    line = f"- {when}: {entry}"
    current = extract_section(body, "Work Log")
    if current:
        new_section = current.rstrip() + "\n" + line
    else:
        new_section = line
    return replace_section(body, "Work Log", new_section)


def count_acceptance(body: str) -> tuple[int, int]:
    ac = extract_section(body, "Acceptance Criteria")
    done = len(re.findall(r"^\s*-\s*\[x\]", ac, re.IGNORECASE | re.MULTILINE))
    todo = len(re.findall(r"^\s*-\s*\[ \]", ac, re.MULTILINE))
    return done, done + todo


# ---------------------------------------------------------------------------
# Filename convention
# ---------------------------------------------------------------------------


_SLUG_CHARS = re.compile(r"[^a-z0-9]+")


def slugify(text: str) -> str:
    s = text.lower().strip()
    s = _SLUG_CHARS.sub("-", s).strip("-")
    return s or "untitled"


def compute_filename(task_id: str, title: str) -> str:
    return f"{task_id}-{slugify(title)}.md"


# ---------------------------------------------------------------------------
# Atomic write
# ---------------------------------------------------------------------------


def atomic_write_text(path: Path, content: str) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    os.replace(tmp, path)


# ---------------------------------------------------------------------------
# Task loading
# ---------------------------------------------------------------------------


def load_task(path: Path, status_dir: str) -> dict:
    """Load a single task file into a dict suitable for JSON output."""
    text = path.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(text)
    ac_done, ac_total = count_acceptance(body)
    objective = extract_section(body, "Objective")
    notes = extract_section(body, "Notes")
    worklog = extract_section(body, "Work Log")

    latest_log = ""
    for line in reversed(worklog.splitlines()):
        if line.strip().startswith("-"):
            latest_log = line.strip().lstrip("- ").strip()
            break

    today = date.today().isoformat()
    due = fm.get("due")
    overdue = bool(
        due and isinstance(due, str) and due < today and status_dir not in ("done", "archive")
    )

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
        "acceptance": {"done": ac_done, "total": ac_total},
        "latest_log": latest_log,
        "filename": path.name,
        "path": str(path),
        "frontmatter": fm,
        "body": body,
    }


def load_all_tasks(root: Path, include_archive: bool = False) -> list[dict]:
    tasks: list[dict] = []
    base = root / "tasks"
    if not base.exists():
        return tasks
    dirs = list(ALL_STATUS_DIRS) if include_archive else list(STATUS_DIRS)
    for status in dirs:
        sdir = base / status
        if not sdir.is_dir():
            continue
        for path in sorted(sdir.glob("*.md")):
            tasks.append(load_task(path, status))
    return tasks


# ---------------------------------------------------------------------------
# Lookup
# ---------------------------------------------------------------------------


def find_task_by_ref(
    root: Path, ref: str, include_archive: bool = True
) -> dict:
    """Find a task by exact ID or unique title substring (case-insensitive).
    Raises NotFoundError or AmbiguousRefError.
    """
    tasks = load_all_tasks(root, include_archive=include_archive)
    ref_lower = ref.strip().lower()

    # Exact ID match first
    for t in tasks:
        if t["id"] and t["id"].lower() == ref_lower:
            return t

    # Then fuzzy match on ID prefix + title substring
    fuzzy = [
        t for t in tasks
        if (t["id"] and ref_lower in t["id"].lower())
        or ref_lower in (t["title"] or "").lower()
        or ref_lower in t["filename"].lower()
    ]
    if not fuzzy:
        raise NotFoundError(f"no task matches {ref!r}")
    if len(fuzzy) > 1:
        candidates = [{"id": t["id"], "title": t["title"], "status": t["status_dir"]} for t in fuzzy]
        raise AmbiguousRefError(
            f"{len(fuzzy)} tasks match {ref!r}; be more specific",
            candidates=candidates,
        )
    return fuzzy[0]


# ---------------------------------------------------------------------------
# ID generation
# ---------------------------------------------------------------------------


def load_config(root: Path) -> dict:
    cfg_path = root / ".mdpm" / "config.json"
    if not cfg_path.exists():
        return {}
    try:
        return json.loads(cfg_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


_ID_PATTERN = re.compile(r"^([A-Za-z]+-)(\d+)$")


def detect_id_prefix(root: Path) -> str:
    """Return the ID prefix for new tasks. Falls back to PRJ-."""
    cfg = load_config(root)
    if cfg.get("id_prefix"):
        return cfg["id_prefix"]
    # Scan existing task IDs
    for t in load_all_tasks(root, include_archive=True):
        if t["id"]:
            m = _ID_PATTERN.match(t["id"])
            if m:
                return m.group(1)
    return "PRJ-"


def next_task_id(root: Path, prefix: str | None = None) -> str:
    prefix = prefix or detect_id_prefix(root)
    max_n = 0
    for t in load_all_tasks(root, include_archive=True):
        if not t["id"]:
            continue
        m = _ID_PATTERN.match(t["id"])
        if m and m.group(1).lower() == prefix.lower():
            max_n = max(max_n, int(m.group(2)))
    return f"{prefix}{max_n + 1:03d}"


# ---------------------------------------------------------------------------
# Mutations
# ---------------------------------------------------------------------------


def write_task_file(path: Path, fm: dict, body: str) -> None:
    """Atomically write a task file. Ensures body has a trailing newline.

    If the file already exists, frontmatter lines whose values are unchanged
    are preserved verbatim (see `merge_frontmatter`).
    """
    if not body.endswith("\n"):
        body = body + "\n"
    original = path.read_text(encoding="utf-8") if path.exists() else ""
    content = merge_frontmatter(original, fm) + "\n" + body.lstrip("\n")
    atomic_write_text(path, content)


def move_task(root: Path, task: dict, new_status: str) -> Path:
    """Move a task's file to tasks/<new_status>/ and update status field.
    Returns the new absolute path. Does NOT touch the work log — caller decides.
    """
    if new_status not in ALL_STATUS_DIRS:
        raise ValidationError(f"unknown status {new_status!r} (valid: {', '.join(ALL_STATUS_DIRS)})")
    src = Path(task["path"])
    dst_dir = root / "tasks" / new_status
    dst_dir.mkdir(parents=True, exist_ok=True)
    dst = dst_dir / src.name
    if src == dst:
        return dst
    if dst.exists():
        raise ConflictError(f"target {dst} already exists")

    # Update frontmatter status field
    fm = dict(task["frontmatter"])
    fm["status"] = new_status if new_status != "archive" else fm.get("status", "done")
    fm["updated"] = date.today().isoformat()
    write_task_file(src, fm, task["body"])

    os.replace(src, dst)
    return dst


def rename_for_title(path: Path, new_title: str, task_id: str) -> Path:
    """Rename a file in place to match <ID>-<slug>.md based on new title."""
    new_name = compute_filename(task_id, new_title)
    if new_name == path.name:
        return path
    new_path = path.with_name(new_name)
    if new_path.exists():
        raise ConflictError(f"target filename {new_path.name} already exists")
    os.replace(path, new_path)
    return new_path


def dependents_of(root: Path, task_id: str, status_filter: tuple[str, ...] = ("backlog", "active", "inbox")) -> list[dict]:
    """Return tasks in the given status dirs that have `task_id` in depends_on."""
    return [
        t
        for t in load_all_tasks(root)
        if t["status_dir"] in status_filter and task_id in (t["depends_on"] or [])
    ]


def newly_unblocked(root: Path, just_completed_id: str) -> list[dict]:
    """Among tasks that depended on `just_completed_id`, return those whose
    OTHER dependencies are all done too (so they're now fully unblocked).
    """
    all_tasks = load_all_tasks(root, include_archive=True)
    done_ids = {t["id"] for t in all_tasks if t["status_dir"] in ("done", "archive") and t["id"]}
    # Include the just-completed task since by the time this is called it may be in done/
    done_ids.add(just_completed_id)

    result = []
    for t in all_tasks:
        if t["status_dir"] not in ("backlog", "active", "inbox"):
            continue
        deps = t["depends_on"] or []
        if just_completed_id not in deps:
            continue
        if all(d in done_ids for d in deps):
            result.append(t)
    return result


def find_dependency_cycle(
    root: Path, task_id: str, new_deps: list[str]
) -> list[str] | None:
    """Check whether assigning `new_deps` to `task_id` would create a cycle.

    Returns a cycle path (list of IDs starting and ending at `task_id`) if a
    cycle is found, else None. Works by walking transitive dependencies of
    each proposed dep and checking if any path reaches back to `task_id`.
    """
    all_tasks = load_all_tasks(root, include_archive=True)
    deps_by_id: dict[str, list[str]] = {
        t["id"]: list(t.get("depends_on") or []) for t in all_tasks if t["id"]
    }
    # Apply the proposed change to our local graph view
    deps_by_id[task_id] = list(new_deps)

    # DFS from each new dep; if we hit task_id, we found a cycle.
    for start in new_deps:
        if start == task_id:
            return [task_id, task_id]
        stack: list[tuple[str, list[str]]] = [(start, [task_id, start])]
        visited = {task_id}
        while stack:
            cur, path = stack.pop()
            if cur == task_id:
                return path
            if cur in visited:
                continue
            visited.add(cur)
            for dep in deps_by_id.get(cur, []):
                if dep == task_id:
                    return path + [dep]
                if dep not in visited:
                    stack.append((dep, path + [dep]))
    return None


# ---------------------------------------------------------------------------
# Public for diagnostics
# ---------------------------------------------------------------------------

__all__ = [
    "STATUS_DIRS",
    "ALL_STATUS_DIRS",
    "TASK_FIELD_ORDER",
    "MdpmError",
    "NotFoundError",
    "AmbiguousRefError",
    "ValidationError",
    "PreconditionError",
    "ConflictError",
    "find_project_root",
    "find_mdpm_project",
    "parse_frontmatter",
    "render_frontmatter",
    "merge_frontmatter",
    "extract_section",
    "replace_section",
    "append_worklog",
    "count_acceptance",
    "slugify",
    "compute_filename",
    "atomic_write_text",
    "load_task",
    "load_all_tasks",
    "find_task_by_ref",
    "load_config",
    "detect_id_prefix",
    "next_task_id",
    "write_task_file",
    "move_task",
    "rename_for_title",
    "dependents_of",
    "newly_unblocked",
    "find_dependency_cycle",
]
