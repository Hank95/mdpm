---
name: pm:board
description: Print the command to launch the local kanban board (does not start a background server)
argument-hint: "[port]"
---

# /pm:board

Tell the user how to start the zero-dependency kanban board for this project.

`$ARGUMENTS` — optional port number (default 8765).

## Steps

1. **Locate the board script.**
   - First check if `board/serve.py` exists in the current repo root. If yes, this was installed locally during `/pm:config`.
   - Otherwise, point at the plugin's copy at `${CLAUDE_PLUGIN_ROOT}/board/serve.py`. The plugin version reads tasks from the current working directory by default.

2. **Print the command** (do NOT run it — the server is long-running and should not be started inside the Claude Code session; it must run in the user's own terminal):

   If `board/serve.py` exists locally:
   ```
   Run this in a separate terminal from your project root:

       python3 board/serve.py --port <PORT>

   Then open http://127.0.0.1:<PORT> in your browser.
   ```

   If using the plugin copy:
   ```
   Run this in a separate terminal from your project root:

       python3 ${CLAUDE_PLUGIN_ROOT}/board/serve.py --port <PORT>

   Then open http://127.0.0.1:<PORT> in your browser.
   ```

   Substitute the actual expanded plugin path when printing to the user — they need a literal runnable command, not a shell variable they have to resolve.

3. **Tell them what to expect:**
   - Four columns: Inbox, Backlog, Active, Done.
   - Auto-refreshes every 10 seconds; they don't need to restart the server after editing task files.
   - Search box filters by title, tag, ID, or assignee.
   - Priority and tag filters available via the dropdowns.
   - Read-only — to change task state, use `/pm:start`, `/pm:done`, `/pm:edit`, or edit the `.md` files directly.

4. **Offer to install the board locally** if the plugin version is being used and the user wants a permanent `board/` directory in their repo (copy `serve.py` and `board.html` from the plugin). Ask before doing it.

## Notes

- **Do not run the server yourself.** It's a long-running process; starting it as a background Bash command inside this session will strand it.
- If the user says "just start it for me," explain that they need to run it in their own terminal so they retain control (Ctrl+C to stop, visible logs, etc.) and give them a copy/pasteable command.
