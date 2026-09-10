# Instruction Economics in LLM System Prompts

If you ship anything on an LLM — a product feature, an internal tool, a coding
agent — you maintain a system prompt, and it has filled up with generic advice:
*write semantic markup, handle the empty case, name your constants*. It does not
matter whether that text lives in your application code, a vendor system prompt,
an agent skill or a `CLAUDE.md`. The same question applies: **is any of it doing
anything?**

We measured it across **198 runs** on two frontier models. Each generic line
turns out to be doing one of three things, and reading it will not tell you
which: the model already does it anyway, the model ignores it anyway, or that
line is the only reason you get the behaviour at all. Two are dead weight. One
is a feature you are paying for.

**This repo ships `prompt-contract`** — an agent skill that runs that check on
your prompt, on your model, and tells you which lines to cut and what cutting
them saves.

![How it works](docs/how-it-works.png)

## Install

```
/plugin marketplace add JashwanthY/llm-prompt-economics
/plugin install prompt-contract@llm-prompt-economics
```

Then ask your agent:

> *"My system prompt is getting long — which lines are actually doing anything?"*

<details>
<summary>Manual install, or other agents</summary>

Copy `skills/prompt-contract/` into `~/.claude/skills/` (all projects) or
`.claude/skills/` (one project).

`SKILL.md` is plain Markdown with YAML frontmatter and the scripts are
dependency-free Python, so any agent that reads a skill file can follow it. I
have not verified Codex or Cursor myself — an issue reporting whether it worked
is welcome.

</details>

---

## What the skill does

Given your prompt and a command that runs your real task, it:

1. **Classifies** every line — guidance, restriction, or *unrecognised*.
   Unrecognised lines are usually your project's contract and are never proposed
   for deletion.
2. **Runs your task without the generic guidance**, keeping the contract intact.
3. **Attributes a verdict** to each directive by comparing what the model
   produced in each arm.
4. **Proposes a trim** of dead weight only.
5. **Measures** original against trimmed — output tokens, latency, artifact size.
6. **Reports** what was removed, what was kept *and which feature each kept line
   buys*, what it could not judge, and the measured saving.

It never deletes anything itself. A line that survives is a feature you are
buying, and whether to keep buying it is your call, not a tool's.

The cheapest useful run needs one execution of your own task without the
guidance — about **$0.15** for a single-artifact task.

## What the study found

| | |
|---|---|
| **Generic guidance is not redundant** | one accessibility feature appeared in **0 of 12** generated files when unmentioned and **12 of 12** when asked for |
| **It is billed at the output** | 811 words cost **+42% output tokens** and **+38% latency**; 73% of the added spend lands where prompt caching cannot reach |
| **Length is the wrong variable** | at matched length, 75 words asking the model to *do* cost **+22%**; 79 words asking it to *withhold* saved **31%** |
| **Scale behaves differently** | 4,746 added words that mostly *describe* rather than *request* cost only **+4%** |
| **Correctness did not move** | on a pipeline whose positive control drops 26 points when one needed parameter is removed |

Method, full results and limitations: [`paper-bloat/main.pdf`](paper-bloat/main.pdf).

## Verify it yourself

Every number in the paper is recomputed from the raw run logs by one offline
script — no API key, no model call:

```bash
pip install -r requirements.txt && npm install jsdom
python3 experiments/verify_paper.py
```

It exits non-zero on any mismatch. All 198 run logs, every experiment design,
the graders and the reference implementations are in
[`experiments/`](experiments/), which is what makes the paper checkable rather
than merely readable.

Re-running the experiments themselves needs `OPENAI_API_KEY`, or
`OPENAI_ENV_FILE` pointing at a `.env` containing one. API nondeterminism means
fresh runs differ in detail; the shipped logs are the record.

## Licence

Code MIT, paper and figures CC BY 4.0. See [LICENSE](LICENSE) and
[CITATION.cff](CITATION.cff).
