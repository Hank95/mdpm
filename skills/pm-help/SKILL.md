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
  /pm:done <id|title>      Complete a task, check for unblocked dependents
  /pm:standup [audience]   Generate a stakeholder-ready standup summary

Planning
  /pm:plan <feature>       Break a feature into 3-8 tasks with dependencies
  /pm:inbox                Triage untriaged incoming requests

Optional sync (needs MCP)
  /pm:sync-jira [push|pull|both]
  /pm:sync-wrike [push|pull|both]

Reference
  /pm:help                 This help

Task state lives in markdown files under tasks/{backlog,active,done,inbox}/.
Run the local kanban board with: python3 board/serve.py (if installed).

Full conventions: see the rules file shipped with the plugin.
```

Just print this block. Don't embellish. Don't run any other commands.
