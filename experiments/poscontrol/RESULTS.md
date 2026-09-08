# Positive control: the instrument is sensitive, and specific

Pre-registered in `design.py`. 12 runs, $0.52. **Criterion met.**

Same task, same grader, same model, same reasoning effort. The only change is the
removal of a parameter the model cannot infer.

| arm | n | score | outcome |
|---|---|---|---|
| full (control) | 4 | 100.0% | — |
| minus_tiers | 4 | 91.6% | partial |
| minus_coupon | 4 | 91.2% | partial |
| minus_tax | 4 | **73.8%** | **detected** |

Pre-registered criterion — at least one ablated arm below 80% — is met by
`minus_tax`.

## The failures land exactly where predicted

This matters more than the headline drop. An instrument that falls over for the
wrong reason is no better than one that cannot move at all.

| arm | predicted | observed |
|---|---|---|
| minus_tax | every tax and total check fails; subtotal and shipping unaffected | **only** tax (14) and total (14) checks failed |
| minus_coupon | the SAVE10 scenarios fail | SAVE10 non-stacking and SAVE10-beats-smaller-tier, 4/4 runs |
| minus_tiers | discount/tax/total fail across tier scenarios | exactly those, on the tier scenarios |

In `minus_tax`, subtotal, discount and shipping checks all still pass. The
grader isolates the removed fact and nothing else.

## What this establishes

Every quality result in this study is a null obtained at ceiling. A null from an
instrument never shown to respond to anything is worth nothing. This control
shows the pipeline **does** register a prompt-induced quality change — a 26-point
drop — when the prompt loses information the model genuinely needs.

So the study's nulls are informative after all: adding generic material the model
already knows produced no measurable change, on an instrument that demonstrably
detects the removal of material it does not know. That is the asymmetry the paper
is about.

## The partial arms are interesting in their own right

`minus_tiers` scored 100% in two of four runs: without being told the thresholds,
the models sometimes guessed 5/10/15% at $100/$250/$500 exactly. `minus_tax`
scored 100% once, guessing 8.25%. Conventional parameters are partially
recoverable from priors; genuinely arbitrary ones are not. This is the same
distinction the paper draws between information the model has and information it
does not, visible here as a graded rather than binary effect.
