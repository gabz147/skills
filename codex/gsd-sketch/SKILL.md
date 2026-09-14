---
name: gsd-sketch
description: "[Ported from Claude personal skill] Sketch UI/design ideas with throwaway HTML mockups, or propose what to sketch next (frontier mode)"
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
Explore design directions through throwaway HTML mockups before committing to implementation.
Each sketch produces 2-3 variants for comparison. Sketches live in `.planning/sketches/` and
integrate with GSD commit patterns, state tracking, and handoff workflows. Loads spike
findings to ground mockups in real data shapes and validated interaction patterns.

Two modes:
- **Idea mode** (default) - describe a design idea to sketch
- **Frontier mode** (no argument or "frontier") - analyzes existing sketch landscape and proposes consistency and frontier sketches

Does not require `/gsd-new-project` - auto-creates `.planning/sketches/` if needed.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/sketch.md
@$HOME/.claude/get-shit-done/workflows/sketch-wrap-up.md
@$HOME/.claude/get-shit-done/references/ui-brand.md
@$HOME/.claude/get-shit-done/references/sketch-theme-system.md
@$HOME/.claude/get-shit-done/references/sketch-interactivity.md
@$HOME/.claude/get-shit-done/references/sketch-tooling.md
@$HOME/.claude/get-shit-done/references/sketch-variant-patterns.md
</execution_context>

<runtime_note>
**Copilot (VS Code):** Use `vscode_askquestions` wherever this workflow calls `AskUserQuestion`.
</runtime_note>

<context>
Design idea: $ARGUMENTS

**Available flags:**
- `--quick` - Skip mood/direction intake, jump straight to decomposition and building. Use when the design direction is already clear.
- `--wrap-up` - Package sketch design findings into a persistent project skill for future build conversations. Runs the sketch-wrap-up workflow.
</context>

<process>
Parse the first token of $ARGUMENTS:
- If it is `--wrap-up`: strip the flag, execute the sketch-wrap-up workflow from @$HOME/.claude/get-shit-done/workflows/sketch-wrap-up.md end-to-end.
- Otherwise: execute the sketch workflow from @$HOME/.claude/get-shit-done/workflows/sketch.md end-to-end.

Preserve all workflow gates (intake, decomposition, target stack research, variant evaluation, MANIFEST updates, commit patterns).
</process>
