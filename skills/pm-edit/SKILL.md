---
name: pm:edit
description: Edit a task's metadata (priority, due date, tags, assignee, dependencies)
argument-hint: "<task id or partial title> [field=value ...]"
---

# /pm:edit

Edit frontmatter fields on an existing task. `$ARGUMENTS` is the ID or title fragment, optionally followed by field updates.

## How to run

Delegate to the CLI — it validates values, preserves field order in the frontmatter, bumps `updated`, appends a work log entry summarizing the change, and renames the file if the title changed:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/mdpm" edit <ref> \
  [--title "New Title"] \
  [--priority high|medium|low] \
  [--due YYYY-MM-DD | --due null] \
  [--tags a,b,c | --tags null] \
  [--depends PRJ-001,PRJ-002 | --depends null] \
  [--assigned-to "Name" | --assigned-to null] \
  [--jira-id ENG-451 | --jira-id null] \
  [--wrike-id 12345 | --wrike-id null] \
  [--note "extra work log entry"] \
  --json
```

## Parsing the user's prompt

Accept natural phrasing and map to CLI flags. Examples:

- "bump PRJ-042 to high priority" → `--priority high`
- "change PRJ-042 due to next Friday" → resolve to ISO date → `--due 2026-04-25`
- "tag PRJ-042 with auth and security" → `--tags auth,security`
  - If the user says "also tag", read current tags via `mdpm show <ref> --json`, append the new ones, pass the full list.
- "assign PRJ-042 to Danny" → `--assigned-to Danny`
- "clear the due date" / "remove the assignee" → pass `null` to the relevant flag
- "rename PRJ-042 to 'Add MFA to login'" → `--title "Add MFA to login"` (the CLI renames the file automatically)

## Interpreting the result

- **ok: true, changes: {...}** — summarize what changed. Concise, one line per field.
- **warnings: ["no fields changed"]** — the user asked for a no-op. Say so and show the current values.
- **ok: false, error: "validation_error"** — usually a bad priority or date format. Relay the CLI message.

## Immutable fields

The CLI refuses to change `id`, `created`, or `status` via `edit`. For status transitions, use `/pm:start`, `/pm:done`, `/pm:block`, or `/pm:move`.

## Notes

- If the user wants to edit the task body (Objective / Acceptance Criteria / Notes), that's NOT a frontmatter edit. Use the Edit tool on the file directly — or suggest they open the task in the kanban board (`python3 board/serve.py`) where the modal has an Edit button.
- `--note` is separate from field changes. Use it when the user wants an arbitrary work-log entry alongside a metadata edit (e.g. "bump to high priority — customer escalated").
