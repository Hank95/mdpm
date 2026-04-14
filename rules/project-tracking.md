# Project Tracking Conventions

This project uses **MDPM** (Markdown Project Manager). All task state lives in markdown files under `tasks/`. Status is a directory.

Read this file in full before doing project management work in this repo.

## Directory Layout

```
tasks/
  inbox/     # untriaged incoming requests (may be auto-populated by Jira/Wrike sync)
  backlog/   # queued work, prioritized
  active/    # in progress right now
  done/      # completed work — never delete from here
docs/
  ROADMAP.md    # current milestone and future work
  DECISIONS.md  # architecture decision log (ADR)
  CHANGELOG.md  # shipped work, newest first
.mdpm/
  config.json        # per-project MDPM config (ID prefix, sync settings)
  sync-state.json    # local sync cache — gitignored
```

## The Golden Rules

1. **Markdown is the source of truth.** Not Jira, not Wrike, not a DB. `.md` files.
2. **Status = directory.** Moving a file changes its status. Don't keep stale `status:` fields; treat the directory as authoritative when they disagree, and fix the frontmatter.
3. **One file per task.** So Claude can read/edit a single task without loading the whole system.
4. **Never delete task files** — except rejected inbox items. Everything else moves to `done/` and stays there.
5. **Work logs are append-only.** Never rewrite history.
6. **IDs are permanent and unique.** Never reuse.
7. **Small, focused tasks.** If a task would take more than a couple of days, decompose it with `/pm:plan`.

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
wrike_id: null        # populated by /pm:sync-wrike
jira_id: null         # populated by /pm:sync-jira
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

1. **Capture.** `/pm:new <title>` creates a backlog task. Inbox items come in via sync or direct drop.
2. **Triage.** `/pm:inbox` walks through incoming items.
3. **Plan.** `/pm:plan <feature>` breaks large work into sized tasks.
4. **Pick.** `/pm:next` recommends what to start, or `/pm:status` shows the dashboard.
5. **Work.** Move the task file from `backlog/` to `active/`. Update the work log as you go.
6. **Ship.** `/pm:done <id>` moves to `done/`, checks dependents, updates CHANGELOG.
7. **Report.** `/pm:standup` produces a stakeholder summary.
8. **(Optional) Sync.** `/pm:sync-jira` / `/pm:sync-wrike` push status outward.

## How Claude Should Behave

When working in a repo that uses MDPM:

- **Start sessions** by reading `docs/ROADMAP.md` to understand current priorities. Optionally run `/pm:status` to see active work.
- **When asked to work on a feature**, check `tasks/active/` first for an existing task. If one covers the work, update it. If not, create one with `/pm:new` before writing code.
- **Log progress.** When completing a meaningful chunk of work, append to the task's Work Log. Keep entries factual and brief.
- **Update acceptance criteria** as you complete them — check the boxes.
- **Move files**, don't copy. Status changes happen by moving the file between status directories.
- **When you finish a task**, use `/pm:done` rather than manually moving files — it triggers dependent checks and CHANGELOG updates.
- **Don't create tasks for trivial, in-session work.** If it's less than 15 minutes of editing, just do it. Tasks are for things that cross sessions or need stakeholder visibility.

## Dependencies

- `depends_on: [PRJ-123]` means "this task cannot start until PRJ-123 is in `done/`".
- A task in `active/` or `backlog/` with unmet dependencies shows up as a blocker in `/pm:status`.
- When a task is completed, `/pm:done` automatically checks whether any dependent tasks are now unblocked and reports them.

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
- **Broken dependency:** if `depends_on` references an ID that doesn't exist anywhere, `/pm:status` will note it. Either fix the ID or remove the dependency.
- **Collision on ID:** two files with the same `id:` — scan `tasks/` with `grep -r "^id:"` and renumber the newer one.

## Sync

Jira and Wrike sync are **optional bridges**. MDPM works fully standalone.

- Sync is driven by MCP servers the user configures. MDPM skills discover available Jira/Wrike MCP tools at runtime rather than hardcoding specific server implementations.
- When no MCP is connected, sync commands degrade gracefully: they print a copy/pasteable summary instead of failing.
- `wrike_id`, `jira_id`, `jira_project` in frontmatter track the link between local tasks and external issues.
- Sync is incremental — only deltas since the last sync are pushed. State is cached in `.mdpm/sync-state.json`.
