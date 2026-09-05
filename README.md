# stillholds

**Most prompt-engineering advice has never been measured.** This repository measures eight
rules taken verbatim from OpenAI's and Anthropic's own documentation, across 15 models and two
vendors, one rule at a time — and ships what survived as an installable skill.

Two rules held on every model tested. Two widely taught techniques did nothing on all but one.
One technique was worth 55 accuracy points on GPT-5.1 and about 12 on GPT-5.6 — no vendor
documentation records that decay.

---

## Install the skill

```bash
git clone <REPO-URL> && cd stillholds
mkdir -p ~/.claude/skills/system-prompt-writing
cp -R skills/system-prompt-writing/{SKILL.md,references} ~/.claude/skills/system-prompt-writing/
```

Restart your agent. It loads when you ask to write, review, or fix a system prompt.

## What it does

Given a prompt and the model you actually ship to, it walks a five-step audit:

0. **Name the model, then fetch its vendor's current guidance.** The measured evidence here is
   narrow and dated; the vendor page is broad and live. The skill states explicit rules for
   what to do when the two disagree.
1. **Delete blanket fallback instructions.** "If in doubt, guess." Costs accuracy on every
   model measured.
2. **Make the output contract explicit.** Name every key. Helps on every model measured — the
   one rule expected to survive future upgrades, because a schema is information no amount of
   capability supplies.
3. **Delete scaffolding that measured nothing.** XML wrappers, role sentences.
4. **Check the model-dependent rules**, which genuinely reverse by vendor.
5. **Verify on your own inputs**, with the noise floor stated.

### Worked example

Before — a real invoice-extraction prompt that was fabricating vendor names:

```
<instructions>
You are an expert invoice-processing assistant with 20 years of experience.
Think step by step.
Extract the invoice details as JSON.
CRITICAL: You MUST always populate every field. If in doubt, use your best
guess. Never leave a field blank.
Be concise.
</instructions>
```

`stillholds score` on this prompt, targeting `gpt-5.4`, reports: **R6 and R7 harmful**,
**R1/R2/R8 expired**, **R4 unmeasurable** — and that **R5, the rule that helps on every model,
is absent**. The fabrication is prompt-caused: the "best guess" line is the audit's most
harmful pattern.

## Use the tooling

```bash
pip install -e .
stillholds score --prompt your-prompt.txt --to gpt-5.6-sol   # audit a prompt
stillholds audit --models gpt-5.6-sol --n 20 --seeds 2       # re-run the measurement
stillholds gen-skill                                          # rebuild the skill from the map
```

`score` is deterministic and makes no API calls. `audit` does, and costs money.

## The evidence

`data/audit/combined-15models.json` — 120 cells, 107 measurable, 45 significant. Every row
carries `band`, `degenerate_ci`, `control_accuracy` and `expired`, so you can recompute any
claim rather than trusting a table.

**Excluded, no variation, and measured null are three different things**, and the audit keeps
them apart. A model already scoring 1.00 without an instruction cannot be improved by it —
reporting that as "no effect" is an absence of measurement wearing a null's clothing. That
distinction is the paper's methodological contribution and it caught a false finding of our own.

## The paper

`paper/main.pdf` — *Does It Still Hold? An Expiry Audit of Prompt-Engineering Guidance Across
15 Models.* Rebuild with `cd paper && python3 build.py && tectonic -X compile main.tex`
(needs `pandoc` and `tectonic`).

## Honest limits

- **One task family.** Structured extraction scored on schema conformance. A rule inert here
  could matter for summarisation, code generation, or dialogue.
- **n = 20, noise floor near ±25 points.** Only the two universal rules clear it comfortably.
- **Two vendors, no open-weight models.**
- **One rule had a construct-validity failure** — its control arm encoded the scoring
  convention. Re-measured with a clean control the direction holds, the magnitudes shrink. See
  §4.7. We report it rather than quietly restating the conclusion.
- **Dated.** The audit date is stamped in the skill. Model behaviour moves; that is the point.

## Contributing

The most valuable contributions are measurements we cannot make:

- **A second task family** — summarisation or code generation. This is the single biggest
  credibility upgrade available, and it converts our main limitation into a finding either way.
- **Open-weight models.** `src/stillholds/registry.py` takes new entries; the harness needs a
  provider branch in `client.py`.
- **Vendors we do not cover.** Google, Mistral, Meta.

Run `stillholds audit --models <id> --n 20 --seeds 2 --out data/audit/<name>.json` and open a
PR with the JSON. Please do not hand-edit result files.

## License

Code and data: MIT. The vendor documentation quoted in `docs/RULES-INVENTORY.md` belongs to
its respective owners and is quoted for analysis.
