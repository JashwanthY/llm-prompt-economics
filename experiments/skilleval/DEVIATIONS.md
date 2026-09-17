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
- **2026-09-17 — Lost runs count against the hypotheses.** §4.4 gives thresholds out
  of 12. A run lost to two infrastructure failures is counted as not meeting the
  criterion (fixed denominator of 12), the conservative reading.
