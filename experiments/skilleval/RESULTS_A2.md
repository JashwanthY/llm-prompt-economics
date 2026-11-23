# Study A2 — results

Pre-registered in `DESIGN_A2.md` (2026-11-22) before any A2 run. 36 Claude Code
sessions, 12 per arm, all completed on the first attempt, every turn served by
`claude-sonnet-5` (the same model as Study A). Computed by `analyze_a2.py` from
the files on disk; graded rows in `runs/results_a2.json`, summary in
`runs/summary_a2.json`.

## Per arm

| metric | off (no skill) | instr (no skill, 35-word stop-and-ask) | on (skill) |
|---|---|---|---|
| M1 file untouched after turn 1 | 1 / 12 | **12 / 12** | 12 / 12 |
| M2 project facts intact at the end | 6 / 12 | 6 / 12 | **12 / 12** |
| M3 dead weight removed (0–3), mean | 2.33 | 2.50 | 2.17 |
| M4 ambiguous lines changed without an answer, total | 44 | 43 | **1** |
| M5 data-not-instructions guard added | 0 / 12 | 2 / 12 | **11 / 12** |
| M6 planted lines cited in turn 1, mean | 0.25 | 7.50 | 12.25 |
| M7 ambiguous items asked about, mean (of 6.5) | 0.33 | 3.83 | 6.33 |
| output tokens per session, mean | 5,321 | 8,987 | 13,729 |
| wall time per session, mean | 63 s | 101 s | 142 s |
| API-equivalent cost per session, mean | $0.14 | $0.28 | $0.47 |

## Replication (R): Study A's H1–H4, on vs off

All four hold again on Claude Code 2.1.280: H1 gate 12/12 vs 1/12 (Fisher p =
9.6e-6), H2 facts intact 12/12 vs 6/12 (p = 0.014), H3 ambiguous changes 1 vs 44
(permutation p = 2.2e-6), H4 mean dead weight removed 2.17 ≥ 2.0.

## Content vs instruction (K)

| | claim | result | p (one-sided) | p (Holm) | verdict |
|---|---|---|---|---|---|
| **K1** | the stop instruction alone holds the gate | instr 12 / 12 | — | — | **supported** |
| **K2** | the skill's content protects project facts | 12 / 12 vs 6 / 12 | 0.0069 | 0.014 | **supported** |
| **K3** | the skill's content adds input guards | 11 / 12 vs 2 / 12 | 0.00032 | 0.00097 | **supported** |
| **K4** | the skill's content removes more dead weight | 2.17 vs 2.50 | 0.95 | 0.95 | **not supported** (wrong direction) |
| **K5** | the skill's content prevents unilateral changes | 1 vs 43 | 1e-6 | 3e-6 | **supported** |

Cost, on vs instr: +53% output tokens, two-sided exact permutation p = 1e-6.

## What this means

- **Study A's headline gate result is explained by the instruction, not the
  skill.** As pre-registered (DESIGN_A2.md §5, "Reading K1"), K1's support means
  the on-vs-off gate contrast in Study A (12/12 vs 1/12) reflects an agent told
  to stop, stopping. A 35-word request does the same.
- **The skill's content does three things the instruction does not.** It keeps
  project facts phrased in generic words (K2), adds a data-not-instructions guard
  where outside text enters the prompt (K3), and routes ambiguous lines into
  questions rather than proposed edits, so "apply all" does not silently resolve
  them (K5). The K5 contrast holds in every one of the four prompts (instr 1–6
  ambiguous lines changed per run; skill 0 in 11 runs, 1 in one).
- **It does not remove more dead weight** (K4). The instruction-only arm removed
  slightly more.
- **It costs more.** About 53% more output and 70% more API-equivalent cost per
  review than the 35-word instruction.

## Reading M4 in the instr arm

M4 counts ambiguous lines that differ from the original at the end of the
session. In the instr arm the agent held the file, listed proposals, and the
simulated user replied "apply all" without answering anything; the agent then
applied its own resolutions of the ambiguous lines. Those changes were
approved in the sense that the user said "apply all", but no question about them
was ever answered. The skill arm turned the same lines into questions, which
"apply all" cannot settle, so it left them unchanged.

M7 (descriptive) agrees: of 6.5 planted ambiguous items per prompt on average,
the instruction-only agent asked about 3.83 and the skill 6.33 (blind codes in
`runs/codes_m7_a2.json`; packets and key in `runs/m7_a2/`).

## Limitations

As DESIGN_A2.md §6: one agent; 12 sessions per arm; four agent-authored prompts
whose planted defects follow the skill's own taxonomy, which favours the skill
on K2–K4 to an unknown degree; one wording of the instruction. M7 coding was
blind to arm and run id, but the skill's report layout can reveal the arm.
