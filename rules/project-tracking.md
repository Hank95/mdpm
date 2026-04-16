# Project Tracking Conventions

This project uses **MDPM** (Markdown Project Manager). All task state lives in markdown files under `tasks/`. Status is a directory.

Read this file in full before doing project management work in this repo.

## For Claude: Use the CLI, Not sed/mv

**The single most important rule:** when you need to change task state or metadata mid-session, call the MDPM CLI — never use `sed`, `awk`, `mv`, or `Edit` tool calls to mutate task files directly.

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/mdpm" [--json] <command> [args]
```

The CLI enforces every invariant automatically: atomic writes, work-log appends, filename renames when titles change, ID uniqueness, status-directory/status-field consistency, acceptance-criteria warnings, newly-unblocked-dependent detection, and CHANGELOG updates. Raw file edits skip all of that and drift the repo into inconsistent state.

### Commands (all operate on the current project, walking up from CWD for `tasks/`)

| Command | Use it for |
| --- | --- |
| `mdpm list [--status S] [--priority P] [--tag T]` | Show tasks (grouped by status by default) |
| `mdpm show <ref>` | Print a full task file |
| `mdpm new "<title>" [--priority P] [--due D] [--tags a,b] [--depends PRJ-001]` | Create a backlog task; ID and filename slug are auto-derived |
| `mdpm start <ref> [--force]` | Move backlog→active, append "Started work." to the log. Fails with exit 4 if deps are unmet unless `--force` |
| `mdpm done <ref> [-m "summary"] [--no-changelog]` | Complete a task: move to done/, append log, update CHANGELOG, print unblocked dependents |
| `mdpm block <ref> <reason...>` | Set `status: blocked`, append reason to the log |
| `mdpm unblock <ref>` | Clear `status: blocked` back to the directory-derived status |
| `mdpm edit <ref> [--title T] [--priority P] [--due D] [--tags a,b] [--depends ...] [--assigned-to N] [--note "..."]` | Change frontmatter fields; renames the file if title changes |
| `mdpm log <ref> <entry...>` | Append a dated work log entry without other changes |
| `mdpm move <ref> <status>` | Raw file move (escape hatch — prefer start/done/archive) |
| `mdpm archive [--older-than 30] [--all] [--tag T]` | Move aged done/ tasks to archive/ |
| `mdpm search <query> [--status S] [--tag T] [--assignee N]` | Find tasks by id/title/tags/body |
| `mdpm next` | Recommend the next task (skips blocked, skips those with unmet deps) |
| `mdpm status` | Dashboard: active, blocked, waiting, overdue |
| `mdpm board [--port N] [--no-open]` | Launch the kanban board (opens browser by default) |

`<ref>` accepts an exact ID (`PRJ-042`), a case-insensitive title substring (`"user login"`), or a filename fragment. Ambiguous refs exit 2 with a candidate list on stderr.

### Structured output for decisions

Pass `--json` to every command you want to branch on programmatically. The response shape is:

```json
{
  "ok": true,
  "action": "done",
  "task": {"id":"PRJ-042","title":"...","status":"done","path":"..."},
  "changes": {"moved_from":"tasks/active/","moved_to":"tasks/done/","worklog_appended":true,"changelog_updated":true},
  "unblocked": [{"id":"PRJ-045","title":"...","status":"backlog"}],
  "warnings": ["2 unchecked acceptance criteria remaining"]
}
```

Two keys drive what you should surface to the user:
- `unblocked` non-empty → mention the newly-unblocked tasks. "Now that PRJ-042 is done, PRJ-045 is ready to start."
- `warnings` non-empty → surface them. Skipped acceptance criteria, unmet deps that were forced through, "already in X state," etc.

Everything else is confirmatory — stay silent unless the user asked for a detailed report.

### Exit codes

`0` success · `2` not found / ambiguous ref · `3` validation error (bad priority/date) · `4` precondition failed (unmet deps on start, blocked task, etc.) · `5` write conflict · `1` anything else.

### Examples of common sessions

```bash
# Start work on what /pm-next would recommend:
python3 "${CLAUDE_PLUGIN_ROOT}/bin/mdpm" --json next
python3 "${CLAUDE_PLUGIN_ROOT}/bin/mdpm" start PRJ-042

# Complete a task and learn what's unblocked:
python3 "${CLAUDE_PLUGIN_ROOT}/bin/mdpm" done PRJ-042 -m "Shipped login with MFA"

# Capture a new task inline:
python3 "${CLAUDE_PLUGIN_ROOT}/bin/mdpm" new "Fix broken nav on mobile" --priority high --tags frontend,bug

# Note partial progress without changing status:
python3 "${CLAUDE_PLUGIN_ROOT}/bin/mdpm" log PRJ-042 "finished happy-path integration tests"

# Block a task when you discover it's stuck:
python3 "${CLAUDE_PLUGIN_ROOT}/bin/mdpm" block PRJ-042 "waiting on SAML config from infra team"
```

Tip: the user's `/pm-*` slash commands are thin wrappers for interactive sessions. When acting on the user's behalf mid-session (without them explicitly invoking a slash command), use the CLI directly — it does the same thing without the skill-to-Claude prompt overhead.

---

## Directory Layout

```
tasks/
  inbox/     # untriaged incoming requests (may be auto-populated by Jira/Wrike sync)
  backlog/   # queued work, prioritized
  active/    # in progress right now
  done/      # recently completed work — never delete from here
  archive/   # aged-out completed tasks moved aside by /pm-archive
docs/
  ROADMAP.md    # current milestone and future work
  DECISIONS.md  # architecture decision log (ADR)
  CHANGELOG.md  # shipped work, newest first
.mdpm/
  config.json        # per-project MDPM config (ID prefix, sync settings)
  sync-state.json    # local sync cache — gitignored
```

## Filename Convention

Every task file is named `<ID>-<kebab-slug>.md`, e.g. `PRJ-042-add-user-login.md`. The ID prefix makes tasks sortable and greppable from the filesystem. When a task's `title:` changes via `/pm-edit`, the file is renamed to keep the slug accurate.

## The Golden Rules

1. **Markdown is the source of truth.** Not Jira, not Wrike, not a DB. `.md` files.
2. **Status = directory.** Moving a file changes its status. Don't keep stale `status:` fields; treat the directory as authoritative when they disagree, and fix the frontmatter.
3. **One file per task.** So Claude can read/edit a single task without loading the whole system.
4. **Never delete task files** — except rejected inbox items. Everything else moves to `done/` and stays there.
5. **Work logs are append-only.** Never rewrite history.
6. **IDs are permanent and unique.** Never reuse.
7. **Small, focused tasks.** If a task would take more than a couple of days, decompose it with `/pm-plan`.

## Task File Format

Every task file has YAML frontmatter followed by markdown body. See `templates/task-template.md` for the canonical shape.

```yaml
---
id: PRJ-001           # <prefix>-<zero-padded 3-digit number>
title: Short descriptive title
priority: high | medium | low
status: backlog | active | blocked | done
created: YYYY-MM-DD
updated: YYYY-MM-DD
due: YYYY-MM-DD | null
tags: [tag1, tag2]
depends_on: [PRJ-000] # IDs that must be in done/ before this can start
assigned_to: name
wrike_id: null        # populated by /pm-sync-wrike
jira_id: null         # populated by /pm-sync-jira
jira_project: null
---

# Title

## Objective
What needs to be done and why (1-3 sentences).

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2

## Notes
Context, links, people to coordinate with.

## Work Log
- YYYY-MM-DD: Entry
```

## Typical Flow

1. **Capture.** `/pm-new <title>` creates a backlog task. Inbox items come in via sync or direct drop.
2. **Triage.** `/pm-inbox` walks through incoming items.
3. **Plan.** `/pm-plan <feature>` breaks large work into sized tasks.
4. **Pick.** `/pm-next` recommends what to start, or `/pm-status` shows the dashboard.
5. **Start.** `/pm-start <id>` moves the task to `active/` and adds a "started work" log entry.
6. **Work.** Update the work log as you go. `/pm-edit` adjusts metadata (priority, due, tags).
7. **Ship.** `/pm-done <id>` moves to `done/`, checks dependents, updates CHANGELOG.
8. **Report.** `/pm-standup` produces a stakeholder summary.
9. **Find things.** `/pm-search <query>` across all tasks, any status.
10. **Tidy.** `/pm-archive` periodically moves old `done/` tasks to `archive/`.
11. **(Optional) Sync.** `/pm-sync-jira` / `/pm-sync-wrike` push status outward.

## How Claude Should Behave

When working in a repo that uses MDPM:

- **Start sessions** by reading `docs/ROADMAP.md` to understand current priorities. Optionally run `/pm-status` to see active work.
- **When asked to work on a feature**, check `tasks/active/` first for an existing task. If one covers the work, update it. If not, create one with `/pm-new` before writing code.
- **Log progress.** When completing a meaningful chunk of work, append to the task's Work Log. Keep entries factual and brief.
- **Update acceptance criteria** as you complete them — check the boxes.
- **Move files**, don't copy. Status changes happen by moving the file between status directories.
- **When you finish a task**, use `/pm-done` rather than manually moving files — it triggers dependent checks and CHANGELOG updates.
- **Don't create tasks for trivial, in-session work.** If it's less than 15 minutes of editing, just do it. Tasks are for things that cross sessions or need stakeholder visibility.

## Dependencies

- `depends_on: [PRJ-123]` means "this task cannot start until PRJ-123 is in `done/`".
- A task with unmet dependencies is **waiting**, not blocked. It's just sequenced.
- A task with `status: blocked` is genuinely stuck on something external (review, missing info, another team). Treat these as high-signal in `/pm-status`.
- When a task is completed, `/pm-done` automatically checks whether any dependent tasks are now unblocked and reports them.

## Priorities

- **high** — blocker or on the critical path of the current milestone
- **medium** — important, not urgent
- **low** — nice to have, deferrable

Keep the high queue short. If everything is high, nothing is.

## Tags

Tags group related work. Common patterns:
- Feature areas: `frontend`, `api`, `infra`
- Work types: `bug`, `tech-debt`, `research`
- Cross-cutting: `security`, `performance`

Use the same tag names consistently across tasks in the same area.

## Don'ts

- Don't rewrite old work log entries.
- Don't delete tasks from `done/`.
- Don't reuse IDs.
- Don't check in `.mdpm/sync-state.json`.
- Don't skip the frontmatter — the schema matters for commands and the board.
- Don't let the `inbox/` get huge. Triage weekly at minimum.

## When Things Go Wrong

- **Stale status field:** if a file is in `active/` but frontmatter says `status: backlog`, the directory wins. Update the frontmatter to match.
- **Broken dependency:** if `depends_on` references an ID that doesn't exist anywhere, `/pm-status` will note it. Either fix the ID or remove the dependency.
- **Collision on ID:** two files with the same `id:` — scan `tasks/` with `grep -r "^id:"` and renumber the newer one.

## Sync

Jira and Wrike sync are **optional bridges**. MDPM works fully standalone.

- Sync is driven by MCP servers the user configures. MDPM skills discover available Jira/Wrike MCP tools at runtime rather than hardcoding specific server implementations.
- When no MCP is connected, sync commands degrade gracefully: they print a copy/pasteable summary instead of failing.
- `wrike_id`, `jira_id`, `jira_project` in frontmatter track the link between local tasks and external issues.
- Sync is incremental — only deltas since the last sync are pushed. State is cached in `.mdpm/sync-state.json`.
