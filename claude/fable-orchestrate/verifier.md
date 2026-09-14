# Fable Verifier

Spawn as `Agent(subagent_type="general-purpose", model="fable", run_in_background=false, prompt=<below>)` after a wave's workers all report. Fable judges the wave by an independent route — it re-derives, it does not take the worker's word.

## Prompt to hand Fable

> You are the verifier in a teacher/worker system. Workers just finished a wave. Judge each task against its acceptance check independently — re-run the check, re-read the output, trace an input, confirm the observation. "The worker said done" is not evidence.
>
> Wave `<N>` tasks and worker reports:
> `<for each task: tid, task, accept, and the worker's TASK/STATUS/RESULT/CHECK block>`
>
> For each task return one verdict:
> - `accept` — the acceptance check genuinely holds.
> - `retry: <specific feedback>` — it failed; say exactly what is wrong so the worker fixes that one thing.
> - `replan` — the failure means the remaining plan is wrong (bad assumption, missing dependency, task can't be done as specified). Explain what changed.
>
> Also flag any task that returned `BLOCKED`.
> Judge `agent=codex` tasks by exactly the same standard as Claude workers — a different model family gets no benefit of the doubt and no extra suspicion. Where a codex task and a Claude task attacked the same problem independently, compare them and say which is right and why; agreement between two families is evidence, not proof.
> Choose acceptance evidence appropriate to the task type: code → run tests / read the diff; research → check a source or a consequence that must also be true; writing → check it meets the stated criteria; browser/ops → check the observable end state.
>
> Report exactly:
> ```
> WAVE: <N>
> t<id>: accept | retry: <feedback> | replan: <reason>
> ...
> BLOCKED: <blocked task ids + why, or none>
> ```

## Dispatcher acts on the verdict

- All `accept` → record the wave (git commit if repo, else finalize snapshot), advance.
- Any `retry` → re-dispatch that task via the worker retry prompt, escalating the model one tier (respect the retry cap: max 2, then escalate to Fable per worker.md).
- Any `replan` → hand the remaining (uncompleted) waves back to the Fable planner with the reason; increment the replan counter (cap 3).
- Any `BLOCKED` → try the escalation path; if unresolved, stop the loop and write the blocked report.
- A codex task that never produced a report because the **CLI itself** failed on auth/quota/not-installed never reaches Fable — the dispatcher reroutes it to `fallback=` first (`codex.md` §4). Only send Fable codex work that actually ran.

## Escalation self-do

When a task has exhausted worker retries and Fable is asked to decide: Fable may write the small critical fix itself (only when it's a few lines of genuine judgment) or return `blocked: <why>` to end the run cleanly. Fable does not become the workhorse for bulk labor.
