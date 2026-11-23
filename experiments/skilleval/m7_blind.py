"""Blind M7 coding for Study A2 (DESIGN_A2.md §4): the coder never sees arm or run id.

  build  writes runs/m7_a2/packet/R01.md … (numbered prompt, ambiguous lines to code,
         the turn-1 reply) in a seeded shuffled order, and runs/m7_a2/key.json
         ({opaque id: run_id}) which the coder must not open.
  merge  reads the coder's runs/m7_a2/coded/R??.json ({"<line>": true|false}) and writes
         runs/codes_m7_a2.json in Study A's format ({run_id: {"<line>": bool}}).

Arm can still leak through the reply's form (the skill's report layout); this is
reported as a limitation, not hidden.
Usage: python3 m7_blind.py build | merge
"""
import json
import random
import sys

from frozen import HERE
from grade_a import AMBIGUOUS, latest_ok_attempt
from validate_key import item_lines

RUNS, PROMPTS = HERE / "runs" / "A2", HERE / "prompts"
OUT = HERE / "runs" / "m7_a2"


def ambiguous_lines(key):
    return sorted({n for item in key["planted"] if item["category"] in AMBIGUOUS for n in item_lines(item)})


def build(seed=18):
    runs = sorted(p for p in RUNS.iterdir() if p.is_dir() and latest_ok_attempt(p))
    random.Random(seed).shuffle(runs)
    (OUT / "packet").mkdir(parents=True, exist_ok=True)
    key = {}
    for i, run in enumerate(runs, 1):
        rid = f"R{i:02d}"
        meta = json.loads((latest_ok_attempt(run) / "meta.json").read_text())
        answer = json.loads((PROMPTS / meta["prompt_id"] / "answer_key.json").read_text())
        prompt = (PROMPTS / meta["prompt_id"] / "prompt.md").read_text().splitlines()
        lines = ambiguous_lines(answer)
        body = [f"# {rid}", "", "## The system prompt under review (numbered)", "", "```"]
        body += [f"{n:>3}  {t}" for n, t in enumerate(prompt, 1)]
        body += ["```", "", "## Lines to code", ""]
        body += [f"- L{n}: {prompt[n - 1].strip()}" for n in lines]
        body += ["", "## The reviewer's reply", "", meta["turn"][0]["final_text"] or "(empty reply)", ""]
        (OUT / "packet" / f"{rid}.md").write_text("\n".join(body))
        key[rid] = run.name
    (OUT / "key.json").write_text(json.dumps(key, indent=1) + "\n")
    print(f"{len(key)} packets")


def merge():
    key = json.loads((OUT / "key.json").read_text())
    codes = {}
    for rid, run_id in sorted(key.items()):
        codes[run_id] = json.loads((OUT / "coded" / f"{rid}.json").read_text())
    (HERE / "runs" / "codes_m7_a2.json").write_text(json.dumps(codes, indent=1) + "\n")
    print(f"merged {len(codes)} runs")


if __name__ == "__main__":
    {"build": build, "merge": merge}[sys.argv[1]]()
