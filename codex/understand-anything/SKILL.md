---
name: understand-anything
description: "[Ported from Claude personal skill] Turn any codebase, wiki, or doc corpus into an interactive knowledge graph (nodes for files/functions/classes/concepts, edges for imports/calls/inheritance/references) using the Understand-Anything multi-agent pipeline from github.com/Lum1104/Understand-Anything. Use when the user types /understand, /understand-domain, /understand-knowledge, asks to \"map this codebase\", \"build a knowledge graph\", \"give me a guided tour of this repo\", \"extract the architecture of X\", \"make sense of this project\", or wants to onboard onto an unfamiliar codebase. Also triggers on requests to install the Understand-Anything plugin, view its dashboard, or interpret a knowledge-graph.json output. Skip for simple grep/exploration tasks where a single-shot read is enough."
---

# Understand-Anything

## Codex Compatibility

This skill was ported from a Claude skill. Interpret Claude Code-specific wording using Codex equivalents:

- Use `functions.shell_command` for shell commands and filesystem inspection.
- Use `apply_patch` for manual file edits.
- Use `update_plan` for task checklists when a plan is useful.
- Use `web.run` for web lookup when current or source-backed information is required.
- Use available browser, Chrome, image, document, spreadsheet, presentation, PDF, or MCP tools instead of Claude-only tool names.
- Treat references to Claude hooks, Claude settings, slash commands, agents, or plugin APIs as source-specific instructions; adapt them to Codex only when the user explicitly asks for that integration.


A multi-agent pipeline that scans a project, extracts every file / function / class / dependency, and emits a knowledge graph at `.understand-anything/knowledge-graph.json` plus an interactive dashboard. Designed for AI coding assistants (Claude Code, Codex, Cursor, Copilot, Gemini CLI, etc.). MIT license. Upstream: https://github.com/Lum1104/Understand-Anything.

## When this skill fires

The user wants to **understand a system as a whole** before editing it - a new repo, a wiki, a domain model. Symptoms:

- "What is this project doing?"
- "Onboard me onto this codebase."
- "Build me a guided tour of X."
- "Extract the architecture."
- Typed slash commands: `/understand`, `/understand-domain`, `/understand-knowledge`.

Skip if the user just wants one file read or one function explained - that's not graph-scale work.

## Install (Claude Code)

```
/plugin marketplace add Lum1104/Understand-Anything
/plugin install understand-anything
```

Other platforms (Codex, Gemini CLI, Hermes, OpenCode, Cline, KIMI, Trae, Vibe, Antigravity, Pi, OpenClaw): clone the repo and run `./install.sh <platform-name>`. Cursor and VS Code Copilot auto-discover.

After install, the three slash commands become available in the host CLI.

## Slash commands

| Command | What it does | Adds which agent |
|---|---|---|
| `/understand` | Builds a structural graph of any codebase. Default verb. | scanner, file-analyzer, architecture-analyzer, tour-builder, graph-reviewer |
| `/understand-domain` | Adds business-domain extraction: flows, process steps, domain boundaries. Use on apps with non-trivial business logic. | + `domain-analyzer` |
| `/understand-knowledge` | Treats input as wiki / article corpus, extracts entities + claims + implicit relations. Use on `.md` knowledge bases, not source code. | + `article-analyzer` |

### Useful flags

- `--language <lang>` - localizes node summaries, dashboard UI, and guided-tour text.
- `--review` - runs the full LLM `graph-reviewer` pass (inline review otherwise). Slower, catches more.

## Architecture (how it actually works)

Two-layer hybrid:

1. **Tree-sitter (deterministic).** Parses source into a concrete syntax tree. Extracts imports, exports, function/class definitions, call sites, inheritance. Builds an `importMap` during scan and passes it to file-analyzers so they never re-derive imports. Same input  to  same output, every run. Also powers fingerprint-based change detection for incremental updates - only re-analyze files whose AST fingerprint changed.

2. **LLM (semantic).** Reads the parsed structure + the original source, then produces what parsers cannot: plain-English summaries, tags, architectural layer assignments, business-domain mapping, guided tours, language-feature callouts.

The split matters: structural facts come from tree-sitter (cheap, reproducible), narrative explanation comes from the LLM (expensive, regenerated only on change).

### Agents

| Agent | Role |
|---|---|
| `project-scanner` | Discover files, detect languages and frameworks |
| `file-analyzer` | Extract functions, classes, imports; produce graph nodes and edges |
| `architecture-analyzer` | Identify architectural layers (presentation, domain, infra, etc.) |
| `tour-builder` | Generate guided learning tours through the graph |
| `graph-reviewer` | Validate graph completeness and referential integrity |
| `domain-analyzer` | Extract business domains, flows, process steps *(used by `/understand-domain`)* |
| `article-analyzer` | Extract entities, claims, implicit relations *(used by `/understand-knowledge`)* |

## Output

- **`.understand-anything/knowledge-graph.json`** - primary artifact. Nodes (files, functions, classes, concepts) + edges (imports, calls, inheritance, references) + per-node summaries + tours.
- **Interactive dashboard** - opens in browser; click any node for summary, relationships, and tours. Localized via `--language`.
- **Guided tours** - ordered node sequences with prose for learning paths (e.g. "request lifecycle from controller to DB").

## How to behave when the user invokes this skill

1. **First check if the plugin is actually installed.** Look for `~/.claude/plugins/` entry or for `.understand-anything/` in the project root. If neither exists, surface the install commands; don't pretend to invoke `/understand` yourself - it's a host-CLI command, not something this skill executes directly.
2. **If `.understand-anything/knowledge-graph.json` already exists, read it first.** The graph is the source of truth for any "what is this project" question. Cite node names from it; don't re-derive structure.
3. **Pick the right verb.** Code repo  to  `/understand`. Domain-heavy app (commerce, finance, healthcare)  to  `/understand-domain`. Markdown wiki / docs corpus  to  `/understand-knowledge`.
4. **Re-running is cheap on unchanged files.** Tree-sitter fingerprints mean only changed files get LLM re-analysis. Suggest `/understand` after big merges or refactors.
5. **Don't replace the graph as a working tool.** When the graph is built, point the user at the dashboard and the tours - that's the deliverable. Your job is orchestration + interpretation, not graph rendering.

## Common pitfalls

- **Calling `/understand` from inside Claude Code's tool layer.** It's a slash command for the host shell, not a Claude tool. Tell the user to type it; don't try to invoke it through Bash.
- **Treating it as a search tool.** It's a one-time build that produces an artifact. Don't re-run on every question - read the existing graph.
- **Confusing the three verbs.** `/understand-knowledge` on a code repo will under-extract structure; `/understand` on a markdown wiki will under-extract semantics.

## Demo

A standalone demo of the produced graph + tour UX lives at `C:\Users\Tarlu\Desktop\Understand-Anything Demo.html` - single file, no install, mocked data, illustrates what the real output looks and feels like.
