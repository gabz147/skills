---
name: skill-scout
description: >
  Discover candidate Claude Code skills, agents, and tools from GitHub trending
  and agent-skill sources, then evaluate each against the user's current live
  skill roster to produce an ADD/PASS verdict with reasoning. Use when the user
  asks to "scout for new skills," "find new skills," "check what's trending for
  Claude Code," "see if there's a skill for X I don't already have," "audit my
  skill roster for duplicates," or runs /skill-scout. Never hardcodes the skill
  roster or the candidate list — both are derived fresh at run time.
---

# Skill Scout

Find new Claude Code skills/agents/tools worth adding, without recommending
anything that already exists in the user's roster under a different name.
Every run re-derives both the roster and the candidate list live — nothing in
this file is a source of truth for either.

## Workflow

### 1. Build the live roster

Never assume roster contents from memory or from a prior run. Glob every
installed `SKILL.md` and extract `name:` + `description:` from its YAML
frontmatter, tolerating both single-line descriptions and YAML block-scalar
descriptions (`description: >` / `description: |` spanning multiple indented
lines). Run this (or equivalent) fresh each invocation:

```powershell
$skills = Get-ChildItem "C:\Users\Tarlu\.claude\skills\*\SKILL.md" | ForEach-Object {
    $dir = $_.Directory.Name
    $text = Get-Content $_.FullName -Raw
    if ($text -match '(?s)^---\r?\n(.*?)\r?\n---') {
        $fm = $Matches[1]
        $name = if ($fm -match '(?m)^name:\s*(.+)$') { $Matches[1].Trim() } else { $dir }
        $desc = ''
        if ($fm -match '(?ms)^description:\s*[>|][-+]?\s*\r?\n((?:^[ \t]+.*\r?\n?)+)') {
            # block scalar: join the indented continuation lines
            $desc = ($Matches[1] -split '\r?\n' | ForEach-Object { $_.Trim() } | Where-Object { $_ }) -join ' '
        } elseif ($fm -match '(?m)^description:\s*(.+)$') {
            $desc = $Matches[1].Trim()
        }
        [PSCustomObject]@{ Name = $name; Dir = $dir; Description = $desc }
    }
}
$skills | Sort-Object Name | Format-Table -AutoSize
```

Keep the resulting `{name, capability}` list in memory for the rest of the
run — it is the roster you diff every candidate against in step 5. If a
`SKILL.md` fails to parse, log its directory name and skip it; do not abort
the whole scan over one bad file.

### 2. Fetch candidate sources via the fallback chain

Fetching is an **explicit ordered fallback chain** — never rely on a single
fetch mechanism as the only route, since some environments block or intercept
it. For each source below, try in order and stop at the first that succeeds:

1. **WebFetch** (or the environment's built-in fetch tool) — works for static,
   server-rendered pages.
2. **browser-harness CLI** — for JS-gated pages:
   ```bash
   browser-harness -c '
   new_tab("<url>")
   wait_for_load()
   print(page_info())
   '
   ```
   then use `js(...)` to extract the specific DOM content needed (repo cards,
   list items, etc).
3. **claude-in-chrome MCP** (`navigate` + `read_page`) — last resort, when the
   first two both fail or return unusable output.

If WebFetch errors out immediately on the very first call (an interception/
policy error, not empty or wrong content from a rendered page), that is an
environment-wide block, not a per-page problem — a static raw file will fail
the exact same way a JS-gated page does. Confirm once against any static URL;
if it still errors immediately, treat tier 1 as dead for the rest of the run
and go straight to tier 2 for every remaining fetch instead of re-trying tier
1 per URL.

Sources to pull, and their known status:

| Source | URL pattern | Status |
|---|---|---|
| GitHub trending (daily) | `github.com/trending` | static |
| GitHub trending (weekly) | `github.com/trending?since=weekly` | static |
| Topic: claude-skills | `github.com/topics/claude-skills` | static |
| Topic: agent-skills | `github.com/topics/agent-skills` | static |
| Topic: claude-code | `github.com/topics/claude-code` | static |
| GitHub search | `github.com/search?q=<query>&type=repositories` (e.g. `"claude skill"`, `"agent skill"`) | JS-gated — needs tier 2 or 3 |

From trending/topic pages, extract `owner/repo`, description, and star count.
From search results, extract the same fields once the page is rendered via
tier 2/3.

If a source fails on all three tiers, **note which source failed and move
on** — do not abort the run. The final report must call out any source that
could not be reached.

### 3. Filter and cap candidates

From everything collected in step 2, keep only repos plausibly relevant as an
installable skill, agent, or dev-workflow tool (i.e. something that could
reasonably become a `SKILL.md`, MCP server, CLI agent, or Claude Code
plugin). Discard unrelated trending noise (random app repos, course
materials, etc). Cap the list at roughly **10-15 candidates**, preferring
higher star counts and more recent pushes when trimming. Deduplicate repos
that appeared from multiple sources.

### 4. Fetch each candidate's README

For each surviving candidate, fetch its README through the raw-content
pattern, trying branches in order until one resolves:

```
https://raw.githubusercontent.com/<owner>/<repo>/HEAD/README.md
https://raw.githubusercontent.com/<owner>/<repo>/main/README.md
https://raw.githubusercontent.com/<owner>/<repo>/master/README.md
```

Use the same fallback chain from step 2 to fetch each URL (plain fetch first,
then browser-harness, then claude-in-chrome). If tier 1 was already found
environment-blocked in step 2, skip straight to tier 2 here too — the raw
content host being a static file doesn't help if the fetch tool
itself is intercepted before it reaches the network.

Summarize what the tool/skill actually does in 1-2 sentences from the
README content. If no README resolves on any branch, mark the candidate as
"README unreachable" and evaluate it only from its description/stars — do not
invent capability details that were never fetched.

### 5. Evaluate each candidate against the roster

For every candidate, compare against the in-memory roster from step 1 on
**two axes**:

- **Name duplication** — does the candidate's name (or an obvious rename of
  it) match an existing roster skill's name?
- **Functional overlap** — does the candidate's summarized capability
  substantially overlap what an existing roster skill already does, even
  under a different name?

Verdict rules:
- **PASS** if it duplicates an existing skill on either axis — you must name
  the specific overlapping roster skill in the reasoning (e.g. "PASS —
  overlaps <roster-skill>, which already covers this capability").
- **PASS** if the candidate is low-quality, abandoned, too narrow/niche to be
  broadly useful, or not actually a skill/agent/tool (e.g. a demo app, a
  tutorial repo).
- If the candidate is itself a bundle of many distinct skills (an
  awesome-list or multi-skill repo), judge it holistically as one row:
  **PASS** if most of its contained skills duplicate roster entries, naming
  the overlapping ones; mention any genuinely novel skill inside it as a
  caveat in the reasoning rather than splitting it into extra rows.
- **ADD** otherwise — it fills a real gap in the current roster.

Never invent repos, star counts, or capabilities that were not actually
fetched in steps 2-4. If data is thin (e.g. README unreachable), say so in
the reasoning rather than guessing.

### 6. Emit the report

Produce a table (or list) with one row per surviving candidate from step 3:

| Candidate (owner/repo) | Stars | Verdict | Why | Install-how (ADD only) |
|---|---|---|---|---|
| owner/repo | 1.2k | ADD | Fills gap: ... | `git clone` into a skills dir, or copy its `SKILL.md` into `C:\Users\Tarlu\.claude\skills\<name>\`, or install via plugin/marketplace if it ships one |
| owner/repo | 340 | PASS | Duplicates `existing-skill-name` — same capability | — |

For each **ADD**, give a concrete install-how: clone the repo into a skills
working directory, copy/adapt its `SKILL.md` into
`C:\Users\Tarlu\.claude\skills\<name>\SKILL.md`, or note if it ships as a
plugin/marketplace entry that can be installed directly.

Close with:
- A one-line list of any sources that failed to fetch (or "all sources
  reachable" if none did).
- A summary line: `N ADD, M PASS` (counts derived from the table just
  produced, never hardcoded).

## Rules

- The roster is always derived live via step 1's glob — never hardcode roster
  entries, counts, or names in this file or in a report.
- PASS any functional duplicate and name the overlapping roster skill
  explicitly; a bare "PASS — duplicate" without naming which skill it
  duplicates is not acceptable.
- Degrade gracefully: if a source is unreachable on all three fetch tiers,
  report the failure and continue with whatever sources did work. A single
  dead source must never abort the whole scout.
- Never invent repos, stars, descriptions, or capabilities — only report data
  that was actually fetched in this run.
- No hardcoded dates, session-specific state, or cached candidate lists —
  every invocation re-fetches and re-derives from scratch.
