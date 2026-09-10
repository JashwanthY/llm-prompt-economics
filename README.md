# Instruction Economics in Agent System Prompts

Your `CLAUDE.md` is full of generic advice — *write semantic markup, handle the
empty case, name your constants*. Is any of it doing anything?

We measured it across **198 runs** on two frontier models:

- **The model doesn't do it unprompted.** One accessibility feature appeared in
  **0 of 12** files when unmentioned, **12 of 12** when asked for.
- **It isn't free.** 811 words of guidance cost **+42% output tokens** and
  **+38% latency**, mostly on the side prompt caching can't help with.
- **It doesn't make the model worse.** Correctness held on every test.

So each generic line is doing one of three things, and **reading it won't tell
you which**: the model already does it, the model ignores it, or that line is
the only reason you get the behaviour. Two are dead weight. One is a feature
you're paying for.

This repo has the measurements — and a skill that runs the same check on **your**
prompt.

![How it works](docs/how-it-works.png)

## Install

```
/plugin marketplace add JashwanthY/instruction-economics
/plugin install prompt-contract@instruction-economics
```

Then just ask:

> *"My CLAUDE.md is getting long — which lines are actually doing anything?"*

<details>
<summary>Other agents, or manual install</summary>

Copy `skills/prompt-contract/` into `~/.claude/skills/` (all projects) or
`.claude/skills/` (one project).

`SKILL.md` is plain Markdown and the scripts are dependency-free Python, so any
agent that reads a skill file can follow it. I haven't verified Codex or Cursor
myself — if you try one, an issue saying whether it worked is welcome.

</details>

## What the skill does

Runs your task once **without** the generic guidance, compares it to a run with,
and tells you which lines to cut and what cutting them saves in tokens and
latency.

It never deletes anything. A line that survives is a feature you're buying, and
that call is yours.

## The paper

[`paper-bloat/main.pdf`](paper-bloat/main.pdf) — method, full results,
limitations.

Every number in it is recomputed from the raw logs by one offline script:

```bash
pip install -r requirements.txt && npm install jsdom
python3 experiments/verify_paper.py
```

No API key needed. All 198 run logs are in [`experiments/`](experiments/), which
is what makes the paper checkable rather than just readable.

## Licence

Code MIT, paper CC BY 4.0.
