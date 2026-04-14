---
name: pm:new
description: Create a new task file in tasks/backlog/ with auto-incrementing ID
argument-hint: "<task title or description>"
disable-model-invocation: true
---

# /pm:new

Create a new task. Arguments `$ARGUMENTS` are the task title / brief description.

## Steps

1. **Ensure the task layout exists.** Create `tasks/backlog/` if missing.

2. **Determine the ID prefix.**
   - Check `.mdpm/config.json` for `id_prefix` if it exists.
   - Otherwise, scan existing tasks for an existing `id:` pattern and reuse it.
   - Fall back to `PRJ-` if no convention exists, but ask the user first if this is the very first task.

3. **Determine the next ID number.**
   - Scan all `tasks/**/*.md` files, extract the numeric portion of every `id:` field.
   - Pick `max(n) + 1`, zero-padded to 3 digits (e.g. `PRJ-001`, `PRJ-042`).

4. **Parse the title.** `$ARGUMENTS` is the raw description. Derive:
   - A short, descriptive `title:` (5-10 words)
   - A filename: `<ID>-<kebab-case slug>.md` (e.g. `PRJ-002-add-user-login.md`). The ID prefix in the filename makes tasks sortable via `ls` and greppable by ID. Never omit it.
   - If the user's message contains obvious priority hints ("urgent", "high-pri"), set priority accordingly. Otherwise default to `medium`.

5. **Ask the user for anything unclear** — only if necessary. Don't pepper them with questions for trivial tasks. Minimum viable task needs: title, priority, and a rough objective. Tags, due dates, and dependencies can be left empty.

6. **Write the file** to `tasks/backlog/<ID>-<slug>.md` using this template:

```markdown
---
id: PRJ-XXX
title: <derived title>
priority: medium
status: backlog
created: <today YYYY-MM-DD>
updated: <today YYYY-MM-DD>
due: null
tags: []
depends_on: []
assigned_to: <from config, else empty>
wrike_id: null
jira_id: null
jira_project: null
---

# <title>

## Objective
<1-3 sentences restating what this task is for. Derived from $ARGUMENTS.>

## Acceptance Criteria
- [ ] <first acceptance criterion, if obvious from the description>
- [ ] <add more as placeholders if the user should fill them in>

## Notes
<Any context the user provided, or leave a placeholder>

## Work Log
- <today YYYY-MM-DD>: Task created
```

7. **Confirm.** Tell the user the file path and ID you created, and offer to open `/pm:plan` if the task looks like it needs decomposition.

## Notes

- Do not start the task (don't move to `active/`). That's a separate intentional action.
- Never reuse an ID. If you're uncertain, scan all directories including `done/`.
