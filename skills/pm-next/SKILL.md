---
name: pm:next
description: Recommend the next task to work on based on priority, dependencies, and due dates
argument-hint: ""
---

# /pm:next

Pick the single best task to start next and explain why.

## Steps

1. **Read `docs/ROADMAP.md`** to understand the current milestone focus.

2. **Scan `tasks/backlog/`** and parse each task's frontmatter: `id`, `title`, `priority`, `depends_on`, `due`, `tags`.

3. **Filter out blocked tasks.** A task is blocked if any ID in `depends_on` is not present in `tasks/done/`.

4. **Rank the unblocked candidates** by:
   1. Overdue first (any task past `due`)
   2. Priority (high → medium → low)
   3. Earliest `due` date
   4. Alignment with the current milestone (tags that match, or mentioned in ROADMAP)
   5. `created` date (older first — don't let things rot)

5. **Also consider `tasks/active/`.** If there's already active work, mention it: the user may want to finish what's in flight rather than start something new. Only recommend starting a new task if active work is stalled or if the user clearly wants the next item.

6. **Return one recommendation** in this format:

```
## Recommendation: [PRJ-123] Task Title

**Why:** <1-2 sentences: priority, milestone alignment, or unblocking effect>

**Acceptance criteria:**
- [ ] ...
- [ ] ...

**Suggested first step:** <concrete action — usually derived from objective/notes>

Shall I move this to `tasks/active/` and get started?
```

7. If there are no unblocked backlog tasks, say so plainly and suggest either triaging `tasks/inbox/` or planning new work with `/pm:plan`.

## Notes

- Read-only until the user confirms. Don't move the file without permission.
- If multiple tasks tie on ranking, pick the one most aligned with the current milestone.
