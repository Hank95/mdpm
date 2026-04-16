# MDPM — Markdown Project Manager

[![Version](https://img.shields.io/github/v/tag/Hank95/mdpm?label=version&sort=semver)](https://github.com/Hank95/mdpm/releases)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](./LICENSE)
[![Claude Code Plugin](https://img.shields.io/badge/Claude_Code-plugin-orange)](https://github.com/Hank95/mdpm)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue)](https://python.org)

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

MDPM is a Claude Code plugin. Run these one at a time in a Claude Code session:

```
/plugin marketplace add Hank95/mdpm
/plugin install mdpm@mdpm
/reload-plugins
```

> The `@mdpm` suffix disambiguates the plugin name from the marketplace name (both are `mdpm`); some Claude Code versions need it to resolve the install correctly.

(Or clone the repo and point Claude Code at a local path — see [Development](#development).)

Once installed, run inside any repo:

```
/pm-config
```

That walks you through first-time setup (ID prefix, default assignee, optional sync config) and creates the `tasks/` and `docs/` layout.

---

## Two surfaces: slash commands and CLI

MDPM exposes the same operations two ways:

- **`/pm-*` slash commands** — for interactive sessions where the user invokes the command and expects Claude to handle it step-by-step (confirming destructive operations, asking about ambiguous refs, etc.).
- **`bin/mdpm` CLI** — a deterministic, stdlib-only Python CLI for scripts and for Claude to use inline. Every operation is atomic, appends work log entries automatically, validates input, and returns structured JSON on `--json`.

Under the hood both surfaces go through `lib/mdpm_core.py` so the behavior is identical. If you're editing tasks inline mid-session, use the CLI (`python3 ${CLAUDE_PLUGIN_ROOT}/bin/mdpm <cmd>`) — never `sed` / `mv` directly. The rules file shipped with the plugin tells Claude to do the same.

Quick CLI tour:

```bash
# Any operation the slash commands do, without the conversational overhead:
mdpm new "Fix broken login" --priority high --tags auth,bug
mdpm start PRJ-042
mdpm log PRJ-042 "integrated with auth provider"
mdpm block PRJ-042 waiting on security review from Alice
mdpm unblock PRJ-042
mdpm done PRJ-042 -m "Shipped with MFA"
mdpm next --json            # structured output for scripting
mdpm status                 # project dashboard
mdpm search "gallery"       # find tasks
mdpm archive --older-than 30
```

Run `mdpm --help` or `mdpm <command> --help` for full argument lists.

## Commands

All slash commands are prefixed with `/pm-`.

### Daily use

| Command | What it does |
| --- | --- |
| `/pm-status` | Dashboard — active work, priorities, blockers (vs waiting), overdue, recently shipped |
| `/pm-next` | Recommends the single best task to start next |
| `/pm-new <title>` | Creates a new backlog task with auto-incrementing ID |
| `/pm-start <id>` | Moves a backlog task to `active/` and begins work |
| `/pm-block <id> <reason>` | Marks a task blocked (status field) with a reason appended to the work log |
| `/pm-done <id>` | Completes a task, moves to `done/`, checks for unblocked dependents |
| `/pm-standup [audience]` | Generates a stakeholder-ready standup summary |

### Editing & finding

| Command | What it does |
| --- | --- |
| `/pm-edit <id> [k=v…]` | Change priority, due date, tags, assignee, dependencies |
| `/pm-search <query>` | Find tasks by title, tag, ID, assignee, or body content |

### Planning & triage

| Command | What it does |
| --- | --- |
| `/pm-plan <feature>` | Breaks a feature into 3–8 tasks with dependency mapping |
| `/pm-inbox` | Walks through `tasks/inbox/` one item at a time |

### Maintenance

| Command | What it does |
| --- | --- |
| `/pm-archive [--older-than N]` | Moves aged `done/` tasks to `tasks/archive/` to reduce clutter |
| `/pm-board [port]` | Prints the command to launch the local kanban board |

### Optional sync (requires an MCP server for the target system)

| Command | What it does |
| --- | --- |
| `/pm-sync-jira [push\|pull\|both]` | Syncs task state with Jira via any connected Jira MCP |
| `/pm-sync-wrike [push\|pull\|both]` | Syncs task state with Wrike via any connected Wrike MCP |

### Setup / reference

| Command | What it does |
| --- | --- |
| `/pm-config` | First-time setup (or reconfigure) |
| `/pm-help` | Lists all commands |

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

## Directory Layout (after `/pm-config`)

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
python3 ${CLAUDE_PLUGIN_ROOT}/bin/mdpm board
# -> opens http://127.0.0.1:8765 in your default browser

# Useful flags:
#   --port N         different port (default 8765, auto-walks forward if busy)
#   --no-open        don't open a browser (good for SSH/Tailscale sessions)
#   --host 0.0.0.0   bind beyond loopback (only on trusted networks — the
#                    board has write endpoints)
```

The `board` subcommand locates `serve.py` inside the installed plugin and points it at whatever project you're in, so you always get the current UI after `/plugin update mdpm`.

- Pure Python stdlib (`http.server`)
- Single-file HTML, dark terminal aesthetic
- Four columns: Inbox, Backlog, Active, Done
- Cards show priority, tags, due dates (with overdue warnings), acceptance progress
- Click a card for the full objective, notes, and latest work log
- **Inline editing**: the detail modal has an **Edit** button that opens the full raw markdown in a textarea. Save writes back to the file with conflict detection (mtime-based) — if the file changed on disk while you were editing, you'll be prompted to reload or overwrite. Cmd/Ctrl+S saves.
- Auto-walks the port forward if the default (8765) is busy (use `--strict-port` to disable)
- "Report bug" link in the header points to this repo's issue tracker

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

To enable: install any Jira or Wrike MCP server (e.g. the official Atlassian MCP), register it in your `.mcp.json`, and run `/pm-sync-jira` or `/pm-sync-wrike`.

---

## Configuration

`/pm-config` writes `.mdpm/config.json`:

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

Edit this file directly to change behavior, or rerun `/pm-config`.

---

## Design Principles

1. **Markdown first.** If you ever walk away from MDPM, your history is still plain files.
2. **Directories over fields.** Filesystem state is self-documenting; a stale `status:` frontmatter field doesn't lie about where a file lives.
3. **Small, focused tasks.** If a task takes more than a couple of days, decompose it.
4. **Append-only history.** Never rewrite work logs.
5. **No lock-in.** Sync to Jira/Wrike is one-way, opt-in, and leaves your local state intact.
6. **Claude-native.** Conventions written so an AI coding agent can do PM work alongside engineering in the same session.

---

## Troubleshooting

**`/pm-help` returns `Unknown skill: pm:help` after install.** Your Claude Code version may be silently rejecting SKILL.md files because of an unrecognized frontmatter field. This was fixed in **v0.2.1**. Update and reinstall:

```
/plugin marketplace update mdpm
/plugin update mdpm
/reload-plugins
```

If you're still on v0.2.0 or older, do a clean reinstall:

```
/plugin uninstall mdpm
/plugin marketplace add Hank95/mdpm
/plugin install mdpm@mdpm
/reload-plugins
```

Verify by checking `/reload-plugins` output — the skill count should increase by 17 (the number of `/pm-*` commands MDPM ships).

**`/plugin marketplace add` opens a TUI prompt on mobile / tmux sessions.** Paste only the source (e.g. `Hank95/mdpm`) — not the whole sequence of commands. Then run `/plugin install mdpm@mdpm` separately.

**Board server says port is busy.** `python3 board/serve.py` auto-walks forward to the next free port starting at 8765. Pass `--port <N>` to start somewhere else, or `--strict-port` to fail instead of falling back.

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
├── skills/                  # one /pm-<name> skill per subdirectory (SKILL.md)
├── rules/
│   └── project-tracking.md  # full conventions (loaded into context)
├── templates/               # files copied into user repos during /pm-config
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
