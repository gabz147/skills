---
name: fable-orchestrate
description: Fable-5 is the teacher — it plans, routes, and verifies any task; the whole model/agent roster (Haiku, Sonnet, Opus, Explore, general-purpose) are the workers that execute. Wave-parallel, autonomous. Use when the user types /fable-orchestrate, or wants Fable to plan and pick which models do the work for coding, research, writing, browser, or ops tasks.
---

# Fable Orchestrate

Fable-5 is the **teacher**: it scopes the goal, **routes** each piece to the best worker in the whole roster, and **verifies** results. It never does grunt work. The session running this skill is a thin **dispatcher** — it does no thinking; it only spawns subagents (via the `Agent` tool's `model` + `subagent_type` overrides) and moves state between them.

Works for **any** task — coding, research, writing, browser automation, ops — not just git repos. Run it when the user says `/fable-orchestrate <goal>`.

## Mechanism

Everything is a subagent spawned with `Agent`. Fable's plan assigns each task an **agent type** and a **model**; the dispatcher just executes what Fable chose. See `roster.md` for the full menu Fable picks from.

- **Planner** — `Agent(subagent_type="Plan"|"general-purpose", model="fable")` → the wave-partitioned task DAG. See `planner.md`.
- **Worker** — `Agent(subagent_type=<Fable's pick>, model=<Fable's pick>, run_in_background=false, ...)` → one task. See `worker.md`. Dispatch a whole wave by issuing **all its worker calls in a single message** so they run in parallel.
- **Verifier** — `Agent(subagent_type="general-purpose", model="fable")` → judges a completed wave against its acceptance checks. See `verifier.md`.
- **`dispatcher`** is a valid "worker" too: for tasks needing **user interaction** a headless subagent can't do (UAC prompts, credentials, a choice only the user can make), Fable routes the task to `agent=dispatcher` and the main session handles it inline.
- **`codex`** is a worker from **outside the Claude family** — OpenAI's `gpt-5.6-sol` via the local `codex` CLI. Not an `Agent` spawn: the dispatcher shells out with `Bash` to `codex exec`. It is **availability-gated** — the user's ChatGPT subscription is sometimes paid and sometimes not, so a preflight smoke test runs before planning and Codex is only on the menu if it passes. See `codex.md`.

The dispatcher never reasons about the goal or does the work itself (except `dispatcher`-routed interactive steps). Tempted to "just fix it"? Stop — route it.

## Autonomy & safety

**Default: reckless — no gates.** Fable plans, workers execute everything (including deploys, deletes, installs, sends) with **no confirmation**. Maximum autonomy. A bad plan can do real, irreversible damage — that is the accepted trade. `--safe` restores the floor (below) for a run.

**Non-interrupting undo trails (always on, even reckless — they never stop the run):**
- **Git repo + code task** → work on branch `fable/<slug>`, `git commit` per accepted wave.
- **File writes outside a repo** → snapshot the named target paths to `.fable/snapshots/<ts>/` before the wave.
- **Read-only tasks** (research, search, browse) → nothing to snapshot.

**`--safe` floor (opt-in):** the first time a task hits a truly irreversible / external action — deploy, force-push, delete outside the workspace, spend money, send a message/email, install software, kill a process — pause and ask the user once, then continue. Without `--safe`, none of these pause.

Persist run state to `.fable/run-<timestamp>.md` (plan + wave progress + retry counts + snapshot refs) so a long run survives context growth and is resumable. Add `.fable/` to `.gitignore` if a repo.

## The loop

```
1. Setup    → parse flags; if code+git, create branch; write state file.
1b. Preflight → unless --no-codex, run the Codex smoke test (codex.md §1: one ~5s
              `codex exec` that must exit 0 and echo FABLE_OK). Record
              `CODEX: available` / `CODEX: unavailable — <reason>` in the state file
              and tell the user in one line. A fail never stops the run — it just
              takes Codex off the roster.
2. Plan     → Fable planner returns the wave-partitioned task DAG (planner.md schema:
              each task tagged agent + model + tools + accept + reversibility).
              The CODEX line is an input to the planner. If --dry-run: print the plan
              and STOP (the preflight still runs first — routing depends on it).
3. Execute  → for the current wave, snapshot any non-repo write targets, then dispatch
              every task to its assigned agent/model — all in ONE message (parallel).
              dispatcher-routed tasks run inline; codex-routed tasks are Bash calls
              in that same message. Collect results.
4. Verify   → Fable verifier judges the wave. Per task: accept | retry(feedback) | replan.
5. Record   → commit the wave (repo) or finalize snapshot; update state file.
6. Advance  → next wave. Repeat 3–6 until all waves done or a guard trips.
7. Report   → Fable does a FINAL cross-wave verification; dispatcher writes the report
              (templates/report.md).
```

## Loop guards (stop runaway autonomy)

- **Per-task retries: max 2.** On the 2nd failure, escalate the model one tier (haiku→sonnet→opus); if the top tier still fails, hand the task to Fable to self-do the small critical piece or mark it blocked.
- **Replans: max 3 per run.** Beyond that, stop.
- **Iteration cap.** If waves executed exceed `2 × planned waves`, stop.
- **Codex died mid-run.** A `codex` task that fails with an auth / quota / not-installed signature is **infrastructure, not the task's fault**: it does not burn a retry. Mark `CODEX: dead` in the state file, re-dispatch that task to its declared `fallback=<agent>×<model>`, reroute every remaining codex task to its fallback too, and never retry Codex for the rest of the run. Codex producing *bad work* is an ordinary `retry`. See `codex.md` §4.
- On any guard trip: stop, write a blocked report naming the exact task and wall it hit, leave state/branch/snapshots intact. Do not thrash.

## Hard rules (from fable-mode delegation)

- **One worker hop per Fable checkpoint.** Never feed one worker's output into another worker without Fable verifying in between.
- Fable owns scope, judgment, routing, verification. Workers own bounded execution only.
- Fable is never a workhorse. Pure mechanical labor goes to a worker even if Fable is idle.

## Flags

- `--dry-run` — plan + route only, print the DAG, execute nothing.
- `--safe` — enable the irreversible-action floor (ask once). Default is reckless.
- `--sequential` — one task at a time (Fable can inspect each before the next); overrides parallel.
- `--model-worker=haiku|sonnet|opus` — force one worker model instead of letting Fable route per task. Does not apply to `agent=codex` tasks (different family, `sol:<effort>` only).
- `--no-codex` — skip the Codex preflight entirely and route Claude-only. Use when you don't want to spend ChatGPT quota.
- `--codex-only-verify` — Codex is available for cross-model **checks** only; Fable may not route implementation work to it.

## References

- `roster.md` — the full menu of models, agent types, and tools Fable routes over. **Read this to route.**
- `planner.md` — Fable planner prompt + the plan output schema the dispatcher parses.
- `worker.md` — the bounded worker prompt template (any task type; initial + retry).
- `codex.md` — the Codex `gpt-5.6-sol` worker: preflight smoke test, effort tiers, `codex exec` dispatch, mid-run fallback. **Read before routing anything to `agent=codex`.**
- `verifier.md` — Fable's accept/retry/replan rules (generalized acceptance checks).
- `templates/report.md` — final report shape.
