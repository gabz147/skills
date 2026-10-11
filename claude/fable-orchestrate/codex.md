# Codex Worker — `gpt-5.6-sol`

A **non-Claude** worker. Codex is not spawned with the `Agent` tool — it is an external CLI the dispatcher runs via `Bash`. Everything else about it is identical to a normal worker: it gets one bounded task, it reports in the `worker.md` format, and Fable verifies it afterward.

Its value is that it is a **different model family**. Route to it for an independent implementation, a second opinion, or a task the Claude tier keeps failing.

**It is availability-gated.** The user's ChatGPT subscription is sometimes active and sometimes not. Never hand Codex a task without a passing preflight in the current run.

---

## 1. Preflight smoke test (Setup, before planning)

Run **once per run**, before the planner is spawned. Skip entirely if `--no-codex` was passed.

```bash
mkdir -p .fable/codex
codex exec --skip-git-repo-check --ephemeral -s read-only \
  -m gpt-5.6-sol -c model_reasoning_effort="low" \
  -o .fable/codex/preflight.txt \
  "Reply with exactly: FABLE_OK" < /dev/null 2>&1 | tail -5
```

Cost: ~20k Codex tokens, ~5s. Timeout it at **120s**.

**PASS** iff *both*:
1. exit code `0`, and
2. `.fable/codex/preflight.txt` contains `FABLE_OK`.

Anything else is **FAIL**. Classify the reason from the combined stdout/stderr — do not guess, read the text:

| Signature in output | Verdict |
|---|---|
| `command not found`, `codex: not found` | `unavailable: not installed` |
| `not logged in`, `run codex login`, `401`, `403` | `unavailable: not authenticated` |
| `429`, `quota`, `usage limit`, `rate limit`, `billing`, `payment`, `subscription`, `plan` | `unavailable: subscription/quota` |
| timeout hit | `unavailable: timeout` |
| exit 0 but no `FABLE_OK` | `unavailable: unexpected output` |
| anything else | `unavailable: <verbatim last line of output>` |

Record the verdict in `.fable/run-<ts>.md` as `CODEX: available` or `CODEX: unavailable — <reason>`, and pass that exact line into the Fable planner prompt (`planner.md`). Tell the user in one line which it was — never silently drop Codex.

**A failed preflight is not a run failure.** The run proceeds with Claude-only routing.

---

## 2. Effort tiers (Codex's equivalent of the model ladder)

Codex is one model, so the dial is `model_reasoning_effort`. The plan writes it as `model=sol:<effort>`:

| Plan token | `model_reasoning_effort` | Rough Claude equivalent |
|---|---|---|
| `sol:low` | `low` | haiku |
| `sol:medium` | `medium` | sonnet |
| `sol:high` | `high` | opus |
| `sol:xhigh` | `xhigh` | opus, hardest sub-problems only |

Retries escalate one tier: `low → medium → high → xhigh`. Past `xhigh`, stop escalating — hand to Fable per `verifier.md`.

The user's `~/.codex/config.toml` defaults to `xhigh` + `service_tier = "priority"`. Always pass `-c model_reasoning_effort=` explicitly so the plan's tier wins over that default.

---

## 3. Dispatching a task to Codex

```bash
codex exec --skip-git-repo-check -C "<cwd>" \
  -s <read-only|workspace-write|danger-full-access> \
  -m gpt-5.6-sol -c model_reasoning_effort="<effort>" \
  -o .fable/codex/<tid>.txt - <<'PROMPT'
<the worker.md prompt text, verbatim>

Emit the TASK/STATUS/RESULT/CHECK/NOTES block as your final message and nothing after it.
PROMPT
```

- Pass the prompt on **stdin** via `-` + heredoc — the prompt is multi-line and quoting it as an argv string breaks.
- `-C <cwd>` sets the working root. Add `--add-dir <path>` for any writable path outside it named in the task.
- Sandbox by the task's `rev` tier: `read` → `read-only`, `write` → `workspace-write`, `external` → `danger-full-access`. Under `--safe`, ask before running an `external` Codex task, same as any other worker.
- `--dangerously-bypass-approvals-and-sandbox` only when a task genuinely cannot run sandboxed (elevation, a system-wide install) **and** the reckless default is in force. Never under `--safe`.
- Read the worker report from `.fable/codex/<tid>.txt`, not from the streamed stdout.
- Codex tasks in the same wave can run in parallel — issue them as separate `Bash` calls in one message, same rule as `Agent` workers.

---

## 4. Mid-run death (the subscription lapses while running)

Any Codex invocation that fails with an **auth/quota/not-installed** signature from the table in §1 is an **infrastructure failure, not a task failure**:

1. Do **not** count it against that task's retry cap.
2. Set `CODEX: dead — <reason>` in the run state file.
3. Re-dispatch that task immediately to its declared `fallback=<agent>×<model>` from the plan.
4. Reroute **every remaining** `agent=codex` task in the plan to its fallback too. Do not re-preflight; do not retry Codex for the rest of the run.
5. Name it in the final report.

A Codex task that runs fine but produces *wrong work* is an ordinary failure — that goes back through `verifier.md` as a normal `retry`.

---

## 5. Report format

Identical to `worker.md`. Codex's final message must be exactly:

```
TASK: <tid>
STATUS: done | blocked
RESULT: <what it produced/changed — one to three lines>
CHECK: <how it confirmed accept: command + result, or the observation>
NOTES: <one line, only if the dispatcher needs it>
```

If the file does not parse into that block, treat it as `retry` with feedback "report format" — not as an infra failure.
