#!/usr/bin/env bash
# AFK autonomous worker loop (v2 — loop-engineering upgrade).
# Repeatedly runs `claude -p` iterations toward the goal in autowork/GOAL.md.
# Survives SSH disconnect (run inside tmux). Usage-limit aware. Kill switch: touch autowork/STOP.
#
# Usage: bash <workspace>/autowork/supervisor.sh [HOURS]
#   HOURS   total run budget in hours; 0 or "inf" = run until STOP / DONE / disk-low (default 0)
#
# Env overrides:
#   AFK_CLAUDE           claude binary                        (default: autodetect)
#   AFK_TIMEOUT          per-iteration cap in seconds          (default 3600)
#   AFK_BREATHER         gap between healthy iters             (default 60)
#   AFK_MAX_IDLE         stop after N consecutive iters with no new commit (default 5, 0 off)
#   AFK_MODEL            model for build iterations            (default: CLI default)
#   AFK_REVIEW_EVERY     every Nth iteration is an adversarial review pass (default 5, 0 off)
#   AFK_REVIEW_MODEL     model for review iterations           (default: AFK_MODEL)
#   AFK_EVAL             1 = judge each iteration with a cheap evaluator (default 1)
#   AFK_EVAL_MODEL       evaluator model                       (default claude-haiku-4-5-20251001)
#   AFK_MAX_BAD          stop after N consecutive STUCK/DRIFTING verdicts (default 3, 0 off)
#   AFK_USAGE_CAP        stop when usage >= this %             (default 0 = disabled)
#   AFK_CAP_WINDOW       window the cap watches: seven_day | five_hour | both (default seven_day)
#   AFK_DISCORD_CHANNEL  Discord channel id for progress posts (default empty = no posts)
#   AFK_DISCORD_ENV      env file containing DISCORD_TOKEN     (default ~/restoration-research/.env)
#   AFK_POST_EVERY       post every Nth iteration update       (default 1)
#
# Done condition (goal-based stop, per the Claude Code loops guidance):
#   autowork/DONE_CHECK.sh exit 0  =>  goal met, loop stops as SUCCESS.
#   The evaluator's DONE verdict alone never stops the run — it notifies so a human
#   (or the next scaffold) can flip DONE_CHECK.sh; booleans stop loops, vibes don't.
set -u

AW="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"   # .../autowork
ROOT="$(dirname "$AW")"                                # the workspace
LOGS="$AW/logs"
SLOG="$AW/supervisor.log"
CLAUDE="${AFK_CLAUDE:-$(command -v claude || echo /usr/bin/claude)}"
TIMEOUT="${AFK_TIMEOUT:-3600}"
BREATHER="${AFK_BREATHER:-60}"
MAX_IDLE="${AFK_MAX_IDLE:-5}"
MODEL="${AFK_MODEL:-}"
REVIEW_EVERY="${AFK_REVIEW_EVERY:-5}"
REVIEW_MODEL="${AFK_REVIEW_MODEL:-$MODEL}"
EVAL="${AFK_EVAL:-1}"
EVAL_MODEL="${AFK_EVAL_MODEL:-claude-haiku-4-5-20251001}"
MAX_BAD="${AFK_MAX_BAD:-3}"
USAGE_CAP="${AFK_USAGE_CAP:-0}"
CAP_WINDOW="${AFK_CAP_WINDOW:-seven_day}"
DCHAN="${AFK_DISCORD_CHANNEL:-}"
POST_EVERY="${AFK_POST_EVERY:-1}"
HOURS="${1:-0}"
mkdir -p "$LOGS"

START=$(date +%s)
if [ "$HOURS" = "inf" ] || [ "$HOURS" = "0" ]; then
  UNLIMITED=1; END=0; ENDSTR="unlimited (until STOP/DONE)"
else
  UNLIMITED=0; END=$(( START + HOURS * 3600 )); ENDSTR="$(date -u -d @$END +%Y-%m-%dT%H:%MZ)"
fi
ITER=1
IDLE=0
BAD=0      # consecutive STUCK/DRIFTING evaluator verdicts
DONEHINTS=0
DONE=0     # iterations actually completed (accurate on every exit path)
OUTCOME="stopped"
say() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" >> "$SLOG"; }
running() { [ "$UNLIMITED" = "1" ] || [ "$(date +%s)" -lt "$END" ]; }
notify() {  # best-effort Discord post; silent no-op unless AFK_DISCORD_CHANNEL is set
  [ -n "$DCHAN" ] || return 0
  AFK_DISCORD_CHANNEL="$DCHAN" bash "$AW/post_update.sh" "$1" >/dev/null 2>&1 &
}
last_worklog() {
  awk '/^## /{p=NR} {l[NR]=$0} END{if(p) for(i=p;i<=NR;i++) print l[i]}' "$AW/WORKLOG.md" 2>/dev/null | head -22
}

# regex covers Claude's real wording ("you've hit your session limit · resets …") plus
# generic rate/quota messages — the original amber loop missed "session limit" and wasted hours.
LIMIT_RE='usage limit|rate.?limit|limit .*reset|hit your .*limit|session limit|too many requests|overloaded|quota|insufficient (credit|quota|balance)'

say "=== afk supervisor v2 start, budget=${HOURS}h, ends ${ENDSTR}, claude=$CLAUDE, model=${MODEL:-cli-default}, review_every=${REVIEW_EVERY}, eval=${EVAL}/${EVAL_MODEL}, cap=${USAGE_CAP}%/${CAP_WINDOW}, timeout=${TIMEOUT}s ==="
notify "🤖 **AFK worker started** — \`$(basename "$ROOT")\` (model \`${MODEL:-default}\`$( [ "$USAGE_CAP" -gt 0 ] && echo ", stops at ${USAGE_CAP}% ${CAP_WINDOW//_/-} usage" )). Iteration updates follow."

while running; do
  [ -f "$AW/STOP" ] && { say "STOP file found — exiting"; break; }

  FREE_MB=$(df --output=avail -m "$ROOT" 2>/dev/null | tail -1 | tr -d ' ')
  FREE_MB="${FREE_MB:-100000}"
  if [ "$FREE_MB" -lt 500 ]; then
    say "low disk (${FREE_MB}MB) — pruning old large iter logs"
    find "$LOGS" -name 'iter_*.log' -mtime +0 -size +5M -delete 2>/dev/null
  fi
  if [ "$FREE_MB" -lt 200 ]; then say "disk critically low (${FREE_MB}MB) — stopping"; break; fi

  # usage cap: hard-stop when the chosen window crosses the cap (0 = disabled)
  if [ "$USAGE_CAP" -gt 0 ]; then
    read -r FH SD RS < <(bash "$AW/usage_gate.sh")
    OVER=0
    case "$CAP_WINDOW" in
      five_hour) [ "$FH" -ge "$USAGE_CAP" ] && OVER=1 ;;
      both)      { [ "$FH" -ge "$USAGE_CAP" ] || [ "$SD" -ge "$USAGE_CAP" ]; } && OVER=1 ;;
      *)         [ "$SD" -ge "$USAGE_CAP" ] && OVER=1 ;;
    esac
    if [ "$OVER" = "1" ]; then
      say "usage cap hit: five_hour=${FH}% seven_day=${SD}% cap=${USAGE_CAP}%/${CAP_WINDOW} — stopping"
      notify "🛑 **AFK worker hit the ${USAGE_CAP}% ${CAP_WINDOW//_/-} usage cap** (5h ${FH}% / 7d ${SD}%). Stopped as instructed."
      OUTCOME="usage-cap"
      break
    fi
  fi

  # iteration type: every Nth is an adversarial review pass instead of a build pass
  KIND="build"; PFILE="$AW/PROMPT.txt"; MARGS=(); [ -n "$MODEL" ] && MARGS=(--model "$MODEL")
  if [ "$REVIEW_EVERY" -gt 0 ] && [ "$ITER" -gt 1 ] && [ $(( ITER % REVIEW_EVERY )) -eq 0 ] && [ -f "$AW/REVIEW_PROMPT.txt" ]; then
    KIND="review"; PFILE="$AW/REVIEW_PROMPT.txt"; MARGS=(); [ -n "$REVIEW_MODEL" ] && MARGS=(--model "$REVIEW_MODEL")
  fi

  LOG="$LOGS/iter_${ITER}.log"
  say "iter $ITER ($KIND) starting (log: $LOG)"
  cd "$ROOT" || break
  HEAD_BEFORE=$(git rev-parse HEAD 2>/dev/null || echo none)
  timeout "$TIMEOUT" "$CLAUDE" -p "$(cat "$PFILE")" \
      ${MARGS[@]+"${MARGS[@]}"} \
      --dangerously-skip-permissions >> "$LOG" 2>&1
  RC=$?
  DONE=$(( DONE + 1 ))
  say "iter $ITER ($KIND) finished rc=$RC ($(wc -c < "$LOG" 2>/dev/null || echo 0) bytes)"

  if [ $(( ITER % POST_EVERY )) -eq 0 ]; then
    ICON="🛠️"; [ "$KIND" = "review" ] && ICON="🔎"
    notify "$ICON **$(basename "$ROOT") — iteration $ITER ($KIND) done** (rc=$RC)
$(last_worklog)"
  fi

  if grep -qiE "$LIMIT_RE" "$LOG" 2>/dev/null; then
    say "usage/session limit detected — backing off, re-probing every 7 min"
    while running && [ ! -f "$AW/STOP" ]; do
      sleep 420
      PROBE=$(timeout 300 "$CLAUDE" -p "reply with exactly: ok" ${MARGS[@]+"${MARGS[@]}"} --dangerously-skip-permissions 2>&1 | tail -3)
      if echo "$PROBE" | grep -qi 'ok' && ! echo "$PROBE" | grep -qiE "$LIMIT_RE"; then
        say "usage restored — resuming"; break
      fi
      say "still limited…"
    done
    # waiting out a usage limit is not "stuck" — don't count it against the guards
  else
    if [ $RC -eq 124 ]; then
      say "iter $ITER hit ${TIMEOUT}s timeout — cooldown 120s"; sleep 120
    elif [ $RC -ne 0 ]; then
      say "iter $ITER error rc=$RC — cooldown 180s"; sleep 180
    else
      sleep "$BREATHER"
    fi

    # goal gate: a boolean check is the ONLY thing allowed to declare victory
    if [ -x "$AW/DONE_CHECK.sh" ] && bash "$AW/DONE_CHECK.sh" >/dev/null 2>&1; then
      say "DONE_CHECK.sh passed — goal achieved, stopping as SUCCESS"
      notify "🏆 **AFK worker: GOAL ACHIEVED** — \`$(basename "$ROOT")\` DONE_CHECK passed after $ITER iterations."
      OUTCOME="success"
      break
    fi

    # no-progress guard: the protocol requires a commit every iteration. Repeated iters with
    # no new commit mean the worker is stuck/erroring/refusing — stop rather than burn usage.
    if [ "$(git rev-parse HEAD 2>/dev/null || echo none)" = "$HEAD_BEFORE" ]; then
      IDLE=$(( IDLE + 1 )); say "no new commit this iter (idle ${IDLE}/${MAX_IDLE})"
    else
      IDLE=0
    fi
    if [ "$MAX_IDLE" -gt 0 ] && [ "$IDLE" -ge "$MAX_IDLE" ]; then
      say "no progress for $IDLE consecutive iterations — stopping to avoid idle burn"
      notify "⚠️ **AFK worker stopped** — $IDLE consecutive iterations without a commit (stuck guard)."
      OUTCOME="stuck"
      break
    fi

    # evaluator: cheap model judges the iteration from WORKLOG + commits (fail-open)
    if [ "$EVAL" = "1" ]; then
      DIFFSTAT=$( { git log --oneline -3; git diff --stat HEAD~1..HEAD 2>/dev/null | tail -6; } 2>/dev/null )
      VERDICT=$(timeout 180 "$CLAUDE" -p "You are the evaluator for an autonomous coding loop. GOAL (head): $(head -c 800 "$AW/GOAL.md" 2>/dev/null). LATEST WORKLOG ENTRY: $(last_worklog). RECENT COMMITS: ${DIFFSTAT:-none}. Judge THIS iteration only. Reply with exactly one word: PROGRESSING (real on-goal progress), STUCK (repeat/no-op/still broken), DRIFTING (off-goal work), or DONE (the goal's success criterion is clearly met)." \
          --model "$EVAL_MODEL" --dangerously-skip-permissions 2>/dev/null \
        | grep -oE 'PROGRESSING|STUCK|DRIFTING|DONE' | tail -1)
      VERDICT="${VERDICT:-PROGRESSING}"
      say "evaluator verdict: $VERDICT"
      case "$VERDICT" in
        STUCK|DRIFTING)
          BAD=$(( BAD + 1 ))
          say "bad verdict streak ${BAD}/${MAX_BAD}"
          if [ "$MAX_BAD" -gt 0 ] && [ "$BAD" -ge "$MAX_BAD" ]; then
            say "evaluator: $BAD consecutive STUCK/DRIFTING verdicts — stopping"
            notify "⚠️ **AFK worker stopped by evaluator** — $BAD consecutive ${VERDICT} iterations on \`$(basename "$ROOT")\`. Check the WORKLOG."
            OUTCOME="evaluator-stop"
            break
          fi ;;
        DONE)
          BAD=0; DONEHINTS=$(( DONEHINTS + 1 ))
          if [ "$DONEHINTS" -eq 2 ]; then
            say "evaluator has signalled DONE twice — DONE_CHECK.sh has not confirmed; notifying"
            notify "💡 **AFK evaluator thinks the goal is met** on \`$(basename "$ROOT")\`, but DONE_CHECK.sh hasn't confirmed. Edit autowork/DONE_CHECK.sh to encode 'done', or \`touch autowork/STOP\`."
          fi ;;
        *) BAD=0 ;;
      esac
    fi
  fi
  ITER=$(( ITER + 1 ))
done

ELAPSED_MIN=$(( ( $(date +%s) - START ) / 60 ))
say "=== afk supervisor done after ${ELAPSED_MIN} min, ${DONE} iterations, outcome=${OUTCOME} ==="
notify "🏁 **AFK worker finished** — \`$(basename "$ROOT")\`: ${OUTCOME} after ${ELAPSED_MIN} min, ${DONE} iterations."
{
  echo ""
  echo "## $(date -u +%Y-%m-%dT%H:%MZ) — afk supervisor shutdown"
  echo "- run ended: ${OUTCOME} (${ELAPSED_MIN} min elapsed, ${DONE} iterations)."
  echo "- see autowork/supervisor.log and git log for the trail."
} >> "$AW/WORKLOG.md"
cd "$ROOT" && git add -A 2>/dev/null && \
  git -c user.name=afk -c user.email=afk@local commit -qm "afk: supervisor shutdown (${OUTCOME})" 2>/dev/null
exit 0
