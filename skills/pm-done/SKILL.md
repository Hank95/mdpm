---
name: pm-done
description: Complete a task — move to done/, append work log, update CHANGELOG, report unblocked dependents
argument-hint: "<task id or partial title>"
---

# /pm-done

Mark a task complete. Argument `$ARGUMENTS` identifies the task.

## How to run

Delegate to the CLI — it handles the file move, appends the completion log entry, updates `docs/CHANGELOG.md`, and computes which dependents are now unblocked, all atomically:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/mdpm" --json done $ARGUMENTS
```

If the user supplied a completion summary in their prompt (e.g. "close PRJ-042 — shipped with MFA"), pass it via `-m "Shipped with MFA"`.

## Pre-flight: check acceptance criteria

Before calling `mdpm done`, run `mdpm --json show $ref` and look at `acceptance.done` vs `acceptance.total`. If there are unchecked items:

1. List them for the user.
2. Ask: mark them complete now, remove the ones that are no longer relevant, or proceed anyway acknowledging they weren't met?
3. If the user wants to edit individual AC items, use the Edit tool on the specific `- [ ]` / `- [x]` lines in the task body, then re-check. The CLI doesn't edit AC boxes directly — that's body content, not frontmatter.
4. When the user confirms they're done, call the CLI.

## Interpreting the result

- **ok: true, unblocked: [...]** — tasks that were waiting on this one are now ready. Tell the user:
  > Now that PRJ-042 is done, PRJ-045 ("Gallery Analytics Hooks") is ready to start. Want me to kick it off?
- **warnings: ["N unchecked acceptance criteria remaining"]** — the CLI completes the task anyway but flags this. Mention it so the user knows.
- **ok: false, error: "not_found" / "ambiguous_ref"** — handle like `/pm-start`.
- **ok: false, error: "precondition_failed"** — usually "already in archive — cannot re-complete". Tell the user; suggest `/pm-new` if they want a follow-up.

## External sync

If the task has a `jira_id` or `wrike_id` in its frontmatter (check via `mdpm show`), offer to push the completion to the external system via `/pm-sync-jira` or `/pm-sync-wrike`.

## Notes

- The CLI writes the CHANGELOG entry automatically. Don't duplicate.
- Never move a done task back to `active/` or `backlog/` — if the user wants to reopen, create a follow-up with `/pm-new`.
- `--no-changelog` exists for cases where the user explicitly doesn't want the CHANGELOG touched (e.g. test tasks). Default behavior is to update it.
