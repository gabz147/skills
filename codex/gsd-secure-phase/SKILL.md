---
name: gsd-secure-phase
description: "[Ported from Claude personal skill] Retroactively verify threat mitigations for a completed phase"
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
Verify threat mitigations for a completed phase. Three states:
- (A) SECURITY.md exists - audit and verify mitigations
- (B) No SECURITY.md, PLAN.md with threat model exists - run from artifacts
- (C) Phase not executed - exit with guidance

Output: updated SECURITY.md.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/secure-phase.md
</execution_context>

<context>
Phase: $ARGUMENTS - optional, defaults to last completed phase.
</context>

<process>
Execute @$HOME/.claude/get-shit-done/workflows/secure-phase.md.
Preserve all workflow gates.
</process>
