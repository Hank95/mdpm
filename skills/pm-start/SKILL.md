---
name: pm:start
description: Move a task from backlog to active and begin work
argument-hint: "<task id or partial title>"
---

# /pm:start

Move a task into `tasks/active/` and officially begin work on it. Argument `$ARGUMENTS` identifies the task (ID like `PRJ-123`, or partial title match).

## How to run

**Delegate to the MDPM CLI** — never manipulate task files manually. It handles file moves, work log appends, dep checks, and filename preservation atomically:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/mdpm" --json start $ARGUMENTS
```

## Interpreting the result

The CLI returns JSON with `ok`, `task`, `changes`, `warnings`. Branch on:

- **ok: false, error: "ambiguous_ref"** — the ref matched multiple tasks. The response includes `candidates`. Print them and ask the user which one they meant.
- **ok: false, error: "not_found"** — no match. Suggest `/pm:list` or `/pm:search`.
- **ok: false, error: "precondition_failed"** — usually unmet dependencies. The message says which ones. Ask the user if they want to start anyway (re-run with `--force`) or start the dependency first.
- **warnings: ["already active — no change"]** — tell the user and show the task's Work Log so they can see where they left off.
- **ok: true** — confirm the move. Print the task id, title, and objective. Ask "What do you want to tackle first?"

## If the user didn't give a ref

Run `python3 "${CLAUDE_PLUGIN_ROOT}/bin/mdpm" list --status backlog` and ask which one they want to start. Then re-invoke this skill with that ID.

## Notes

- The CLI already appends "Started work." to the work log. Don't duplicate.
- Don't move files with `mv` or edit the status field with `sed`. The CLI does all of it atomically — if you skip it, you'll leave the repo with the file in `active/` but the `status:` frontmatter still saying `backlog`, which will confuse `/pm:status`.
- Starting a blocked task implies the block is resolved. If `status: blocked` in the task, ask the user "is the blocker cleared?" before running `mdpm start`.
