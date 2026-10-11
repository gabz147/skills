---
name: human-writing
description: "[Ported from Claude personal skill] ) Rewrites or generates written content (college essays, personal statements, cover letters, emails, reflections, narratives) to sound authentically human, not AI-generated. Use this skill whenever the user wants writing that feels personal, natural, and like a real person wrote it. Trigger on phrases like \"write this like a human,\" \"make it sound less AI,\" \"college essay,\" \"personal statement,\" \"rewrite this naturally,\" \"don't make it sound like ChatGPT,\" or any request for personal/narrative writing where voice and authenticity matter. Even if the user just says \"write me an essay\" or \"help me with this application,\" default to human-voice mode."
---

# Human Writing

## Codex Compatibility

This skill was ported from a Claude skill. Interpret Claude Code-specific wording using Codex equivalents:

- Use `functions.shell_command` for shell commands and filesystem inspection.
- Use `apply_patch` for manual file edits.
- Use `update_plan` for task checklists when a plan is useful.
- Use `web.run` for web lookup when current or source-backed information is required.
- Use available browser, Chrome, image, document, spreadsheet, presentation, PDF, or MCP tools instead of Claude-only tool names.
- Treat references to Claude hooks, Claude settings, slash commands, agents, or plugin APIs as source-specific instructions; adapt them to Codex only when the user explicitly asks for that integration.


The goal is writing that a real person would actually produce, with personality, specific details,
natural rhythm, and imperfection that reads as intentional rather than sloppy. AI writing is
detectable because it's too smooth, too balanced, too predictable. Human writing has texture.

Technically: AI text scores low on "burstiness" (0.2-0.4) vs. humans (0.6-1.2). Humans spike on
unexpected word choices, abrupt sentence length changes, structural breaks. Aim for that spread.

## ABSOLUTE RULE: NO EM DASHES, EVER

Never use em dashes (-) in any output produced under this skill. Not one. Not in the body, not in
parentheticals, not "tastefully." Em dashes are the single clearest tell that text was written by
an AI. The user has explicitly banned them.

This includes the long em dash (-), the en dash (-) used as a sentence break, and any double-hyphen
sequence (--) used the same way. If you catch yourself reaching for one, replace it with:
- A period and a new sentence
- A comma
- A colon
- Parentheses
- The word "is," "and," "but," "so," "because"

Before returning any draft under this skill, scan the text and verify there are zero em dashes. If
you find one, fix it. This is non-negotiable.

## Before You Write

If the user provides existing text, start rewriting. Don't ask for a writing sample first - mirror
the voice already on the page.

If starting from scratch with no voice signal: infer from the conversation. Only ask if the format
is ambiguous (e.g., "write me an essay" with no topic) or if you need a specific personal detail
you couldn't possibly invent. Ask one thing at most.

If the user shares writing samples, use them. A few sentences reveals cadence, vocabulary, and tone.

## What to Avoid (AI Tells)

These patterns immediately signal AI authorship. Avoid them entirely:

**Vocabulary to ban:**
- delve, tapestry, intricate, multifaceted, crucially, notably, it is worth noting
- embark, navigate, realm, beacon, foster, leverage, robust, pivotal, paramount
- transformative, holistic, nuanced, synergy, testament to, journey
- "In today's [fast-paced / ever-changing / interconnected] world"
- "I have always been passionate about"
- "not only...but also"
- "It is important to note that" / "It should be noted that"
- "as someone who" (signals performed identity)
- "genuinely" and "truly" before any emotion or belief (performed sincerity)
- "I really appreciated..." - the adverb is the tell

**Structure to avoid:**
- Opening with a quote (especially an inspirational one)
- The 5-paragraph essay arc where every paragraph telegraphs its purpose
- Transitions like: Furthermore, Moreover, In conclusion, To summarize, In addition
- Balanced "on one hand / on the other hand" framing when the person should just have a view
- Ending with a generic call to action or restatement of the thesis
- Listing everything in groups of three (the AI default cadence)
- Parallel clause structures that repeat the same grammatical shape sentence after sentence
- Three or more consecutive sentences starting with "I"
- Em dashes. See the absolute rule above. Zero em dashes, ever.

**Tone to avoid:**
- Performed emotion ("I was filled with a profound sense of wonder")
- Hedged everything ("it seems to suggest that it might potentially")
- Passive voice as the default: "it was decided," "it can be seen that"
- Claiming universal truths from personal experience ("This taught me that failure is the
  greatest teacher")
- Being too fair, too balanced. Humans have actual opinions.

**Transition replacements:**
When you'd normally reach for "Furthermore" or "Moreover," try:
- Just starting the next sentence (often no transition is needed at all)
- "The thing is..." / "Here's the problem:" / "What I didn't expect:"
- "That said," / "Even so," / "Still,"
- A rhetorical question: "So why does this matter?"

## What to Do Instead

**Sentence rhythm:**
Mix dramatically. Short ones hit. Then a longer one that builds and breathes and carries the
reader somewhere. Then short again. AI writes in one consistent medium-length register. Don't.
The technical measure is burstiness - humans spread wide (0.6-1.2), AI clusters low (0.2-0.4).
Aim to be uncharacteristically varied.

**Specificity over generality:**
Every vague claim should become concrete. Not "I learned a lot" but what exactly. The specific
moment, the specific thing you understood that you didn't before. Not "my professor inspired me"
but which professor, which class, what they said on what day, and why that specific thing landed.
Names, places, times, sensory details. If a sentence could apply to anyone, rewrite it until it
could only apply to this person.

**Show, don't announce:**
Don't name the emotion. Describe the physical or behavioral thing that happened. "I was anxious"
becomes "I rewrote the opening paragraph eleven times." "I was excited" becomes "I texted my mom
immediately, which I almost never do." Let the reader feel it without being told to.

**Have an actual opinion:**
If the person believes something, say it plainly. Not "one could argue that..." Just "I think."
Confidence in perspective is one of the clearest signals of human authorship.

**Natural imperfection:**
A perfectly structured argument with clean transitions reads like a legal brief. Humans sometimes
contradict themselves slightly, start over mid-thought, admit uncertainty, trail off and come back.
You can write a sentence that's a little long and wanders before it lands. That's fine. The goal
is not flawlessness. The goal is that it sounds like a specific person.

**Tense consistency:**
Personal narratives drift. Pick present or past and stick with it unless there's an intentional
contrast. AI-written essays often shift tenses at paragraph breaks - watch for it.

**Contractions:**
Use them. Even in somewhat formal writing, "I don't" reads more natural than "I do not" unless
the emphasis is intentional.

## For College Essays Specifically

Word counts matter. Most prompts are 250-650 words. Stay in that range. A bloated essay signals
AI even before you read it.

The biggest mistakes:
- Writing what you think they want to hear instead of what actually happened
- Picking the "impressive" topic (mission trip, sports injury, immigrant grandparent) instead of
  the weird specific real one
- Explaining what you learned instead of showing the moment it happened
- Starting with action that turns out to be a metaphor ("As I stood on the soccer field...")

What works:
- Start mid-scene or mid-thought, not at the beginning of the story
- One specific moment, not a summary of years
- The reader should be able to picture exactly where you are
- The insight at the end should feel earned, not announced
- Your personality should be visible in every paragraph, not just described in it

When writing a college essay, always ask: "Would this sentence also appear in 10,000 other essays?"
If yes, rewrite it.

## For Emails and Cover Letters

**Emails to professors, bosses, or anyone you need something from:**
- Open with something brief and human ("Hope your semester is wrapping up okay.") before the ask.
  One sentence. Not a paragraph.
- State what you need clearly and early. Don't bury the ask in qualifications.
- "I'm writing to respectfully request..." is the most AI-sounding opener imaginable. Just say
  what you want.
- Don't apologize for emailing. Don't call yourself "a dedicated student" or describe your work
  ethic in the abstract.
- Close short. "Thanks for your time." Done.

**Cover letters:**
- The first sentence decides whether it gets read. Don't start with "I am excited to apply for..."
- Specificity wins: name the exact project, product, or moment that made you want to work there.
  Vague enthusiasm reads as a form letter.
- One page. Shorter is almost always better.
- Don't restate your resume. Tell them something the resume can't: what you actually care about,
  how you think, why this specific role.
- Avoid "I am a detail-oriented team player with a passion for..." - every cover letter ever
  written contains this sentence.

## For Rewrites

When the user gives you existing text to make more human:

1. Read it through once and identify the 3 biggest AI signals
2. Rewrite those sections first. Don't just swap words, restructure the thought.
3. Vary the sentence lengths intentionally
4. Replace every generic claim with a specific one (flag where you need info from the user)
5. Cut anything that could be deleted without losing meaning. AI writing is usually 20-30%
   longer than it needs to be.
6. Final pass: search the draft for em dashes. Remove every single one.

Return the rewrite and briefly note what the main changes were and why. Don't explain every
sentence. Just the 2-3 structural moves you made.

## Tone Calibration

After producing a draft, offer to tune it:
- More casual / more formal
- Shorter / more developed
- Bolder voice / more understated
- More emotional / more matter-of-fact

Don't adjust without being asked, but make clear the dial exists.

## Stop-Slop integration (reference files)

This skill folds in [hardikpandya/stop-slop](https://github.com/hardikpandya/stop-slop) (MIT) as exhaustive lookup tables. The rules above stay primary; the references give you a wider net of specific phrases, structures, and worked examples to scan against.

Three companion files live in `references/`:

- **`references/phrases.md`** - full ban list: throat-clearing openers, emphasis crutches, business jargon, adverbs, meta-commentary, performative emphasis, telling-not-showing, vague declaratives. Treat as a search list when scrubbing a draft.
- **`references/structures.md`** - structural patterns to avoid: binary contrasts, negative listing, dramatic fragmentation, rhetorical setups, false agency (inanimate objects performing human verbs), narrator-from-a-distance voice, passive voice, Wh- sentence starters, broken rhythm patterns.
- **`references/examples.md`** - five before/after rewrites showing the rules applied in combination.

### Core stop-slop rules (load these into the rewrite pass)

In addition to everything above, every draft must satisfy:

1. **Cut filler phrases.** Throat-clearing openers, emphasis crutches, all adverbs. (See `references/phrases.md`.)
2. **Break formulaic structures.** No binary contrasts ("not X. Y."), no negative listings, no rhetorical "what if" setups, no false agency. (See `references/structures.md`.)
3. **Active voice with a human subject.** Every sentence needs a person doing something. No inanimate objects performing human actions ("the complaint becomes a fix," "the data tells us"). Name the actor.
4. **Be specific.** No vague declaratives ("The reasons are structural"). Name the actual thing. No lazy extremes ("every," "always," "never") doing vague work.
5. **Put the reader in the room.** "You" beats "People." Concrete scenes beat disembodied observations.
6. **Vary rhythm.** Mix sentence lengths. Two items beat three. End paragraphs differently. (Re-asserts the burstiness target above.)
7. **Trust readers.** State facts directly. Skip softening, justification, hand-holding, and self-referential meta-asides ("the rest of this essay...").
8. **Cut quotables.** If a sentence sounds like a pull-quote, rewrite it.

### Quick check (run before delivering any draft)

- Any adverbs? Kill them.
- Any passive voice? Find the actor, put them at the front.
- Inanimate thing doing a human verb ("the decision emerges")? Name the person.
- Sentence starts with What/When/Where/Which/Who/Why/How? Restructure.
- Any "here's what/this/that" throat-clearing? Cut to the point.
- Any "not X, it's Y" contrast? State Y directly.
- Three consecutive sentences match length? Break one.
- Paragraph ends with a punchy one-liner? Vary it.
- **Em-dash anywhere? Remove it.** (Reinforces the absolute rule at the top of this file.)
- Vague declarative ("The implications are significant")? Name the specific implication.
- Narrator-from-a-distance ("Nobody designed this")? Put the reader in the scene.
- Meta-joiner ("The rest of this essay...")? Delete.

### Scoring rubric (use when the user asks "is this human enough?")

Rate the draft 1-10 on each:

| Dimension | Question |
|-----------|----------|
| Directness | Statements or announcements? |
| Rhythm | Varied or metronomic? |
| Trust | Respects reader intelligence? |
| Authenticity | Sounds like a specific person? |
| Density | Anything cuttable? |

**Below 35/50: revise before returning.**
