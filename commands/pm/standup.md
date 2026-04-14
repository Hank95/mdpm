---
description: Generate a stakeholder-ready standup summary (yesterday / today / blockers)
argument-hint: "[audience]"
---

# /pm:standup

Produce a standup summary suitable for posting to Slack, email, or pasting into a Jira/Wrike update.

Argument `$1` (optional): audience — e.g., "engineering", "exec", "pm". Defaults to a neutral engineering-PM tone.

## Steps

1. **Determine date boundaries.**
   - "Yesterday" = any work log entry dated within the last working day (if today is Monday, include Friday through Sunday).
   - "Today" = the current date's active tasks.

2. **Collect yesterday's shipped work** from `tasks/done/*.md` — look at `updated:` in frontmatter and the final work log entry.

3. **Collect today's active work** from `tasks/active/*.md`.

4. **Identify blockers** — any task with `status: blocked` or any active task with unmet `depends_on`.

5. **Write the summary** in this format:

```
**Standup — YYYY-MM-DD**

**Yesterday**
- Shipped: [PRJ-120] Title — one-line description of what was delivered
- Progress: [PRJ-123] Title — what moved forward (from latest work log)

**Today**
- [PRJ-123] Title — what I'm picking up
- [PRJ-124] Title — what's next after

**Blockers**
- [PRJ-125] needs design review from <assigned_to from notes>
- (or: None)
```

6. **Tone by audience:**
   - Default / no argument: concise, engineering-focused, use task IDs.
   - "exec": drop task IDs, emphasize business outcomes and milestones from ROADMAP.
   - "pm" / "stakeholder": mention risks and dates, include any `due:` dates that are slipping.

7. **Offer to push.** After showing the summary, ask:
   > Want me to sync this to Jira/Wrike via `/pm:sync-jira` or `/pm:sync-wrike`, or are you copying it manually?

## Notes

- Read-only — don't modify task files.
- Keep it under ~150 words. Standups should be scannable.
