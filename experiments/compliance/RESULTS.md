# Compliance under prompt bloat — results

Pre-registered in `design.py` before any run. 24 runs, all completed, no errors,
no missing files. Cost $3.68.

**Question.** The dose experiment measured whether padded prompts still produce
*working* output. It never measured rule-*following*. The motivating production
bug was 87 hardcoded hex colours against a rule the skill states twice — so this
run states five mechanically checkable house rules once, before the task, then
appends the same 0/68/246/811-word padding ladder after it.

## Headline: no erosion. The hypothesis is not supported.

Violations pooled across both models, n=6 files per dose:

| dose | padding words | hex outside `:root` | any hex (strict) | other four rules |
|---|---|---|---|---|
| L0 | 0 | 0 | 65 | 0 |
| L1 | 68 | 1 | 53 | 1 |
| L2 | 246 | 0 | 66 | 0 |
| L3 | 811 | 0 | 37 | 0 |

Rule-following did not degrade with dose. If anything the heaviest dose scored
best, which is the direction that would embarrass the hypothesis, and n=6 makes
it noise either way.

## This test had far less measurement power than it looks

Four of the five rules were never broken at **any** dose, including zero
padding: inline handlers 0/24, missing `data-testid` 0/24, `innerHTML` 0/24,
bad id prefix 1/24. A rule that never fires under any condition cannot detect
erosion — it measures the rule's difficulty, not the model's attention. This is
the same ceiling failure the calibration gate exists to catch, and the design
should have banded these rules before the run rather than after.

Only rule 1 had range, and only under the strict reading. Its variation is
non-monotonic and points in **opposite directions** for the two models —
luna 38/12/23/37, terra 27/41/43/0 across L0-L3 — which is what noise looks
like, not a dose effect.

## Rule 1 was ambiguous, so both readings are reported

The rule says *"Never write a hardcoded hex colour. Define all colours as CSS
custom properties in `:root` and reference them with `var(--name)` everywhere."*
Sentence 1 forbids any hex; sentence 2 tells the model to centralize colours in
`:root`, which normally requires literal values there. Both readings are scored:

- **intent** (hex outside `:root`): 1 violation in 24 files
- **strict** (any hex at all): 221, essentially all of them `:root` definitions

terra at L3 wrote `rgb()` in `:root` and scored zero under both. luna wrote hex
in `:root`. That is a formatting preference, not a compliance failure.

## What did replicate: the cost

| dose | padding words | output tokens | latency |
|---|---|---|---|
| L0 | 0 | 5,287 | 41.0s |
| L1 | 68 | 5,715 (+8%) | 50.7s (+24%) |
| L2 | 246 | 6,213 (+18%) | 50.3s (+23%) |
| L3 | 811 | 6,621 (+25%) | 52.2s (+28%) |

The dose experiment's cost finding reproduces on a different task, with a rules
block present, at +25% output tokens and +28% latency for no measured return.

## Consequence for the paper

The claim "bloat erodes rule-following" is not supported and must not be made.
The supported claim is narrower and still holds: **general-knowledge padding buys
nothing and costs tokens and latency.** The production hex bug is not explained
by padding — these models followed an explicitly stated hex rule at every dose,
including 811 words of it.

## Measurement bugs found and fixed before believing the numbers

The first version of `check.py` reported violations in 17/24 files. Both causes
were mine: `<style>` sits inside `body`, so summing `style + body` counted every
hex twice; and compliant `:root` definitions were scored as violations. Corrected
counts are above.
