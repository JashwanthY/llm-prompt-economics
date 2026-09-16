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

**This repo ships `prompt-contract`** — an agent skill that reviews your prompt
against these findings, reports what to cut, sharpen or keep with line numbers
and counts, and changes nothing until you approve.

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

Copy `skills/prompt-contract/SKILL.md` into a `prompt-contract` folder in your
agent's skills directory:

| agent | folder |
|---|---|
| Claude Code | `~/.claude/skills/prompt-contract/` |
| Cursor, Codex | `~/.agents/skills/prompt-contract/` |

It is one Markdown file with YAML frontmatter, so any agent that reads skills can
follow it. I have not verified Cursor or Codex loading it myself — an issue
reporting whether it worked is welcome.

</details>

---

## What the skill does

Point your agent at a prompt and it:

1. **Sorts every line** into contract (facts the model could not guess), work
   orders (requests for more output) and restrictions (requests for less).
2. **Finds the problems** — duplicates, conflicts with no rule for which wins,
   vague rules, shouting in place of precision, web or file input with no guard,
   work orders nobody needs.
3. **Reports** in a fixed format: counts and shares, then each finding with its
   line number, why it matters (citing the study's numbers) and the exact
   proposed change, then the questions only you can answer.
4. **Stops.** Nothing changes until you reply *"apply all"*, *"apply 1, 3"* or
   *"skip"*.
5. **Applies what you approved**, and offers an optional check run of your real
   task on the old and new prompt to measure the difference.

The skill is instructions only — one `SKILL.md`, no scripts. The review costs
nothing beyond your agent reading the prompt; the check run costs a few runs of
your task, and it asks first.

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
