---
description: Sync task state with Jira via MCP (optional, graceful degradation)
argument-hint: "[push|pull|both]"
---

# /pm-sync-jira

Bridge MDPM tasks with Jira. Works only if a Jira MCP server is connected.

Argument `$1`: `push` (default), `pull`, or `both`.
- `push` — send local state out to Jira
- `pull` — bring in newly assigned Jira issues as inbox items
- `both` — pull first, then push

## Steps

### 0. Detect the Jira MCP

Look for tools prefixed with something like `mcp__jira__*`, `mcp__atlassian__*`, `mcp__*jira*__*`, or any tool whose name clearly matches Jira (create_issue, update_issue, transition_issue, get_issue, search_issues, add_comment).

**If no Jira MCP is available:**
- Do NOT fail. Instead, generate a copy/pasteable summary suitable for pasting into a Jira comment or ticket body:

  ```
  Jira MCP not detected. Here's a summary you can paste into Jira:

  **Active:**
  - [PRJ-123] Title — <latest work log>
    Acceptance criteria progress: 3/5

  **Completed today:**
  - [PRJ-120] Title — <what shipped>

  **Blockers:**
  - [PRJ-125] — needs <thing>, waiting on <person>
  ```

- Tell the user: "To enable automatic sync, install an Atlassian/Jira MCP server (e.g. `@modelcontextprotocol/server-atlassian` or the official Atlassian MCP), register it in your `.mcp.json`, and rerun this command."
- Exit.

### 1. Load Jira config

Check `.mdpm/config.json` for:
- `jira.default_project` — project key for new issues (e.g. `ENG`)
- `jira.issue_type` — default issue type (`Task`, `Story`, `Bug`)
- `jira.status_map` — map of MDPM status → Jira workflow transition name
  - Example default: `{"backlog": "To Do", "active": "In Progress", "blocked": "Blocked", "done": "Done"}`
- `jira.priority_map` — map of MDPM priority → Jira priority (default: `{"high": "High", "medium": "Medium", "low": "Low"}`)
- `jira.field_map` — overrides

If config is missing, ask the user for the minimum needed (default_project) and offer to save it.

### 2. Push (default)

For each task in `tasks/active/` and recently updated `tasks/done/`:

- **If `jira_id` is null:** Create a new Jira issue via the available MCP tool. Field mapping:

  | MDPM field                      | Jira field                |
  |---------------------------------|---------------------------|
  | `title`                         | Summary                   |
  | Objective + Acceptance Criteria | Description               |
  | `priority`                      | Priority                  |
  | `tags`                          | Labels                    |
  | `status`                        | Workflow transition       |
  | `due`                           | Due date                  |
  | `assigned_to`                   | Assignee (by name)        |
  | `jira_project` or config        | Project key               |

  Store the returned issue key (e.g. `ENG-451`) back into the task's `jira_id:` frontmatter, and its project key into `jira_project:`.

- **If `jira_id` exists:** Update the Jira issue:
  - Transition status to the mapped Jira workflow state if status changed locally
  - Post new work log entries as comments — only entries created after `last_synced` in `.mdpm/sync-state.json`
  - Update summary, priority, labels, due date, assignee if changed
  - When the task moves to `done/`, transition to the Done workflow state (configurable).

Track last-sync timestamps in `.mdpm/sync-state.json` so you only push deltas.

### 3. Pull

Query Jira for issues:
- Assigned to the current user (`assignee = currentUser()`)
- In the configured projects
- With status indicating they are open / not yet done
- Not already tracked locally (no matching `jira_id` in any MDPM task)

For each new issue:
- Create a file in `tasks/inbox/` with:
  - Filename: `<id>-<slugified summary>.md` (e.g. `PRJ-INBOX-003-fix-broken-login.md`)
  - `id: PRJ-INBOX-XXX` (placeholder)
  - `jira_id: ENG-451`
  - `jira_project: ENG`
  - `title`, `priority`, `tags`, `due` copied from Jira
  - Objective populated from the issue description
- Don't auto-triage. Leave to the user via `/pm-inbox`.

### 4. Report

Summarize:
```
Jira sync complete:
- Pushed 2 status updates
- Posted 4 work log comments
- Created 1 new Jira issue (PRJ-123 → ENG-451)
- Pulled 3 new inbox items — run /pm-inbox to triage
```

## Notes

- Never delete local tasks when Jira issues are closed by someone else. Treat Jira state as advisory on pull, authoritative on push.
- If an API call fails, log and continue. Don't abort the whole sync.
- MCP-agnostic by design: discover available Jira tools at runtime; don't hardcode a specific server's tool names.
- If the user has multiple Jira MCPs configured (rare but possible), ask which one to use before proceeding.
