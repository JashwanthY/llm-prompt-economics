"""Study A extras beyond the pre-registered summary (final-review I10): from `runs/results_a.json`
plus the run artifacts on disk, compute descriptive numbers the reviewer asked to see published
alongside the headline metrics. Agents are never pooled (DESIGN.md §4.4); every table below is kept
per agent, per arm. Writes `runs/extras_a.json`.

1. M4 selectivity: per arm, the fraction of ambiguous planted lines (the same set M4 counts) that
   changed versus the fraction of all other non-blank lines that changed, and their ratio — does the
   skill concentrate its edits on the ambiguous lines it is supposed to flag, or does it edit broadly?
2. Word retention: mean of (words_after / words_before) per arm, using the word counts grade_a.py now
   records on every row.
3. Init-skills tally: for each arm, how many runs' turn-1 `meta.json` (the authoritative init list,
   captured at session start before any skill discovery race) listed `prompt-contract`, and the set
   difference between what the two arms saw.
"""
import json
from pathlib import Path

from frozen import HERE
from grade_a import AMBIGUOUS, RUNS, best_ratio
from validate_key import item_lines

PROMPTS = HERE / "prompts"


def _ambiguous_lines(key):
    return sorted({n for p in key["planted"] if p["category"] in AMBIGUOUS for n in item_lines(p)})


def _attempt_dir(row, runs):
    return Path(runs) / row["run_id"] / f"a{row['attempt']}"


def m4_selectivity(rows, runs=RUNS, prompts=PROMPTS):
    keys = {}
    out = {}
    for agent in sorted({r["agent"] for r in rows}):
        out[agent] = {}
        for arm in ("on", "off"):
            amb_changed = amb_total = other_changed = other_total = 0
            for r in (r for r in rows if r["agent"] == agent and r["arm"] == arm):
                pid = r["prompt_id"]
                if pid not in keys:
                    keys[pid] = json.loads((Path(prompts) / pid / "answer_key.json").read_text())
                key = keys[pid]
                att_dir = _attempt_dir(r, runs)
                before = (att_dir / "before.md").read_text(encoding="utf-8")
                end = (att_dir / ("after_t2.md" if r["turns"] == 2 else "after_t1.md")).read_text(encoding="utf-8")
                lines = before.splitlines()
                amb_nums = set(_ambiguous_lines(key))
                amb_total += len(amb_nums)
                amb_changed += sum(best_ratio(lines[n - 1], end) < 0.9 for n in amb_nums)
                other_nums = [i for i, l in enumerate(lines, 1) if l.strip() and i not in amb_nums]
                other_total += len(other_nums)
                other_changed += sum(best_ratio(lines[i - 1], end) < 0.9 for i in other_nums)
            amb_frac = amb_changed / amb_total if amb_total else None
            other_frac = other_changed / other_total if other_total else None
            ratio = amb_frac / other_frac if amb_frac is not None and other_frac else None
            out[agent][arm] = {
                "ambiguous_changed": amb_changed, "ambiguous_total": amb_total, "ambiguous_fraction": amb_frac,
                "other_changed": other_changed, "other_total": other_total, "other_fraction": other_frac,
                "ratio": ratio,
            }
    return out


def word_retention(rows):
    out = {}
    for agent in sorted({r["agent"] for r in rows}):
        out[agent] = {}
        for arm in ("on", "off"):
            arm_rows = [r for r in rows if r["agent"] == agent and r["arm"] == arm]
            ratios = [r["words_after"] / r["words_before"] for r in arm_rows
                      if r.get("words_before") and r.get("words_after") is not None]
            out[agent][arm] = {"mean_retention": sum(ratios) / len(ratios) if ratios else None, "n": len(ratios)}
    return out


def init_skills_tally(rows, runs=RUNS):
    out = {}
    for agent in sorted({r["agent"] for r in rows}):
        out[agent] = {}
        unions = {}
        for arm in ("on", "off"):
            arm_rows = [r for r in rows if r["agent"] == agent and r["arm"] == arm]
            n_with_data = n_with_pc = 0
            seen = set()
            for r in arm_rows:
                meta = json.loads((_attempt_dir(r, runs) / "meta.json").read_text())
                skills = meta["turn"][0].get("skills")
                if skills is None:
                    continue
                n_with_data += 1
                seen |= set(skills)
                if "prompt-contract" in skills:
                    n_with_pc += 1
            unions[arm] = seen
            out[agent][arm] = {"n_runs": len(arm_rows), "n_with_skills_data": n_with_data,
                                "n_with_prompt_contract": n_with_pc, "skills_seen": sorted(seen)}
        out[agent]["only_in_on"] = sorted(unions["on"] - unions["off"])
        out[agent]["only_in_off"] = sorted(unions["off"] - unions["on"])
    return out


def compute(rows, runs=RUNS, prompts=PROMPTS):
    return {
        "M4_selectivity": m4_selectivity(rows, runs, prompts),
        "word_retention": word_retention(rows),
        "init_skills": init_skills_tally(rows, runs),
    }


if __name__ == "__main__":
    results = json.loads((HERE / "runs" / "results_a.json").read_text())
    extras = compute(results["rows"])
    (HERE / "runs" / "extras_a.json").write_text(json.dumps(extras, indent=2) + "\n")
    print("wrote runs/extras_a.json")
