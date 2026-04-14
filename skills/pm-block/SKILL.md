---
name: pm:block
description: Mark a task as blocked with a reason appended to the work log
argument-hint: "<task id or partial title> [reason]"
disable-model-invocation: true
---

# /pm:block

Mark a task as blocked. Use this when progress is stopped by something external — a review you're waiting on, a missing design decision, an API that's down, another team's work, a teammate out sick.

Don't confuse **blocked** (external obstacle) with **waiting** (depends_on not yet shipped — that's just sequenced work, not stuck). If the task is just waiting for an upstream backlog item, don't block it.

`$ARGUMENTS`:
- First token(s) are the task ID (e.g. `PRJ-042`) or a title fragment.
- Everything after is the reason. If no reason is given, ask the user for one — `blocked` without context is noise in `/pm:status`.

## Steps

1. **Locate the task.** Search `tasks/active/` first (most common), then `tasks/backlog/`. If multiple matches, list and ask. If no match, report and stop.

2. **Refuse if the task is in `done/` or `archive/`.** You can't block a completed task. Suggest `/pm:new` for a follow-up or `/pm:edit` to adjust metadata.

3. **Get the reason.** Parse from `$ARGUMENTS` if present. Otherwise ask:
   > What's blocking this? (One sentence — e.g. "waiting on security review from Alice", "API credentials expired", "design not approved yet")

4. **Update frontmatter:**
   - `status: blocked`
   - `updated: <today YYYY-MM-DD>`
   - Do NOT move the file. A blocked task stays where it was (usually `active/`) — moving it would hide it from the active queue and bury it in backlog. The directory keeps it visible; the `status` field + `/pm:status` surface the block.

5. **Append a work log entry:**
   ```
   - <today YYYY-MM-DD>: Blocked — <reason>.
   ```

6. **Confirm:**
   ```
   ⛔ [PRJ-042] Task Title — marked blocked.
   Reason: <reason>

   It will show up under Blockers in /pm:status until cleared.
   To clear: /pm:edit PRJ-042 status=active  (or /pm:start if it moved back to backlog)
   ```

7. **Offer to push.** If the task has a `jira_id` or `wrike_id` and a sync MCP is available, offer to push the block state + reason as a comment so stakeholders see it.

## Notes

- **Blocked tasks stay visible in `active/`.** Hiding them in a separate directory would make them easy to forget.
- The reason is mandatory — don't let the user skip it. Blocks without reasons rot.
- To **unblock**, the user runs `/pm:edit <id> status=active` (or starts it fresh with `/pm:start` if it had been moved back to backlog). Consider making that flow smoother in a future iteration.
