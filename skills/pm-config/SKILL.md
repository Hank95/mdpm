---
name: pm:config
description: Initialize or reconfigure MDPM (ID prefix, task directories, sync preferences)
argument-hint: ""
disable-model-invocation: true
---

# /pm:config

First-time setup (or reconfiguration) for MDPM in the current repo.

## Steps

1. **Check existing state.** Look for:
   - `tasks/` directory with `backlog/`, `active/`, `done/`, `inbox/` subdirectories
   - `docs/ROADMAP.md`, `docs/DECISIONS.md`, `docs/CHANGELOG.md`
   - `.mdpm/config.json`
   - A `CLAUDE.md` at the repo root that references project tracking

   If everything exists, tell the user "MDPM is already initialized. Run `/pm:config` to modify settings, or start with `/pm:status`."

2. **Walk through setup.** Ask only what you need, one question at a time:

   **a. ID prefix.** What prefix should tasks use? Examples: `PRJ-`, `ENG-`, a project abbreviation. Default: `PRJ-`.

   **b. Default assignee.** Who's the primary owner for new tasks? (Name, not email.)

   **c. Stakeholder audiences.** (Optional.) For `/pm:standup` customization — names/titles of people who'll read the output. Skip if just for personal use.

   **d. Sync layer.** Do you plan to sync to Jira, Wrike, both, or neither? If one is selected:
      - For Jira: ask for the default project key (e.g. `ENG`).
      - For Wrike: ask for a default folder (can be filled later via `/pm:sync-wrike`).
      - Remind them they still need an MCP server configured for the sync to work automatically.

   **e. Kanban board.** Do you want the local kanban board installed? If yes, we'll drop `board.html` and `serve.py` into a `board/` subdirectory at the repo root.

3. **Create the layout:**
   ```
   tasks/
     backlog/.gitkeep
     active/.gitkeep
     done/.gitkeep
     inbox/.gitkeep
   docs/
     ROADMAP.md       (if missing)
     DECISIONS.md     (if missing)
     CHANGELOG.md     (if missing)
   .mdpm/
     config.json
   ```

   Use the templates shipped with the MDPM plugin at `${CLAUDE_PLUGIN_ROOT}/templates/` where possible. Don't overwrite existing files — if `ROADMAP.md` exists, leave it alone.

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

5. **Add the rules file reference to `CLAUDE.md`.** If a `CLAUDE.md` exists, append a Project Tracking section pointing at the plugin's rules file. If not, create one from the template. The reference should look like:

   ```
   ## Project Tracking
   This project uses MDPM. See the conventions at `${CLAUDE_PLUGIN_ROOT}/rules/project-tracking.md`.

   Quick ref: `tasks/backlog/` queued, `tasks/active/` in progress, `tasks/done/` shipped, `tasks/inbox/` untriaged.
   Run `/pm:help` to list commands, `/pm:status` for a dashboard.
   ```

6. **Optionally install the board.** If the user opted in, copy `board.html` and `serve.py` to `board/` in the repo. Tell them to run `python3 board/serve.py` to view.

7. **Confirm.** Print a summary of what was created, and suggest `/pm:new` to create the first task.

## Notes

- Don't overwrite existing files silently. If `.mdpm/config.json` exists, show the current values and ask which to change.
- This is the only command that creates directories outside of `tasks/`. Keep the footprint minimal.
- `.mdpm/` should be git-tracked (it holds config), but `.mdpm/sync-state.json` should be gitignored (it's local sync cache).
