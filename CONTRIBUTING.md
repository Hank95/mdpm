# Contributing to MDPM

Thanks for taking a look. MDPM is small on purpose — it's meant to stay lightweight and markdown-native — but ideas, bug reports, and focused PRs are welcome.

## Before opening a PR

Please open an issue first if you're proposing:

- A new skill (the surface area of `/pm-*` commands)
- A change to the task schema (frontmatter fields, filename convention)
- Writeable endpoints on the kanban server
- Anything that adds a runtime dependency (Python packages, npm, etc. — MDPM is stdlib-only by design)

Small bug fixes and typo corrections can go straight to a PR.

## Design principles

When in doubt, check the design decisions before proposing changes:

1. **Markdown is the source of truth.** No database, no required API.
2. **Status is a directory.** Filesystem state is self-documenting.
3. **One file per task.** So Claude can read/edit tasks without loading everything.
4. **Append-only work logs.** Never rewrite history.
5. **Never delete task files** (except rejected inbox items).
6. **Zero runtime dependencies** for the board. Python stdlib only.
7. **Sync is optional and MCP-agnostic.** Skills discover available Jira/Wrike MCPs at runtime; they never hardcode a specific server.
8. **Graceful degradation.** If an optional integration isn't available, print a copy/pasteable summary instead of failing.

Changes that violate these principles need a strong justification and a discussion up front.

## Repo layout

```
.claude-plugin/       plugin.json + marketplace.json
skills/pm-*/SKILL.md  one skill per slash command
rules/                project-tracking.md — loaded into Claude's context
templates/            files copied into user repos by /pm-config
board/                zero-dependency kanban (serve.py + board.html)
examples/             sample task files
```

## Local development

Clone and point Claude Code at the local directory:

```bash
git clone https://github.com/Hank95/mdpm
cd mdpm
# In Claude Code:
/plugin marketplace add .
/plugin install mdpm
/reload-plugins
/pm-help
```

Edit a skill's `SKILL.md`, run `/reload-plugins`, re-invoke the skill. Iteration loop is fast because it's just markdown.

## Testing

There's no formal test suite. Before opening a PR, exercise:

1. A clean `/pm-config` in an empty git repo
2. The full flow: `/pm-new` → `/pm-start` → `/pm-done`
3. `/pm-status` output with a mix of backlog, active, blocked, and waiting tasks
4. `/pm-sync-jira` and `/pm-sync-wrike` with no MCP connected — both must fall back to a copy/pasteable summary, not fail
5. The board: `python3 board/serve.py` — check that tasks render, filters work, auto-refresh picks up file changes

If your change touches `serve.py`, also smoke-test:

```bash
python3 -c "from board.serve import load_all_tasks, parse_frontmatter; print('ok')"
```

## Commit style

- Use the imperative mood ("Add /pm-block skill", not "Added /pm-block skill")
- First line under ~72 chars
- Body optional but encouraged for anything non-trivial — explain *why*, not *what*

## Versioning

MDPM uses semver. When bumping:

1. Update `version` in **both** `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`
2. Merge to `main`
3. Tag the release: `git tag -a v0.X.0 -m "summary" && git push origin v0.X.0`

Users pick up the new version via `/plugin marketplace update mdpm && /plugin update mdpm`.

## License

By contributing you agree that your contributions will be licensed under the repo's MIT license.
