---
name: prompt-contract
description: How to decide what belongs in a system prompt, agent instruction file, CLAUDE.md, AGENTS.md or SKILL.md — and what to leave out. Use when writing a new system prompt or skill from scratch, reviewing one in a PR, deciding whether a rule is worth adding, debugging an agent that ignores its instructions, or answering "is this prompt too long / what should I cut". Built on measurements of what models actually do with each kind of instruction, not on prompt-engineering folklore.
---

# Write the contract, not the advice

A system prompt is a **contract**: the things the model cannot infer and must
get right. Everything else is a work order you are placing, and you will be
billed for it.

Two mistakes follow from getting this backwards. Teams fill prompts with
general advice the model doesn't need, and leave out the specifics only they
know. Then they cut the wrong half when the prompt gets long.

## The one thing to internalise

**Knowing is not doing.**

A capable model knows what accessible markup is, what idempotency is, what a
good commit message looks like. That does not mean it produces them unprompted.
In measurements across 48 generated artifacts, a specific accessibility feature
appeared in **0 of 12** outputs when unmentioned and **12 of 12** when asked
for — one line, all the difference. Meanwhile other conventions appeared every
time regardless, and some requests were ignored no matter how firmly they were
made.

You cannot tell which is which by reading the line. This is the central
practical fact about system prompts, and almost all advice about them ignores it.

## What to include

**1. Contract first — everything the model cannot infer.** This is the part
that earns its tokens, and in practice it is most of a good prompt:

- Exact names: keys, fields, components, endpoints, files, IDs
- Exact values: thresholds, rates, limits, enum members, formats
- Structure: the shape of the output, what wraps what, what order
- Precedence: which rule wins when two apply
- Domain facts and invariants: what must never be true at the same time
- Where things live and what may not be touched

A model with no context will guess these, and its guesses will be plausible and
wrong. **Every line here is load-bearing. Never cut this half.**

**2. Work orders — general instructions whose output you actually want.**
"Handle the empty case." "Emit structured logs." These are legitimate, and each
one is a purchase: it makes the model produce more, and you pay for the extra on
the output side. Include one when you want the thing it produces. Not as
insurance.

**3. Restrictions — instructions that ask for less.** "Never use X." "Do not
add commentary." These are the cheapest lines in a prompt: they reduce output
rather than adding to it, and measured cost was within noise. If you are unsure
whether to keep a restriction, keep it.

## What to leave out

- **Advice the model follows anyway.** Dead weight. You cannot identify it by
  reading — measure it (below).
- **Advice the model ignores anyway.** Also dead weight, and worse: it creates
  the impression the behaviour is covered when it isn't.
- **Insurance.** Lines added "just in case", to feel thorough, or because
  another prompt had them. If you cannot say what output a line produces, it is
  probably not producing any.
- **Restated capability.** Explaining what the model is or how to think.
- **Emphasis as a substitute for specificity.** `CRITICAL: You MUST ALWAYS` is
  not more precise than the same sentence in plain words. If a rule is being
  missed, the fix is usually a sharper contract, not louder formatting.

## Length is the wrong question

"Too long" is not the problem, and shortening is not the goal. A long prompt
that is mostly contract is fine. A short prompt missing a threshold is broken.

Ask of each line: **what does this produce that I would otherwise not get?** If
the answer is "nothing", cut it regardless of length. If the answer is a thing
you want, keep it regardless of length.

The failure mode of aggressive trimming is silent: you delete the line that was
the only reason your output had some property, everything still runs, and the
property is quietly gone.

## How to check, rather than guess

Run your real task once with a block of general instructions **removed**, keeping
the whole contract. Compare against a run with them in. For each instruction,
count something mechanical in the output that indicates compliance:

- present in both → the model does it anyway → **delete the line**
- absent in both → the model ignores it → **delete the line**
- absent without, present with → **that line is why you get it — keep it if you
  want it**

Compare per unit of output size, not raw counts: a longer artifact contains more
of everything, and a count that doubles while the output grows 76% has barely
moved. The `guidance-audit` skill automates this.

## Reviewing someone else's prompt

1. Separate contract from everything else. Contract is not up for discussion.
2. For each remaining line, ask what output it produces. No answer → candidate.
3. Check whether the "candidates" survive a run without them.
4. Keep restrictions; they are cheap.
5. Report what each cut would cost, and let the owner decide. Deleting a work
   order deletes the feature — that is a product call, not a prompt call.

## What is measured here, and what is not

**Measured** (172 runs, two frontier models from one vendor, code-generation
tasks, 2026-09): models frequently do not apply general good practice
unprompted; instructions that ask for work materially increase output volume;
instructions that ask for restraint had no detectable cost; and correctness did
not degrade as general instructions were added, on tasks where the models were
already near-perfect.

**Not measured, and stated as principle:** that contract belongs first, that
emphasis is a poor substitute for specificity, and that this transfers beyond
code generation and beyond one vendor. Treat those as reasoning, not evidence.

**Expect the boundary to move.** Which instructions a model follows unprompted
changes with every release. That is why this skill teaches a procedure rather
than shipping a list of lines to delete — re-check after a model upgrade.
