---
name: gsd-inbox
description: "[Ported from Claude personal skill] Triage and review open GitHub issues and PRs against project templates and contribution guidelines."
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
One-command triage of the project's GitHub inbox. Fetches all open issues and PRs,
reviews each against the corresponding template requirements (feature, enhancement,
bug, chore, fix PR, enhancement PR, feature PR), reports completeness and compliance,
and optionally applies labels or closes non-compliant submissions.

**Flow:** Detect repo  to  Fetch open issues + PRs  to  Classify each by type  to  Review against template  to  Report findings  to  Optionally act (label, comment, close)
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/inbox.md
</execution_context>

<context>
**Flags:**
- `--issues` - Review only issues (skip PRs)
- `--prs` - Review only PRs (skip issues)
- `--label` - Auto-apply recommended labels after review
- `--close-incomplete` - Close issues/PRs that fail template compliance (with comment explaining why)
- `--repo owner/repo` - Override auto-detected repository (defaults to current git remote)
</context>

<process>
Execute the inbox workflow from @$HOME/.claude/get-shit-done/workflows/inbox.md end-to-end.
Parse flags from arguments and pass to workflow.
</process>
