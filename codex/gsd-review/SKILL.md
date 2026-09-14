---
name: gsd-review
description: "[Ported from Claude personal skill] Request cross-AI peer review of phase plans from external AI CLIs"
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
Invoke external AI CLIs (Gemini, Claude, Codex, OpenCode, Qwen Code, Cursor) to independently review phase plans.
Produces a structured REVIEWS.md with per-reviewer feedback that can be fed back into
planning via /gsd-plan-phase --reviews.

**Flow:** Detect CLIs  to  Build review prompt  to  Invoke each CLI  to  Collect responses  to  Write REVIEWS.md
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/review.md
</execution_context>

<context>
Phase number: extracted from $ARGUMENTS (required)

**Flags:**
- `--gemini` - Include Gemini CLI review
- `--claude` - Include Claude CLI review (uses separate session)
- `--codex` - Include Codex CLI review
- `--opencode` - Include OpenCode review (uses model from user's OpenCode config)
- `--qwen` - Include Qwen Code review (Alibaba Qwen models)
- `--cursor` - Include Cursor agent review
- `--all` - Include all available CLIs
</context>

<process>
Execute the review workflow from @$HOME/.claude/get-shit-done/workflows/review.md end-to-end.
</process>
