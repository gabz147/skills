#!/usr/bin/env python3
"""Bridge a manifest into DaVinci Resolve Free without hard-coded user paths."""
from __future__ import annotations
import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--mode", choices=("build", "render", "both"), default="both")
    parser.add_argument("--resolve-cmd", default=os.environ.get("ARC_RESOLVE_CMD", "resolve.cmd"))
    parser.add_argument("--poll-seconds", type=float, default=3.0)
    args = parser.parse_args()
    manifest = Path(args.manifest).resolve()
    if not manifest.is_file():
        raise SystemExit(f"Manifest not found: {manifest}")
    manifest_data = json.loads(manifest.read_text(encoding="utf-8"))
    skill_dir = Path(__file__).resolve().parent
    resolve_script = skill_dir / "resolve_montage.py"
    ping = subprocess.run([args.resolve_cmd, "--json", "bridge", "ping"], text=True, capture_output=True)
    if ping.returncode != 0:
        raise SystemExit("Resolve bridge is unavailable. Open Resolve and run Workspace > Scripts > cli_anything_daemon.")

    def execute(mode: str) -> dict:
        wrapper = Path(tempfile.gettempdir()) / f"arc_montage_resolve_{os.getpid()}_{mode}.py"
        code = (f"MANIFEST_PATH = {str(manifest)!r}\nMODE = {mode!r}\n"
                f"exec(compile(open({str(resolve_script)!r}, 'rb').read(), {str(resolve_script)!r}, 'exec'))\n")
        wrapper.write_text(code, encoding="utf-8")
        try:
            run = subprocess.run([args.resolve_cmd, "--json", "bridge", "exec", "--file", str(wrapper)], text=True, capture_output=True)
        finally:
            wrapper.unlink(missing_ok=True)
        if run.returncode != 0:
            raise SystemExit(run.stderr or run.stdout or f"Resolve {mode} failed")
        try:
            return json.loads(run.stdout)
        except json.JSONDecodeError:
            return {"raw": run.stdout}

    result = {}
    if args.mode in {"build", "both"}:
        result["build"] = execute("build")
    if args.mode in {"render", "both"}:
        result["render"] = execute("render")
        output = Path(result["render"].get("output", ""))
        deadline = time.time() + 86_400
        while time.time() < deadline:
            state = subprocess.run([args.resolve_cmd, "--json", "bridge", "call", "project.IsRenderingInProgress"], text=True, capture_output=True)
            if state.returncode == 0 and "true" not in state.stdout.lower():
                break
            time.sleep(args.poll_seconds)
        if not output.is_file() or output.stat().st_size == 0:
            raise SystemExit("RENDER_FAILED: Resolve reported completion but the expected output is missing: " + str(output))
        result["output"] = str(output)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
