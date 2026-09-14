#!/usr/bin/env bash
# Print "<five_hour_pct> <seven_day_pct> <five_hour_resets_at>" from the Claude usage API.
# Prints "0 0 -" on any failure so the loop fails OPEN (the supervisor's own limit
# backoff still catches a genuinely exhausted quota).
TOKEN=$(jq -r '.claudeAiOauth.accessToken // empty' "$HOME/.claude/.credentials.json" 2>/dev/null)
[ -n "$TOKEN" ] || { echo "0 0 -"; exit 0; }
J=$(curl -sS -m 15 https://api.anthropic.com/api/oauth/usage \
      -H "Authorization: Bearer $TOKEN" -H "anthropic-beta: oauth-2025-04-20" 2>/dev/null)
FH=$(echo "$J" | jq -r '.five_hour.utilization // 0' 2>/dev/null | cut -d. -f1)
SD=$(echo "$J" | jq -r '.seven_day.utilization // 0' 2>/dev/null | cut -d. -f1)
RS=$(echo "$J" | jq -r '.five_hour.resets_at // "-"' 2>/dev/null)
case "$FH" in ''|*[!0-9]*) FH=0;; esac
case "$SD" in ''|*[!0-9]*) SD=0;; esac
echo "$FH $SD ${RS:--}"
