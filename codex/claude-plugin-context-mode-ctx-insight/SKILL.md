---
name: claude-plugin-context-mode-ctx-insight
description: "[Ported from Claude plugin marketplace skill] | Open the context-mode Insight analytics dashboard in the browser. Shows personal metrics: session activity, tool usage, error rate, parallel work patterns, project focus, and actionable insights. First run installs dependencies (~30s). Subsequent runs open instantly. Trigger: /context-mode:ctx-insight"
---

# Context Mode Insight

## Codex Compatibility

This skill was ported from a Claude skill. Interpret Claude Code-specific wording using Codex equivalents:

- Use `functions.shell_command` for shell commands and filesystem inspection.
- Use `apply_patch` for manual file edits.
- Use `update_plan` for task checklists when a plan is useful.
- Use `web.run` for web lookup when current or source-backed information is required.
- Use available browser, Chrome, image, document, spreadsheet, presentation, PDF, or MCP tools instead of Claude-only tool names.
- Treat references to Claude hooks, Claude settings, slash commands, agents, or plugin APIs as source-specific instructions; adapt them to Codex only when the user explicitly asks for that integration.


Open the personal analytics dashboard in the browser.

## Instructions

1. Call the `ctx_insight` MCP tool (no parameters needed, or pass `port: 4747` to customize). Optional data-dir overrides: `sessionDir`/`insightSessionDir` for `INSIGHT_SESSION_DIR`, and `contentDir`/`insightContentDir` for `INSIGHT_CONTENT_DIR`.
2. The tool will:
   - Copy source files to cache (first run only)
   - Install dependencies (first run only, ~30s)
   - Build the dashboard (~1s)
   - Start a local server
   - Open the browser
3. Display the tool's output to the user - it contains progress steps and the dashboard URL.
4. Tell the user:
   - "Dashboard is running at http://localhost:4747"
   - "Refresh the page to see updated metrics"
   - "Dashboard stops automatically when Claude exits. To stop sooner: kill the PID shown above."
