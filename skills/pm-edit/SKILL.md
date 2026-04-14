---
name: pm:edit
description: Edit a task's metadata (priority, due date, tags, assignee, dependencies)
argument-hint: "<task id or partial title> [field=value ...]"
---

# /pm:edit

Edit frontmatter fields on an existing task without disturbing the body.

`$ARGUMENTS` is an ID or title fragment, optionally followed by `key=value` pairs for one-shot edits. Examples:

- `/pm:edit PRJ-042` → interactive mode
- `/pm:edit PRJ-042 priority=high due=2026-05-01`
- `/pm:edit login tags=[auth,security] assigned_to=Danny`

## Steps

1. **Locate the task** across all of `tasks/{inbox,backlog,active,done,archive}/`. If multiple matches, list them and ask which. If not found, report that.

2. **Parse any inline field assignments** from `$ARGUMENTS`. Supported editable fields:
   - `priority` — one of `high`, `medium`, `low`
   - `due` — `YYYY-MM-DD` or `null` to clear
   - `tags` — list (e.g. `[a, b, c]`)
   - `assigned_to` — name or `null`
   - `depends_on` — list of IDs
   - `title` — short descriptive title (also renames the file slug)
   - `jira_id`, `jira_project`, `wrike_id` — external sync links
   - `status` — only accept `blocked` here; other status changes happen via `/pm:start` / `/pm:done`.

3. **If no inline assignments were provided**, enter interactive mode:
   - Show the current frontmatter values.
   - Ask which fields to change, one at a time.
   - Don't fire off a survey — accept short answers and move on.

4. **Validate.** Before writing:
   - `priority` must be one of the allowed values.
   - `due` must parse as a date.
   - `depends_on` IDs should exist somewhere under `tasks/` — warn if not, but allow it (user may be planning ahead).
   - `status: blocked` requires a reason; prompt for one and append to the Work Log.

5. **Update the file:**
   - Modify frontmatter in place — preserve field order and any comments.
   - Set `updated:` to today's date.
   - If `title` changed, regenerate the filename slug and `git mv` the file so the new name matches `<ID>-<new-slug>.md`.
   - Append a Work Log entry summarizing the edit:
     ```
     - <today>: Edited — priority high→medium, added tag "security"
     ```

6. **Confirm** with a compact before/after diff of the fields that changed.

## Notes

- **Do not edit Acceptance Criteria, Objective, Notes, or Work Log content** via this skill. Those are body edits — the user can open the file directly, or we can add a dedicated body-edit skill later.
- **Don't change `id:` ever.** IDs are immutable. If the user asks, refuse and explain.
- **Don't change `created:`.** Only `updated:` moves.
- **Status transitions:** `backlog → active` uses `/pm:start`; `active → done` uses `/pm:done`. This skill only handles `→ blocked` transitions (and clearing `blocked` back to whatever was before).
