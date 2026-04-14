---
name: pm:status
description: Show project dashboard — active work, upcoming priorities, and blockers
argument-hint: ""
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

4. **Identify blockers vs waiting tasks.** Two distinct concepts:
   - **Blocked** — a task with `status: blocked` in frontmatter. Something external (review, external team, missing info) is stopping progress. These deserve attention.
   - **Waiting** — a task whose `depends_on` references another task not yet in `done/`, but the dependency is itself in `backlog/` or `active/` (i.e. just hasn't shipped yet). These are sequenced, not stuck. Don't mix them with blockers.
   - **Orphaned** — `depends_on` references an ID that doesn't exist anywhere. Call this out separately as a data issue.

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
- [PRJ-123] blocked — <reason from work log or notes>

## Waiting on upstream
- [PRJ-123] waiting on [PRJ-099] "<title of dep>" (<status of dep>)

## Overdue
- [PRJ-123] was due YYYY-MM-DD

## Recently Shipped (last 7 days)
- [PRJ-120] Title — YYYY-MM-DD
```

7. **Be terse.** Single-line entries unless there's a blocker that needs explaining. No filler.

## Notes

- If there's nothing in a section, omit the section entirely rather than saying "None".
- Don't modify any files. This command is read-only.
