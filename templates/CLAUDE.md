# Project Instructions

## Project Tracking

This project uses **MDPM** (Markdown Project Manager), installed as a Claude Code plugin. Task state lives in markdown files under `tasks/`; status is a directory.

**Quick reference:**

- `tasks/inbox/` — untriaged requests
- `tasks/backlog/` — queued work
- `tasks/active/` — in progress
- `tasks/done/` — completed (never delete)
- `tasks/archive/` — old completed work moved aside to reduce clutter (still searchable)
- `docs/ROADMAP.md` — milestones and priorities
- `docs/DECISIONS.md` — architecture decision log
- `docs/CHANGELOG.md` — shipped work

**Start every session** by reading `docs/ROADMAP.md` to understand current priorities, then run `/pm:status` for a dashboard.

**Commands:** `/pm:help` lists them all. Most-used: `/pm:status`, `/pm:next`, `/pm:new <title>`, `/pm:start <id>`, `/pm:done <id>`, `/pm:standup`.

The full conventions (task format, golden rules, sync behavior) are loaded automatically by the MDPM plugin — no need to reference an external path here.
