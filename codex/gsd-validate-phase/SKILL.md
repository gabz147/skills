---
name: gsd-validate-phase
description: "[Ported from Claude personal skill] Retroactively audit and fill Nyquist validation gaps for a completed phase"
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
Audit Nyquist validation coverage for a completed phase. Three states:
- (A) VALIDATION.md exists - audit and fill gaps
- (B) No VALIDATION.md, SUMMARY.md exists - reconstruct from artifacts
- (C) Phase not executed - exit with guidance

Output: updated VALIDATION.md + generated test files.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/validate-phase.md
</execution_context>

<context>
Phase: $ARGUMENTS - optional, defaults to last completed phase.
</context>

<process>
Execute @$HOME/.claude/get-shit-done/workflows/validate-phase.md.
Preserve all workflow gates.
</process>
