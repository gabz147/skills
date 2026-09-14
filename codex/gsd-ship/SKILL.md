---
name: gsd-ship
description: "[Ported from Claude personal skill] Create PR, run review, and prepare for merge after verification passes"
---

## Codex Compatibility

This skill was ported from a Claude skill. Interpret Claude Code-specific wording using Codex equivalents:

- Use `functions.shell_command` for shell commands and filesystem inspection.
- Use `apply_patch` for manual file edits.
- Use `update_plan` for task checklists when a plan is useful.
- Use `web.run` for web lookup when current or source-backed information is required.
- Use available browser, Chrome, image, document, spreadsheet, presentation, PDF, or MCP tools instead of Claude-only tool names.
- Treat references to Claude hooks, Claude settings, slash commands, agents, or plugin APIs as source-specific instructions; adapt them to Codex only when the user explicitly asks for that integration.

<objective>
Bridge local completion  to  merged PR. After /gsd-verify-work passes, ship the work: push branch, create PR with auto-generated body, optionally trigger review, and track the merge.

Closes the plan  to  execute  to  verify  to  ship loop.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/ship.md
</execution_context>

Execute the ship workflow from @$HOME/.claude/get-shit-done/workflows/ship.md end-to-end.
