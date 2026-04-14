---
name: pm:inbox
description: Triage incoming requests in tasks/inbox/ — one at a time
argument-hint: ""
disable-model-invocation: true
---

# /pm:inbox

Walk through `tasks/inbox/` one item at a time and decide what to do with each.

## Steps

1. **List inbox contents.**
   - If `tasks/inbox/` is empty or missing, say so and exit. Optionally, offer to pull new items from Jira/Wrike via `/pm:sync-jira` or `/pm:sync-wrike`.

2. **Sort inbox** by `created` date ascending (oldest first — stop things from rotting).

3. **For each item**, show this summary to the user:

   ```
   ## Inbox item 1 of N: [PRJ-INBOX-003] Short title
   Source: <from jira_id or wrike_id if present, else "direct">
   Created: YYYY-MM-DD

   <Objective section, truncated to ~3 lines>

   **Triage options:**
   a) Accept → move to backlog (set priority, tags, due)
   b) Start now → move directly to active
   c) Plan → run /pm:plan to decompose
   d) Reject → delete (or archive if synced to Jira/Wrike)
   e) Snooze → leave in inbox, move on
   f) Delegate → set assigned_to and leave in backlog
   ```

4. **Process the user's choice**:
   - **Accept:** Ask for priority (default medium), tags, optional due date. Update frontmatter. Assign a real task ID (replace any `PRJ-INBOX-*` placeholder with the next sequential `PRJ-XXX`). Rename the file to `<new-id>-<slug>.md` to match the MDPM filename convention. Move to `tasks/backlog/`.
   - **Start now:** Same as Accept (including the filename rename), but move to `tasks/active/` and set `status: active`. Append work log entry: "Triaged from inbox, started work."
   - **Plan:** Keep the inbox file in place, invoke `/pm:plan` logic on its contents. After planning, move the original inbox item to `done/` with a work log entry "Replaced by decomposition into PRJ-XXX, PRJ-YYY."
   - **Reject:** Confirm with the user. If the task has a `jira_id` or `wrike_id`, offer to close it in the external system via sync. Then delete the file (inbox is the ONLY directory where deletion is allowed).
   - **Snooze:** No change. Move to next item.
   - **Delegate:** Ask for assignee name, set `assigned_to`, move to `tasks/backlog/`.

5. **After each item**, pause and move to the next. Don't batch decisions — the user processes one at a time.

6. **At the end**, summarize:
   ```
   Inbox triage complete:
   - N accepted to backlog
   - N started (moved to active)
   - N rejected
   - N snoozed (still in inbox)
   ```

## Notes

- Inbox items may have been created by `/pm:sync-jira` or `/pm:sync-wrike` (pulled from external systems). Preserve their `jira_id` / `wrike_id` when moving them to backlog.
- Rejection is the **only** time a task file can be deleted. Every other state moves files between directories.
- If the user wants to bulk-approve ("accept all as medium priority"), that's fine — but still apply per-item checks for `depends_on` and tags.
