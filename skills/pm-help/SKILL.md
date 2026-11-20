---
description: List all MDPM commands with a one-line description
---

# /pm-help

Print the full MDPM command reference.

## Output

```
MDPM — Markdown Project Manager

Setup
  /pm-config               Initialize or reconfigure MDPM in this repo

Daily use
  /pm-status               Dashboard — active work, priorities, blockers
  /pm-next                 Recommend the next task to start
  /pm-new <title>          Create a new backlog task
  /pm-start <id>           Move a backlog task to active and begin work
  /pm-done <id>            Complete a task, check for unblocked dependents
  /pm-standup [audience]   Generate a stakeholder-ready standup summary

Planning & triage
  /pm-plan <feature>       Break a feature into 3-8 tasks with dependencies
  /pm-inbox                Triage untriaged incoming requests

Board
  /pm-board                Launch the local kanban board (opens browser)

Experimental sync (needs a Jira or Wrike MCP server)
  /pm-sync-jira [push|pull|both]
  /pm-sync-wrike [push|pull|both]

Everything else — just ask
  Blocking, editing, searching and archiving have no slash command. Say what
  you want ("block PRJ-042, waiting on Alice", "find tasks about auth",
  "archive anything done over 30 days ago") and Claude runs the mdpm CLI.

Reference
  /pm-help                 This help

Task state lives in markdown files under tasks/{inbox,backlog,active,done,archive}/.
Filenames follow <ID>-<slug>.md so they sort naturally (e.g. PRJ-001-gallery.md).

For scripting or inline automation, the same operations are available as a CLI:
  python3 ${CLAUDE_PLUGIN_ROOT}/bin/mdpm --json <command>
Run `mdpm --help` for the full command list.
```

Just print this block. Don't embellish. Don't run any other commands.
