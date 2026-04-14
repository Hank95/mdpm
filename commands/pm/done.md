---
description: Complete a task — move to tasks/done/, append final work log, check for unblocked dependents
argument-hint: "<task id or partial title>"
---

# /pm:done

Mark a task complete. Argument `$ARGUMENTS` identifies the task (ID like `PRJ-123`, or a partial title match).

## Steps

1. **Locate the task file.**
   - First check `tasks/active/` — completing a task from there is the common path.
   - If not found, check `tasks/backlog/` and `tasks/inbox/` (rare but valid — skipping states is allowed).
   - If multiple matches, list them and ask the user which one.
   - If no `$ARGUMENTS` given, list everything in `tasks/active/` and ask which to close.

2. **Check acceptance criteria.**
   - Parse the `## Acceptance Criteria` section.
   - If any `- [ ]` items remain unchecked, show them to the user and ask whether to:
     a) Mark them complete now
     b) Remove them (if no longer relevant)
     c) Proceed anyway (acknowledging they weren't met)
   - Only proceed once the user confirms.

3. **Update frontmatter:**
   - `status: done`
   - `updated: <today YYYY-MM-DD>`

4. **Append a work log entry** with today's date and a brief summary of what was shipped. Derive it from the most recent work log entries plus any context the user provides. Example:
   ```
   - 2026-04-14: Completed. Shipped lightbox component, deployed to staging.
   ```

5. **Move the file** from its current directory to `tasks/done/`. Preserve the filename.

6. **Check for unblocked dependents.** Scan all remaining tasks in `backlog/`, `active/`, and `inbox/` for any whose `depends_on` list includes this task's ID. For each match:
   - Note that the dependency is now satisfied.
   - If ALL of its `depends_on` entries are now in `done/`, point it out to the user as newly unblocked and available to start.

7. **Update `docs/CHANGELOG.md`.** Append an entry under today's date in the Added/Changed/Fixed section that best fits. If there's no section for today yet, create one.

8. **Report back:**
   ```
   ✓ [PRJ-123] Task Title — moved to tasks/done/

   Unblocked by this completion:
   - [PRJ-125] Next thing — ready to start
   ```

9. **Offer follow-up.** If there are newly-unblocked tasks, ask if they want to run `/pm:next`. If a stakeholder sync is configured, offer `/pm:sync-jira` or `/pm:sync-wrike` to push the completion.

## Notes

- **Never delete the task file.** It moves to `done/`, stays there forever.
- The work log is append-only. Never rewrite prior entries.
- If the task has a `jira_id` or `wrike_id`, mention it so the user knows a sync will close the external issue too.
