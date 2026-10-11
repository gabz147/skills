---
name: humanize
description: >
  Rewrite or audit text so it reads like a real person wrote it, not an LLM. Use
  when the user says writing "sounds like AI / ChatGPT," asks to humanize, de-slop,
  or make a draft sound natural, asks "does this sound AI?", or wants a blog post,
  LinkedIn post, email, essay, or marketing copy to feel authentic. Strips AI tells
  (delve, tapestry, "not X but Y", em-dash overuse, tricolons, robotic rhythm) and
  restores a human voice. Includes a linter to score text before and after.
---

# Humanize

Make text sound like a smart person thinking out loud, not a language model
performing. Good writing varies its rhythm, takes a position, uses concrete detail,
and lets some thoughts hang. AI writing is uniformly polished, hedged, and padded
with importance. Your job is to find the tells and replace them with what a person
would actually write.

`references/ai-tells.md` is the full playbook (banned words by tier, structural
patterns, tone tells). Skim it before any non-trivial rewrite.

## Two modes

**Audit** — user asks "does this sound AI?" / "score this." Run the linter, read the
report back, name the top 3 offenders, give a verdict. Don't rewrite unless asked.

**Rewrite** — user wants it fixed. Run the linter to find targets, do the three
passes below, run the linter again to confirm the score dropped, return the text.

## The linter (objective check)

```bash
python3 scripts/ai_tells_lint.py path/to/draft.md        # or:
pbpaste | python3 scripts/ai_tells_lint.py               # text via stdin
python3 scripts/ai_tells_lint.py draft.md --json         # machine-readable
```

It reports an **AI-tell score (0–100)**, the banned words/phrases found (with line
numbers), em-dash density, "Not X but Y" and tricolon counts, and sentence-length
variance. It never edits — it only measures. Use it to target work and to prove the
rewrite worked (the score should drop into the 0–15 "reads human" band). It catches
vocabulary and gross structure; *you* still judge voice, specificity, and rhythm,
which no linter can score.

## Pick a voice first (rewrite mode)

1. **User named a voice or tone?** Use it ("punchy," "keep it professional").
2. **User pasted a writing sample?** Mirror it — match their rhythm, vocabulary, and
   quirks. Don't describe the profile, just write in it.
3. **Neither?** Ask once, quickly: clear-thinker / casual-storyteller /
   sharp-opinionated / warm-professional / mirror-my-sample. If they're impatient or
   say "just make it human," default to **clear-thinker** and go.

## Three passes (don't do them at once)

**Pass 1 — kill the vocabulary.** Replace every Tier-1/Tier-2 word with the plain
alternative from the dictionary. Often the real fix is restructuring the sentence so
the fancy word was never needed. Collapse transition clusters (max ~2 formal
transitions in the whole piece).

**Pass 2 — break the structures (matters more than words).** Hunt and destroy:
parallel negation ("not X, but Y"), tricolons (groups of three), em-dash overuse,
rhetorical-question-then-answer, mirror sentences, colon/dash reveals, dramatic
setups ("Here's the thing:"), and inflation of importance. See §2 of the reference.
Watch for *secondary convergence* — don't trade one cliché for another.

**Pass 3 — add human texture.** Vary sentence length hard (long, then short, then a
fragment). Make less predictable, concrete word choices ("we burned $40k" beats "the
initiative faced challenges"). Start a sentence or two with "And" or "But." Let the
author's actual opinion show — cut the hedging. Leave ~30% of paragraphs without a
tidy bow. Allow mild imperfection; robotic perfection is the tell.

## LinkedIn / social (extra rules)
Lead with the hook, not setup. Short sentences (avg <20 words), generous line breaks.
No "thought leadership" framing or "key takeaway." End on something real and
unresolved, not a neat lesson.

## Quality checklist (run before returning)
- [ ] Linter score dropped to the "reads human" band (≤15); re-run to confirm
- [ ] Zero Tier-1 words; Tier-2 words at most once each, only where natural
- [ ] No "Not X, but Y", no tricolons, ≤1 em dash per 500 words
- [ ] No rhetorical-Q+answer, no mirror sentences, no dramatic setups
- [ ] Sentence length visibly varies; at least one "And"/"But" opener
- [ ] The author's opinion is visible; hedging removed
- [ ] ≥30% of paragraphs don't end on a tidy conclusion
- [ ] Concrete details (names, numbers) replace generic ones where possible

## What to protect
Keep the meaning and facts intact — you're editing voice, not substance. Keep the
intelligence high; "human" is not "dumbed down." Don't over-correct into a different
fakeness ("Fellow humans, am I right?") — the goal is invisible editing. Don't add
emojis or hashtags unless asked. Return just the rewritten text; explain changes only
if asked.
