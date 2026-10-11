---
name: gsd-audit-fix
description: "[Ported from Claude personal skill] Autonomous audit-to-fix pipeline - find issues, classify, fix, test, commit"
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
Run an audit, classify findings as auto-fixable vs manual-only, then autonomously fix
auto-fixable issues with test verification and atomic commits.

Flags:
- `--max N` - maximum findings to fix (default: 5)
- `--severity high|medium|all` - minimum severity to process (default: medium)
- `--dry-run` - classify findings without fixing (shows classification table)
- `--source <audit>` - which audit to run (default: audit-uat)
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/audit-fix.md
</execution_context>

<process>
Execute the audit-fix workflow from @$HOME/.claude/get-shit-done/workflows/audit-fix.md end-to-end.
</process>
