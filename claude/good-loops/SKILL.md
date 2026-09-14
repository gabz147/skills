---
name: good-loops
description: Design effective agent loops ("loop engineering") instead of hand-prompting an agent every step. Use when the user wants to build a /goal-style loop, an autonomous or overnight run, a reason-act-observe workflow, a maker-checker pair, or a fleet/manager-with-helpers setup — or asks how to make an agent iterate to a verifiable done state. Triggers on "build a loop", "loop engineering", "agent loop", "/goal", "make it iterate until", "run this overnight", "self-checking agent".
---

# Good Loops

Loop engineering = replacing yourself as the person who prompts the agent. You design the
system that prompts it instead. A loop is a **recursive goal**: define a purpose, the agent
iterates until done.

## The one mental model: reason → act → observe

```
reason (plan)  →  act (implement)  →  observe (verify)
       ^                                      |
       |______ not done? feedback ___________|
                          |
                     done? stop → report to human
```

Think of it as a smart intern you don't micromanage: hand a goal, they figure out the next
step, check their own work, go again, and only come back when they're done.

**Why it's worth it:** AI never one-shots to 100%. The human-feedback-then-iterate cycle is
going to happen *either way*. A loop outsources that cycle to the agent, so by attempt 3-4
quality is far higher than the first try would have been. The loop's whole value is the
**verification step**, not the architecture.

## Two pillars (get these right, the rest is detail)

1. **Goal — what does "done" mean?** Humans are great at defining the end goal. Push it to be
   as *objective* as possible. Best loops say literally: "keep iterating until X metric == Y."
   Fall back to subjective ("until you're confident") only when you truly can't measure it —
   and add a hard cap so it can't run forever.
2. **Verification — how does it check?** The agent must have the *tools* to actually verify the
   thing it's building. The check looks different per artifact:
   - UI / image / game → screenshot in a browser, compare visually, play the levels
   - code / script → run the test, check flow, lint
   - writing → check tone, voice, structure
   A loop is only as good as its done-check.

## Choose the smallest topology that works

Most tasks **don't need a big architecture** — one terminal session + a good prompt is usually
enough. Don't reach for swarms because a tweet told you to; you'll just scale bugs.

| Topology | Shape | Use when |
|---|---|---|
| **Solo loop** (default) | one agent reasons-acts-observes-repeats | most things; you want speed |
| **Maker-checker** | one agent does the work, a second grades + gives feedback | scoring needs to be independent/trustworthy |
| **Manager + helpers** | one orchestrator delegates to sub-agents | genuinely parallel or large multi-part jobs |

If scoring is subjective, promote the checker into a **dedicated scorer sub-agent** you've run
through evals, so you trust its judgment.

## Checklist — what makes a loop actually work

- [ ] **Checkable goal** — objective metric where possible
- [ ] **Hard stop** — max passes / time / cost cap, so an unhittable goal can't run for days
- [ ] **Good tools** — the agent can actually perform its verification (browser, test runner, etc.)
- [ ] **Memory** — carries context across iterations
- [ ] **Separate checker** — when self-grading isn't trustworthy
- [ ] **Plan first** — reason before acting
- [ ] **Logging** — you can see what each pass did
- [ ] **Cost sanity** — the run is worth the tokens/time

## Before you write the loop, answer two questions

1. **What does done mean?** (the stop condition — objective metric > subjective confidence)
2. **How will it check?** (the verification method + the tools needed for it)

## Reality check (avoid the hype trap)

- The majority of tasks still don't need a loop — add one mainly for the *verification*.
- Loops don't give 100% perfect output; they get you much closer on the first try.
- 24/7 fleets of agents aren't automatically better. Match the loop to *your* work. Knowledge
  work and solo projects often want short, on-cadence or event-triggered loops, not endless runs.
- Sweet spot for long runs is ~35 min to a few hours, or a "chunky loop before bed" → wake up
  to 4-8h of output, then iterate on it as a human. Multi-day runs are rarely worth it; if a
  loop runs 12h+ it usually means the done criteria is unhittable.
- Just because a hardcore coder writes only loops doesn't mean you must. Stay current, try it,
  but don't force it into every session.

## Example /goal prompt shape

```
/goal Recreate <reference> using only HTML/CSS (no image gen).
  ACT: build a version, render it in a browser, screenshot it.
  OBSERVE: score the screenshot against the reference (0-10) on
           {layout, color, proportions}. Log the score + what's off.
  ITERATE: fix the weakest dimension, repeat.
  DONE: average score >= 9.  HARD CAP: 8 passes.
```

The pattern that matters: explicit act, an **observable** verification with a number, a clear
stop condition, and a hard cap.

---
*Source: distilled from a video on loop engineering / agent loops (reason-act-observe).*
