---
name: pm-status
description: Show project dashboard — active work, upcoming priorities, and blockers
argument-hint: ""
---

# /pm-status

Read the project's task state and produce a concise dashboard.

## How to run

Delegate to the CLI. Use `--json` so you can rearrange and format the output to fit the user's audience:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/mdpm" --json status
```

## What to produce

The CLI returns:
```json
{
  "counts": {"inbox": N, "backlog": N, "active": N, "done": N},
  "active": [...],
  "blocked": [...],
  "waiting": [...],
  "overdue": [...]
}
```

Combine with `docs/ROADMAP.md` (read it via Read tool) to identify the current milestone. Produce a dashboard like:

```
# Project Status — <current milestone from ROADMAP>

## Active (<count>)
- [PRJ-123] Title — priority, due YYYY-MM-DD
  Last log: <latest_log from mdpm show>

## Up Next (top 3 from backlog, ranked by priority)
- [PRJ-124] Title — priority, tags

## Inbox (<count> untriaged)
- <titles only — suggest /pm-inbox to triage>

## Blockers
- [PRJ-123] blocked — <reason from latest blocking log entry>

## Waiting on upstream
- [PRJ-123] waiting on [PRJ-099] ("<title of dep>", <status>)

## Overdue
- [PRJ-123] was due YYYY-MM-DD

## Recently Shipped (last 7 days)
- [PRJ-120] Title — YYYY-MM-DD
```

For "Recently Shipped" and "Up Next", run `mdpm --json list --status done` and `mdpm --json list --status backlog` respectively and filter/sort in your response.

## Output discipline

- Omit any section that would be empty. Don't print "Blockers: None."
- Single-line entries unless a blocker needs explanation.
- No filler. This is a scan, not a report.

## Notes

- Read-only — don't modify any files.
- The distinction between "Blockers" (status field is blocked — external obstacle) and "Waiting on upstream" (unmet `depends_on` — just sequenced) matters. The CLI gives you both separately in the JSON; keep them separate in the dashboard.
