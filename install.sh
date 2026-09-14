#!/usr/bin/env bash
# Usage: ./install.sh [all|claude|codex]   FORCE=1 to overwrite existing skills
set -euo pipefail
client="${1:-all}"
repo="$(cd "$(dirname "$0")" && pwd)"
install_one() {
  local c="$1" dst="$2" src="$repo/$1" copied=0 skipped=0
  [ -d "$src" ] || { echo "missing source folder $src" >&2; return; }
  mkdir -p "$dst"
  for item in "$src"/* "$src"/.[!.]*; do
    [ -e "$item" ] || continue
    name="$(basename "$item")"
    if [ -e "$dst/$name" ] && [ "${FORCE:-0}" != "1" ]; then skipped=$((skipped+1)); continue; fi
    rm -rf "$dst/$name"
    cp -R "$item" "$dst/$name"
    copied=$((copied+1))
  done
  echo "$c: copied $copied, skipped $skipped existing -> $dst"
}
[ "$client" = all ] || [ "$client" = claude ] && install_one claude "$HOME/.claude/skills"
[ "$client" = all ] || [ "$client" = codex ]  && install_one codex "$HOME/.codex/skills"
echo "Restart Claude Code / Codex so the skill lists reload."
