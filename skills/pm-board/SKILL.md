---
name: pm-board
description: Print the command to launch the local kanban board (does not start a background server)
argument-hint: "[port]"
---

# /pm-board

Tell the user how to start the zero-dependency kanban board.

`$ARGUMENTS` — optional port number (default 8765).

## What to say

The CLI ships a `board` subcommand that locates `serve.py` relative to the installed plugin (so there are no hardcoded paths), points it at the current project, and opens the browser automatically:

```
Run this in a separate terminal, from your project root:

    python3 ${CLAUDE_PLUGIN_ROOT}/bin/mdpm board [--port <PORT>]

Ctrl+C to stop. It'll open http://127.0.0.1:<port> in your default browser.
```

Substitute the actual expanded plugin path when printing to the user — they need a verbatim command, not a shell variable.

If the user has set up a shell alias (e.g. `alias mdpm="python3 ${CLAUDE_PLUGIN_ROOT}/bin/mdpm"`), they can just run `mdpm board`.

## Flags to mention if asked

- `--port N` — override the default 8765
- `--no-open` — start the server without opening a browser (useful when running over SSH / Tailscale)
- `--strict-port` — fail instead of auto-walking forward when the port is busy
- `--host 0.0.0.0` — bind beyond loopback (useful for Tailscale or LAN access). **Warn the user** that the board exposes read/write endpoints to anyone who can reach the host:port — only do this on a trusted network.

## What to expect

- Four columns: Inbox, Backlog, Active, Done.
- Auto-refreshes every 10 seconds; no restart needed after `.md` edits.
- Search box + priority/assignee dropdowns.
- Click any card for the detail modal; **Edit** opens the raw markdown in-browser with Cmd/Ctrl+S to save and mtime-based conflict detection.
- `report bug` link in the header goes to the MDPM issue tracker.
- Port auto-walks forward if the default is busy (disable with `--strict-port`).

## Notes

- **Do not start the server yourself.** It's long-running — backgrounding it inside this session would strand the process. Give the user a copy/pasteable command to run in their own terminal.
- If the user previously opted into a local copy via an older `/pm-config` and has `./board/` in their repo, the plugin-path invocation still supersedes it. They can delete `./board/` if they want to eliminate the stale copy.
