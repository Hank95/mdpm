---
name: pm:help
description: List all MDPM commands with a one-line description
argument-hint: ""
---

# /pm:help

Print the full MDPM command reference.

## Output

```
MDPM — Markdown Project Manager

Setup
  /pm:config               Initialize or reconfigure MDPM in this repo

Daily use
  /pm:status               Dashboard — active work, priorities, blockers
  /pm:next                 Recommend the next task to start
  /pm:new <title>          Create a new backlog task
  /pm:start <id>           Move a backlog task to active and begin work
  /pm:block <id> <reason>  Mark a task blocked with a reason
  /pm:done <id>            Complete a task, check for unblocked dependents
  /pm:standup [audience]   Generate a stakeholder-ready standup summary

Editing & finding
  /pm:edit <id> [k=v ...]  Change priority, due, tags, assignee, etc.
  /pm:search <query>       Find tasks by title, tag, ID, assignee, or content

Planning & triage
  /pm:plan <feature>       Break a feature into 3-8 tasks with dependencies
  /pm:inbox                Triage untriaged incoming requests

Maintenance
  /pm:archive [--older-than N]   Move aged done tasks to tasks/archive/
  /pm:board                Launch the local kanban board (opens browser)

Optional sync (needs MCP)
  /pm:sync-jira [push|pull|both]
  /pm:sync-wrike [push|pull|both]

Reference
  /pm:help                 This help

Task state lives in markdown files under tasks/{inbox,backlog,active,done,archive}/.
Filenames follow <ID>-<slug>.md so they sort naturally (e.g. PRJ-001-gallery.md).

For scripting or inline automation, the same operations are available as a CLI:
  python3 ${CLAUDE_PLUGIN_ROOT}/bin/mdpm --json <command>
Run `mdpm --help` for the full command list.
```

Just print this block. Don't embellish. Don't run any other commands.
