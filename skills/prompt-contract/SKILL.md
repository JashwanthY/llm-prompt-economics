---
name: prompt-contract
description: Audit and trim a system prompt, CLAUDE.md, AGENTS.md or SKILL.md by measuring which of its lines actually change the model's output, then report the token and latency saving. Use when someone asks what to cut from a prompt, says their prompt or skill is too long, asks whether a rule is worth adding, is reviewing prompt changes in a PR, is debugging an agent that ignores its instructions, or wants to know what generic best-practice instructions are costing them. Also use when writing a new system prompt from scratch and deciding what belongs in it.
---

# Write the contract, not the advice

A system prompt is a **contract**: what the model cannot infer and must get
right. Every other line is a work order you are placing, and you are billed for
it at the output.

**The organising fact: knowing is not doing.** A capable model knows what
accessible markup is, what idempotency is, what a good commit message looks
like. It frequently does not produce them unprompted. Across 48 generated
artifacts one accessibility feature appeared in **0 of 12** outputs when
unmentioned and **12 of 12** when asked for. Other conventions appeared every
time regardless. Some requests were ignored however firmly made.

**You cannot tell which is which by reading the line.** That is why this skill
measures instead of advising.

## Three kinds of line

| kind | example | cost | verdict |
|---|---|---|---|
| **Contract** | key names, thresholds, precedence, invariants | earns it | **never cut** |
| **Work order** | "handle the empty case", "emit structured logs" | billed at the output | keep **iff** you want what it produces |
| **Restriction** | "never use X", "no commentary" | no detectable cost | keep when unsure |

The failure mode of trimming is silent: delete the line that was the only reason
your output had some property, and everything still runs without it. **Shorter
is not the goal. Knowing is the goal.**

---

# The procedure

Run this end to end. Report the summary in step 6 — that is the deliverable.

## Step 1 — Get what you need from the user

You need three things. Ask for whatever is missing:

1. **The prompt file** to audit.
2. **A command that runs their real task**, reading the prompt from
   `$PROMPT_FILE` and writing its artifact to `$OUT_FILE`. A wrapper script is
   fine. Without this you can only classify, not measure — say so plainly and
   stop at step 2.
3. **How many runs** they will pay for. Default 3 per variant. Six runs of a
   single-file generation task is roughly $0.30; a long agentic loop is more.
   Tell them the estimate before spending anything.

## Step 2 — Classify, free

```
python3 scripts/audit.py classify <prompt-file>
```

Splits lines into *guidance* (recognised generic directives — auditable),
*restraint* (asks for less — leave them), and *review* (unrecognised).

**Never propose deleting a `review` line.** Those are usually the contract. The
tool has no signal on them and neither do you.

If most of the file is `review`, say so: that prompt is mostly contract and
there is little to cut. That is a finding, not a failure.

## Step 3 — Produce the off-arm

Write a copy of the prompt with the *generic guidance block removed* and
**every contract line kept**. Run the task N times against it, saving outputs.

## Step 4 — Bucket the lines

```
python3 scripts/audit.py report <prompt-file> --off 'runs/off_*.<ext>' --on 'runs/on_*.<ext>'
```

Counts are compared per 10KB, because a longer artifact contains more of
everything. Without `--on` you get candidates, not verdicts.

- **already-followed** → delete, the model does it anyway
- **ignored** → delete, the model does not do it either way
- **amplified / only-when-asked** → **this line is why you get that** — keep it
  if the user wants the feature

## Step 5 — Propose a trimmed prompt, and measure it

Write `trimmed.md` removing **only** the *already-followed* and *ignored* lines.
Never remove contract, restriction, `review`, or anything the user said they
want. Then:

```
python3 scripts/measure.py --cmd '<their command>' \
    --variant original=<prompt-file> --variant trimmed=trimmed.md --runs 3
```

Variants are interleaved so session drift lands on all of them equally.

## Step 6 — Report

Give the user exactly this, and nothing dressed up:

- **What I removed** — each line, and which bucket it fell in
- **What I deliberately kept** — the amplified/only-when-asked lines, naming the
  feature each one buys, so they can overrule you
- **What I could not judge** — the `review` lines, untouched
- **Measured effect** — output tokens, latency and artifact size, original vs
  trimmed, with intervals and the run count
- **What this does not prove** — that the output is still correct

Then: **"Run your own tests before adopting the trimmed prompt."** Say it
plainly. This measures whether directives were *followed*, never whether the
result is *right*.

## If you cannot run their task

Stop at step 2. Give the classification, mark the priors in
`references/signatures.json` as hints, and state clearly that nothing was
measured. Bias toward keeping. A wrong deletion is silent and permanent; a wrong
retention costs tokens.

---

# What to include when writing a new prompt

**Contract first**, and expect it to be most of the file: exact names, keys,
fields, endpoints, IDs; exact values, thresholds, rates, limits, formats;
output structure; which rule wins when two apply; domain invariants; what may
not be touched. A model with no context guesses these, plausibly and wrongly.

**Leave out:** advice the model follows anyway; advice it ignores anyway;
insurance lines added "just in case"; restated capability; and emphasis used as
a substitute for precision — `CRITICAL: You MUST ALWAYS` is not more specific
than the same sentence in plain words. If a rule keeps being missed, the fix is
usually a sharper contract, not louder formatting.

# Evidence, and its limits

**Measured** — 198 runs, two frontier models from one vendor, code-generation
tasks, September 2026: models frequently do not apply general good practice
unprompted; instructions that ask for work materially increase output volume;
instructions that ask for restraint had no detectable cost; correctness did not
degrade as general instructions were added, on tasks where the models were
already near-perfect (so this bounds harm, it does not exclude it).

**Reasoning, not evidence** — that contract belongs first, that emphasis is a
poor substitute for specificity, and that any of this transfers beyond code
generation or beyond one vendor.

**The boundary moves.** Which instructions a model applies unprompted changes
with every release, which is why this skill measures on the user's model rather
than shipping a list of lines to delete. Treat `references/signatures.json` as
hints about what to check first, never as verdicts.
