---
name: afk
description: "[Ported from Claude personal skill] Launch a non-stop autonomous Codex worker on a goal the user describes. Scaffolds a project workspace and runs a self-restarting `codex -p` supervisor loop in tmux that keeps building toward the goal - surviving SSH disconnects and usage limits - until the user stops it. Use when the user runs `/afk (goal)`, or asks to run something autonomously / overnight / non-stop / unattended, to \"keep Codex working\", or to fire-and-forget a build."
---

# AFK - autonomous fire-and-forget worker

## Codex Compatibility

This skill was ported from a Claude skill. Interpret Claude Code-specific wording using Codex equivalents:

- Use `functions.shell_command` for shell commands and filesystem inspection.
- Use `apply_patch` for manual file edits.
- Use `update_plan` for task checklists when a plan is useful.
- Use `web.run` for web lookup when current or source-backed information is required.
- Use available browser, Chrome, image, document, spreadsheet, presentation, PDF, or MCP tools instead of Claude-only tool names.
- Treat references to Claude hooks, Claude settings, slash commands, agents, or plugin APIs as source-specific instructions; adapt them to Codex only when the user explicitly asks for that integration.


`/afk <goal>` turns a one-line goal into a long-running autonomous build: a tmux-hosted loop
that repeatedly invokes `claude -p --dangerously-skip-permissions` on the goal. Each iteration
makes one verified step and appends to a shared WORKLOG (its only cross-iteration memory), and
the loop self-restarts until the user stops it. Generalizes the user's amber-low-poly
`autowork/supervisor.sh` (see memory `autowork-supervisor-pattern`).

`SKILL_DIR` below = the directory this SKILL.md lives in.

## When invoked, do this (the skill args ARE the user's goal text)

1. **Capture the goal.** `GOAL` = the args. If empty, ask for it. If it's vague, you may ask
   1-2 sharpening questions, but default to proceeding - the loop self-corrects.
2. **Pick a workspace.** Slugify the goal (lowercase, words to `-`, ~4 words)  to  `DIR=~/afk/<slug>`.
   If `$DIR` already exists, append `-2`, `-3`, ... `SESSION=afk-<slug>`.
3. **Scaffold.** Pipe the goal into the init script:
   `printf '%s\n' "<GOAL + any clarifications>" | bash "SKILL_DIR/scripts/afk-init.sh" "$DIR"`
   This git-inits `$DIR`, copies `supervisor.sh` + `AUTOWORK.md` + `PROMPT.txt` into
   `$DIR/autowork/`, writes `GOAL.md`, and seeds `WORKLOG.md`.
   Optionally tailor `$DIR/autowork/AUTOWORK.md` to the goal's domain (e.g. note the intended
   stack for a SaaS app) - keep the protocol section intact.
4. **Preflight.** `command -v claude` and `command -v tmux` must succeed. Choose the run budget:
   default **0 (unlimited - runs until stopped)**. If the user named a duration ("for 8 hours",
   "overnight" ? 10), pass that integer instead.
5. **Launch (background, never block):**
   `tmux new-session -d -s "$SESSION" "bash $DIR/autowork/supervisor.sh <HOURS>"`
   then verify with `tmux has-session -t "$SESSION"`.
6. **Report back** (below). Do not wait on the loop or tail it in the foreground.

## After launch, tell the user
- the workspace path and the tmux session name
- watch live:   `tmux attach -t <SESSION>`   (detach with Ctrl-b then d)
- tail progress: `tail -f <DIR>/autowork/supervisor.log` and `<DIR>/autowork/WORKLOG.md`
- **stop it:** `touch <DIR>/autowork/STOP` (clean stop after the current iteration) - or
  `tmux kill-session -t <SESSION>` (hard stop now)

## Notes / guardrails
- Every iteration runs `--dangerously-skip-permissions` with no human in the loop. Only use this
  for goals where unattended file edits and command execution inside the workspace are acceptable.
  The protocol tells the worker to stay inside `$DIR`.
- It consumes Claude usage continuously. On a session/usage limit it auto-backs-off and re-probes
  every 7 minutes, resuming when access returns.
- Safety floor: if `AFK_MAX_IDLE` (default 5) consecutive iterations produce no new git commit,
  the loop stops itself - so a stuck/refusing worker can't burn usage all night doing nothing.
- Tunables via env on the launch command: `AFK_TIMEOUT` per-iteration cap (default 3600s),
  `AFK_BREATHER` gap between healthy iters (default 60s), `AFK_MAX_IDLE` no-progress stop
  (default 5, 0 disables), `AFK_CLAUDE` claude path.
- Runs are independent - different goals get different slugs/sessions and can run concurrently.
  `tmux ls` lists active runs; `ls ~/afk` lists all workspaces.
