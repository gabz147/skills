#!/usr/bin/env bash
# Full kit by default. Legacy client argument installs only that skill library.
set -euo pipefail
repo="$(cd "$(dirname "$0")" && pwd)"
case "${1:-}" in
  all|claude|codex)
    client="$1"
    shift
    set -- --skills-only --client "$client" "$@"
    ;;
esac
if [[ "${FORCE:-0}" == 1 ]]; then set -- --replace "$@"; fi
exec python3 "$repo/setup.py" "$@"
