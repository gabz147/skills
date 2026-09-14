# Fable Mode Delegation

Use this after Gate 1. Decide whether the orchestrator should self-execute, delegate to Sonnet, or hand code execution to Codex.

## Roles

- Opus 4.8 + fable-mode: owns scope, judgment, risk, verification, and final report.
- Sonnet 5: owns bounded throughput where mistakes are cheap to detect and redo.
- Codex: owns filesystem/code edits and local command execution in the VM.
- Discord: owns the human control plane.
- Obsidian brain: owns durable memory.

## Delegate To Sonnet When

- Scope is already defined.
- Success criteria are checkable afterward.
- The work is bounded to explicit files, directories, sources, or outputs.
- The task is evidence gathering, summarization, drafting, first-pass review, game content, boilerplate, or mechanical transformation.
- The output will be reviewed by Opus before any medium/high-risk action.

## Do Not Delegate To Sonnet When

- The task is the judgment itself.
- The request is ambiguous and misreading it would compound.
- Secrets, auth, permissions, destructive operations, deploys, money, or irreversible writes are involved.
- The output is hard to verify.
- Sonnet has failed verification twice on the same task.

## Codex Loop For Code

1. Opus scopes and writes a concrete spec.
2. Codex edits and runs local checks.
3. Codex reports changed files, commands, and failures.
4. Opus verifies the diff and test output.
5. Medium/high-risk execution waits for explicit user approval.

## Routing By Task

- Research/summarization: Sonnet gathers; Opus spot-checks sources.
- Mechanical coding: Sonnet may draft spec/tests; Codex edits; Opus verifies.
- Architecture/cross-cutting coding: Opus plans; Codex edits; Opus verifies.
- Code review: Sonnet first pass; Opus verdict.
- UI/game content/prompt variants: Sonnet drafts; Opus or user selects.
- Debugging triage: Sonnet and Codex gather evidence; Opus decides root cause.
- Security, secrets, destructive actions, high-risk decisions: Opus only plus user approval.

## Hard Rule

There is at most one Sonnet hop between Opus checkpoints. Never feed Sonnet output into another Sonnet task without Opus verification.

## Discord Commands

- `/ask`: capture a low-risk question as a brain handoff.
- `/task`: capture a task as a brain handoff for Opus/Fable Mode scoping.
- `/status`: show post-Fable stack readiness.

These commands live in `~/codex-discord-remote/remote_bot.py` and become live after the remote bot is safely restarted/synced.

## Brain Write Convention

- Discord bot writes raw handoffs to `~/brain/handoffs/`.
- Sonnet workers may write raw notes to `~/brain/inbox/` only when delegated.
- Opus/Fable Mode promotes decisions, verified run logs, and routing updates.
- Codex may edit brain files when explicitly implementing or recording a task.
