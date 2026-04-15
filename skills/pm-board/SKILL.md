---
name: pm:board
description: Print the command to launch the local kanban board (does not start a background server)
argument-hint: "[port]"
---

# /pm:board

Tell the user how to start the zero-dependency kanban board.

`$ARGUMENTS` — optional port number (default 8765).

## Steps

1. **Recommend running from the plugin directly.** This always picks up the latest board UI when MDPM is updated; a copy installed into the user's repo via `/pm:config` can go stale after `/plugin update`.

   Print this (substitute the actual plugin path and port — don't leave `${CLAUDE_PLUGIN_ROOT}` as a literal since the user needs a runnable command):

   ```
   Run this in a separate terminal, from your project root:

       python3 ${CLAUDE_PLUGIN_ROOT}/board/serve.py --root . --port <PORT>

   Then open http://127.0.0.1:<PORT> in your browser.
   ```

2. **Mention the fallback** — if the user previously copied `board/serve.py` into their repo via `/pm:config`, they can still run `python3 board/serve.py` from the project root, but they should occasionally refresh the copy after plugin updates:
   ```
   cp ${CLAUDE_PLUGIN_ROOT}/board/board.html ./board/board.html
   cp ${CLAUDE_PLUGIN_ROOT}/board/serve.py    ./board/serve.py
   ```

3. **Tell them what to expect:**
   - Four columns: Inbox, Backlog, Active, Done.
   - Auto-refreshes every 10 seconds.
   - Search box filters by title, tag, ID, or assignee; priority and assignee dropdowns narrow further.
   - Click any card for the full detail modal; hit **Edit** to modify the raw markdown in-browser with conflict detection on save (Cmd/Ctrl+S).
   - `report bug` link in the header goes to the MDPM issue tracker.
   - Port is auto-walked forward if the default is busy; pass `--strict-port` if you need a deterministic port for scripting.

4. **Do not run the server yourself.** It's a long-running process; starting it as a background Bash command inside this session would strand it. Give the user a copy/pasteable command instead.

## Notes

- If the user previously ran `/pm:config` with the board option, their repo has a `board/` directory. Running from that local copy still works, but it won't pick up UI improvements shipped in later plugin versions unless they recopy. The plugin-path invocation avoids this entirely.
- Preferred default: plugin-path invocation. Only suggest the local-copy path if the user asks or already has it set up.
