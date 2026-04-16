---
name: pm-next
description: Recommend the next task to work on based on priority, dependencies, and due dates
argument-hint: ""
---

# /pm-next

Pick the single best task to start next and explain why.

## How to run

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/mdpm" --json next
```

The CLI already filters out blocked tasks and tasks with unmet dependencies, and ranks by: overdue first → priority → due date → created.

## What to produce

The response contains `recommendation` (the top pick) and `candidates` (top 5 for context).

1. Read `docs/ROADMAP.md` to understand the current milestone.
2. Read the recommended task's body via `mdpm --json show <id>` for its acceptance criteria and notes.
3. Check `tasks/active/` via `mdpm list --status active` — if there's already work in flight, mention it. The user may want to finish what's active rather than start something new.

Format:

```
## Recommendation: [PRJ-123] Task Title

**Why:** <1-2 sentences: priority, milestone alignment, or unblocking effect>

**Acceptance criteria:**
- [ ] ...
- [ ] ...

**Suggested first step:** <concrete action derived from Objective/Notes>

Shall I move this to `tasks/active/` and get started?
```

If the user says yes, invoke `/pm-start <id>`.

## Fallbacks

- **recommendation: null** — no unblocked backlog tasks. Say so plainly. Suggest `/pm-inbox` to triage or `/pm-plan` to plan new work.
- **Active work already in flight** — mention it but let the user decide whether to context-switch.

## Notes

- Read-only until the user confirms the pick.
- If candidates tie on all ranking dimensions, just pick the first one the CLI returned.
