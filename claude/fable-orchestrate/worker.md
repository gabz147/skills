# Worker

Spawn as `Agent(subagent_type=<Fable's agent pick>, model=<Fable's model pick>, run_in_background=false, prompt=<below>)`.
To run a wave in parallel, issue **all** its worker calls in a **single message**.

Two workers are not `Agent` spawns:
- `agent=dispatcher` — the main session does it inline (it can talk to the user).
- `agent=codex` — a `Bash` call to `codex exec`, same prompt text, see §Codex dispatch below and `codex.md`.

Workers execute one bounded task of any kind — research, code, writing, browser, ops — and report facts. They do not expand scope, do not touch anything outside their task, and do not commit (the dispatcher records per wave).

## Initial task prompt

> You are a worker in a teacher/worker system. Do exactly this one task, nothing more.
>
> Task `<tid>`: `<task text from plan>`
> Bounded to: `<paths/sources named in the task>`
> Tools you may use: `<tools>`
> Acceptance check: `<accept text>`
>
> Rules:
> - Do only what the task requires. Change nothing outside the named scope.
> - If the task turns out to need an irreversible/external action not named in it (deploy, push, delete outside scope, spend, send, install, kill a process), stop and report `BLOCKED: <why>` instead of doing it.
> - Confirm the acceptance check yourself before reporting (run the command, re-read the file, take the screenshot).
>
> Report back exactly:
> ```
> TASK: <tid>
> STATUS: done | blocked
> RESULT: <what you produced/changed — files, findings, or output — one to three lines>
> CHECK: <how you confirmed accept: command + result, or the observation>
> NOTES: <one line, only if the dispatcher needs it>
> ```

## Retry prompt (after Fable returns `retry`)

Same task, prepend Fable's feedback so the worker fixes the specific failure:

> Your previous attempt at task `<tid>` failed verification.
> Verifier feedback: `<fable feedback>`
> What you did last time: `<prior RESULT>`
> Fix exactly that failure and re-confirm the acceptance check. Don't redo working parts. Same report format.

## Codex dispatch

Same prompt text, delivered on stdin instead of to `Agent`:

```bash
codex exec --skip-git-repo-check -C "<cwd>" -s <read-only|workspace-write|danger-full-access> \
  -m gpt-5.6-sol -c model_reasoning_effort="<low|medium|high|xhigh>" \
  -o .fable/codex/<tid>.txt - <<'PROMPT'
<the initial or retry prompt above, verbatim>

Emit the TASK/STATUS/RESULT/CHECK/NOTES block as your final message and nothing after it.
PROMPT
```

Read the report from `.fable/codex/<tid>.txt`. Sandbox mode follows the task's `rev` tier (`read`/`write`/`external`). Full details and the mid-run failure handling are in `codex.md`.

## Escalation

Retries escalate the model one tier: `haiku → sonnet → opus` (codex: `sol:low → sol:medium → sol:high → sol:xhigh`). If the top tier fails twice, do not retry again — hand the task to Fable (`verifier.md`) for a self-do-or-block decision. Never chain one worker's output into another worker without Fable verifying between them.

A Codex task that fails on **auth/quota** is not a retry — it reroutes to `fallback=` and does not consume the retry cap (`codex.md` §4).
