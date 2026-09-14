---
name: gsd-help
description: "[Ported from Claude personal skill] Show available GSD commands and usage guide"
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
Display the complete GSD command reference.

Output ONLY the reference content below. Do NOT add:
- Project-specific analysis
- Git status or file context
- Next-step suggestions
- Any commentary beyond the reference
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/help.md
</execution_context>

<process>
Output the complete GSD command reference from @$HOME/.claude/get-shit-done/workflows/help.md.
Display the reference content directly - no additions or modifications.
</process>
