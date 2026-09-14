---
name: claude-plugin-plugins-cwc-makers-cardputer-buddy
description: "[Ported from Claude plugin marketplace skill] Iterate on the Cardputer-Adv MicroPython app bundle (Codex Buddy, Snake, Hello) after the device is already provisioned via m5-onboard. Use when the user wants to add a new app, push a single changed .py without re-flashing, watch device serial logs, or run a one-shot REPL command. Trigger on \"add an app\", \"push to the cardputer\", \"tail the device\", \"run on the device\", or follow-up work after /maker-setup."
---

# Cardputer Buddy app bundle

## Codex Compatibility

This skill was ported from a Claude skill. Interpret Claude Code-specific wording using Codex equivalents:

- Use `functions.shell_command` for shell commands and filesystem inspection.
- Use `apply_patch` for manual file edits.
- Use `update_plan` for task checklists when a plan is useful.
- Use `web.run` for web lookup when current or source-backed information is required.
- Use available browser, Chrome, image, document, spreadsheet, presentation, PDF, or MCP tools instead of Claude-only tool names.
- Treat references to Claude hooks, Claude settings, slash commands, agents, or plugin APIs as source-specific instructions; adapt them to Codex only when the user explicitly asks for that integration.


The `buddy/` directory in the local `build-with-claude` clone is the MicroPython payload that `m5-onboard` installs onto `/flash/`. Work inside that clone.

## Device layout

```
/flash/
??? main.py              launcher menu (replaces UIFlow's boot flow)
??? buddy_*.py           shared libs (BLE, UI, state, protocol, chars)
??? burst_frames.py      sprite frames
??? apps/
    ??? claude_buddy.py  BLE client  to  Claude Desktop's Hardware Buddy
    ??? hello_cardputer.py
    ??? snake.py
```

`main.py` scans `/flash/apps/` at boot and lists every `.py` as a menu entry. Drop a file into `buddy/device/apps/`, push it, and it appears on next boot.

## Adding an app

Crib from `buddy/device/apps/hello_cardputer.py` - smallest example of keyboard polling, font, and exit conventions. Then push without re-flashing:

```bash
python3 onboard/scripts/install_apps.py --port <PORT> --src buddy
```

`<PORT>` is whatever `detect.py` reported last run (e.g. `/dev/cu.usbmodem1101`, `/dev/ttyACM0`, `COM3`).

## Dev loop tooling (`buddy/scripts/`)

```bash
# Push a subset of files over USB-serial
python3 buddy/scripts/push.py --port <PORT> --files apps/snake.py

# Watch device logs
python3 buddy/scripts/tail_serial.py --port <PORT>

# One-shot REPL exec
python3 buddy/scripts/repl_run.py --port <PORT> --script "import os; print(os.listdir('/flash'))"
```
