---
name: mercura
description: "[Ported from Claude personal skill] Work on the Mercura V2 project - \"Mercura - Aurelia's Academy\", a React/JSX single-page app located at C:\\Users\\Tarlu\\Desktop\\model\\Mercura V2. Use when the user types /mercura, says \"open mercura\", \"mercura v2\", or otherwise references this project. Triggers should treat the project root as that folder."
---

# Mercura V2 - Aurelia's Academy

## Codex Compatibility

This skill was ported from a Claude skill. Interpret Claude Code-specific wording using Codex equivalents:

- Use `functions.shell_command` for shell commands and filesystem inspection.
- Use `apply_patch` for manual file edits.
- Use `update_plan` for task checklists when a plan is useful.
- Use `web.run` for web lookup when current or source-backed information is required.
- Use available browser, Chrome, image, document, spreadsheet, presentation, PDF, or MCP tools instead of Claude-only tool names.
- Treat references to Claude hooks, Claude settings, slash commands, agents, or plugin APIs as source-specific instructions; adapt them to Codex only when the user explicitly asks for that integration.


A React/JSX single-page application. The user's working project for this product.

## Project location

Absolute path (Windows): `C:\Users\Tarlu\Desktop\model\Mercura V2`
Bash-style path: `C:/Users/Tarlu/Desktop/model/Mercura V2`

Sibling assets (sprites, logos, reference imagery, the personality doc) live one level up at `C:\Users\Tarlu\Desktop\model`.

## Structure

```
Mercura V2/
??? index.html              # entry - Tailwind CDN + Google Fonts + Babel inline JSX
??? index.bundle-src.html   # bundled variant
??? app.jsx                 # root React app
??? assets/
??? components/
?   ??? AICompanion.jsx
?   ??? PageTitle.jsx
?   ??? SectionLabel.jsx
?   ??? Sidebar.jsx
??? data/
?   ??? mock.js
??? layouts/
??? pages/
    ??? Concepts.jsx
    ??? Dashboard.jsx
    ??? Progress.jsx
    ??? Review.jsx
    ??? Settings.jsx
    ??? Study.jsx
```

## Stack notes

- React + inline JSX via Babel in the browser (no build step in `index.html`)
- Tailwind via CDN
- EB Garamond + Inter from Google Fonts
- Custom CSS variables in `oklch()` - vellum/ink/gold palette, scholarly aesthetic
- Background `<video>` element behind the whole app (`.mercura-bg-video`)

## Aesthetic

Scholarly / academy feel - vellum cream backgrounds, gold accents, EB Garamond serif. This is distinct from the dark "iridescent glass" Mercura aesthetic (see the iridescent-glass skill); do not conflate them.

Aurelia is the project's character/companion, rendered by `components/AICompanion.jsx`. She sits **fixed in the bottom-right** of the viewport across all pages - preserve that placement when editing layout/companion code. (The user briefly asked for bottom-left then reverted - keep her on the right unless told otherwise.) Important sprite rule from user memory: **all Aurelia character sprites must share identical pixel dimensions; pad new ones to the smallest existing canvas.**

## Pages

| Route | File | Notes |
|-------|------|-------|
| `#dashboard` | `pages/Dashboard.jsx` | Weak areas, recent activity, start session |
| `#study` | `pages/Study.jsx` | Adaptive flashcard session |
| `#concepts` | `pages/Concepts.jsx` | Concept browser |
| `#progress` | `pages/Progress.jsx` | Stats |
| `#review` | `pages/Review.jsx` | Spaced-repetition queue |
| `#generate` | `pages/Generate.jsx` | Grok image generation (grok-imagine-image / -pro) with reference upload (drag, paste, click), Aurelia vision reaction |
| `#settings` | `pages/Settings.jsx` | API key, chat/image/vision model selectors, system prompt editor |

## Aurelia - key wiring

- `components/AICompanion.jsx` - fixed bottom-right across all pages via `layouts/Layout.jsx`
- `window.aureliaThink(text, ms?)` - shows a thought bubble above Aurelia for `ms` ms (default 6 s)
- `window.aureliaSetExpression(emotion)` - swaps her sprite; valid keys: `happy angry mad annoyed bored curious crying shy panicked surprised lovestruck peaceful laughing playful joyful` (plus aliases `idle sad thinking stern`)
- `window.aureliaOpen()` - programmatically opens her chat panel
- Emotion sprites live at `assets/companion-<emotion>.png` (15 PNGs, background-removed)
- Personality / system prompt: `window.AURELIA_DEFAULT_PROMPT` (set in `app.jsx`, sourced from `C:\Users\Tarlu\Desktop\model\AURELIA - PERSONALITY.docx`)
- Settings persisted to `localStorage` under key `mercura.settings.v1` (`grokApiKey`, `model`, `imageModel`, `visionModel`, `systemPrompt`)
- Chat image generation: Aurelia detects `[generate:<prompt>]` tag in LLM reply, fires `grok-imagine-image`, renders image inline in the chat panel as a non-blocking async op

## xAI / Grok models available on this account

Chat: `grok-4-fast-non-reasoning` (default), `grok-4-fast-reasoning`, `grok-4-1-fast-non-reasoning`, `grok-4-1-fast-reasoning`, `grok-4-0709`, `grok-3`, `grok-3-mini`, `grok-code-fast-1`
Image: `grok-imagine-image` (default), `grok-imagine-image-pro`
Vision: supported natively by all `grok-4*` models - default `grok-4-fast-non-reasoning`
Note: `grok-2-*` and `grok-2-vision-*` are NOT on this team's account.

## Roadmap / ideas (not yet built)

### Proactive behavior
- **Page-aware comments** - detect active route, fire `aureliaThink()` with a context-relevant quip. Already fully scaffolded - just needs a lookup table of route  to  comment and a `hashchange` listener.
- **Idle chime** - after 3-5 min of inactivity, pop a nudge. `setTimeout` reset on every user interaction.
- **Study streak awareness** - congratulate or guilt-trip based on streak counter stored in localStorage.

### Chat enhancements
- **Memory across sessions** - persist last N messages to localStorage so Aurelia remembers context from the previous session.
- **Concept-aware replies** - when on the Concepts page, pass the selected concept name into the system prompt so she gives targeted advice without the user re-explaining.
- **Voice output** - pipe Aurelia's text replies through `window.speechSynthesis`; zero API cost.

### Generate page
- **Image history strip** - horizontal scroll of last 5-10 generated images at the bottom of the Generate page. Delete individually, click to restore.
- **"Surprise me" button** - Aurelia creates her own image prompt based on what the user is studying, sends it to image gen.
- **Image-to-prompt reverse** - upload any image, ask Aurelia to describe it, copy the description as a new prompt.

### Companion interactions
- **Click reactions** - clicking the Aurelia sprite fires a short quip matching her current expression (mad? she tells you to stop poking her).
- **Global drag-and-drop** - drag any image onto any page  to  Aurelia reacts via vision, no need to go to Generate.
- **Expression preview in Settings** - small sprite preview next to the system prompt textarea that updates live.

### Study integration
- **Wrong-answer coach** - on Review, when user answers incorrectly, Aurelia's expression shifts and she offers a one-line mnemonic via API.
- **Session summary** - after a study session ends, Aurelia gives a short Aurelia-flavored debrief: wins, weak spots, one focus for next time.

## Default actions when /mercura is invoked

1. Treat `C:\Users\Tarlu\Desktop\model\Mercura V2` as the working project.
2. The user has a one-click launcher at `Mercura V2\Open Mercura.bat` - double-clicking it starts a local Python HTTP server on port 8765 (in its own cmd window - close that window to stop the server) and opens Chrome at `http://127.0.0.1:8765/index.html`. Running it again while the server is already up just reopens the tab. This is the user's preferred way to open the app.
3. **Opening the app - must be over HTTP, not `file://`.** `index.html` loads JSX via `<script type="text/babel" src="components/*.jsx">` and Babel-standalone fetches those via XHR, which Chrome blocks under `file://` (page renders blank - no sprite, no sidebar, no pages). To open:
   1. Start a local server in the project root (background): `cd "C:/Users/Tarlu/Desktop/model/Mercura V2" && python -m http.server 8765 --bind 127.0.0.1` via Bash with `run_in_background: true`. Port 8765 is the convention for this project. If it's already running, skip.
   2. Navigate the MCP Chrome tab to `http://127.0.0.1:8765/index.html` using `mcp__claude-in-chrome__navigate`. Because this is HTTP (not file://), the MCP tool works and you can also drive the page (clicks, screenshots, console reads) for debugging.
3. For edits, prefer the Edit tool on files inside the project folder. After edits, reload the tab via `mcp__claude-in-chrome__navigate` to the same URL (or have the user hit Ctrl+Shift+R) - the `?v=8` query strings cache-bust some files but a fresh fetch is safer.
4. **Do NOT** open via `start chrome "file:///..."` - that path was tried and produced a broken page; the user noticed the missing sprite/dashboard and called it out.
