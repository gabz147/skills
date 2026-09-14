#!/usr/bin/env bash
# Scaffold an AFK workspace.
# Usage: afk-init.sh <workspace_dir>     (goal text is read from stdin)
set -eu
DIR="$1"
SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GOAL="$(cat)"   # goal text piped in

mkdir -p "$DIR/autowork/logs"
cd "$DIR"
[ -d .git ] || git init -q
git config user.name  >/dev/null 2>&1 || git config user.name  afk
git config user.email >/dev/null 2>&1 || git config user.email afk@local

# Keep deps, build output, secrets, and logs out of the repo. The worker runs `git add -A`
# every iteration; without this, node_modules/venvs bloat history and a stray .env leaks secrets.
if [ ! -f "$DIR/.gitignore" ]; then
  cat > "$DIR/.gitignore" <<'EOF'
# dependencies / virtualenvs (huge; never commit)
node_modules/
.venv/
venv/
__pycache__/
*.pyc
# build output (regenerable)
dist/
build/
.next/
.cache/
# secrets & local-only config
.env
.env.*
*.local
# logs (incl. the supervisor's own iter logs)
*.log
autowork/logs/
# os cruft
.DS_Store
EOF
fi

cp "$SKILL_DIR/scripts/supervisor.sh" "$DIR/autowork/supervisor.sh"
chmod +x "$DIR/autowork/supervisor.sh"
cp "$SKILL_DIR/assets/AUTOWORK.md" "$DIR/autowork/AUTOWORK.md"
cp "$SKILL_DIR/assets/PROMPT.txt"  "$DIR/autowork/PROMPT.txt"
printf '%s\n' "$GOAL" > "$DIR/autowork/GOAL.md"

TS="$(date -u +%Y-%m-%dT%H:%MZ)"
{
  echo "# AFK WORKLOG — append-only memory shared across iterations"
  echo "# Each iteration reads the last few entries to orient, then appends one of its own."
  echo ""
  echo "## $TS — kickoff"
  echo "- goal: $(head -1 "$DIR/autowork/GOAL.md")"
  echo "- state: not started"
  echo "- next-best step: scaffold the project and land a first runnable slice"
} > "$DIR/autowork/WORKLOG.md"

# baseline commit so the no-progress guard has a clean HEAD to compare against
git add -A
git -c user.name=afk -c user.email=afk@local commit -qm "afk: kickoff scaffold" 2>/dev/null || true

echo "scaffolded $DIR"
