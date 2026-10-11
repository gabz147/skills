---
name: gsd-autonomous
description: "[Ported from Claude personal skill] Run all remaining phases autonomously - discuss to plan to execute per phase"
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
Execute all remaining milestone phases autonomously. For each phase: discuss  to  plan  to  execute. Pauses only for user decisions (grey area acceptance, blockers, validation requests).

Uses ROADMAP.md phase discovery and Skill() flat invocations for each phase command. After all phases complete: milestone audit  to  complete  to  cleanup.

**Creates/Updates:**
- `.planning/STATE.md` - updated after each phase
- `.planning/ROADMAP.md` - progress updated after each phase
- Phase artifacts - CONTEXT.md, PLANs, SUMMARYs per phase

**After:** Milestone is complete and cleaned up.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/autonomous.md
@$HOME/.claude/get-shit-done/references/ui-brand.md
</execution_context>

<context>
Optional flags:
- `--from N` - start from phase N instead of the first incomplete phase.
- `--to N` - stop after phase N completes (halt instead of advancing to next phase).
- `--only N` - execute only phase N (single-phase mode).
- `--interactive` - run discuss inline with questions (not auto-answered), then dispatch plan to execute as background agents. Keeps the main context lean while preserving user input on decisions.

Project context, phase list, and state are resolved inside the workflow using init commands (`gsd-sdk query init.milestone-op`, `gsd-sdk query roadmap.analyze`). No upfront context loading needed.
</context>

<process>
Execute the autonomous workflow from @$HOME/.claude/get-shit-done/workflows/autonomous.md end-to-end.
Preserve all workflow gates (phase discovery, per-phase execution, blocker handling, progress display).
</process>
