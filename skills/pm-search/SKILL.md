---
name: pm:search
description: Search tasks by title, tag, ID, assignee, or content
argument-hint: "<query> [--status <state>] [--tag <tag>]"
disable-model-invocation: true
---

# /pm:search

Find tasks matching a query. `$ARGUMENTS` is the search expression.

## Steps

1. **Parse arguments.**
   - The first positional token(s) are the query string (may be multi-word).
   - Optional flags:
     - `--status <inbox|backlog|active|done|archive|all>` — restrict to a status (default: `all`).
     - `--tag <tag>` — only tasks whose `tags` contain this value.
     - `--assignee <name>` — only tasks assigned to this person.
     - `--id` — query is an ID pattern (exact or prefix match like `PRJ-0*`).

2. **Determine search scope** based on `--status`. Default searches all of `tasks/{inbox,backlog,active,done,archive}/`.

3. **Match strategy.** A task matches if any of these are true (unless flags narrow the search):
   - The query (case-insensitive) appears in `id`, `title`, `tags`, `assigned_to`, or the body text (objective, notes, acceptance criteria, work log).
   - For `--id` mode, match the `id:` field only, supporting simple glob patterns.
   - Tag/assignee filters are AND-combined with the query.

4. **Rank results.**
   1. Exact ID match first.
   2. Title match second.
   3. Tag match third.
   4. Body content match last.
   Within a tier, sort by status (`active` → `backlog` → `inbox` → `done` → `archive`), then by `updated` desc.

5. **Output** — concise, 1-3 lines per hit:
   ```
   Found N matches for "<query>":

   ACTIVE
     [PRJ-042] Add user login — priority:high due:2026-05-01
       Matched in: title, tags[auth]

   BACKLOG
     [PRJ-055] Password reset flow — priority:medium
       Matched in: body

   DONE
     [PRJ-001] Gallery page component — 2026-04-28
   ```

6. **If nothing matches**, say so and suggest:
   - Broadening with `--status all`
   - Removing tag/assignee filters
   - Running `/pm:status` to see what exists overall

## Notes

- Read-only. Never modify task files.
- For large repos, cap output at ~20 results and tell the user how to narrow further.
- Don't show full task bodies — only the matched context (a line or two of snippet is fine).
