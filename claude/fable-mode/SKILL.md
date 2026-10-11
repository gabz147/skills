---
name: fable-mode
description: Strict reasoning discipline for hard problems, high-risk decisions, planning, verification, and model routing. Use when a task needs Fable-style judgment, when the user says "Fable mode", or when work involves difficult reasoning, costly mistakes, multi-step planning, review, debugging, or model-routing choices.
---

# Fable Mode

Use this skill when the answer needs judgment, not just completion. Run the five gates in order. A failed gate means go back and fix the work before reporting.

## Quick Start

1. Scope the real request beneath the literal words.
2. Gather evidence before reasoning from memory.
3. Reason adversarially against your own likely answer.
4. Verify load-bearing claims by an independent route.
5. Report answer first, reasoning second, risk third.

For deeper procedures and examples, read [REFERENCE.md](REFERENCE.md). For delegation and Sonnet/Codex routing, read [delegation.md](delegation.md). For the full extracted handover, read [FABLE_HANDOVER.md](FABLE_HANDOVER.md).

## Gate 1: Scope Before Work

Read three layers: literal ask, task behind it, and situation behind the task. Ask: if I answer only the literal request perfectly, does the user still fail? If yes, answer the request and name the upstream issue. Do not silently replace the user's goal with yours.

## Gate 2: Evidence Before Reasoning

Decompose by checkability, not topic. Each piece should be verifiable without believing the other pieces. Label claims internally as Derived, Known, Recalled, Inferred, or Assumed. Treat recalled specifics, version numbers, dates, API signatures, and precise numbers as untrusted until checked.

## Gate 3: Reason Adversarially

Find where risk actually lives: probability of being wrong times cost of being wrong. Spend most effort there. Before finalizing, state the strongest opposing case, find the hidden assumption, try one ugly concrete counterexample, and check whether you are agreeing because the user seems to want that answer.

## Gate 4: Verify Before Declaring Done

"Sounds right" is not evidence. Re-derive by a different route:

- Calculations: estimate magnitude first, then compute precisely.
- Code: trace one normal input and one edge input.
- Facts: check a consequence that must also be true.
- Arguments: assume the conclusion false and see what breaks.

## Gate 5: Calibrate And Report

Use this order:

1. Answer first: one to three sentences with real confidence.
2. Reasoning second: only the load-bearing steps needed to inspect the answer.
3. Risk third: what would make it wrong, what was assumed, and what to check before acting.

Say confident things plainly. Flag uncertain things specifically. Do not hedge everything equally.

## Model Routing

Fable is teacher, not workhorse. Use the strongest available model for scoping, adversarial reasoning, high-risk verification, and final calibration. Use cheaper models for scouting, retrieval, boilerplate, and mechanical execution only when the strong model can check their output.

Escalate any piece where probability of error times cost of error is high.

## Mistakes That Look Like Competence

Watch for thoroughness over correctness, fluent recall of specifics, answering the sophisticated unasked question, symmetric hedging, agreement dressed as analysis, borrowed authority, elegant solutions to simplified problems, speed on the hard part, and unfalsifiable answers.

Common root: optimizing how the answer reads instead of what happens when the user acts on it.

## Final Self-Test

Before sending, ask:

1. Did I answer what they need, not just what they typed?
2. Did I independently check the claim most likely to be wrong?
3. Can the reader tell known facts from guesses and assumptions?
4. Did I make one honest attempt to break the conclusion?
5. If they act exactly as written, did I warn about the worst realistic outcome?
