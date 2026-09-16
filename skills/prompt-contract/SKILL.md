---
name: prompt-contract
description: Audit and trim a system prompt, CLAUDE.md, AGENTS.md or SKILL.md by judging which lines are load-bearing and measuring which ones actually change the model's output, then report a score, the token and latency saving, and what to cut. Use when someone asks what to cut from a prompt, says their prompt or skill is too long, asks whether a rule is worth adding, is reviewing prompt changes in a PR, is debugging an agent that ignores its instructions, or wants to know what generic best-practice instructions are costing them. Also use when writing a new system prompt from scratch and deciding what belongs in it.
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

**You cannot tell which is which by reading the line.** Reading tells you what a
line *asks for*; only running the task tells you what it *changes*.

## Three kinds of line

| kind | what it is | cost | verdict |
|---|---|---|---|
| **Contract** | facts that exist only in this project: key names, thresholds, precedence, invariants, file and field names | earns it | **never cut** |
| **Work order** | generic good practice: "handle the empty case", "emit structured logs" | billed at the output | keep **iff** you want what it produces |
| **Restriction** | "never use X", "no commentary" | no detectable cost | keep when unsure |

The test for contract is not how the line is phrased — it is **could a capable
model have guessed this?** `Round tax half-up to 2 decimals` is contract: the
model would otherwise guess, plausibly and wrongly. `Use rem units` is a work
order: the model knows what rem units are.

Watch for lines that look generic but are not. *"Every control must carry an
`aria-label` equal to its `action_id` from `actions.json`"* mentions a public web
standard, but it names a field and a file that exist only in this project. It is
contract. **When a line names something that exists nowhere else, it is contract
however generic its vocabulary sounds.**

The failure mode of trimming is silent: delete the line that was the only reason
your output had some property, and everything still runs without it. **Shorter
is not the goal. Knowing is the goal.**

---

# The procedure

Run this end to end. Report the summary in step 6 — that is the deliverable.

## Step 1 — Get what you need

1. **The prompt file** to audit.
2. **A command that runs their real task**, reading the prompt from
   `$PROMPT_FILE` and writing its artifact to `$OUT_FILE`. A wrapper script is
   fine. Without this you can review but not measure — say so plainly.
3. **How many runs** they will pay for. Default 3 per variant. Six runs of a
   single-file generation task is roughly 30 US cents; a long agentic loop is more.
   Tell them the estimate before spending anything.

## Step 2 — Read the prompt and classify it yourself

```
python3 scripts/audit.py lines <prompt-file>
```

That numbers the directive lines. It does **not** judge them — no script here
matches keywords, because two attempts to do so both failed in the dangerous
direction (`references/why-no-keyword-matching.md`). The judgement is yours.

Put every line in one of the three kinds above. For each, ask: *could a capable
model have guessed this without being told?* If no, it is contract. Show your
classification with a one-line reason each, so the user can overrule you.

Also flag, without deleting:
- **emphasis as a substitute for precision** — `CRITICAL: You MUST ALWAYS` is not
  more specific than the same sentence in plain words
- **restated capability** — telling the model to do something it cannot not do
- **insurance lines** added "just in case" that name no actual requirement

## Step 3 — Score the prompt

Report two ratios. Do not blend them into one number; they measure different
things and the second one needs runs.

- **Contract share** = contract lines ÷ directive lines.
  **≥70% lean · 40–69% mixed · <40% advice-heavy.**
- **Dead weight** = directives measured as doing nothing ÷ directives decided.
  Available only after step 5. **≤20% tight · 21–50% loose · >50% bloated.**

Until you have measured, say **"unmeasured"** for dead weight. Never estimate
it from reading — that is the one claim this skill exists to stop people making.

## Step 4 — Write probes and produce the off-arm

For each work order, write a probe: something countable in the **generated
output** that responds to that directive. See `references/writing-probes.md`.
If a directive has no countable consequence, report it as unmeasurable.

Then copy the prompt with the **work orders removed and every contract and
restriction line kept**, and run the task N times against each version, saving
the outputs.

## Step 5 — Bucket the lines

```
python3 scripts/audit.py report <prompt-file> --probes probes.json \
    --off 'runs/off_*.<ext>' --on 'runs/on_*.<ext>'
```

Counts are compared per 10KB, because a longer artifact contains more of
everything. Without `--on` you get candidates, not verdicts.

- **already-followed** → delete, the model does it anyway
- **ignored** → delete, the model does not do it either way
- **amplified / only-when-asked** → **this line is why you get that** — keep it
  if the user wants the feature

Then write `trimmed.md` removing **only** already-followed and ignored lines,
and measure it:

```
python3 scripts/measure.py --cmd '<their command>' \
    --variant original=<prompt-file> --variant trimmed=trimmed.md --runs 3
```

Variants are interleaved so session drift lands on all of them equally.

## Step 6 — Report

Give the user exactly this, and nothing dressed up:

- **Score** — contract share and dead weight, with the run count behind them
- **What I removed** — each line, and which bucket it fell in
- **What I deliberately kept** — the amplified/only-when-asked lines, naming the
  feature each one buys, so they can overrule you
- **What I could not judge** — lines with no countable consequence, untouched
- **Measured effect** — output tokens, latency and artifact size, original vs
  trimmed, with intervals
- **What this does not prove** — that the output is still correct

Then: **"Run your own tests before adopting the trimmed prompt."** Say it
plainly. This measures whether directives were *followed*, never whether the
result is *right*.

## If you cannot run their task

Stop after step 3. Give the classification and the contract share, and state
clearly that dead weight is unmeasured and no line was proven idle. Bias toward
keeping. A wrong deletion is silent and permanent; a wrong retention costs
tokens.

---

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
with every release. That is why this skill measures on the user's own model
rather than shipping a list of lines to delete, and why the worked examples in
`references/writing-probes.md` are examples, never verdicts.

See also `references/prompt-authoring.md` when writing a new prompt from scratch.
