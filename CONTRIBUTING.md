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
6. **Zero runtime dependencies.** Python stdlib only — for the CLI, the board, and the tests.
7. **Sync is optional and MCP-agnostic.** Skills discover available Jira/Wrike MCPs at runtime; they never hardcode a specific server.
8. **Graceful degradation.** If an optional integration isn't available, print a copy/pasteable summary instead of failing.

Changes that violate these principles need a strong justification and a discussion up front.

## Repo layout

```
.claude-plugin/       plugin.json + marketplace.json
skills/pm-*/SKILL.md  one skill per slash command
rules/                project-tracking.md — first section injected at session start
hooks/                hooks.json — SessionStart hook that runs `mdpm session-context`
bin/, lib/            the CLI and the core library it shares with the board
tests/                unittest suite
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

The CLI, the core library, and the board server are covered by a standard-library test suite. Run it before opening a PR — CI runs the same command on Python 3.11 and 3.14:

```bash
python3 -m unittest discover -s tests
```

Bug fixes should come with a test that fails without the fix. If you touch frontmatter handling, the rule to preserve is in `tests/test_frontmatter.py`: rewriting a task must leave every line it didn't need to change byte-identical.

Skills are prompts, so they can't be unit-tested. If you change one, exercise it by hand:

1. A clean `/pm-config` in an empty git repo
2. The full flow: `/pm-new` → `/pm-start` → `/pm-done`
3. `/pm-status` output with a mix of backlog, active, blocked, and waiting tasks
4. `/pm-sync-jira` and `/pm-sync-wrike` with no MCP connected — both must fall back to a copy/pasteable summary, not fail

Validate the manifests with `claude plugin validate .`.

## Commit style

- Use the imperative mood ("Add /pm-plan skill", not "Added /pm-plan skill")
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
