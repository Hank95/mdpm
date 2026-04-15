---
name: pm:search
description: Search tasks by title, tag, ID, assignee, or content
argument-hint: "<query> [--status <state>] [--tag <tag>]"
---

# /pm:search

Find tasks matching a query. `$ARGUMENTS` is the search expression.

## How to run

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/mdpm" search "<query>" [--status S] [--tag T] [--assignee N] --json
```

## Parsing the user's prompt

Extract the query and any filter hints:

- "find tasks about authentication" → `search "authentication"`
- "what's in the backlog about gallery" → `search "gallery" --status backlog`
- "anything assigned to Danny" → `search "" --assignee Danny` (query can be empty — filters narrow)
- "#frontend tasks" → `search "" --tag frontend`

## Interpreting the result

Show the hits grouped by status (active first, then backlog, inbox, done, archive), with the matched field (title/tags/id/body) annotated. Keep it scannable — don't print task bodies. Example:

```
Found 3 matches for "gallery":

ACTIVE
  [PRJ-042] Gallery Page Component — matched in: title, tags[gallery]

BACKLOG
  [PRJ-055] Gallery analytics hooks — matched in: body

DONE
  [PRJ-001] Old gallery spec — 2026-04-10 — matched in: title
```

- No hits → say so. Suggest broadening with `--status all` or dropping filters.
- More than ~15 results → show the top 10 and tell the user how to narrow (tag, status, assignee).

## Notes

- Read-only. Never modify task files.
- The CLI searches across all directories including `archive/` by default. That's usually what the user wants.
