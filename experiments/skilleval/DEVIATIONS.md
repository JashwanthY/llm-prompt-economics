# Deviations from DESIGN.md

Every change to the pre-registered design, with its reason. Nothing here changes
a hypothesis, metric or pass criterion unless it says so.

## Pre-run technical corrections — before any Study A data

- **2026-09-17 — Claude Code tool restriction.** DESIGN.md §3 shows
  `--allowedTools Read Edit Write Glob Grep`. That flag pre-approves tools without
  removing the others; `--tools` sets the available set, which is what §3 describes
  ("Claude Code gets file tools only"). The set also includes `Skill`, the tool
  through which Claude Code loads any skill — without it the skill arm could not use
  the skill at all. Both arms get the same set:
  `--tools Read Edit Write Glob Grep Skill`.
- **2026-09-17 — Manipulation check added (descriptive).** For every run the grader
  records whether the agent actually opened the skill (Claude Code: a `Skill` tool
  call; Codex: a read of `prompt-contract/SKILL.md` in its events). It changes no
  hypothesis; a skill-arm run that never opened the skill is reported, not dropped.
- **2026-09-17 — Codex isolation by not loading the user's config.** DESIGN.md §3
  isolates Codex by disabling each personal skill and each MCP server in the user's
  config. The dry-run canary showed that leaves MCP tools from the user's
  desktop-app plugins (`[plugins.*]`, e.g. `mcp__cua_repl.js`) reaching the session.
  Codex now runs with `--ignore-user-config` (auth still from `CODEX_HOME`), so no
  user config — MCP servers, plugins, model or other settings — is loaded; personal
  skills, which are discovered from directories rather than config, stay disabled
  per run. The rerun canary then showed the account-connected apps server
  `codex_apps`, which is not config-sourced; Codex also runs with `--disable apps`.
  The canary and skills probe were rerun and passed.
- **2026-09-17 — Codex's bundled skills count as shipped.** The isolation probe
  treats Codex's bundled skills in `~/.codex/skills/.system/` the way it treats
  Claude Code's built-in skills: present in both arms, not a leak. The first
  dry-run probe flagged `imagegen` because a disabled personal copy shares its name
  with the bundled one. Limitation: a personal skill with the same name as a
  bundled skill cannot be told apart by the probe, which compares names.
- **2026-09-17 — Both agents run at their shipped default reasoning effort.**
  DESIGN.md §2 pins the Codex model; the dry-run session showed Codex's shipped
  model under isolation is `gpt-6-astra` with no reasoning-effort setting
  (`reasoning_effort: null` in its session log), so no effort override is passed —
  as for Claude Code, which also runs at its default. `frozen.json` records the
  effort as null. Reasoning tokens are logged per run, so a change in the
  server-side default during the study would be visible.
- **2026-09-17 — How the model id is logged per run.** Codex's `exec --json`
  stream carries no model field, so the runner reads the model that served each
  Codex turn from Codex's own session log for that thread (`~/.codex/sessions`),
  and every turn also records the requested model (`-m` for Codex, `sonnet` for
  Claude Code). Claude Code's served model comes from its event stream. The
  dry-run metas committed before this change show `model: null` for Codex; the
  lookup was checked against their session log and returns `gpt-6-astra`.
- **2026-09-17 — Lost runs count against the hypotheses.** §4.4 gives thresholds out
  of 12. A run lost to two infrastructure failures is counted as not meeting the
  criterion (fixed denominator of 12), the conservative reading.
- **2026-09-17 — The generic-contract trap must conceal a real identifier.** DESIGN.md §4.1 asks each prompt for a trap line "naming facts only this product has… phrased in generic-sounding words". P2's first version named no identifier, so an auditor flagging it as vague would have been correct while the trap metric counted it as damage. `validate_key.py` now requires at least one identifier-shaped token in the trap, `brief.md` states the requirement, and P2 was re-authored under that brief. P1, P3 and P4 were authored before the sentence was added and pass the tightened check unchanged. The accepted shapes are `snake_case`, `camelCase`, an ALLCAPS code, a path, a file name, or a value containing digits; hyphenated words are not accepted, because ordinary English hyphenation is indistinguishable from kebab-case identifiers.
- **2026-09-17 — Study A ran in two windows.** A Codex subscription usage limit was reached after 11 of 48 runs. Claude Code's 24 runs were completed on 2026-09-17; Codex's remaining 19 runs were never run. Arms stay strictly alternating within each agent and no primary claim pools agents (DESIGN.md §4.4); the between-agent time gap is therefore a confound only for agent-to-agent comparison, which the design does not make.
- **2026-09-17 — Study A analysed with the Codex arm incomplete.** The Codex subscription limit left 19 of its 24 runs unrun at analysis time. Claude Code's 24 runs are complete and its hypotheses are evaluated as pre-registered; Codex's 5 finished runs are graded and published, but its arms are marked incomplete and its hypotheses are not evaluated. Codex remains resumable in schedule order.
- **2026-09-17 — Study A is a single-agent evaluation.** After the Codex usage limit, the author chose not to complete the Codex arm. Study A's claims rest on Claude Code's 24 runs; Codex's 5 finished runs are published as raw data and excluded from every claim, its arms marked incomplete and its hypotheses not evaluated.
- **2026-09-17 — DESIGN.md §7's `verify_paper.py` extension is deferred.** DESIGN.md §7 calls for extending `experiments/verify_paper.py` to re-derive Study A's numbers from the committed run artifacts. That extension is not implemented in this worktree; it is deferred to the paper-writing stage, which is also when `verify_paper.py` next runs in full (Ruling R2).
- **2026-09-17 — Manipulation check corrected: skill name, not any Skill call.** The grader originally set `skill_invoked` true for Claude whenever any `Skill` tool call occurred in turn 1. In all 12 off-arm (no-skill) Claude runs, that call was Claude Code's built-in `claude-api` skill, not `prompt-contract` — `summary_a.json` published `skill_invoked.off = 12`, which would have read as the manipulation check failing completely. `grade_a.py::grade_attempt` now parses the turn-1 `Skill` tool_use block's `input.skill` and requires it to equal `prompt-contract` (falling back to a raw-text scan only if no structured block parses). `results_a.json` and `summary_a.json` were regenerated after this fix; corrected counts are `skill_invoked`: claude on 12, off 0. M1-M4 headline numbers are unaffected — `skill_invoked` is a descriptive manipulation check, not an input to any metric or hypothesis.
- **2026-09-17 — The off-arm baseline is not a bare agent.** Every run in both arms — on and off — had Claude Code's built-in `claude-api` skill available and loaded it in all 12 off-arm runs (see the manipulation-check correction above). Both arms therefore differ only in whether `prompt-contract` was present; the off arm is "Claude Code with its shipped built-in skills" rather than a skill-free baseline.
- **2026-09-17 — Usernames redacted from published transcripts.** Claude Code writes absolute paths into its event stream, so the committed run transcripts contained the author's macOS username. Every occurrence of the author's username in `experiments/skilleval/runs/`, `tests/fixtures/` and the two authoring transcripts under `prompts/` (44 files) was replaced with `<user>`, including one non-path occurrence inside captured shell output; `prompt.md` and `answer_key.json` were not touched, so the hashes recorded in `frozen.json` still match. Nothing else in those files changed, and regrading after the substitution reproduces `results_a.json`, `summary_a.json` and `extras_a.json` byte for byte.
