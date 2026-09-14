# TASK HANDOFF — from Opus orchestrator

TASK_ID: `{project}-{yyyymmdd}-{n}`
RISK: `LOW | MEDIUM`

## Objective

One sentence. What done looks like.

## Scope

IN: explicit files, directories, topics, or sources.

OUT: explicit exclusions such as `.env`, credentials, destructive commands, unrelated refactors.

## Inputs

Paths, snippets, links, prior context. Assume no other memory.

## Success Criteria

- Checkable item 1
- Checkable item 2
- Checkable item 3

## Constraints

- Do not declare the task complete.
- Report findings only.
- If anything is ambiguous, stop and return `BLOCKED` with one question.
- If you touch anything outside IN scope, report it as a deviation.

## Return Format

Use `templates/report.md`.
