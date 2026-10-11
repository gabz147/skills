---
name: gsd-new-project
description: "[Ported from Claude personal skill] Initialize a new project with deep context gathering and PROJECT.md"
---

## Codex Compatibility

This skill was ported from a Claude skill. Interpret Claude Code-specific wording using Codex equivalents:

- Use `functions.shell_command` for shell commands and filesystem inspection.
- Use `apply_patch` for manual file edits.
- Use `update_plan` for task checklists when a plan is useful.
- Use `web.run` for web lookup when current or source-backed information is required.
- Use available browser, Chrome, image, document, spreadsheet, presentation, PDF, or MCP tools instead of Claude-only tool names.
- Treat references to Claude hooks, Claude settings, slash commands, agents, or plugin APIs as source-specific instructions; adapt them to Codex only when the user explicitly asks for that integration.

<runtime_note>
**Copilot (VS Code):** Use `vscode_askquestions` wherever this workflow calls `AskUserQuestion`. They are equivalent - `vscode_askquestions` is the VS Code Copilot implementation of the same interactive question API.
</runtime_note>

<context>
**Flags:**
- `--auto` - Automatic mode. After config questions, runs research  to  requirements  to  roadmap without further interaction. Expects idea document via @ reference.
</context>

<objective>
Initialize a new project through unified flow: questioning  to  research (optional)  to  requirements  to  roadmap.

**Creates:**
- `.planning/PROJECT.md` - project context
- `.planning/config.json` - workflow preferences
- `.planning/research/` - domain research (optional)
- `.planning/REQUIREMENTS.md` - scoped requirements
- `.planning/ROADMAP.md` - phase structure
- `.planning/STATE.md` - project memory

**After this command:** Run `/gsd-plan-phase 1` to start execution.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/new-project.md
@$HOME/.claude/get-shit-done/references/questioning.md
@$HOME/.claude/get-shit-done/references/ui-brand.md
@$HOME/.claude/get-shit-done/templates/project.md
@$HOME/.claude/get-shit-done/templates/requirements.md
</execution_context>

<process>
Execute the new-project workflow from @$HOME/.claude/get-shit-done/workflows/new-project.md end-to-end.
Preserve all workflow gates (validation, approvals, commits, routing).
</process>
