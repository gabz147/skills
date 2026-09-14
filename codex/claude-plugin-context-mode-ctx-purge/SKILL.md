---
name: claude-plugin-context-mode-ctx-purge
description: "[Ported from Claude plugin marketplace skill] | Purge the context-mode knowledge base. Permanently deletes all indexed content and resets session stats. This is destructive and cannot be undone. Trigger: /context-mode:ctx-purge"
---

# Context Mode Purge

## Codex Compatibility

This skill was ported from a Claude skill. Interpret Claude Code-specific wording using Codex equivalents:

- Use `functions.shell_command` for shell commands and filesystem inspection.
- Use `apply_patch` for manual file edits.
- Use `update_plan` for task checklists when a plan is useful.
- Use `web.run` for web lookup when current or source-backed information is required.
- Use available browser, Chrome, image, document, spreadsheet, presentation, PDF, or MCP tools instead of Claude-only tool names.
- Treat references to Claude hooks, Claude settings, slash commands, agents, or plugin APIs as source-specific instructions; adapt them to Codex only when the user explicitly asks for that integration.


Permanently deletes ALL session data for this project: knowledge base, session events, analytics, and stats.

## Instructions

1. **Warn the user**: This is irreversible. Everything will be deleted:
   - FTS5 knowledge base (all indexed content from `ctx_index`, `ctx_fetch_and_index`, `ctx_batch_execute`)
   - Session events DB (analytics, metadata, resume snapshots)
   - Session events markdown file
   - In-memory session stats
2. Call the `mcp__context-mode__ctx_purge` MCP tool with `confirm: true`.
3. Report the result to the user - the response lists exactly what was deleted.

## When to Use

- When the KB contains stale or incorrect content polluting search results.
- When switching between unrelated projects in the same session.
- When you want a completely fresh start for this project.

## Important

- `ctx_purge` is the **only** way to delete session data. No other mechanism exists.
- `ctx_stats` is read-only - shows statistics only.
- `/clear` and `/compact` do NOT affect any context-mode data.
- There is no undo. Re-index content if you need it again.
