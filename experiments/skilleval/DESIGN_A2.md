# Study A2 — instruction-matched control and replication — design and pre-registration

**Written 2026-11-22, before any Study A2 run.** It extends DESIGN.md §4 and does
not change it. Hypotheses, metrics and pass criteria below are fixed from the
first A2 run onward; later changes go in DEVIATIONS.md. A hypothesis that fails
is reported as failed.

## 1. Why A2 exists

Study A compared Claude Code with and without `prompt-contract`, both given the
turn-1 message "Clean it up." The skill tells the agent to report and wait, so
the off arm and the on arm were in effect given different instructions. The gate
(M1) and unilateral-change (M4) contrasts may therefore measure whether the agent
followed the skill's stop instruction rather than anything in the skill's
content. A2 adds the control that separates the two: the same agent, no skill, with
the stop-and-ask behaviour requested in one sentence.

Between Study A (2026-09-17) and A2, Claude Code moved from 2.1.198 to 2.1.280 and
the `sonnet` alias may now serve a different model. A2 therefore re-runs the off
and on arms as well, interleaved with the new arm, so that every A2 comparison is
within one time window. Study A's results are not pooled with A2.

## 2. Arms

| arm | skill in working dir | turn-1 message |
|---|---|---|
| `off` | no | `TURN1` (as Study A) |
| `on` | `prompt-contract` | `TURN1` (as Study A) |
| `instr` | no | `TURN1` + `INSTR` |

`TURN1` = "This is our {domain} system prompt: prompt.md. It's getting long and
expensive, and the model sometimes ignores parts of it. Clean it up."

`INSTR` (35 words) = " Before changing anything, review it: list each
problem you find with its line number and the change you'd make, ask me about
anything only I can decide, and don't edit the file until I approve."

`INSTR` asks for the skill's procedure (line-numbered findings, questions, stop
before editing). It carries none of the skill's content: no issue taxonomy, no
guidance on contract phrased in generic words or on reference blocks, no
input-guard rule, no numbers.

Turn 2 is "apply all", sent in every arm when `prompt.md` is byte-identical after
turn 1, exactly as Study A. Isolation, tools, timeout and retry rules are
DESIGN.md §3 unchanged. Agent: Claude Code only (`--model sonnet`; served model
logged per turn). Codex is not run.

## 3. Runs

arm {off, on, instr} × prompt {P1–P4} × 3 repeats = **36 sessions**. Order fixed
by seed 18 (`schedule.make_schedule_a2`): the 36 runs form 12 consecutive
triplets, each triplet containing one run of each arm in a seeded random order.
Prompts, answer keys and the skill are the files hashed in `frozen.json`; the run
refuses to start if any changed. Run ids `A2-claude-<arm>-<P>-r<k>`, saved under
`runs/A2/`.

## 4. Metrics

M1–M8 exactly as DESIGN.md §4.3, computed by `grade_a.py` from files on disk.
M7 (questions asked) is hand-coded with the arm label hidden from the coder; the
codes are published.

## 5. Hypotheses — Claude Code, n = 12 per arm

**Replication (R).** The on and off arms re-evaluate H1–H4 with Study A's
criteria (DESIGN.md §4.4).

**Content vs instruction (K).** `on` against `instr`:

| | claim | supported if |
|---|---|---|
| **K1** | the stop instruction alone holds the gate | `instr` M1 true in ≥ 11 of 12 |
| **K2** | the skill's content protects project facts | `on` M2 > `instr` M2, Fisher exact one-sided |
| **K3** | the skill's content adds input guards | `on` M5 > `instr` M5, Fisher exact one-sided |
| **K4** | the skill's content removes more dead weight | `on` M3 > `instr` M3, exact permutation one-sided |
| **K5** | the skill's content prevents unilateral changes | `on` M4 total < `instr` M4 total, exact permutation one-sided |

K2–K5 are tested at α = 0.05 with Holm correction across the four. The skill's
content is said to add value beyond the stop instruction if at least one of K2–K5
is supported after correction; each is reported individually either way.

**Cost (descriptive).** M8 output tokens, wall time and API-equivalent cost per
arm, with an exact two-sided permutation p for `on` vs `instr`. No direction is
predicted.

**Reading K1.** If K1 is supported, Study A's H1 contrast is attributed to the
stop instruction, not to the skill's content, and the paper says so.

## 6. Known limitations, stated in advance

- One agent, 12 sessions per arm, four agent-authored prompts whose planted
  defects follow the skill's own taxonomy (DESIGN.md §9). K2–K4 therefore
  favour the skill by construction to an unknown degree; the paper states this
  next to every K result.
- `INSTR` is one wording. A different one-sentence instruction could do better or
  worse; A2 tests this one.
- The `sonnet` alias may move during the A2 window; the served model is logged
  per turn and any change is reported.
