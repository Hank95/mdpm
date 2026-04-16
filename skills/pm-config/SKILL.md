---
description: Initialize or reconfigure MDPM (ID prefix, task directories, sync preferences)
---

# /pm-config

First-time setup (or reconfiguration) for MDPM in the current repo.

## Steps

1. **Check existing state.** Look for:
   - `tasks/` directory with `backlog/`, `active/`, `done/`, `inbox/` subdirectories
   - `docs/ROADMAP.md`, `docs/DECISIONS.md`, `docs/CHANGELOG.md`
   - `.mdpm/config.json`
   - A `CLAUDE.md` at the repo root that references project tracking

   If everything exists, tell the user "MDPM is already initialized. Run `/pm-config` to modify settings, or start with `/pm-status`."

2. **Walk through setup.** Ask only what you need, one question at a time:

   **a. ID prefix.** What prefix should tasks use? Examples: `PRJ-`, `ENG-`, a project abbreviation. Default: `PRJ-`.

   **b. Default assignee.** Who's the primary owner for new tasks? (Name, not email.)

   **c. Stakeholder audiences.** (Optional.) For `/pm-standup` customization — names/titles of people who'll read the output. Skip if just for personal use.

   **d. Sync layer.** Do you plan to sync to Jira, Wrike, both, or neither? If one is selected:
      - For Jira: ask for the default project key (e.g. `ENG`).
      - For Wrike: ask for a default folder (can be filled later via `/pm-sync-wrike`).
      - Remind them they still need an MCP server configured for the sync to work automatically.

   **e. Kanban board.** The board is available two ways:
   - **Recommended:** run it from the plugin directly (`python3 ${CLAUDE_PLUGIN_ROOT}/board/serve.py --root .`). Always current after `/plugin update mdpm`.
   - **Local copy:** drop `board.html` and `serve.py` into `board/` in the repo. Self-contained but goes stale after plugin updates — requires recopying.

   Default to the plugin-path approach (don't copy anything). Only copy the files if the user explicitly asks for a self-contained local install.

3. **Create the layout:**
   ```
   tasks/
     backlog/.gitkeep
     active/.gitkeep
     done/.gitkeep
     inbox/.gitkeep
     archive/.gitkeep   # for /pm-archive to move aged done tasks into
   docs/
     ROADMAP.md       (if missing)
     DECISIONS.md     (if missing)
     CHANGELOG.md     (if missing)
   .mdpm/
     config.json
   ```

   Use the templates shipped with the MDPM plugin (find them at `${CLAUDE_PLUGIN_ROOT}/templates/` if you need to read them) — but do NOT write the plugin path into user files. Don't overwrite existing files: if `ROADMAP.md` exists, leave it alone.

4. **Write `.mdpm/config.json`** with the answers from step 2:
   ```json
   {
     "id_prefix": "PRJ-",
     "default_assignee": "Henry",
     "stakeholders": [],
     "jira": {
       "default_project": "ENG",
       "status_map": {"backlog": "To Do", "active": "In Progress", "blocked": "Blocked", "done": "Done"},
       "priority_map": {"high": "High", "medium": "Medium", "low": "Low"}
     },
     "wrike": {
       "folder_id": null
     }
   }
   ```

5. **Ensure `CLAUDE.md` has a Project Tracking section.** If a `CLAUDE.md` exists at the repo root, append the section below (don't clobber existing content). If not, create one by copying `${CLAUDE_PLUGIN_ROOT}/templates/CLAUDE.md` into the repo root.

   **Critical:** the block you write into the user's `CLAUDE.md` must NOT contain any `${CLAUDE_PLUGIN_ROOT}` references or absolute paths. The plugin loads its own rules file automatically when skills run — the project's `CLAUDE.md` just needs to orient Claude to the directory layout and point at `/pm-help`.

   Use this exact block (literally — do not expand any variables, do not insert absolute paths):

   ```
   ## Project Tracking

   This project uses **MDPM** (Markdown Project Manager).

   Quick ref: `tasks/inbox/` untriaged, `tasks/backlog/` queued, `tasks/active/` in progress, `tasks/done/` shipped, `tasks/archive/` aged-out.
   Run `/pm-help` to list commands, `/pm-status` for a dashboard.
   ```

6. **Kanban board setup** (follows from step 2e).
   - **Default (plugin-path):** don't copy anything into the repo. Tell the user:
     ```
     Run the board with:
         python3 ${CLAUDE_PLUGIN_ROOT}/board/serve.py --root .
     ```
     Substitute the actual expanded plugin path when printing so it's runnable verbatim.
   - **Only if the user asked for a local copy:** copy `board.html` and `serve.py` from the plugin to a `board/` directory in the repo, and remind them they'll need to refresh those files manually after `/plugin update mdpm` or they'll miss UI improvements.

7. **Update `.gitignore`.** `.mdpm/config.json` is intended to be committed (project-wide config), but `.mdpm/sync-state.json` is a local sync cache and should not be. Ensure the repo's `.gitignore` includes:
   ```
   # MDPM local sync cache
   .mdpm/sync-state.json
   ```
   - If `.gitignore` exists and already contains a `.mdpm/sync-state.json` entry, leave it alone.
   - If `.gitignore` exists but is missing the entry, append the two lines above.
   - If `.gitignore` doesn't exist, create one with just those lines. (Don't dump a kitchen-sink gitignore into someone's project.)

8. **Confirm.** Print a summary of what was created, and suggest `/pm-new` to create the first task.

## Notes

- Don't overwrite existing files silently. If `.mdpm/config.json` exists, show the current values and ask which to change.
- This is the only command that creates directories outside of `tasks/`. Keep the footprint minimal.
- `.mdpm/` should be git-tracked (it holds config), but `.mdpm/sync-state.json` should be gitignored (it's local sync cache).
