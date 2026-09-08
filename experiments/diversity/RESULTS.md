# Diversity: bulk versus restriction — what converges, and what costs

Pre-registered in `design.py`. 36 runs, $4.81, all completed, no errors.

## Pre-registered result: not supported

Group homogeneity (mean pairwise similarity on the pre-registered primary
metric; higher = runs more alike):

| arm | luna | terra |
|---|---|---|
| minimal | 0.578 | 0.306 |
| padded (bulk, 811 words) | 0.473 | 0.457 |
| conservative (restriction, ~90 words) | 0.478 | 0.402 |

| test | luna Δ (p) | terra Δ (p) | combined (Fisher) |
|---|---|---|---|
| metric validation: conservative > minimal | −0.100 (.976) | +0.095 (.170) | p = .463 — **not supported** |
| H1: padded > minimal | −0.105 (.964) | +0.151 (.060) | p = .222 — **not supported** |

The two models point in opposite directions on both contrasts. By the rule
fixed before the run, a failed metric validation makes H1 uninterpretable from
the primary metric: the metric could not detect convergence even under explicit
"be conventional" pressure.

## Why the primary metric failed, found afterwards

**The structure half is confounded with length.** Padded outputs are ~75%
larger (luna 10k → 18k chars, terra 6k → 18k). A difflib ratio over tag
sequences falls as documents grow and elaborate, so bulk that makes the model
write *more* lowers structural similarity even where design choices converge.
This is why luna's padded arm scores as *less* alike than minimal across the
whole pair distribution (0.32–0.67 vs 0.41–0.71), not because of one outlier.

**The hue half has a blue-default ceiling on luna.** Luna's minimal runs already
choose azure/blue in 4 of 6 (hue similarity 0.687 at baseline), leaving little
diversity for an instruction to remove.

Both are metric defects I did not anticipate when validating on the dose
outputs, where every group had similar length. The validation checked that the
metric separates *different briefs*; it did not check invariance to *output
length*, which is exactly what bulk changes.

## Exploratory: the collapse is visible on the model that had diversity to lose

Secondary measures, terra, 6 runs per arm (post-hoc, not the pre-registered test):

| arm | dominant accent hue per run | distinct accents | fonts |
|---|---|---|---|
| minimal | orange, red, azure, spring, spring, green | **5** | arial, georgia |
| padded | spring ×3, azure ×3 | 2 | inter |
| conservative | azure ×5, cyan | 2 | arial |

With no instructions, terra produced five different accent colours and two
typefaces in six runs. Add 811 words of engineering guidance that never mentions
colour — or ~90 words of "be conventional" — and it settles on two hues and one
face. Luna shows the ceiling instead: 3 / 3 / 2 accents, blue-leaning from the
start.

This is the pattern the hypothesis predicts, on one model, on a secondary
measure, at n=6. It is reported as a lead, not a result.

## What did replicate: cost, now separated into its two causes

| arm | output tokens | latency | HTML size |
|---|---|---|---|
| minimal | 5,114 | 38.7s | 14.4k chars |
| padded (bulk) | 8,713 (**+70%**) | 79.2s (**+104%**) | 25.2k (+76%) |
| conservative (restriction) | 4,951 (−3%) | 39.7s (+2%) | 14.0k (−2%) |

This is the cleanest cost result in the study. Two things people put in skills
were separated: **bulk costs, restriction does not.** Ninety words of rules cost
nothing; 811 words of generic guidance doubled latency on an open-ended task and
made the model write 76% more HTML. The 844-line skill that motivated this work
is expensive because of its generic half, not its rules.

## Consequence

The convergence hypothesis is neither supported nor refuted here. It needs a
length-invariant convergence metric (e.g. a fixed-length design-feature vector,
or an LLM-judged pairwise "same design?" with a validated rubric), a positive
control arm that fully specifies a design and must score near 1.0, and more than
six runs per group. The cost separation stands on its own.
