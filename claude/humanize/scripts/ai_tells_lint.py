#!/usr/bin/env python3
"""
ai_tells_lint.py — flag statistical "tells" that make writing read as AI-generated.

Pure stdlib. No network, no deps. Reads a file argument or stdin.

Usage:
    python3 ai_tells_lint.py draft.md
    cat draft.md | python3 ai_tells_lint.py
    python3 ai_tells_lint.py draft.md --json

It does NOT rewrite anything. It produces an objective report (and a 0-100
"AI-tell score") so the editor can target the worst offenders and re-run after
rewriting to confirm the tells are gone. Word/phrase lists are kept in sync with
references/ai-tells.md but embedded here so the script runs standalone.
"""

import sys
import re
import json
from collections import Counter

# --- Lists (high-signal subset of references/ai-tells.md) -------------------

TIER1 = [
    "delve", "delves", "delving", "tapestry", "landscape", "pivotal",
    "underscore", "underscores", "underscoring", "testament", "intricate",
    "intricacies", "meticulous", "meticulously", "nuanced", "multifaceted",
    "embark", "spearhead", "spearheading", "bolster", "bolstered", "garner",
    "garnered", "interplay", "realm", "labyrinth", "symphony", "paramount",
    "unprecedented", "aforementioned",
]

TIER2 = [
    "crucial", "vibrant", "foster", "fostering", "enhance", "enhancing",
    "leverage", "leveraging", "navigate", "navigating", "resonate",
    "resonates", "illuminate", "showcase", "showcasing", "enduring",
    "robust", "holistic", "comprehensive", "innovative", "dynamic",
    "seamless", "seamlessly", "cutting-edge", "game-changer", "game-changing",
    "transformative", "groundbreaking", "utilize", "utilizes", "facilitate",
    "encompass", "harness", "harnessing", "remarkable", "profound",
    "elevate", "empower", "empowering", "streamline", "supercharge",
]

# Multi-word phrases / openers — matched as substrings on lowercased text.
PHRASES = [
    "it's worth noting", "it is worth noting", "it's important to note",
    "it is important to note", "let's dive in", "let's dive into",
    "let's unpack", "let's break this down", "dive deeper", "at its core",
    "in the realm of", "when it comes to", "a testament to",
    "this is where", "at the end of the day", "the bottom line is",
    "here's the thing", "here's the deal", "without further ado",
    "in a nutshell", "buckle up", "take it to the next level",
    "unlock the power", "bridge the gap", "move the needle",
    "in today's", "in conclusion", "in summary", "rest assured",
    "needle in a haystack", "navigate the complexities", "ever-evolving",
    "ever-changing", "fast-paced world", "in the world of",
    "i hope this helps", "i hope this email finds you well",
    "please don't hesitate", "as per my last", "circle back", "touch base",
    "thought leader", "thought leadership", "value proposition",
    "moving forward", "that being said", "needless to say",
    "it goes without saying", "look no further",
]

# Sentence/paragraph openers (checked at sentence start).
OPENERS = [
    "certainly", "absolutely", "indeed", "moreover", "furthermore",
    "additionally", "notably", "importantly", "interestingly",
    "consequently", "nevertheless", "nonetheless", "subsequently", "overall",
    "great question", "that's a great", "in essence",
]

# --- Helpers ----------------------------------------------------------------


def split_sentences(text):
    # naive but good enough: split on . ! ? followed by space/newline/eol
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p.strip() for p in parts if p.strip()]


def word_count(text):
    return len(re.findall(r"\b[\w'-]+\b", text))


def line_of(text, idx):
    return text.count("\n", 0, idx) + 1


def find_words(text_lower, raw, words):
    """Return Counter of word -> count and dict word -> first line."""
    counts = Counter()
    first_line = {}
    for w in words:
        # build a word-boundary pattern; allow hyphenated words
        pat = re.compile(r"(?<![\w'-])" + re.escape(w) + r"(?![\w'-])")
        for m in pat.finditer(text_lower):
            counts[w] += 1
            if w not in first_line:
                first_line[w] = line_of(raw, m.start())
    return counts, first_line


def find_phrases(text_lower, raw, phrases):
    counts = Counter()
    first_line = {}
    for p in phrases:
        start = 0
        while True:
            i = text_lower.find(p, start)
            if i == -1:
                break
            counts[p] += 1
            if p not in first_line:
                first_line[p] = line_of(raw, i)
            start = i + len(p)
    return counts, first_line


def find_openers(sentences, raw, openers):
    counts = Counter()
    for s in sentences:
        low = s.lower().lstrip("\"'*->#• \t")
        for o in openers:
            if low.startswith(o):
                counts[o] += 1
                break
    return counts


def stdev(nums):
    if len(nums) < 2:
        return 0.0
    mean = sum(nums) / len(nums)
    var = sum((n - mean) ** 2 for n in nums) / (len(nums) - 1)
    return var ** 0.5


# --- Analysis ---------------------------------------------------------------


def analyze(raw):
    low = raw.lower()
    wc = max(1, word_count(raw))
    sentences = split_sentences(raw)
    slens = [word_count(s) for s in sentences] or [0]

    t1, t1_line = find_words(low, raw, TIER1)
    t2, t2_line = find_words(low, raw, TIER2)
    ph, ph_line = find_phrases(low, raw, PHRASES)
    op = find_openers(sentences, raw, OPENERS)

    em_dashes = raw.count("—") + raw.count(" -- ")
    em_per_1k = em_dashes / wc * 1000

    # "Not X, but Y" rhetorical negation
    neg = re.findall(
        r"\bnot (?:just |only |merely |simply )?[^,.;!?]{2,60}?,?\s+but\b",
        low,
    )
    neg += re.findall(
        r"\b(?:isn't|aren't|wasn't|weren't|isn’t|aren’t)\b[^.;!?]{2,60}?\bit'?’?s\b",
        low,
    )

    # tricolon: "X, Y, and/or Z"
    tricolon = re.findall(r"\b[\w'-]+,\s+[\w'-]+,\s+(?:and|or)\s+[\w'-]+", low)

    # rhetorical question immediately answered by a short sentence
    rhet = 0
    for i, s in enumerate(sentences[:-1]):
        if s.endswith("?") and word_count(sentences[i + 1]) <= 12:
            rhet += 1

    mean_len = sum(slens) / len(slens)
    sd = stdev(slens)
    pct_short = sum(1 for n in slens if n <= 7) / len(slens) * 100
    pct_long = sum(1 for n in slens if n >= 30) / len(slens) * 100

    # --- score (penalty points, capped at 100) ---
    score = 0
    score += sum(t1.values()) * 6
    score += sum(t2.values()) * 3
    score += sum(ph.values()) * 5
    score += sum(op.values()) * 4
    if em_per_1k > 2:
        score += min(20, (em_per_1k - 2) * 4)
    if len(slens) >= 4:
        if sd < 4:
            score += 16
        elif sd < 7:
            score += 8
    score += len(neg) * 5
    score += len(tricolon) * 3
    score += rhet * 4
    score = int(min(100, round(score)))

    return {
        "words": wc,
        "sentences": len(sentences),
        "score": score,
        "verdict": verdict(score),
        "tier1": t1, "tier1_line": t1_line,
        "tier2": t2, "tier2_line": t2_line,
        "phrases": ph, "phrases_line": ph_line,
        "openers": op,
        "em_dashes": em_dashes, "em_per_1k": round(em_per_1k, 1),
        "negation": len(neg), "tricolon": len(tricolon), "rhetorical_qa": rhet,
        "sentence_mean": round(mean_len, 1), "sentence_stdev": round(sd, 1),
        "pct_short": round(pct_short), "pct_long": round(pct_long),
    }


def verdict(score):
    if score <= 10:
        return "reads human"
    if score <= 30:
        return "mostly human, a few tells"
    if score <= 60:
        return "noticeably AI"
    return "strongly AI"


# --- Reporting --------------------------------------------------------------


def fmt_counter(c, lines=None, limit=20):
    items = c.most_common(limit)
    out = []
    for w, n in items:
        tag = f" (×{n})" if n > 1 else ""
        loc = f" [line {lines[w]}]" if lines and w in lines else ""
        out.append(f"    {w}{tag}{loc}")
    return "\n".join(out)


def report(r):
    L = []
    bar = "=" * 56
    L.append(bar)
    L.append(f"  AI-TELL SCORE: {r['score']}/100  —  {r['verdict']}")
    L.append(f"  {r['words']} words, {r['sentences']} sentences")
    L.append(bar)

    if r["tier1"]:
        L.append(f"\n■ Tier-1 words (strong tells) — {sum(r['tier1'].values())}:")
        L.append(fmt_counter(r["tier1"], r["tier1_line"]))
    if r["tier2"]:
        L.append(f"\n■ Tier-2 words (overused) — {sum(r['tier2'].values())}:")
        L.append(fmt_counter(r["tier2"], r["tier2_line"]))
    if r["phrases"]:
        L.append(f"\n■ Banned phrases — {sum(r['phrases'].values())}:")
        L.append(fmt_counter(r["phrases"], r["phrases_line"]))
    if r["openers"]:
        L.append(f"\n■ Formulaic sentence openers — {sum(r['openers'].values())}:")
        L.append(fmt_counter(r["openers"]))

    L.append("\n■ Structure:")
    L.append(f"    em dashes: {r['em_dashes']} ({r['em_per_1k']}/1k words"
             + ("  ⚠ high" if r["em_per_1k"] > 2 else "  ok") + ")")
    L.append(f"    'Not X, but Y' negations: {r['negation']}"
             + ("  ⚠" if r["negation"] else ""))
    L.append(f"    tricolons (X, Y, and Z): {r['tricolon']}"
             + ("  ⚠" if r["tricolon"] > 1 else ""))
    L.append(f"    rhetorical question + answer: {r['rhetorical_qa']}"
             + ("  ⚠" if r["rhetorical_qa"] else ""))

    L.append("\n■ Rhythm:")
    flag = "  ⚠ too uniform" if r["sentence_stdev"] < 7 and r["sentences"] >= 4 else "  ok"
    L.append(f"    sentence length: mean {r['sentence_mean']}, "
             f"stdev {r['sentence_stdev']}{flag}")
    L.append(f"    short (<=7w): {r['pct_short']}%   long (>=30w): {r['pct_long']}%")
    if r["sentence_stdev"] < 7 and r["sentences"] >= 4:
        L.append("    → vary sentence length: follow a long sentence with a short one.")

    if r["score"] == 0:
        L.append("\nNo tells detected. Reads human.")
    L.append("")
    return "\n".join(L)


def main():
    args = [a for a in sys.argv[1:] if a != "--json"]
    as_json = "--json" in sys.argv
    if args:
        with open(args[0], "r", encoding="utf-8") as f:
            raw = f.read()
    else:
        raw = sys.stdin.read()
    if not raw.strip():
        print("No input text.", file=sys.stderr)
        sys.exit(1)
    r = analyze(raw)
    if as_json:
        serial = {k: (dict(v) if isinstance(v, Counter) else v) for k, v in r.items()}
        print(json.dumps(serial, indent=2))
    else:
        print(report(r))


if __name__ == "__main__":
    main()
