---
name: guidance-audit
description: Find out which lines of a system prompt, CLAUDE.md, AGENTS.md or SKILL.md are actually doing anything, by running the task once without them and measuring what the model does anyway. Use when someone says their prompt or skill is too long, asks what they can safely cut, is reviewing added guidance in a PR, is investigating an agent that got slower or more expensive, or asks whether generic best-practice instructions are worth keeping. Not for choosing prompting techniques to raise accuracy on a fixed task — that is a different question.
---

# Every generic line is a work order

A frontier model knows what semantic HTML is. That does not mean it writes it.
Measured across 48 generated files, a `prefers-reduced-motion` query appeared in
**0 of 12** files without the instruction and **12 of 12** with it. `rem` units
rose fivefold by density. Meanwhile `const`/`let` and `addEventListener` were
already there without being asked, and requests for comments and `try`/`catch`
were ignored whether asked or not.

So a generic line is in one of three states, and **you cannot tell which by
reading it**:

| state | what it means | what to do |
|---|---|---|
| already-followed | model does it at the same rate anyway | **delete** — dead weight |
| ignored | model doesn't do it either way | **delete** — dead weight |
| amplified / only-when-asked | your line is why you get it | **keep if you want that** |

The third state is a feature you are buying. Cutting it to shorten a prompt
silently removes the feature — this is how teams lose their accessibility.
**Shorter is not the goal. Knowing is the goal.**

## When this applies

Generation tasks you can actually run — code, documents, structured output. You
need to be able to execute the task and save the output. If you cannot run it,
skip to *If you cannot measure* below.

## Procedure

**Step 1 — Classify, free.**

```
python3 scripts/audit.py classify <your-prompt-file>
```

Splits directives into *guidance* (recognised generic directives, auditable),
*restraint* (asks the model to do less — no detectable cost, leave them), and
*review* (unrecognised — may be project requirements the model cannot infer).
**Never delete a `review` line on this tool's say-so.** It has no signal on them.

**Step 2 — Produce the off-arm.** Run your real task 3 times with the generic
guidance **removed**, keeping every project-specific requirement. Save the
outputs. For a single-file generation task this is roughly $0.15 and a few
minutes; for a long agentic loop, more.

**Step 3 — Report.**

```
python3 scripts/audit.py report <prompt-file> --off 'out/off_*.html'
```

Add `--on 'out/on_*.html'` (3 runs with the guidance in place) to separate
*already-followed* from *amplified*. Without an on-arm you get candidates, not
verdicts — a line can look present-without-it and still be multiplying the
result fivefold.

**Step 4 — Decide, per line.** Delete everything in *already-followed* and
*ignored*. For each *amplified* or *only-when-asked* line, ask a product
question: **do we want this feature?** Keep it if yes. That decision is not the
tool's to make and not the prompt's — it is yours.

**Step 5 — Verify.** Re-run your own tests on the trimmed prompt. This tool
measures whether a directive was *followed*. It says nothing about whether your
output is *correct*.

## What the numbers mean

Counts are compared per 10KB, because a longer output contains more of
everything. A raw count that doubles while the file grows 76% has barely moved.
The tool differences two arms with the same crude regex, so the regex need not
be perfect — any bias applies to both arms and cancels.

## If you cannot measure

Bucket by hand using the priors in `references/signatures.json`, and say plainly
that you are guessing. Bias toward keeping. A wrong deletion is silent and
permanent; a wrong retention costs tokens.

## What this does not tell you

- Whether your output is correct. Run your own tests.
- Whether a line helps *accuracy*. Different question, different skill.
- Anything about lines with no mechanical signature.
- Anything about creativity or output diversity. That was tested and the result
  was inconclusive.

## Provenance

Priors in `references/signatures.json` were measured on 2026-09-07 against
`gpt-5.6-luna` and `gpt-5.6-terra`, on self-contained front-end HTML builds,
172 runs. **They are hints about what to check first, not verdicts.** The
boundary between what a model does unprompted and what it does when asked moves
with every model release — which is why this skill re-derives the buckets on
your model and your task rather than shipping a list of lines to delete. If the
stamp above is more than 90 days old, or your model is not in that set, treat
every prior as unknown and measure.
