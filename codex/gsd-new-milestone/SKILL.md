---
name: gsd-new-milestone
description: "[Ported from Claude personal skill] Start a new milestone cycle - update PROJECT.md and route to requirements"
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
Start a new milestone: questioning  to  research (optional)  to  requirements  to  roadmap.

Brownfield equivalent of new-project. Project exists, PROJECT.md has history. Gathers "what's next", updates PROJECT.md, then runs requirements  to  roadmap cycle.

**Creates/Updates:**
- `.planning/PROJECT.md` - updated with new milestone goals
- `.planning/research/` - domain research (optional, NEW features only)
- `.planning/REQUIREMENTS.md` - scoped requirements for this milestone
- `.planning/ROADMAP.md` - phase structure (continues numbering)
- `.planning/STATE.md` - reset for new milestone

**After:** `/gsd-plan-phase [N]` to start execution.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/new-milestone.md
@$HOME/.claude/get-shit-done/references/questioning.md
@$HOME/.claude/get-shit-done/references/ui-brand.md
@$HOME/.claude/get-shit-done/templates/project.md
@$HOME/.claude/get-shit-done/templates/requirements.md
</execution_context>

<context>
Milestone name: $ARGUMENTS (optional - will prompt if not provided)

Project and milestone context files are resolved inside the workflow (`init new-milestone`) and delegated via `<files_to_read>` blocks where subagents are used.
</context>

<process>
Execute the new-milestone workflow from @$HOME/.claude/get-shit-done/workflows/new-milestone.md end-to-end.
Preserve all workflow gates (validation, questioning, research, requirements, roadmap approval, commits).
</process>
