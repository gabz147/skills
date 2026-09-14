---
name: claude-plugin-context-mode-ctx-stats
description: "[Ported from Claude plugin marketplace skill] | Show how much context window context-mode saved this session. Displays token consumption, context savings ratio, and per-tool breakdown. Read-only - shows stats only, no reset capability. To wipe the knowledge base entirely, use ctx_purge instead. Trigger: /context-mode:ctx-stats"
---

# Context Mode Stats

## Codex Compatibility

This skill was ported from a Claude skill. Interpret Claude Code-specific wording using Codex equivalents:

- Use `functions.shell_command` for shell commands and filesystem inspection.
- Use `apply_patch` for manual file edits.
- Use `update_plan` for task checklists when a plan is useful.
- Use `web.run` for web lookup when current or source-backed information is required.
- Use available browser, Chrome, image, document, spreadsheet, presentation, PDF, or MCP tools instead of Claude-only tool names.
- Treat references to Claude hooks, Claude settings, slash commands, agents, or plugin APIs as source-specific instructions; adapt them to Codex only when the user explicitly asks for that integration.


Show context savings for the current session.

## Instructions

1. Call the `mcp__context-mode__ctx_stats` MCP tool (no parameters needed).
2. **CRITICAL**: You MUST copy-paste the ENTIRE tool output as markdown text directly into your response message. Do NOT summarize, do NOT collapse, do NOT paraphrase. The user must see the full tables without pressing ctrl+o. Copy every line exactly as returned by the tool.
3. After the full output, add ONE sentence highlighting the key savings metric, e.g.:
   - "context-mode saved **12.4x** - 92% of data stayed in sandbox."
   - If no data yet: "No context-mode calls yet this session."

## Purge

- **`ctx_purge(confirm: true)`** - Permanently deletes all indexed content from the knowledge base. Use `/context-mode:ctx-purge` for this.
