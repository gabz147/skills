#!/usr/bin/env bash
# GOAL GATE — the supervisor runs this after every iteration; exit 0 = goal achieved,
# the run stops as SUCCESS. This is the /goal pattern: "done" must be a boolean check.
#
# The scaffolding Claude should REPLACE the body with a real check when the goal is
# objectively verifiable, e.g.:
#   - test suite green:        cd "$(dirname "$0")/.." && npm test --silent
#   - artifact exists + valid: [ -s dist/app.glb ] && node scripts/validate.mjs
#   - score threshold:         [ "$(node scripts/lighthouse.mjs)" -ge 90 ]
# Keep it FAST and QUIET. If the goal is open-ended (no objective "done"), leave this
# as-is — the loop then runs until STOP, with the evaluator nudging when it looks done.
exit 1
