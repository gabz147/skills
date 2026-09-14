#!/usr/bin/env bash
# Full kit by default. Legacy client argument installs only that skill library.
set -euo pipefail
repo="$(cd "$(dirname "$0")" && pwd)"
args=()
if [[ "${1:-}" =~ ^(all|claude|codex)$ ]]; then
  args+=(--skills-only --client "$1")
  shift
fi
if [[ "${FORCE:-0}" == 1 ]]; then args+=(--replace); fi
exec python3 "$repo/setup.py" "${args[@]}" "$@"
