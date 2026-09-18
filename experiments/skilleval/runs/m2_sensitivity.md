# M2 sensitivity — a wording test, not a fact-survival test

M2 as pre-registered (`grade_a.py::m2_traps_intact`) requires every token in a prompt's
`generic_contract` trap to appear verbatim in the end state, plus ≥90% of the reference
block's non-blank lines to survive with a match ratio ≥0.9. P1's trap carries two tokens on
line 24: the product-specific identifier `Billing_Escalation_L2` and the generic phrase
"standard escalation macro". An agent that keeps the identifier and the fact it names, but
paraphrases the surrounding phrase, is currently graded as having lost the trap — even though
the underlying fact (which escalation macro applies) survived.

This file does not regrade M2 in `runs/results_a.json` or `runs/summary_a.json`; it reports
what M2 would look like under a variant restricted to identifier-shaped tokens, computed
directly from the committed run artifacts (before.md / after_t{1,2}.md for all 12
`claude-off` runs and all 12 `claude-on` runs), so the finding can be checked independently of
the published numbers.

## What changes token-by-token

Filtering each prompt's `generic_contract.tokens` down to the identifier-shaped ones
(`validate_key.IDENTIFIER`) drops:

- **P1**: `standard escalation macro` (keeps `Billing_Escalation_L2`)
- **P2**: `pricing logic` and `finance's dashboards` (keeps `PRICING_RULES`)
- **P3**: nothing — `record_key` and `source_lookup` are both identifier-shaped
- **P4**: nothing — `pipeline_id`, `inv_ingest_v3`, `schema_version`, `2026-04` are all identifier-shaped

So the variant only relaxes P1 and P2's trap; P3 and P4 are unchanged, and the reference-block
coverage requirement (≥90% of non-blank lines) is unchanged for every prompt.

## Computed numbers (claude agent, both arms, all 12 runs each)

Recomputed with `m2_traps_intact()` against a copy of each prompt's answer key whose
`generic_contract.tokens` list is filtered to identifier-shaped tokens only:

| variant | claude-off M2 | claude-on M2 | Fisher two-sided p |
|---|---|---|---|
| pre-registered (every token) | 4 / 12 | 12 / 12 | 1.3461e-03 |
| identifier-shaped tokens only | 7 / 12 | 12 / 12 | 3.7267e-02 |

These match the reviewer's stated figures (4/12 → 7/12, p 1.35e-03 → 3.73e-02) to the
precision given; the on arm is 12/12 under both variants (dropping tokens can only make the
trap check easier, and the on arm already kept the full trap verbatim in every run).

Per-row detail (identifier-only token set in brackets):

- P1 (`['Billing_Escalation_L2']`): r1, r2, r3 all flip from False to True — all three
  off-arm P1 runs kept the identifier and the fact, dropped only the generic phrase.
- P2 (`['PRICING_RULES']`): r1 False→False, r2 True→True (unchanged), r3 False→False — P2's
  three non-passing runs fail on the token/coverage check for reasons independent of the
  dropped phrases.
- P3, P4: unchanged in every run (token set unaffected by the filter).

Net effect: 3 additional off-arm passes, all from P1.

## What this means for H2

H2 ("project facts survive": M2 true in ≥ 11 of 12) is evaluated only for the on arm, which is
12/12 under both variants, so H2 itself is unaffected. What changes is the on-vs-off contrast
this file exists to caveat: M2 as pre-registered overstates how many off-arm runs lost the
underlying *fact* (they lost a specific *phrase* that happened to share the trap's answer-key
line), by a factor that moves the significance of the off-arm's poor showing from p≈1.3e-03 to
p≈3.7e-02 for the affected prompt. Both remain significant at conventional thresholds, but the
effect is smaller and less robust than the headline number alone suggests, and readers should
treat M2 as primarily a wording-fidelity metric rather than a pure fact-survival metric.

## Scope

`validate_key.py`'s `generic_contract` check now requires every token to be identifier-shaped
(previously: at least one). This binds prompt authoring for Studies B and C only — P1-P4 are
frozen (DEVIATIONS.md) and are not re-authored; `validate_key.py` is not run over them in any
test. Checked directly against the four committed answer keys: P1 and P2 would fail the
tightened check (each carries a non-identifier-shaped token, dropped above); P3 and P4 already
satisfy it unchanged (every one of their tokens is identifier-shaped). This differs from the
brief's framing that "the four existing prompts will now fail that check" — only two of the
four (P1, P2) do; P3 and P4 pass. Reported here per the instruction to publish computed
numbers even when they differ from the brief's.
