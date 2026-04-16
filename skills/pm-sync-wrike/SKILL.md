---
name: pm-sync-wrike
description: Sync task state with Wrike via MCP (optional, graceful degradation)
argument-hint: "[push|pull|both]"
---

# /pm-sync-wrike

Bridge MDPM tasks with Wrike. Works only if a Wrike MCP server is connected.

Argument `$1`: `push` (default), `pull`, or `both`.
- `push` — send local state out to Wrike
- `pull` — bring in newly assigned Wrike tasks as inbox items
- `both` — pull first, then push

## Steps

### 0. Detect the Wrike MCP

Look for tools prefixed with something like `mcp__wrike__*`, `mcp__*wrike*__*`, or any tool whose name clearly matches Wrike (create_task, update_task, get_folder, etc.).

**If no Wrike MCP is available:**
- Do NOT fail. Instead, generate a copy/pasteable summary:

  ```
  Wrike MCP not detected. Here's a standup-style summary you can paste directly:

  **Active:**
  - [PRJ-123] Title — <latest work log>

  **Completed today:**
  - [PRJ-120] Title — <what shipped>

  **Blockers:**
  - [PRJ-125] needs <thing>
  ```

- Tell the user how to enable: "Install a Wrike MCP server (https://github.com/modelcontextprotocol/servers or similar), add its config to `.mcp.json`, and rerun this command."
- Exit.

### 1. Load Wrike config

Check `.mdpm/config.json` for:
- `wrike.folder_id` — where to create new tasks
- `wrike.status_map` — map of MDPM status → Wrike custom status name
- `wrike.field_map` — any overrides to the default field mapping

If the config is missing, ask the user for the minimum (folder_id) and offer to save it.

### 2. Push (default)

For each task in `tasks/active/` and recently updated `tasks/done/`:

- **If `wrike_id` is null:** Create a new Wrike task using whatever MCP tool is available. Map fields:
  - `title` → Wrike title
  - Objective + Acceptance Criteria → description
  - `priority` → Wrike priority (High/Normal/Low)
  - `tags` → Wrike tags
  - `due` → Wrike due date
  - `assigned_to` → Wrike assignee (best-effort name match)
  - Status → Wrike status per `status_map`
  Store the returned Wrike ID back into the task file's `wrike_id:` frontmatter.

- **If `wrike_id` exists:** Update the Wrike task:
  - Transition status if changed
  - Post new work log entries as Wrike comments (only entries newer than the last sync timestamp)
  - Update due date, assignee, priority if changed

Track a `last_synced` timestamp in `.mdpm/sync-state.json` so you only push incremental updates.

### 3. Pull

Query Wrike for tasks:
- Assigned to the current user
- In folders the user cares about (from config)
- Not already tracked locally (no matching `wrike_id` in any MDPM task)

For each new Wrike task, create a file in `tasks/inbox/`:
- Filename: `<id>-<slugified title>.md` (e.g. `PRJ-INBOX-003-update-hero-copy.md`)
- ID: temporary `PRJ-INBOX-XXX` — a real ID gets assigned during triage (filename is renamed at that point too)
- `wrike_id`: the Wrike task ID
- Populate objective from Wrike description

Suggest `/pm-inbox` to triage.

### 4. Report

Summarize what changed:
```
Wrike sync complete:
- Pushed 3 status updates
- Created 1 new Wrike task (PRJ-123 → WRIKE-abc)
- Pulled 2 new inbox items — run /pm-inbox to triage
```

## Notes

- Never delete local tasks because they were deleted/closed in Wrike. The user decides what to do.
- If a Wrike API call fails, log it and continue. Don't abort the whole sync.
- This skill is deliberately MCP-agnostic — it discovers available tools rather than hardcoding a specific server implementation.
