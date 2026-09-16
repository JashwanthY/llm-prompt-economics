# Writing a new prompt from scratch

The audit procedure in `SKILL.md` tells you what an existing prompt is wasting.
This is the other direction: what to put in a prompt you are writing now.

## Contract first, and expect it to be most of the file

A model with no context guesses these, plausibly and wrongly:

- **Exact names** — keys, fields, endpoints, IDs, file paths, table names
- **Exact values** — thresholds, rates, limits, timeouts, formats, units
- **Output structure** — what shape the result must take
- **Precedence** — which rule wins when two apply
- **Domain invariants** — what must always or never be true
- **Boundaries** — what may not be touched

If you are unsure whether something is contract, ask: *could a capable model
have guessed this?* If no, write it down. If yes, it is a work order — include
it only if you want what it produces.

## Leave out

- Advice the model follows anyway
- Advice it ignores anyway
- Insurance lines added "just in case" that name no actual requirement
- Restated capability — telling the model to do what it cannot not do
- **Emphasis used as a substitute for precision.** `CRITICAL: You MUST ALWAYS`
  is not more specific than the same sentence in plain words

If a rule keeps being missed, the fix is usually a sharper contract, not louder
formatting. "Be careful with dates" is a wish; "store all timestamps as UTC
epoch milliseconds" is a contract, and it is the one that gets followed.

## A note on work orders

Work orders are not waste by default. A work order is a **feature request you
are paying for at the output**. "Respect `prefers-reduced-motion`" costs tokens
every run and buys you an accessibility feature that, in one measured setting,
appeared in **zero** of twelve files when it was not asked for.

That is a product decision, not a prompt-hygiene decision. Keep the ones whose
feature you want. Delete the ones you were including out of habit. The audit
exists to tell you which is which, because reading them will not.
