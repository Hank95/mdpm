---
name: pm:archive
description: Move aged completed tasks from tasks/done/ to tasks/archive/ to reduce clutter
argument-hint: "[--older-than <days>] [--tag <tag>] [--all]"
---

# /pm:archive

Move tasks from `tasks/done/` into `tasks/archive/` to reduce clutter while keeping them searchable.

## How to run

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/mdpm" --json archive [--older-than N] [--tag T] [--all]
```

Default: `--older-than 30` (tasks completed more than 30 days ago).

## Pre-flight confirmation

**Always preview before running.** Archival is a bulk operation — show the user what's about to move:

1. Run `mdpm --json list --status done` and filter by the same criteria (`--older-than` → compare `updated` against today minus N days).
2. Show a compact list:
   ```
   Archiving N tasks (completed > 30 days ago):
     - [PRJ-001] Gallery page component — 2026-03-15
     - [PRJ-004] Nav bar refactor — 2026-03-18
     ...
   Proceed? [y/N]
   ```
3. If the user confirms, run the CLI. Otherwise stop.

## Interpreting the result

- `count: N, moved: [...]` — confirm with a one-line summary: "Archived N tasks. Still in done/: M tasks completed within the last 30 days."
- `warnings: ["no eligible tasks to archive"]` — say so and suggest checking `mdpm list --status done` to see what's there.

## Notes

- **Never delete.** Archival is just a file move; archived tasks remain searchable via `mdpm search`.
- Don't archive tasks that aren't in `tasks/done/`. The CLI enforces this, but don't suggest otherwise.
- The kanban board excludes the archive column by design — the point of archiving is to stay focused on current work.
