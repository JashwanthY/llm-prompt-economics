# Calibration: could not build an off-ceiling task

Pre-registered in `design.py`. 12 runs at zero padding, $0.81. **No task
admitted.** The pre-registered band (55-80%) was not met by any candidate, and
the band was not moved.

| task | checks | pooled score at zero padding | verdict |
|---|---|---|---|
| sheet | 22 | 95.5% | reject — at ceiling |
| cart | 80 | 100.0% | reject — at ceiling |
| form | 31 | 98.4% | reject — at ceiling |

## What was attempted

Three tasks written specifically to be hard, each stating many constraints that
must hold simultaneously and producing exact values rather than prose:

- **sheet** — a formula engine with operator precedence, parentheses, `SUM` over
  rectangular ranges, transitive recomputation, cycle detection, `#DIV/0`,
  `#REF`, and multi-step undo.
- **cart** — a pricing engine with three discount tiers, coupon codes with
  explicit non-stacking precedence, conditional free shipping, and tax applied
  to the post-discount subtotal only.
- **form** — cross-field validation with exact error strings, ordered
  missing-class reporting, an age boundary, and submit gating.

## The probe was deepened, and the result did not move

The first grader had 37 checks across the three tasks and every task scored at
ceiling. Because "100%" can mean *the probe is shallow* rather than *the work is
flawless*, the graders were expanded to **133 checks** — boundary values either
side of every threshold, error propagation through arithmetic, coupon
case-insensitivity, an exactly-18-today date boundary — and the same 12 files
were re-graded at no cost. Scores did not move: 95.5% / 100% / 98.4%.

Across 12 runs and 133 checks, only three distinct checks were ever missed, each
twice: case-insensitive username-taken matching, and two undo behaviours.

## Instrument validation

Because every earlier measurement bug in this study was a check that could not
observe what it claimed to test, each grader was validated three ways before use:

| control | cart | form | sheet |
|---|---|---|---|
| hand-written correct reference | 80/80 | 31/31 | 22/22 |
| empty stub page | 0/80 | 0/31 | 0/22 |
| single-rule mutation | breaks exactly the matching checks | | |

The controls caught two real defects in the graders and one in a reference:

- `textOf()` returned `""` for a **missing** element, which is indistinguishable
  from "this field is valid". An empty stub page scored 6/31 on the form task by
  having no error spans at all. Fixed to return `null` when absent.
- `err(k) !== ""` was satisfied by `null`, so the simultaneous-errors check also
  passed on a page with nothing in it.
- The reference implementation parsed `"2008-09-08"` with `new Date()`, which
  reads as UTC midnight and shifts a day earlier when read back with local-time
  `getDate()`. The check that caught it was correct; the reference was wrong.

## Conclusion

The harm hypothesis remains **untested, not refuted**. Three deliberate attempts
to build an instrument sensitive enough to detect quality degradation from
prompt bloat have now failed, because these models do not fail these tasks often
enough to leave room for a decrease.

This bounds the claim usefully: whatever prompt bloat does to current frontier
models, it is not large enough to show up in single-file front-end builds with
richly specified, mechanically checkable requirements. Detecting it — if it
exists — needs a task class where the models are not already near-perfect.
