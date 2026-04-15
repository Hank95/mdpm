---
name: pm:new
description: Create a new task file in tasks/backlog/ with auto-incrementing ID
argument-hint: "<task title or description>"
---

# /pm:new

Create a new task. `$ARGUMENTS` is the task title or a brief description.

## How to run

Delegate to the CLI — it auto-derives the ID from the project's prefix (via `.mdpm/config.json` or by scanning existing IDs), builds the filename as `<ID>-<slug>.md`, and writes the task atomically with a canonical template:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/mdpm" new "<title>" \
  --priority medium \
  [--due YYYY-MM-DD] \
  [--tags a,b,c] \
  [--depends PRJ-001,PRJ-002] \
  [--assigned-to "Henry"] \
  [--objective "1-3 sentence objective"] \
  --json
```

## Parsing the user's prompt

1. **Extract a clean title** from `$ARGUMENTS`. 5-10 words. Trim filler ("could you please", "I want to").
2. **Detect priority hints**: "urgent", "high-priority", "blocker" → `--priority high`. "nice to have", "whenever" → `--priority low`. Otherwise omit (CLI defaults to medium).
3. **Detect due dates**: "by Friday", "due 5/1", "end of month" → resolve to ISO date and pass via `--due`.
4. **Detect tags**: if the user mentions an area ("this is for the billing feature", "frontend refactor"), include it in `--tags`.
5. **Don't ask questions for trivial tasks.** Minimum viable: title + default priority. The user can edit later with `/pm:edit`.

## Interpreting the result

- **ok: true** — confirm with the assigned ID and file path. If the description looked like a multi-step feature (5+ distinct actions), offer `/pm:plan <id>` to decompose.
- **ok: false, error: "conflict"** — unlikely but possible if a filename collision happens. Re-run; the CLI should pick the next ID.

## Notes

- The CLI writes `created: <today>`, `updated: <today>`, and an initial Work Log line automatically. Don't duplicate.
- Do NOT move the task to `tasks/active/`. `/pm:new` creates in `backlog/`; `/pm:start` handles the transition to active.
- Never use the Write tool to create task files manually — you'd bypass ID generation and filename convention.
