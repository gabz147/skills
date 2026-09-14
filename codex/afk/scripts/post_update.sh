#!/usr/bin/env bash
# Post a progress update to a Discord channel via bot token. Best-effort: never fails the loop.
# Usage: post_update.sh "message"   (or pipe the message on stdin)
# Env: AFK_DISCORD_CHANNEL (required)  channel id to post to
#      AFK_DISCORD_ENV     (optional)  env file with DISCORD_TOKEN (default ~/restoration-research/.env)
set -u
CH="${AFK_DISCORD_CHANNEL:-}"
[ -n "$CH" ] || exit 0
ENVF="${AFK_DISCORD_ENV:-$HOME/restoration-research/.env}"
BOT=$(grep -m1 '^DISCORD_TOKEN=' "$ENVF" 2>/dev/null | cut -d= -f2- | tr -d '"' | tr -d "'")
[ -n "${BOT:-}" ] || exit 0
MSG="${1:-}"
[ -n "$MSG" ] || MSG="$(cat)"
[ -n "$MSG" ] || exit 0
jq -n --arg c "$MSG" '{content: ($c | .[0:1900])}' | \
  curl -sS -m 20 -X POST "https://discord.com/api/v10/channels/$CH/messages" \
    -H "Authorization: Bot $BOT" -H "Content-Type: application/json" -d @- >/dev/null 2>&1
exit 0
