# Fable Orchestrate — Run Report

**Goal:** <goal>
**Branch:** fable/<slug>
**Result:** completed | blocked
**Waves:** <done>/<planned>   **Replans:** <n>   **Commits:** <n>
**Codex (gpt-5.6-sol):** available — <n> tasks run | unavailable — <reason>, routed Claude-only | died mid-run — <reason>, <n> tasks rerouted to fallback

## What shipped
- <wave 1 summary — commit sha>
- <wave 2 summary — commit sha>

## Blocked (if any)
- Task <tid>: <what it needed, which wall it hit (retry cap / replan cap / safety floor)>
- Left for you: <the exact decision or action required>

## Verification
- <Fable's final cross-wave check: what was independently confirmed>
- Acceptance checks passing: <n>/<total>

## Next
- <branch is at <sha>; review with `git diff main...fable/<slug>`>
- <any manual step held back by the safety floor: deploy / push / secret>
