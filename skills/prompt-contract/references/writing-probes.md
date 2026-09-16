# Writing a probe

A probe turns one directive into something countable in the **generated
output** — never in the prompt. You write probes after you have classified the
prompt yourself.

```json
[{"line": 17,
  "feature": "reduced-motion support",
  "pattern": "prefers-reduced-motion"},
 {"line": 22,
  "feature": "no inline event handlers",
  "pattern": "\\son[a-z]+\\s*=\\s*[\"']",
  "inverted": true}]
```

- **`pattern`** — a Python regex, counted with `re.M | re.I` in each artifact.
- **`inverted`** — set when *absence* is compliance ("no inline styles",
  "never use var"). A compliant file scores 1, a violating file 0.
- **`line`** — optional, for citing back to the user.

## What makes a probe good

It does not need to be a perfect detector. The audit **differences two arms**,
so any bias applies to both and cancels. What matters is that the count
*responds* to the directive.

- **Count a consequence, not a word.** For "use rem units", count `\d(\.\d+)?rem\b`
  in the artifact, not the phrase "rem units".
- **Prefer a pattern that can appear many times.** Density over 10KB is the
  unit; a yes/no probe carries less signal.
- **If you cannot think of a countable consequence, say so.** Some directives
  ("write clear code", "use good judgement") have no mechanical trace. Report
  them as unmeasurable. That is a finding, not a gap.

## Worked examples, from the study

These are **examples of probe design**, and a record of what was observed on
one task family — self-contained front-end HTML builds, two GPT-5.6 models,
September 2026. They are **not a lookup table** and not verdicts for your
prompt. Which bucket a directive falls into depends on your model and your
task, and it moves with every model release. Re-derive it.

| feature | pattern | observed there |
|---|---|---|
| reduced motion | `prefers-reduced-motion` | only-when-asked — 0/12 files without, 12/12 with |
| rem units | `\d(\.\d+)?rem\b` | only-when-asked — 4–7x by density |
| aria attributes | `\saria-[a-z]+=` | only-when-asked — ~1.25–1.35x per KB |
| CSS custom properties | `--[a-z][\w-]*\s*:` | only-when-asked |
| semantic elements | `<(main\|section\|header\|footer\|nav\|article)` | partial |
| responsive | `@media` | partial |
| const/let over var | `\b(const\|let)\s` | already-followed — present in every file measured |
| no `var` | `\bvar\s` (inverted) | already-followed |
| event listeners | `addEventListener\(` | already-followed |
| no inline handlers | `\son[a-z]+\s*=\s*["']` (inverted) | already-followed |
| flex/grid layout | `display\s*:\s*(flex\|grid)` | already-followed |
| no `!important` | `!important` (inverted) | already-followed |
| code comments | `^\s*//\|/\*` | ignored — zero in all 48 files, with and without |
| error handling | `\bcatch\s*\(` | ignored — zero in all 48 files, with and without |
| debounce/throttle | `debounce\|throttle` | ignored |

Note the shape of that table: the *already-followed* and *ignored* rows are
where the waste was, and both are invisible from reading the prompt. That is
the whole argument for measuring.

These examples are all HTML/CSS/JS because that is what was studied. Nothing
about the method is web-specific — for a backend prompt you might probe
`^\s*log(ger)?\.` for structured logging, or `\bidempotenc` in a design doc.
Write the probe your prompt calls for.
