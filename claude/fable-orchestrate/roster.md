# The Roster — what Fable routes over

Fable assigns each task **one agent type × one model**. Pick the cheapest combination that can do the task well enough for Fable to verify afterward. Escalate only where probability-of-error × cost-of-error is high.

## Models (the `model` override)

| Model | Use for | Never for |
|-------|---------|-----------|
| `haiku` | Cheap mechanical work: locating files, boilerplate, renames, simple transforms, gathering/listing, first-pass scouting. | Anything needing judgment or hard-to-check output. |
| `sonnet` | Default worker: real implementation, writing, drafting, non-trivial edits, most tasks. | The judgment itself. |
| `opus` | Hard sub-problems that are still *labor*, not judgment — a gnarly algorithm, a subtle refactor Sonnet keeps failing, dense synthesis. | Routine work Sonnet handles (waste of cost). |
| `fable` | **Planning, routing, verification, final judgment only.** | Any grunt work, ever. Not a workhorse. |
| `sol:low`<br>`sol:medium`<br>`sol:high`<br>`sol:xhigh` | **Codex `gpt-5.6-sol`, a non-Claude model.** Independent implementation, a second opinion on a Claude-family result, or a task Sonnet/Opus both failed. Effort tier ≈ haiku/sonnet/opus/opus-hard. | Anything, if the run's preflight said `unavailable`. Bulk cheap work (Haiku is cheaper and local). |

Routing rule: start at `haiku`, step up to `sonnet`, then `opus`, only when the task genuinely needs it. Retries escalate one tier automatically (see SKILL.md guards).

**Codex is availability-gated.** The dispatcher runs a smoke test before planning and tells you `CODEX: available` or `CODEX: unavailable — <reason>` (the user's ChatGPT subscription comes and goes). If it says unavailable, `agent=codex` is off the menu for the whole run — do not route a single task to it. If available, every `agent=codex` task must also declare `fallback=<agent>×<model>` so the dispatcher can reroute it if the subscription dies mid-run. See `codex.md`.

## Agent types (the `subagent_type` override)

| Agent | Tools it has | Route here when |
|-------|--------------|-----------------|
| `Explore` | Read-only search/read | Research, codebase mapping, "find where/what", gathering evidence. Cannot write — safe, fast. |
| `general-purpose` | All tools | Multi-step tasks that read AND write: implement a feature, run commands, edit files, browser work. The default worker agent. |
| `claude` | All tools | Same as general-purpose; use when you want a plain catch-all executor. |
| `Plan` | Read-only + architecture | Give to the **Fable planner** for design-heavy goals (paired with `model=fable`). |
| `dispatcher` | The main session | Tasks needing **user interaction** a headless agent can't do: UAC/admin prompts, entering credentials, a decision only the user can make, watching a live thing. The dispatcher runs these inline instead of spawning. |
| `codex` | fs + shell in its own sandbox (`-C <dir>`, `-s <mode>`) | A **different model family** is the point: independent implementation of something Claude also built, a cross-check on a result you can't verify from the inside, or a hard task after the Claude ladder topped out. Not an `Agent` spawn — the dispatcher shells out to `codex exec`. Model must be `sol:<effort>`; requires a passing preflight and a `fallback=`. |

Specialized agents exist too (e.g. `gsd-*`, `statusline-setup`). Ignore them unless the goal is obviously theirs; the four general agents above cover almost everything.

## Tools a task may need (name them in the plan so the worker knows)

- `fs` — read/write files, edit code.
- `bash` / `shell` — run commands, tests, builds.
- `web` — WebSearch / WebFetch for external info.
- `browser` — the claude-in-chrome tools for real web pages.
- `mcp` — a specific MCP server (name it: Supabase, Gmail, Drive, context-mode, etc.).

Codex tasks have `fs` + `bash` inside their sandbox. They do **not** have this session's `browser`/`mcp` tools — never route a browser or MCP task to `agent=codex`.

## Task type → typical routing

| Task type | Agent × Model | Notes |
|-----------|---------------|-------|
| Find/understand code or facts | `Explore` × `haiku`/`sonnet` | Read-only, cheap. |
| Implement / edit code | `general-purpose` × `sonnet` (or `opus` if hard) | Repo → committed per wave. |
| Write / draft prose | `general-purpose` × `sonnet` | Output to a file. |
| Bulk mechanical transform | `general-purpose` × `haiku` | Boilerplate, renames, formatting. |
| Web research | `Explore`/`general-purpose` × `sonnet` + `web` | Fable spot-checks sources. |
| Browser automation | `general-purpose` × `sonnet` + `browser` | Verify by screenshot/console. |
| Interactive / admin step | `dispatcher` | UAC, creds, user choice. |
| Plan / route / verify | `Plan`/`general-purpose` × `fable` | Teacher only. |
| Independent second implementation | `codex` × `sol:medium` + `fallback=general-purpose×sonnet` | Only when having two independent attempts is worth the cost — Fable then compares them. |
| Cross-model check on a Claude result | `codex` × `sol:medium` + `fallback=Explore×sonnet` | Different family catches what the Claude family shares. Give it read-only scope. |
| Claude ladder exhausted on a hard task | `codex` × `sol:high` + `fallback=general-purpose×opus` | Try a different family before declaring blocked. |
