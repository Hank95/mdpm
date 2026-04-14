---
name: pm:plan
description: Break a feature or epic into 3-8 scoped tasks with dependency mapping
argument-hint: "<feature description or task ID to decompose>"
disable-model-invocation: true
---

# /pm:plan

Decompose a feature into a set of tasks with proper sequencing.

Argument `$ARGUMENTS` is either:
- A freeform feature description ("add user authentication with magic links")
- An existing task ID (like `PRJ-042`) to decompose into subtasks

## Steps

1. **Load context.**
   - Read `docs/ROADMAP.md` to understand the current milestone.
   - Read `docs/DECISIONS.md` — existing architecture constraints matter.
   - If `$ARGUMENTS` is a task ID, read that task file for objective/notes/AC.

2. **Ask clarifying questions only if truly needed.** The user is busy. Make reasonable assumptions from the codebase and stated description. Ask at most 1-2 focused questions, not a survey.

3. **Decompose** into **3-8 tasks**. Each task must:
   - Be completable in a bounded chunk (hours to a couple of days, not weeks).
   - Have a clear "done" condition — visible in acceptance criteria.
   - Be independently testable/demonstrable where possible.
   - Have explicit `depends_on` if it requires another task in the set to be finished first.

4. **Present the plan** to the user for review BEFORE creating files:

   ```
   ## Plan: <feature name>

   1. [NEW] Task A — 1-line description (priority: high)
   2. [NEW] Task B — 1-line description (priority: high, depends on: A)
   3. [NEW] Task C — 1-line description (priority: medium, depends on: A)
   4. [NEW] Task D — 1-line description (priority: medium, depends on: B, C)
   ...

   Dependencies: A → B, A → C, {B,C} → D
   Estimated sequence: A, then B+C in parallel, then D.
   ```

5. **Get confirmation.** Ask: "Create these as backlog tasks?" Let the user edit the plan before writing files. They may want to split/merge tasks, adjust priorities, or drop items.

6. **Create the task files** once confirmed. For each task:
   - Generate a unique ID using the same rules as `/pm:new` (scan all existing IDs, pick max + 1).
   - Use the template from `/pm:new`.
   - Populate `depends_on` with the correct IDs of sibling tasks.
   - Set `tags` consistently across the set (often a shared feature name).
   - Write to `tasks/backlog/`.

7. **If decomposing from an existing task**, link back:
   - Add a note to each new subtask: `Parent: PRJ-042`.
   - Update the parent task's notes to list the children.
   - Leave the parent in place — don't auto-close it. The user decides whether to keep it as a tracking umbrella or delete it.

8. **Report back** with file paths created and the suggested first task to start. Offer `/pm:next` to confirm the sequence.

## Notes

- Don't over-decompose. 3 focused tasks beats 8 trivial ones.
- Don't create tasks for future maintenance ("monitor for regressions") — only concrete deliverables.
- Dependency chains longer than 3 levels deep usually mean you're over-planning. Flatten where possible.
