---
name: pm:start
description: Move a task from backlog to active and begin work
argument-hint: "<task id or partial title>"
disable-model-invocation: true
---

# /pm:start

Move a task into `tasks/active/` and officially begin work on it. Argument `$ARGUMENTS` identifies the task (ID like `PRJ-123`, or partial title match).

## Steps

1. **Locate the task.**
   - First check `tasks/backlog/` for an exact ID or title match.
   - If not found there, check `tasks/inbox/` (implicitly triage-and-start in one move).
   - If multiple matches, list them and ask which one.
   - If no `$ARGUMENTS` given, list everything in `tasks/backlog/` sorted by priority and ask which to start.

2. **Check dependencies.**
   - Read `depends_on` from the task's frontmatter.
   - For each ID, verify it exists in `tasks/done/`. If any are missing (still in `backlog/`, `active/`, or orphaned), warn the user and ask:
     a) Start anyway (ignore the dependency gap)
     b) Cancel and start a different task
     c) Start the dependency first (suggest running `/pm:start <dep-id>` instead)
   - If the task has `status: blocked` in frontmatter, flag that explicitly — starting a blocked task usually means the user is clearing the blocker. Ask if the block is actually resolved.

3. **Update frontmatter:**
   - `status: active`
   - `updated: <today YYYY-MM-DD>`

4. **Append a work log entry:**
   ```
   - <today YYYY-MM-DD>: Started work.
   ```
   If the user supplied context in `$ARGUMENTS` beyond the ID (e.g. "start PRJ-123 — picking up after design review"), include it in the log entry.

5. **Move the file** from its current directory (usually `tasks/backlog/`) to `tasks/active/`. Preserve the `<ID>-<slug>.md` filename.

6. **Confirm** and orient the user:
   ```
   ✓ [PRJ-123] Task Title — now active

   Objective: <first sentence of Objective section>

   Acceptance Criteria:
   - [ ] ...
   - [ ] ...

   Ready. What do you want to tackle first?
   ```

## Notes

- Don't edit the Objective / Acceptance Criteria / Notes sections — this skill only moves the file and appends to the Work Log.
- If there's already active work, point it out but don't block the user. Context-switching is sometimes the right call; they'll decide.
- Never move a task from `done/` back to `active/`. If the user wants to reopen shipped work, they should create a new follow-up task (`/pm:new`) referencing the original.
