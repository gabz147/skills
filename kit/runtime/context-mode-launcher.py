"""Run pinned Context Mode with disposable tool-output storage and no hooks."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent

def main():
    cache_parent = ROOT / "work-cache"
    cache_parent.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="context-mode-", dir=cache_parent) as cache:
        env = os.environ.copy()
        env.update(CONTEXT_MODE_PLATFORM="codex", CONTEXT_MODE_PROJECT_DIR=os.getcwd(),
                   CONTEXT_MODE_DIR=cache, CONTEXT_MODE_DATA_DIR=cache)
        node = shutil.which("node")
        if not node:
            raise SystemExit("Node.js 22.5+ is required")
        child = subprocess.Popen([node, str(ROOT / "context-mode" / "server.bundle.mjs")],
                                 env=env, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr,
                                 creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
        try:
            return child.wait()
        finally:
            if child.poll() is None:
                child.terminate()
                child.wait(timeout=10)

if __name__ == "__main__":
    raise SystemExit(main())
