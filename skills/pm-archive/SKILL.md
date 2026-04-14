---
name: pm:archive
description: Move aged completed tasks from tasks/done/ to tasks/archive/ to reduce clutter
argument-hint: "[--older-than <days>] [--tag <tag>] [--all]"
---

# /pm:archive

Archive tasks from `tasks/done/` into `tasks/archive/`. Archived tasks are still on disk, still searchable via `/pm:search`, just moved out of the primary view so `/pm:status` and the board stay focused on current work.

`$ARGUMENTS` parsing:
- `--older-than <days>` — archive done tasks whose `updated:` date is more than N days ago (default: 30).
- `--tag <tag>` — only archive tasks with this tag.
- `--all` — archive everything currently in `done/` regardless of age.

## Steps

1. **Ensure `tasks/archive/` exists.** Create it (with `.gitkeep`) if missing.

2. **Select candidates** from `tasks/done/` based on the flags above. If no flags given, use `--older-than 30`.

3. **Preview.** Show the user a compact list:
   ```
   Archiving 12 tasks (completed > 30 days ago):

   - [PRJ-001] Gallery page component — 2026-03-15
   - [PRJ-004] Nav bar refactor — 2026-03-18
   - ...

   Proceed? [y/N]
   ```
   Wait for confirmation. Never archive silently.

4. **On confirm**, for each task:
   - Move the file from `tasks/done/` to `tasks/archive/`. Preserve the `<ID>-<slug>.md` filename.
   - Append a Work Log entry:
     ```
     - <today>: Archived.
     ```

5. **Update `docs/CHANGELOG.md` is NOT required** — archival isn't a shipping event. Just move the files.

6. **Report:**
   ```
   ✓ Archived 12 tasks to tasks/archive/
   Still in tasks/done/: 4 tasks (completed within last 30 days)
   ```

## Notes

- **Never delete.** Archival is just a directory move.
- **Never archive tasks outside `done/`.** Active or backlog tasks don't belong in archive.
- Archived tasks should still be visible in `/pm:search` when the user passes `--status archive` or `--status all` (the search skill already covers this).
- The kanban board (`board/board.html`) intentionally does NOT show archived tasks — that's the whole point of archiving.
