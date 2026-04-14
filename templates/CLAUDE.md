# Project Instructions

## Project Tracking

This project uses **MDPM** (Markdown Project Manager). Full conventions live in the plugin's rules file at `${CLAUDE_PLUGIN_ROOT}/rules/project-tracking.md` — read it before doing project-management work here.

**Quick reference:**

- `tasks/inbox/` — untriaged requests
- `tasks/backlog/` — queued work
- `tasks/active/` — in progress
- `tasks/done/` — completed (never delete)
- `docs/ROADMAP.md` — milestones and priorities
- `docs/DECISIONS.md` — architecture decision log
- `docs/CHANGELOG.md` — shipped work

**Start every session** by reading `docs/ROADMAP.md` to understand current priorities. Run `/pm:status` for a dashboard.

Use `/pm:help` to see all available project management commands.
