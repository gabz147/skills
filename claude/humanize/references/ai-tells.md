# AI Writing Tells — Reference Dictionary

The full playbook of patterns that make text read as machine-generated. Use it as
a checklist when auditing or rewriting. Synthesized from Wikipedia's *Signs of AI
Writing*, the Carnegie Mellon (2025) and Reuters Institute studies, the
`berenslab/llm-excess-vocab` corpus (≈900 annotated excess words), GPTZero's
vocabulary research, and editing-community lore. Structure is a stronger tell than
vocabulary — fix Section 2 before Section 1.

---

## 1. Vocabulary

Replace the word, or better, restructure so the fancy word isn't needed at all.
Don't swap one cliché for another (see "secondary convergence" in §2).

### Tier 1 — strongest signals (humans almost never reach for these)
| AI word | Human alternative |
|---|---|
| delve / delve into | dig into, look at, get into |
| tapestry | mix, blend, web |
| landscape (figurative) | space, world, field, scene |
| pivotal | important, key, big |
| underscore | show, point to, highlight |
| testament (a testament to) | proof of, shows |
| intricate / intricacies | complicated, detailed, the details of |
| meticulous / meticulously | careful, carefully, thorough |
| nuanced | subtle, has shades to it |
| multifaceted | many-sided, complex |
| embark (on a journey) | start, begin |
| spearhead | lead, drive, run |
| bolster | support, strengthen, back up |
| garner | get, earn, attract, pick up |
| interplay | interaction, how they affect each other |
| realm | area, space, world |
| labyrinth / labyrinthine | maze, tangle, mess |
| symphony (figurative) | mix, blend |
| paramount | most important, top priority |
| unprecedented | new, never happened before, first |
| aforementioned | the / that / earlier |

### Tier 2 — overused (humans use them; AI leans on them constantly)
| AI word | Human alternative |
|---|---|
| crucial | important, key |
| vibrant | lively, busy, colorful |
| foster | encourage, build, grow |
| enhance | improve, boost, sharpen |
| leverage (verb) | use, take advantage of |
| navigate (figurative) | deal with, handle, work through |
| resonate | connect, land, hit home |
| illuminate | clarify, show, explain |
| showcase | show, display, put on show |
| enduring | lasting, long-term |
| robust (outside engineering) | strong, solid, reliable |
| holistic | whole, full-picture |
| comprehensive (of your own output) | full, complete, thorough |
| innovative | new, fresh, creative |
| dynamic | active, changing, fast-moving |
| seamless / seamlessly | smooth, easy, without friction |
| cutting-edge | latest, newest |
| game-changer / game-changing | big deal, breakthrough |
| transformative | big, far-reaching |
| utilize | use |
| facilitate | help, make easier, run |
| harness | use, tap, put to work |
| elevate | raise, lift, improve |
| empower | give the tools to, let, enable |
| streamline | simplify, tighten, speed up |
| remarkable / profound / stunning | (usually just cut — let the fact stand) |

### Tier 3 — transitions (fine once; AI clusters them)
More than ~2 formal transitions in a short section is itself a tell. Replace clusters
with plain connectors, or delete — good writing often needs no explicit transition.

| AI transition | Human alternative |
|---|---|
| Furthermore / Moreover / Additionally | Also, And, Plus, On top of that |
| Consequently / Hence / Thus | So, Because of that |
| Nevertheless / Nonetheless | Still, But, Even so |
| Subsequently | Then, After that, Later |
| Notably / Importantly / Interestingly | (usually delete) |
| Indeed | (usually delete) |
| In conclusion / In summary | (just conclude — don't announce it) |
| It's worth noting that / It's important to note that | (delete; state the thing) |

---

## 2. Structural patterns (the strong tells)

**Parallel negation — "Not X, but Y."** Appears 5–10× more in AI text. Say what
happened.
*Bad:* "Not because I lacked skill, but because the context changed."
*Good:* "The context changed, so I adapted."

**Tricolon — the rule of three.** Three adjectives / nouns / phrases to sound
complete. Humans rarely do this outside speeches. Keep the one or two that matter.
*Bad:* "collaboration, innovation, and problem-solving"
*Good:* "figuring things out together"

**Em-dash overuse — the "ChatGPT dash."** AI uses em dashes where a comma, period,
or parentheses belongs. Cap at ~1 per 500 words, only for real emphasis.

**Rhetorical question + immediate answer.** A transition device AI overuses. Lead
with the answer.
*Bad:* "What does this mean in practice? It means teams need autonomy."
*Good:* "Teams need autonomy."

**Mirror structure.** Consecutive sentences with identical shape. Break the symmetry
— let the second thought take a different length and angle.
*Bad:* "Engineers want clarity. Managers want context."
*Good:* "Engineers want clarity. Managers want something fuzzier — the context around
the decision you can't see from outside."

**Colon / dash reveals.** "The result: a disaster." "The outcome? Four agreed."
Weave it into a normal sentence.

**Dramatic setups.** "Here's the thing:", "Here's what nobody tells you:", "Let's
dive in", "Let's unpack this", "Buckle up." Drop the drumroll; start with the point.

**Inflation of importance.** "a pivotal moment," "a testament to," "cannot be
overstated." AI editorializes about significance instead of stating facts. Cut the
sentence; if it matters, the content shows it.

**Neat endings on every paragraph.** AI wraps each thought in a bow. Let ~30% of
paragraphs just stop. Let some ideas hang.

**Secondary convergence (the trap).** When you kill one pattern, don't replace it
with a new crutch. Drop "Furthermore" and don't make every transition "That said" or
"The thing is." Vary it — sometimes no transition at all.

---

## 3. Tone & voice tells
- **Too balanced.** Equal weight to every side. Humans have opinions and lean in.
- **Too polished.** No fragments, no false starts, no sentence opening with "And" or
  "But." Uniform perfection reads as machine.
- **Sycophancy.** "Great question!", "Absolutely!", "What a fantastic approach!"
  Humans are more measured, sometimes blunt.
- **Hedging.** "Generally speaking," "to some extent," "it could be argued that."
  Just say what you think.
- **No personal voice.** Missing the humor, irritation, tangents, and specific
  quirks of a real writer.

## 4. Content red flags
- **Generic conclusions** that fit anything: "Ultimately, it's about finding the
  right balance."
- **No concrete detail.** Plausible but unspecific. Real writing has names, dates,
  numbers, places, "you had to be there" detail.
- **Regression to the mean.** "We lost $40k on that campaign" becomes "the initiative
  faced financial challenges." Restore the specifics.

## 5. Punctuation & formatting tells
- **Curly quotes / apostrophes** (’ “ ”) from markdown conversion — humans typing in
  most editors get straight ones.
- **Title Case Headings** instead of sentence case.
- **Bold sprayed on every key term**; emoji bullet points; hashtag stacks.
- **Markdown leaking into plain text** (`**bold**`, `#`, backticks where none belong).
- **Perfectly uniform list items** all the same length and grammatical shape.

## 6. Model-specific first-word tells
LLMs disproportionately open with these — avoid starting on them.
- ChatGPT: *as, yes, sure, here, certainly, title, the, creating*
- Claude: *in, from, this, how, based, here, according, the*
- Gemini: *my, creating, while, here, yes, this*
- DeepSeek: *based, yes, step, comprehensive, here, certainly*
- Grok: *step, introduction, yes, creating, certainly*

## 7. Vocabulary by era (context, not a whitelist)
- **2023–mid 2024 (GPT-4):** delve, tapestry, intricate, meticulous, pivotal,
  underscore, testament, vibrant, interplay, landscape, bolster, garner.
- **Mid 2024–mid 2025 (GPT-4o):** align with, foster, enhance, highlight, showcase,
  underscore, pivotal, vibrant.
- **Mid 2025 on (GPT-5):** emphasizing, enhance, highlighting, showcasing.
The exact words drift; the *behaviors* in §2–§4 are the durable tells.

---

### Sources
- Wikipedia: *Signs of AI Writing* — en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing
- berenslab/llm-excess-vocab (≈900 annotated excess words)
- Reuters Institute: "How AI-generated prose diverges from human writing"
- GPTZero AI-vocabulary research; lguz/humanize-writing-skill; jalaalrd/anti-ai-slop-writing
