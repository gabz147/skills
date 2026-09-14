---
name: davinci
description: "[Ported from Claude personal skill] Use when working with DaVinci Resolve on this machine - importing media, building timelines, applying LUTs/grades, rotating/scaling clips, queueing renders, or any Resolve scripting task. Drives Resolve through the in-app daemon bridge installed at C:\\Users\\Tarlu\\cli-anything\\resolve.cmd. Resolve Free on this machine; external IPC blocked, so all calls go through the file-queue bridge. Triggers on /davinci, \"davinci resolve\", \"resolve project\", \"apply lut\", \"render video\", \"edit this clip\", or when the user gives a video file path and asks for color/timeline/render work."
---

# DaVinci Resolve via the bridge

## Codex Compatibility

This skill was ported from a Claude skill. Interpret Claude Code-specific wording using Codex equivalents:

- Use `functions.shell_command` for shell commands and filesystem inspection.
- Use `apply_patch` for manual file edits.
- Use `update_plan` for task checklists when a plan is useful.
- Use `web.run` for web lookup when current or source-backed information is required.
- Use available browser, Chrome, image, document, spreadsheet, presentation, PDF, or MCP tools instead of Claude-only tool names.
- Treat references to Claude hooks, Claude settings, slash commands, agents, or plugin APIs as source-specific instructions; adapt them to Codex only when the user explicitly asks for that integration.


This machine runs DaVinci Resolve **Free** edition. External scripting IPC is blocked by Blackmagic; everything routes through an in-app Python daemon launched from `Workspace  to  Scripts  to  cli_anything_daemon`.

## Launcher

```
C:\Users\Tarlu\cli-anything\resolve.cmd
```

All commands are subcommands of this launcher. The `--json` flag returns structured output suitable for parsing.

## First action every session: liveness check

```powershell
resolve.cmd --json bridge ping
```

- `alive: true`  to  daemon is running, proceed.
- `alive: false` or timeout  to  daemon is not running. Tell the user: *"open Resolve, then click `Workspace  to  Scripts  to  cli_anything_daemon`"*. You CANNOT start it yourself - it must be triggered from inside Resolve's UI. Wait for the user to confirm before continuing.

## Bridge surface

| Command | Purpose |
|---|---|
| `bridge ping` | Liveness check |
| `bridge status` | Queue depth + daemon heartbeat |
| `bridge call TARGET [ARGS...]` | Invoke a Resolve API method |
| `bridge shutdown` | Stop daemon cleanly |
| `bridge purge` | Clear stale queue files (use if things wedge) |

## TARGET semantics

Dotted path against the daemon's root objects: `resolve`, `pm`, `project`, `fusion`. Intermediate segments auto-call as no-arg getters; the final segment is called with `ARGS`.

```powershell
# read state
resolve.cmd --json bridge call resolve.GetCurrentPage
resolve.cmd --json bridge call resolve.GetProjectManager.GetCurrentProject.GetName
resolve.cmd --json bridge call resolve.GetProjectManager.GetCurrentProject.GetTimelineCount

# write state
resolve.cmd --json bridge call resolve.OpenPage color
resolve.cmd --json bridge call pm.SaveProject
```

## Workflow patterns

### Import a clip and put it on a timeline

```powershell
# 1. switch to media page so imports route correctly
resolve.cmd --json bridge call resolve.OpenPage media

# 2. import (use the Media Pool - top-level append to the root folder)
resolve.cmd --json bridge call resolve.GetMediaStorage.AddItemListToMediaPool "C:\path\to\clip.mov"

# 3. open or create a timeline named "v1"
resolve.cmd --json bridge call project.GetMediaPool.CreateEmptyTimeline v1

# 4. add the clip(s) to the current timeline
resolve.cmd --json bridge call project.GetMediaPool.AppendToTimeline
```

### Change timeline resolution (must be done on an EMPTY project setting, or on a new timeline)

Project-level settings - call before creating the timeline:

```powershell
resolve.cmd --json bridge call project.SetSetting timelineResolutionWidth "1920"
resolve.cmd --json bridge call project.SetSetting timelineResolutionHeight "1080"
resolve.cmd --json bridge call project.SetSetting timelineFrameRate "23.976"
```

### Transform a clip (rotate, scale, position)

`timelineItem.SetProperty(name, value)` - known property keys: `Pan`, `Tilt`, `ZoomX`, `ZoomY`, `ZoomGang`, `RotationAngle`, `AnchorPointX`, `AnchorPointY`, `Pitch`, `Yaw`, `FlipX`, `FlipY`.

```powershell
# get the first timeline item on V1
# (use GetItemListInTrack - pass the track type and index)
resolve.cmd --json bridge call project.GetCurrentTimeline.GetItemListInTrack video 1
# then with that item handle in a Python helper, call SetProperty("RotationAngle", 90)
```

For multi-step manipulations like "import clip, rotate, scale, apply LUT, render" - write a Python helper script and either drop it in `%APPDATA%\Blackmagic Design\DaVinci Resolve\Support\Fusion\Scripts\Utility\` to run from Workspace  to  Scripts, OR send it as a series of bridge calls. The bridge supports any dotted path the daemon can resolve, but multi-statement logic (loops, conditionals) is cleaner as an in-Resolve script.

### Apply a LUT

Built-in LUTs live at `C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\LUT\`. The big subfolders are `Film Looks` (cinematic emulations like `Rec709 Kodak 2383 D65.cube`, `Rec709 Fujifilm 3513DI D65.cube`), `Blackmagic Design` (camera color science), `Arri`, `Sony`, `RED`.

**Custom LUTs (downloaded `.cube` files)** must be copied into a LUT folder Resolve scans **and then `project.RefreshLUTList()` must be called before `SetLUT` will accept the path**. Without RefreshLUTList, `SetLUT` silently returns False even with a valid absolute path. Workflow:

```python
# 1. Copy the .cube into a folder Resolve scans (Custom/ subfolder is fine)
# 2. Tell Resolve to rescan
project.RefreshLUTList()
# 3. Now SetLUT accepts the absolute or relative path
item.SetLUT(1, r"C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\LUT\Custom\my.cube")
# 4. Verify with GetLUT - returns the relative path Resolve recorded
item.GetLUT(1)   # -> "Custom\\my.cube"
```

User LUT folder: `%APPDATA%\Blackmagic Design\DaVinci Resolve\Support\LUT\` (note the path is `\LUT\` not `\Fusion\LUTs\` - the latter exists but Resolve doesn't scan it for color page LUTs).

Apply via `timelineItem.SetLUT(nodeIndex, lutPath)` - nodeIndex 1-based since Resolve 16.2.

### Render

Three-step pattern: load a preset, configure, queue:

```powershell
resolve.cmd --json bridge call resolve.OpenPage deliver
resolve.cmd --json bridge call project.LoadRenderPreset "H.264 Master"
resolve.cmd --json bridge call project.SetRenderSettings   # takes a kwargs dict - easier via helper script
resolve.cmd --json bridge call project.AddRenderJob
resolve.cmd --json bridge call project.StartRendering
# poll:
resolve.cmd --json bridge call project.IsRenderingInProgress
```

## When the bridge isn't the right tool

- Anything requiring real-time playback feedback or visual judgement (color grading by eye, motion graphics positioning). Write the script, let the user verify by looking at Resolve.
- Operations that genuinely need the Fusion node graph manipulation - possible via `timelineItem.GetFusionCompByIndex(1).<methods>` but verbose; consider writing a helper script.
- File transcoding / format conversion that doesn't need Resolve's pipeline - use ffmpeg directly.

## Reference

- Full API: `C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting\README.txt` (113 KB; every method documented)
- Memory file with bridge architecture: `~\.claude\projects\C--Users-Tarlu\memory\davinci_resolve_free_bridge.md`
- Bridge source: `C:\Users\Tarlu\cli-anything\davinci-resolve\agent-harness\cli_anything\davinci_resolve\core\bridge.py`
- Daemon source: `C:\Users\Tarlu\AppData\Roaming\Blackmagic Design\DaVinci Resolve\Support\Fusion\Scripts\Utility\cli_anything_daemon.py`

## Gotchas

- `resolve` IS the only top-level root that Resolve injects. `pm`, `project`, `fusion` are pre-resolved by the daemon for convenience.
- Some operations require being on a specific page (color grading wants Color page; rendering wants Deliver). `OpenPage` first if a call fails with no error.
- Project settings keys are case-sensitive Resolve strings; check the README for exact names.
- A response with `_object: PyRemoteObject` means the call returned a Resolve handle that the bridge can't pass back over JSON - chain further methods inline (e.g. `...GetCurrentProject.GetName` instead of two calls).
- LUT paths use Windows backslashes inside Resolve; pass them as raw strings.
