# MDPM — Markdown Project Manager

A lightweight, markdown-native project tracker for [Claude Code](https://claude.ai/code). Tasks live as `.md` files with YAML frontmatter; **status is a directory**. Zero dependencies. Optional Jira/Wrike sync via MCP.

> For developers and hybrid PM/engineers who want the lightest possible tracking system that works equally well for humans and AI coding agents — and who occasionally need to surface status to stakeholders in Jira or Wrike without context-switching.

---

## Why MDPM?

- **Markdown is the source of truth.** No database, no API, no web service required. Everything is a file in your repo.
- **Status is a directory.** `tasks/backlog/`, `tasks/active/`, `tasks/done/`, `tasks/inbox/`. `ls` tells you the state of the project.
- **One file per task.** Claude can read or edit a single task without loading the whole system.
- **Never delete history.** Task files move between directories; the work log is append-only.
- **AI-friendly by design.** The conventions were written so Claude Code can do project management work alongside actual engineering work, in the same session.
- **Optional Jira / Wrike bridges.** When you need stakeholder visibility, sync is one command away — but MDPM works 100% standalone if you never enable it.

---

## Install

MDPM is a Claude Code plugin.

```bash
# 1. Add this marketplace to Claude Code
/plugin marketplace add Hank95/mdpm

# 2. Install the plugin
/plugin install mdpm
```

(Or clone the repo and point Claude Code at it directly — see [Development](#development).)

Once installed, run inside any repo:

```
/pm:config
```

That walks you through first-time setup (ID prefix, default assignee, optional sync config) and creates the `tasks/` and `docs/` layout.

---

## Commands

All commands are namespaced under `/pm:`.

### Daily use

| Command | What it does |
| --- | --- |
| `/pm:status` | Dashboard — active work, priorities, blockers (vs waiting), overdue, recently shipped |
| `/pm:next` | Recommends the single best task to start next |
| `/pm:new <title>` | Creates a new backlog task with auto-incrementing ID |
| `/pm:start <id>` | Moves a backlog task to `active/` and begins work |
| `/pm:done <id>` | Completes a task, moves to `done/`, checks for unblocked dependents |
| `/pm:standup [audience]` | Generates a stakeholder-ready standup summary |

### Editing & finding

| Command | What it does |
| --- | --- |
| `/pm:edit <id> [k=v…]` | Change priority, due date, tags, assignee, dependencies |
| `/pm:search <query>` | Find tasks by title, tag, ID, assignee, or body content |

### Planning & triage

| Command | What it does |
| --- | --- |
| `/pm:plan <feature>` | Breaks a feature into 3–8 tasks with dependency mapping |
| `/pm:inbox` | Walks through `tasks/inbox/` one item at a time |

### Maintenance

| Command | What it does |
| --- | --- |
| `/pm:archive [--older-than N]` | Moves aged `done/` tasks to `tasks/archive/` to reduce clutter |
| `/pm:board [port]` | Prints the command to launch the local kanban board |

### Optional sync (requires an MCP server for the target system)

| Command | What it does |
| --- | --- |
| `/pm:sync-jira [push\|pull\|both]` | Syncs task state with Jira via any connected Jira MCP |
| `/pm:sync-wrike [push\|pull\|both]` | Syncs task state with Wrike via any connected Wrike MCP |

### Setup / reference

| Command | What it does |
| --- | --- |
| `/pm:config` | First-time setup (or reconfigure) |
| `/pm:help` | Lists all commands |

---

## Task Format

Every task lives in `tasks/<status>/<slug>.md`:

```yaml
---
id: PRJ-001
title: Gallery Page Component
priority: high            # high | medium | low
status: backlog           # backlog | active | blocked | done
created: 2026-04-10
updated: 2026-04-10
due: 2026-04-18
tags: [gallery, frontend]
depends_on: []
assigned_to: Henry
wrike_id: null
jira_id: null
jira_project: null
---

# Gallery Page Component

## Objective
Build the responsive gallery page for BTR community sites as part of the platform rebuild.

## Acceptance Criteria
- [ ] Lightbox viewer with swipe support on mobile
- [ ] Lazy loading for images below the fold
- [ ] Responsive grid layout — 1 col mobile, 2 col tablet, 3 col desktop
- [ ] Accessible (keyboard navigation, alt text, focus management)

## Notes
Check with design on the approved mockup. Coordinate with infra if CDN changes are needed.

## Work Log
- 2026-04-10: Task created, scoped initial requirements
```

See `examples/gallery-page-component.md` for a real-world example.

---

## Directory Layout (after `/pm:config`)

```
your-project/
├── .mdpm/
│   ├── config.json          # MDPM project config (committed)
│   └── sync-state.json      # sync cache (gitignored)
├── tasks/
│   ├── inbox/               # untriaged incoming requests
│   ├── backlog/             # prioritized queue
│   ├── active/              # in progress
│   └── done/                # shipped (never delete)
├── docs/
│   ├── ROADMAP.md           # milestones and priorities
│   ├── DECISIONS.md         # ADR log
│   └── CHANGELOG.md         # shipped work, newest first
└── CLAUDE.md                # references the MDPM rules
```

---

## Kanban Board

A zero-dependency local board ships with the plugin:

```bash
python3 board/serve.py
# -> http://127.0.0.1:8765
```

- Pure Python stdlib (`http.server`)
- Single-file HTML, dark terminal aesthetic
- Four columns: Inbox, Backlog, Active, Done
- Cards show priority, tags, due dates (with overdue warnings), acceptance progress
- Click a card for the full objective, notes, and latest work log
- Read-only view — edit the `.md` files to change state

No build step, no npm, no watcher. Just run `serve.py`.

---

## Sync — Jira and Wrike

Sync is an **optional bridge** for surfacing local task state to stakeholders. It runs on top of whatever Jira or Wrike MCP server you've configured in Claude Code.

- **MCP-agnostic.** MDPM discovers available Jira/Wrike tools at runtime. It doesn't ship its own server.
- **Graceful degradation.** If no MCP is connected, the sync command prints a copy/pasteable standup summary instead of failing.
- **Incremental.** Only deltas since the last sync are pushed (state is cached in `.mdpm/sync-state.json`).
- **Push + pull.** Push local state outward, or pull newly assigned external issues into `tasks/inbox/` for triage.

### Field mappings

**Jira**

| MDPM field | Jira field |
| --- | --- |
| `title` | Summary |
| Objective + Acceptance Criteria | Description |
| `priority` | Priority |
| `tags` | Labels |
| `status` | Workflow transition |
| `due` | Due date |
| `assigned_to` | Assignee |
| `jira_id` | Issue key |
| `jira_project` | Project key |
| Work Log entries | Comments |

**Wrike**

| MDPM field | Wrike field |
| --- | --- |
| `title` | Title |
| Objective + Acceptance Criteria | Description |
| `priority` | Priority |
| `tags` | Tags |
| `status` | Custom status (via config map) |
| `due` | Due date |
| `assigned_to` | Assignee |
| `wrike_id` | Task ID |
| Work Log entries | Comments |

To enable: install any Jira or Wrike MCP server (e.g. the official Atlassian MCP), register it in your `.mcp.json`, and run `/pm:sync-jira` or `/pm:sync-wrike`.

---

## Configuration

`/pm:config` writes `.mdpm/config.json`:

```json
{
  "id_prefix": "PRJ-",
  "default_assignee": "Henry",
  "stakeholders": [],
  "jira": {
    "default_project": "ENG",
    "status_map": {
      "backlog": "To Do",
      "active": "In Progress",
      "blocked": "Blocked",
      "done": "Done"
    },
    "priority_map": {
      "high": "High",
      "medium": "Medium",
      "low": "Low"
    }
  },
  "wrike": {
    "folder_id": null
  }
}
```

Edit this file directly to change behavior, or rerun `/pm:config`.

---

## Design Principles

1. **Markdown first.** If you ever walk away from MDPM, your history is still plain files.
2. **Directories over fields.** Filesystem state is self-documenting; a stale `status:` frontmatter field doesn't lie about where a file lives.
3. **Small, focused tasks.** If a task takes more than a couple of days, decompose it.
4. **Append-only history.** Never rewrite work logs.
5. **No lock-in.** Sync to Jira/Wrike is one-way, opt-in, and leaves your local state intact.
6. **Claude-native.** Conventions written so an AI coding agent can do PM work alongside engineering in the same session.

---

## Updating

Users can pull new versions with:

```
/plugin marketplace update mdpm
/plugin update mdpm
```

Releases are tagged with semver git tags (e.g. `v0.2.0`). The `version` field in both `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` must match the tag.

---

## Development

Clone and point Claude Code at the local plugin:

```bash
git clone https://github.com/Hank95/mdpm
cd mdpm
# In Claude Code:
/plugin install ./mdpm
```

Contributions welcome — open an issue or PR.

Project structure:

```
mdpm/
├── .claude-plugin/
│   ├── plugin.json          # plugin manifest
│   └── marketplace.json     # marketplace listing
├── skills/                  # one /pm:<name> skill per subdirectory (SKILL.md)
├── rules/
│   └── project-tracking.md  # full conventions (loaded into context)
├── templates/               # files copied into user repos during /pm:config
│   ├── CLAUDE.md
│   ├── docs/
│   └── tasks/
├── board/
│   ├── board.html           # kanban UI
│   └── serve.py             # stdlib HTTP server
├── examples/                # sample task files
└── LICENSE
```

---

## License

MIT — see [LICENSE](./LICENSE).
