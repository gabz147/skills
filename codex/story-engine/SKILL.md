---
name: story-engine
description: "[Ported from Claude personal skill] Write Wattpad-style serialized fiction - addictive chapters, strong hooks, cliffhangers, and emotional character voice. Use when the user wants to write or plan a story, novel, fanfic, romance, or serialized web fiction; outline chapters; develop characters; draft or revise fiction prose; or asks for \"Wattpad-style\" writing."
---

# Story Engine

## Codex Compatibility

This skill was ported from a Claude skill. Interpret Claude Code-specific wording using Codex equivalents:

- Use `functions.shell_command` for shell commands and filesystem inspection.
- Use `apply_patch` for manual file edits.
- Use `update_plan` for task checklists when a plan is useful.
- Use `web.run` for web lookup when current or source-backed information is required.
- Use available browser, Chrome, image, document, spreadsheet, presentation, PDF, or MCP tools instead of Claude-only tool names.
- Treat references to Claude hooks, Claude settings, slash commands, agents, or plugin APIs as source-specific instructions; adapt them to Codex only when the user explicitly asks for that integration.


Wattpad-style serialized fiction: emotionally addictive, character-driven, fast-moving, written for mobile readers who decide in one paragraph whether to keep tapping **next**.

## The loop

Never freewrite a whole book blind. Work in this order; loop the last two steps per chapter.

1. **Premise** - lock the GMCS spine: **G**oal, **M**otivation, **C**onflict, **S**takes (one sentence each). Pick the genre + 1-3 tropes and a fresh angle on them.
2. **Story bible** - before chapter 1, create/extend `story-bible.md` (characters, relationships, world, continuity). See [STORY-BIBLE.md](STORY-BIBLE.md). Reread it before every chapter.
3. **Outline** - beat out the arc, then outline the *next* chapter as a mini-arc: something happens  to  something changes  to  it ends on a question. See [STRUCTURE.md](STRUCTURE.md).
4. **Draft** the chapter using the rules below + [CRAFT.md](CRAFT.md).
5. **Revise** with the checklist - every chapter gets one pass before it's "done".

## Non-negotiables

- **Hook in the first lines.** Open on the moment of change, not backstory or someone waking up. Chapter 1 lands a high-tension / high-emotion beat fast; the inciting incident hits inside the first 10-15%.
- **Chapters 1,000-2,000 words.** Mobile-sized. One scene, one turn.
- **End every chapter on a question.** Cut just before the consequences resolve - ride the momentum into the next part. Tie the cliffhanger to the character's goal or the main conflict.
- **Short sentences, short paragraphs.** Use white space. Vary rhythm - clipped for tension, longer for breath. Lean dialogue-forward.
- **Voice over polish.** Specific, flawed, emotionally legible characters (wants, fears, small habits). Never sound like a dictionary or a quote board.
- **Show, don't tell.** Let the prose imply feelings and relationships; don't state them.
- **Pace the scene to its energy.** Fast when they're running; slow at the romantic dinner. Don't summarize days - dramatize them as scenes.

## Anti-AI-slop

Fiction dies on autopilot phrasing. Ban these on sight: *"little did they know", "in that moment", "a testament to", "couldn't help but", "sent shivers down her spine", "barely above a whisper", "the air was thick with", "a mix of X and Y", "she let out a breath she didn't know she was holding".* Cut filtering verbs (*felt / saw / heard / realized*) - write the sensation itself. Never name an emotion you can stage. Full list + fixes in [CRAFT.md](CRAFT.md#anti-ai-slop).

## Revision checklist (run per chapter)

- [ ] First 2 lines hook? Opens on change, not setup?
- [ ] Scene pace matches its energy? No skipped/summarized days?
- [ ] Dialogue fits the situation and each character's distinct voice?
- [ ] Feelings/relationships shown, not told?
- [ ] The POV character wants something this chapter and moves toward/away from it?
- [ ] Ends on an unresolved beat tied to goal or conflict?
- [ ] No AI-slop phrases; no filtering verbs; varied sentence rhythm?
- [ ] Continuity matches the story bible? (Then update the bible.)

## Genre & tropes

Lean into the genre's beloved tropes, then twist one. Trope menus by genre + arc templates are in [STRUCTURE.md](STRUCTURE.md).

Built from craft patterns in open-source LLM fiction tools and Wattpad Creators craft guides - see [SOURCES.md](SOURCES.md).
