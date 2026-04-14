---
name: pm:help
description: List all MDPM commands with a one-line description
argument-hint: ""
disable-model-invocation: true
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
  /pm:board [port]         Print the command to launch the kanban board

Optional sync (needs MCP)
  /pm:sync-jira [push|pull|both]
  /pm:sync-wrike [push|pull|both]

Reference
  /pm:help                 This help

Task state lives in markdown files under tasks/{inbox,backlog,active,done,archive}/.
Filenames follow <ID>-<slug>.md so they sort naturally (e.g. PRJ-001-gallery.md).
```

Just print this block. Don't embellish. Don't run any other commands.
