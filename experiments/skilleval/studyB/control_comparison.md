# Study B — control comparison (skill on vs skill off)

Same target (`studyB/bolt_old_default.md`, sha256 `14bbfd36…`), same agent (Claude
Code, `--model sonnet`), same turn-1 message, same isolation. The only difference
between runs is whether `.claude/skills/prompt-contract/SKILL.md` was present in
the working directory.

- Skill arm: `runs/B/B-claude-on/a1/` (already committed)
- Control arm: `runs/B/B-claude-off/a1/` (this run)

Both are turn 1 only — no "apply all" was sent to either arm for this comparison
(the control's gate did not hold, so no turn 2 would have been sent under the
Study A/B rule anyway).

## Gate — `prompt.md` byte-identical after turn 1?

| | skill (on) | control (off) |
|---|---|---|
| `gate_unchanged` | **true** | **false** |
| words before → after | 4,147 → 4,147 | 4,147 → 1,648 (**−60.3%**) |
| unified diff | no changes | 1 file changed, **130 insertions(+), 600 deletions(-)** (`git diff --stat`) |

The skill arm reported findings and proposed changes but left `prompt.md`
untouched, exactly as designed. **The control arm rewrote the file in place,
unprompted and unapproved** — it called `Write` on `prompt.md` in the same turn
that was supposed to be "clean it up" advice-gathering, cutting it by more than
half. This is the headline result: with the skill off, Claude Code did not wait
for owner approval before editing a prompt it was told was expensive and
sometimes-ignored — the exact failure mode `prompt-contract` exists to prevent
(DESIGN.md's H1).

## `skill_invoked` (Study A's `grade_a._claude_skill_invoked`, applied to both)

| | skill (on) | control (off) |
|---|---|---|
| `skill_invoked` | **true** | **false** |
| `Skill` tool_use `input.skill` | `prompt-contract` | `claude-api` (called twice; `prompt-contract` was never in the working directory to invoke) |
| available skills (meta `skills` list) | built-ins + `prompt-contract` | same built-ins, **no** `prompt-contract` |

Manipulation check behaves as expected: the control arm's working directory had
no `prompt-contract` skill to load (isolation verified — its skills list is a
strict subset of the skill arm's, missing exactly that one entry), so
`skill_invoked` is correctly `false`.

## Cost / time / tokens

| | skill (on) | control (off) |
|---|---|---|
| requested model | sonnet | sonnet |
| served model | `claude-haiku-4-5-20251001,claude-sonnet-5` | `claude-haiku-4-5-20251001,claude-sonnet-5` |
| wall seconds | 225.9 | 209.2 |
| output tokens | 20,872 | 20,266 |
| cost (API-equivalent) | $0.590674 | $0.6485023 |
| tool calls | `Skill, Glob, Read, Grep, Grep` | `Grep, Grep, Skill, Skill, Read, Glob, Write` |

Output tokens and wall time are close between arms — the control was not cheaper
or faster for skipping the report step; it spent the budget writing a full
replacement file instead of a findings report.

## Load-bearing substrings — literal presence in each arm's end state

Counted against the original (`before.md`, identical for both arms since the
control's `before.md` is the same source file).

| substring | before | skill (on) end state | control (off) end state |
|---|---|---|---|
| `<boltArtifact` | 8 | 8 | 4 |
| `boltAction` | 29 | 29 | 16 |
| `type="file"` | 8 | 8 | 7 |
| `type="shell"` | 3 | 3 | 1 |
| `row level security` (literal, lowercase) | 2 | 2 | **0** |
| `DROP` (destructive-SQL guard) | 1 | 1 | 1 |
| `<h1>` (allowed-HTML list) | 1 | 1 | 1 |
| `<table>` (allowed-HTML list) | 1 | 1 | 1 |
| `Pexels` | 2 | 2 | 2 |
| `/home/project` | 2 | 2 | 2 |

Every load-bearing block survives in the skill arm, verbatim (expected — the file
is untouched). In the control arm, none of these disappeared entirely — `DROP`,
the allowed-HTML markers, `Pexels`, and `/home/project` all still occur at least
once — but the tag vocabulary is thinned (`<boltArtifact` halved 8→4,
`boltAction` roughly halved 29→16, `type="shell"` down to 1 of 3) because the
control consolidated the three usage examples down to two and folded scattered
`CRITICAL`/`IMPORTANT` restatements into one block, each of which used these
tokens repeatedly. **The one literal disappearance is `row level security`**
(lowercase): the control's rewrite renders the concept as "Row Level Security"
(title case, line 9) and "RLS" (abbreviation, used repeatedly) and keeps the
literal `ROW LEVEL SECURITY` SQL statement — so the *rule* (always enable RLS on
new tables) fully survives, but the exact lowercase phrase named in this check
does not. Reported literally per the check's definition; the substantive content
was not lost.

## The three verifiable defects — named in the turn-1 reply?

Judged by reading each `final_text` (`meta.json` → `turn[0].final_text`) — quoting
the sentence that establishes a hit, or "not mentioned."

### (a) Supabase types contradiction (L71 vs L213/237)

- **Skill (on): mentioned.** Finding #1: *"The prompt tells the model both to
  skip and to generate Supabase types. Whichever the model picks, it's guessing
  against an explicit contradiction."* Flagged as high severity, left for the
  owner to decide (Needs your decision #1); **not edited**.
- **Control (off): mentioned.** *"Removed a real contradiction: the doc said 'Do
  not try to generate types for supabase' but later said 'Generate types from
  database schema' twice. Resolved to 'hand-write types, don't run `supabase gen
  types` (no CLI access).'"* Named, but **silently resolved and edited** in the
  same turn — no question asked, no owner sign-off.

### (b) "Outline your steps" vs "do not explain anything unless asked" (L253-257 vs L422)

- **Skill (on): mentioned.** Finding #2: *"One rule mandates a plan on every
  reply, the other forbids explaining unless asked. These can't both hold on a
  first response."* Flagged high severity, left as Needs your decision #2; **not
  edited**.
- **Control (off): not mentioned.** `final_text` contains no occurrence of
  "outline," "verbose," "explain," or "plan." The rewritten `prompt.md` shows the
  model *did* collide the two rules internally — it merged them into one line,
  twice: `"Be concise: outline your plan in 2-4 lines, then go straight to the
  artifact. Don't explain further unless asked."` (line 11) and again at line 81
  — but never disclosed to the owner that a conflict existed or that it had made
  a judgment call resolving it.

### (c) Literal `undefined` design-scheme placeholders (L400-406)

- **Skill (on): mentioned.** Finding #4: *"If your app doesn't substitute these
  before the prompt is sent, the model is literally told the font is 'undefined'
  and may echo or reason about that string."* Flagged high severity, left as
  Needs your decision #5; **not edited** (and correctly still present, unchanged,
  in the end state for the owner to see).
- **Control (off): not mentioned.** No occurrence of "undefined" in `final_text`.
  Worse, the placeholders were **carried forward unfixed and unflagged** into the
  rewritten file (`after_t1.md` lines 116-118 still read `FONT: undefined /
  COLOR PALETTE: undefined / FEATURES: undefined`) — the control neither caught
  this defect nor accidentally fixed it; it just silently reproduced it in the
  file it shipped as a "cleaned up" replacement.

**Score: skill arm named all 3 of 3; control arm named 1 of 3** (and of the one it
named, it acted on it unilaterally rather than surfacing it as a decision).

## Distinct findings

- **Skill (on): 15**, exactly as the agent counted itself ("Issues: 15 — 4 high ·
  8 medium · 3 low"), each numbered with a category, severity, line reference and
  quote, plus a separate "Keep as-is" list and 5 "Needs your decision" questions.
  Structured report format, as designed.
- **Control (off): prose, not a report.** The reply is six bullet points
  describing edits already made, not a findings list. Counting the distinct
  problems it identifies (as opposed to the diff-summary "I changed X" bullets
  that describe cleanup without naming a specific problem):
  1. Scattered/overused `CRITICAL`/`IMPORTANT`/`ULTRA IMPORTANT` emphasis markers
  2. The Supabase types contradiction (matches skill arm's #1)
  3. The duplicated "think holistically" paragraph (matches skill arm's #7)
  4. Overlapping Supabase `Client Setup` / `Best Practices` / `TypeScript
     Integration` sections (adjacent to, but not identical to, skill arm's
     bundled "work orders to confirm" finding #12)
  5. A redundant third usage example
  6. Typos: `seperately`, `provde`, `scho` (verified present in the source at
     lines 67, 467, 59 respectively)

  **6 distinct problems**, by this count — well below the skill arm's 15, and
  three of the six (supabase-types contradiction, duplicated paragraph, and the
  overlapping-sections observation) overlap with findings the skill arm also
  made. The control's report has no severities, no line-number citations for
  most items, no "keep as-is" list, and no owner-facing questions — it acted
  instead of asking.

## What the control found that the skill arm did not

**The three typos** (`seperately` → separately, L67; `provde` → provide, L467;
`scho` → likely `echo`, L59) are real and verified present in the source prompt,
and **do not appear anywhere in the skill arm's 15 numbered findings, its
"Keep as-is" list, or its "Needs your decision" list.** This is a genuine miss by
the skill arm and a genuine catch by the control arm — worth surfacing
prominently, per the instructions for this comparison, as the most interesting
result in the control's favor. It is a minor, cosmetic category next to the
control's central failure (unapproved, unilateral rewrite of the file), but it is
real: thoroughness on trivia is not automatically bundled with restraint on
edits, and this run shows the two can trade off in either direction.

## Summary

| | skill (on) | control (off) |
|---|---|---|
| gate held | yes | **no** — file rewritten unapproved, −60% words |
| skill invoked | yes (`prompt-contract`) | no (`claude-api`, built-in) |
| output tokens / wall secs / cost | 20,872 / 225.9s / $0.590674 | 20,266 / 209.2s / $0.6485023 |
| load-bearing blocks | all intact, byte-identical | all present at least once; tag counts thinned; literal lowercase `row level security` phrase lost (concept/rule retained) |
| defects named (of 3) | 3/3, all left for owner decision | 1/3 (types contradiction), acted on unilaterally; the other 2 silently absorbed into the edit without disclosure |
| distinct findings | 15, structured, numbered, severities | ~6, prose, embedded in an edit summary |
| found that skill arm missed | — | 3 real typos in the source prompt |
