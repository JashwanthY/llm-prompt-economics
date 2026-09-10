# Instruction Economics in Agent System Prompts

**A generic line in a system prompt is not a reminder — it is a work order, and
you are billed for it at the output.**

Agent system prompts accumulate general engineering guidance alongside the
project-specific facts a model cannot infer. This repository measures what that
general material costs and what it buys, across **198 runs** on two frontier
models, and releases the method as a tool you can point at your own prompt.

| | |
|---|---|
| **Paper** | [`paper-bloat/main.pdf`](paper-bloat/main.pdf) — source in [`preprint.md`](paper-bloat/preprint.md) |
| **Tool** | [`skills/prompt-contract/`](skills/prompt-contract/) — installable agent skill |
| **Data** | [`experiments/`](experiments/) — every design, run log and grader |
| **Check** | `python3 experiments/verify_paper.py` — re-derives every number, offline |

## What the study found

**Generic guidance is not redundant.** The model does not apply it unprompted. A
`prefers-reduced-motion` query appears in **0 of 12** artifacts when unmentioned
and **12 of 12** when asked for. Other conventions appear regardless, and some
requests are ignored however firmly made — and you cannot tell which is which by
reading the line.

**Most of the bill arrives at the output.** 811 words of input guidance produce
**+42% output tokens** and **+38% latency**, rising in all twelve paired cells.
Output is priced around eight times input and is not reduced by prompt caching,
so 73% of the added spend lands where caching cannot reach.

**Length is the wrong variable.** At matched length, 75 words asking the model to
*do* cost **+22%** output while 79 words asking it to *withhold* saved **31%** —
a 53-point swing, both arms fully correct. At skill scale, 4,746 added words that
are mostly templates and specification cost only **+4%**.

**Correctness does not move**, on a pipeline whose positive control registers a
26-point drop when a single needed parameter is removed.

## The tool

[`skills/prompt-contract`](skills/prompt-contract/) packages the method. Point it
at your prompt and a command that runs your real task, and it classifies every
line, runs the task without the generic guidance, attributes a verdict to each
directive, proposes a trim of dead weight only, measures original against
trimmed, and reports what changed and what it saved.

It never deletes: a line that survives attribution is a feature you are buying,
and whether to keep buying it is your call.

## Reproducing

```bash
pip install -r requirements.txt
npm install jsdom                      # the behavioural graders run in Node

python3 experiments/verify_paper.py    # offline; re-derives every claim
python3 paper-bloat/build.py           # regenerate main.tex
tectonic paper-bloat/main.tex
```

Re-running the experiments themselves needs an API key in `OPENAI_API_KEY`, or
`OPENAI_ENV_FILE` pointing at a `.env` that contains one. API nondeterminism
means runs are not seed-reproducible, which is why the complete logs are
included — every number in the paper can be checked without a model call.

The paper builds for several venues from one source:

```bash
python3 paper-bloat/build.py --venue ieee     # or acm, neurips, iclr
```

See [`paper-bloat/README.md`](paper-bloat/README.md) for what that does and does
not solve.

## Licence

Code under MIT, paper text and figures under CC BY 4.0. See [LICENSE](LICENSE)
and [CITATION.cff](CITATION.cff).
