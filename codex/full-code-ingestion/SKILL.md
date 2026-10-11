---
name: full-code-ingestion
description: "[Ported from Claude personal skill] Enter a strict no-summarization reading mode for deep codebase/large-file analysis. Chunk-based sequential ingestion, preserve exact logic and naming, build an internal file/function/dependency map before any explanation. Triggers on commands INGEST CODE, NEXT CHUNK, BUILD MAP, EXPLAIN."
---

# Full Code Ingestion Mode

## Codex Compatibility

This skill was ported from a Claude skill. Interpret Claude Code-specific wording using Codex equivalents:

- Use `functions.shell_command` for shell commands and filesystem inspection.
- Use `apply_patch` for manual file edits.
- Use `update_plan` for task checklists when a plan is useful.
- Use `web.run` for web lookup when current or source-backed information is required.
- Use available browser, Chrome, image, document, spreadsheet, presentation, PDF, or MCP tools instead of Claude-only tool names.
- Treat references to Claude hooks, Claude settings, slash commands, agents, or plugin APIs as source-specific instructions; adapt them to Codex only when the user explicitly asks for that integration.


Deep, lossless reading of full codebases and large files. No summarization during ingestion - preserve exact logic, naming, and structure.

## When to Use

Use this skill when the user issues any of:

- `INGEST CODE` - begin full ingestion workflow on a file / repo / web source
- `NEXT CHUNK` - continue processing the next chunk of the current ingestion
- `BUILD MAP` - output the architecture, dependency graph, and execution flow for the current ingestion
- `EXPLAIN` - provide high-level explanation (only allowed after ingestion is complete)

Also use it implicitly when the user asks for deep analysis of a large codebase, a reverse-engineering pass, or an architecture writeup that must not lose detail.

## Core Rules

1. **No summarization during ingestion.** Never compress or paraphrase code while reading. Treat every file as source of truth.
2. **Chunk-based sequential processing.** If input exceeds context, split into chunks, process in order, maintain continuity across chunks.
3. **Stateful understanding.** Continuously build an internal model of:
   - File structure
   - Functions / classes / exports
   - Imports / dependencies
   - Execution flow
   - Key variables and data transformations

## Ingestion Workflow

### Step 1 - Detect input type
- Single file / multiple files / full repo / web source.

### Step 2 - Acquire RAW content (priority order)
1. Local files (preferred)
2. Raw URLs (e.g. `raw.githubusercontent.com`)
3. Direct file dumps from the user
4. HTML stripped to plaintext - LAST resort only

Never rely on a summarized fetch of code.

### Step 3 - Chunk processing loop
For each chunk:
1. Read fully, end to end
2. Extract: functions, classes, imports, side effects
3. Track relationships: function calls, data flow, mutations
4. Record findings as structured notes (not prose)
5. Request the next chunk if more remains

### Step 4 - Build internal model
Once all chunks are ingested, construct:
- Dependency graph
- Execution flow map
- File / module relationships

## Output Modes

**During ingestion:** structured notes only. No high-level summaries, no "this code basically does X".

**After ingestion complete:** now allowed to summarize, explain architecture, answer questions.

## Failure Handling

- File truncated  to  request continuation, do not infer.
- Context limit reached  to  compress your NOTES, never the code.
- Missing dependencies  to  ask the user for the files.

## Strict Prohibitions

- Do not skip sections.
- Do not infer missing code.
- Do not compress logic prematurely.
- Do not replace code with summaries.

## Behavioral Mode

You are acting as a static code analyzer and reverse engineer, not a summarizer.

Priority: **Accuracy > Completeness > Speed.**

## Example Flow

```
User: INGEST CODE https://github.com/org/repo/blob/main/server.ts
You:  [fetch raw file]
      [chunk 1] structured notes: imports, class Server, route table...
      "Continue? (NEXT CHUNK)"
User: NEXT CHUNK
You:  [chunk 2] notes on middleware, auth pipeline, db adapters...
...
User: BUILD MAP
You:  [full dependency graph + execution flow]
User: EXPLAIN
You:  [high-level architecture summary, now permitted]
```
