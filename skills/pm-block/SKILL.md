---
name: pm:block
description: Mark a task as blocked with a reason appended to the work log
argument-hint: "<task id or partial title> [reason]"
---

# /pm:block

Mark a task blocked when progress is stopped by something external — a review, a missing decision, an API that's down, another team's work.

**Blocked vs waiting:** don't confuse them. "Waiting" means `depends_on` points at a task that hasn't shipped yet — that's just sequenced work. "Blocked" means someone outside the task's normal path has to act before it can move.

## How to run

Delegate to the CLI — it sets `status: blocked`, bumps `updated`, and appends the reason to the Work Log atomically:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/mdpm" block <ref> <reason...> --json
```

Example:
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/mdpm" block PRJ-042 waiting on security review from Alice --json
```

## Parsing the user's prompt

- Strip the task ID / ref from `$ARGUMENTS` — first token.
- Everything after is the reason. Pass it as positional args.
- If no reason is given, **ask** — don't call the CLI. `mdpm block` rejects empty reasons with a validation error anyway. A block without context rots in `/pm:status`.

## Interpreting the result

- **ok: true** — confirm with a short summary. Tell the user the block will show up in `/pm:status` under Blockers until cleared with `/pm:edit PRJ-042 status=active` or the blocker command chain below.
- **ok: false, error: "precondition_failed"** — can't block a task that's in `done/` or `archive/`. Suggest `/pm:new` for a follow-up.

## External sync

If the task has a `jira_id` or `wrike_id`, offer to push the block state as a comment to the external system via `/pm:sync-jira` or `/pm:sync-wrike`.

## Unblocking

To clear the block, use `/pm:unblock <ref>` — it restores `status:` to the directory-derived value and logs "Unblocked." in the work log.

## Notes

- A blocked task stays in its current directory (usually `active/`). Moving it to a "blocked" directory would hide it from the active queue — we want it visible so it doesn't get forgotten.
- The CLI's reason is mandatory. Never fabricate one.
