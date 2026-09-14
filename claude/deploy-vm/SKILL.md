---
name: deploy-vm
description: Deploy a local build or directory to the user's "targon" Google Compute VM and prove it landed and runs. Use whenever the user says "deploy to targon", "push this to the VM", "ship to the VM", "scp this over", "copy the build to targon", "run this on targon", or asks to get local code/artifacts onto their VM and smoke-tested. Also use when a task ends with "and deploy it" / "get it on the VM" for work done in a local repo. Do not use for git-based deploys, cloud PaaS pushes, or any host other than targon unless the user overrides the target.
---

# Deploy to VM (targon)

Ship a local build to the `targon` Google Compute VM, verify the bytes arrived intact, run a smoke test on the VM, and report the **exact** output. The whole point is no silent failures: `scp` can exit 0 having copied nothing useful, and a process can "start" and immediately die. Prove each hop instead of assuming it.

## The target

Baked-in defaults for this machine — override only if the user names a different host.

| Field | Value |
|-------|-------|
| Instance | `targon` |
| Zone | `us-south1-c` |
| Project | `project-4f261a4a-994f-4a37-820` (gcloud default; usually omit) |
| Remote user | `Tarlu` → home `/home/Tarlu` |
| OS | Debian 12 (Linux) |
| Transport | `gcloud compute ssh` / `gcloud compute scp` — patched to run **inline** (OpenSSH), no PuTTY window. See the `[[gcloud_ssh_openssh_patch]]` memory. |

Command shapes (PowerShell on Windows — quote the whole `--command` string):

```powershell
# Run a command on the VM, output comes back inline
gcloud compute ssh targon --zone=us-south1-c --command="<remote shell>"

# Copy a file up
gcloud compute scp <local-path> targon:<remote-path> --zone=us-south1-c

# Copy a directory up
gcloud compute scp --recurse <local-dir> targon:<remote-dir> --zone=us-south1-c
```

If ssh/scp errors on the first try, run one bare `gcloud compute ssh targon --zone=us-south1-c --command="echo ok"` to re-establish the connection (first connect can provision keys / prompt), then continue. Don't retry a failing transfer more than twice — diagnose instead.

## Workflow

Work through these in order. Report exact command output at each gate, not a paraphrase.

### 1. Confirm what and where

Establish the local artifact and the remote destination before touching the network.
- **Local**: the file or directory to ship. If it's a build, confirm it's freshly built (check mtime, or build it) — don't ship stale output.
- **Remote**: a path under `/home/Tarlu/`. Default to `/home/Tarlu/<project-name>/` unless the user says otherwise. Create it first so `scp` doesn't scatter files:
  ```powershell
  gcloud compute ssh targon --zone=us-south1-c --command="mkdir -p /home/Tarlu/<dest> && echo MKDIR_OK"
  ```

### 2. Transfer — and prove it arrived intact

Copy, then verify by comparing a checksum on both ends. A matching hash is the only trustworthy "it transferred" signal; `scp` exit code alone is not.

```powershell
# Copy
gcloud compute scp --recurse <local-dir> targon:/home/Tarlu/<dest> --zone=us-south1-c

# Local hash (per file, or a manifest for a dir)
Get-FileHash <local-file> -Algorithm SHA256 | Select-Object -ExpandProperty Hash

# Remote hash
gcloud compute ssh targon --zone=us-south1-c --command="sha256sum /home/Tarlu/<dest>/<file>"
```

For a whole directory, compare a sorted manifest of hashes on each side (e.g. remote `find <dest> -type f -exec sha256sum {} \; | sort`) rather than eyeballing one file. If any hash differs or a file is missing, **stop and report** — re-copy the offending files, don't proceed to smoke test.

### 3. Smoke test on the VM

Run the smallest command that proves the deployed thing actually works — not just that files exist. Pick per artifact type:
- **Script / CLI**: run it with `--help`, `--version`, or a trivial real invocation and capture output + exit code.
- **Server**: start it, poll its health endpoint (`curl -s -o /dev/null -w "%{http_code}" http://localhost:<port>/health`), then confirm the process is alive (`pgrep -af <name>`). If it should keep running, launch under `nohup`/`tmux` so it survives the ssh session closing; if it's just a liveness check, start it, probe, and stop it.
- **Static / data**: verify the expected entrypoint file exists and is non-empty (`test -s <file> && echo OK`).

```powershell
gcloud compute ssh targon --zone=us-south1-c --command="cd /home/Tarlu/<dest> && <smoke command>; echo EXIT=$?"
```

The trailing `echo EXIT=$?` makes the remote exit code visible — a smoke test that "ran" but exited non-zero is a failure.

### 4. Report — exact output, honest verdict

Give the user a compact report with the real evidence, in this shape:

```
Deploy: <local> → targon:/home/Tarlu/<dest>
Transfer: <N files, hashes matched | MISMATCH on X>
Smoke test: <command run>
  <exact stdout/stderr, trimmed>
  EXIT=<code>
Verdict: <DEPLOYED & VERIFIED | FAILED at step N: reason>
```

State failures plainly with the output that shows them. If a step was skipped (e.g. no smoke test possible), say so — don't imply verification that didn't happen.

## Notes & gotchas

- **Windows quoting**: keep the entire remote command inside one double-quoted `--command="..."` string. Chain remote steps with `&&`/`;` *inside* that string, not with PowerShell operators. This is the source of past scp/ssh quoting bugs on this machine.
- **First connect** may provision SSH keys or prompt once — if a command hangs or asks something, tell the user; don't feed credentials from a screenshot.
- **Long-running processes**: an ssh `--command` process is killed when the session ends. Use `nohup <cmd> >/home/Tarlu/<dest>/run.log 2>&1 &` or a `tmux new-session -d` so a deployed server keeps running after you disconnect, then verify with a fresh ssh + `pgrep`.
- **Elevated/system changes** on the VM (systemd units, ports <1024, apt installs) need `sudo`; targon's `Tarlu` has sudo but say what you're about to run before running it.
- **Overriding the target**: if the user names a different instance/zone, use theirs and skip the targon defaults — everything else in this workflow still applies.
