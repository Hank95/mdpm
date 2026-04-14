---
name: pm:status
description: Show project dashboard — active work, upcoming priorities, and blockers
argument-hint: ""
disable-model-invocation: true
---

# /pm:status

Read the project's task state and produce a concise dashboard for the user.

## Steps

1. **Check the tracking layout.** Confirm that `tasks/active/`, `tasks/backlog/`, `tasks/done/`, and `tasks/inbox/` exist. If `tasks/` does not exist at all, tell the user MDPM has not been initialized and suggest running `/pm:config`.

2. **Read `docs/ROADMAP.md`** to identify the current milestone.

3. **Scan each status directory** and collect task metadata from YAML frontmatter:
   - `tasks/active/*.md` — in-progress work
   - `tasks/backlog/*.md` — queued work (sort by priority, then `created` date)
   - `tasks/inbox/*.md` — untriaged incoming requests
   - `tasks/done/*.md` — only count for a "recently completed" tally (items updated in the last 7 days)

4. **Identify blockers.** Any task with `status: blocked` in frontmatter, or any active task whose `depends_on` references a task not in `done/`.

5. **Check for overdue tasks** — any active or backlog task with a `due:` date earlier than today.

6. **Produce the dashboard** using this format:

```
# Project Status — <current milestone from ROADMAP>

## Active (<count>)
- [PRJ-123] Title — priority, assigned_to, due YYYY-MM-DD
  Last log: <most recent work log entry>

## Up Next (top 3 from backlog, sorted by priority)
- [PRJ-124] Title — priority, tags
- ...

## Inbox (<count> untriaged)
- <titles only, no detail — suggest /pm:inbox to triage>

## Blockers
- [PRJ-123] blocked on [PRJ-099] "<title of dep>"

## Overdue
- [PRJ-123] was due YYYY-MM-DD

## Recently Shipped (last 7 days)
- [PRJ-120] Title — YYYY-MM-DD
```

7. **Be terse.** Single-line entries unless there's a blocker that needs explaining. No filler.

## Notes

- If there's nothing in a section, omit the section entirely rather than saying "None".
- Don't modify any files. This command is read-only.
