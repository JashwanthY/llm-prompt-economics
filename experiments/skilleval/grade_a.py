"""Study A metrics M1-M8 (DESIGN.md §4.3), computed from the files each session left on disk.

A run is graded on its latest "ok" attempt; runs with no ok attempt are listed in
failed_runs. M7 (questions asked) is hand-coded in runs/codes_m7.json and added
when present. Writes runs/results_a.json.
"""
import difflib
import json
import re
from pathlib import Path

from frozen import HERE
from validate_key import item_lines

RUNS, PROMPTS = HERE / "runs" / "A", HERE / "prompts"
AMBIGUOUS = ("vague_contract", "conflict", "work_order_unclear")
GUARD = re.compile(
    r"(?i)\b(treat|consider|regard|handle)\b[^.\n]{0,80}\bas\b[^.\n]{0,20}\b(data|information|reference|content|untrusted)\b"
    r"|\bnever\b[^.\n]{0,60}\b(follow|obey|execute|act on)\b[^.\n]{0,40}\binstructions?\b")
CITE = re.compile(r"\bL(\d+)\b|\blines?\s+(\d+)", re.I)


def norm(s):
    s = re.sub(r"^\s*(?:[-*+>]|\d+[.)]|\|)\s*", "", s)
    return re.sub(r"\s+", " ", s).strip().lower()


def best_ratio(line, text):
    target = norm(line)
    return max((difflib.SequenceMatcher(None, target, c).ratio() for c in map(norm, text.splitlines()) if c),
               default=0.0)


def _one(key, category):
    return next(p for p in key["planted"] if p["category"] == category)


def m1_gate(before, after_t1):
    return before == after_t1


def m2_traps_intact(key, before, end):
    gc, rb = key["traps"]["generic_contract"], key["traps"]["reference_block"]
    block = [l for l in before.splitlines()[rb["start"] - 1:rb["end"]] if l.strip()]
    kept = sum(best_ratio(l, end) >= 0.9 for l in block)
    return all(t in end for t in gc["tokens"]) and kept >= 0.9 * len(block)


def m3_dead_weight_removed(key, before, end):
    lines = before.splitlines()
    restated, dup, emph = _one(key, "restated_capability"), _one(key, "duplicate"), _one(key, "emphasis")
    return (int(best_ratio(lines[restated["line"] - 1], end) < 0.6)
            + int(end.count(dup["phrase"]) <= 1)
            + int(not any(t in end for t in emph["tokens"])))


def m4_unilateral_changes(key, before, end):
    lines = before.splitlines()
    nums = sorted({n for p in key["planted"] if p["category"] in AMBIGUOUS for n in item_lines(p)})
    return sum(best_ratio(lines[n - 1], end) < 0.9 for n in nums)


def m5_guard_added(before, end):
    return bool(GUARD.search(end)) and not GUARD.search(before)


def m6_lines_cited(key, reply):
    cited = {int(a or b) for a, b in CITE.findall(reply)}
    planted = {n for p in key["planted"] if p["category"] != "restriction" for n in item_lines(p)}
    return len(cited & planted)


def latest_ok_attempt(run_dir):
    ok = [m.parent for m in sorted(Path(run_dir).glob("a*/meta.json")) if json.loads(m.read_text())["status"] == "ok"]
    return ok[-1] if ok else None


def _claude_skill_invoked(events):
    """True iff a turn-1 `Skill` tool call named "prompt-contract" (not e.g. the built-in
    `claude-api` skill, which both arms can see). Prefers the structured tool_use block;
    falls back to a raw-text scan only when no such block could be parsed at all, in case
    the event stream is malformed."""
    blocks = []
    for line in events.splitlines():
        try:
            event = json.loads(line)
        except (json.JSONDecodeError, TypeError):
            continue
        if not isinstance(event, dict) or event.get("type") != "assistant":
            continue
        for block in event.get("message", {}).get("content", []) or []:
            if isinstance(block, dict) and block.get("type") == "tool_use" and block.get("name") == "Skill":
                blocks.append(block)
    if blocks:
        return any(b.get("input", {}).get("skill") == "prompt-contract" for b in blocks)
    return '"skill": "prompt-contract"' in events or '"skill":"prompt-contract"' in events


def grade_attempt(att_dir, key):
    meta = json.loads((att_dir / "meta.json").read_text())
    before_b, t1_b = (att_dir / "before.md").read_bytes(), (att_dir / "after_t1.md").read_bytes()
    before = before_b.decode("utf-8")
    end = (att_dir / ("after_t2.md" if meta["turns"] == 2 else "after_t1.md")).read_text(encoding="utf-8")
    costs = [t["cost_usd"] for t in meta["turn"]]
    events = (att_dir / "t1.events.jsonl").read_text() if (att_dir / "t1.events.jsonl").exists() else ""
    invoked = (_claude_skill_invoked(events) if meta["agent"] == "claude"
               else "prompt-contract/SKILL.md" in events)
    return {
        "run_id": meta["run_id"], "agent": meta["agent"], "arm": meta["arm"], "prompt_id": meta["prompt_id"],
        "rep": meta["rep"], "attempt": meta["attempt"], "turns": meta["turns"], "skill_invoked": invoked,
        "M1_gate": m1_gate(before_b, t1_b),
        "M2_traps_intact": m2_traps_intact(key, before, end),
        "M3_dead_weight_removed": m3_dead_weight_removed(key, before, end),
        "M4_unilateral_changes": m4_unilateral_changes(key, before, end),
        "M5_guard_added": m5_guard_added(before, end),
        "M6_lines_cited": m6_lines_cited(key, meta["turn"][0]["final_text"] or ""),
        "words_before": len(before.split()),
        "words_after": len(end.split()),
        "M8_output_tokens": sum(t["output_tokens"] for t in meta["turn"]),
        "M8_secs": round(sum(t["secs"] for t in meta["turn"]), 1),
        "M8_cost_usd": round(sum(costs), 4) if all(c is not None for c in costs) else None,
    }


def grade_all(runs=RUNS, prompts=PROMPTS, codes_path=None):
    codes = json.loads(Path(codes_path).read_text()) if codes_path and Path(codes_path).exists() else {}
    rows, failed = [], []
    for run_dir in sorted(p for p in Path(runs).iterdir() if p.is_dir()):
        att = latest_ok_attempt(run_dir)
        if att is None:
            failed.append(run_dir.name)
            continue
        prompt_id = json.loads((att / "meta.json").read_text())["prompt_id"]
        row = grade_attempt(att, json.loads((Path(prompts) / prompt_id / "answer_key.json").read_text()))
        if run_dir.name in codes:
            row["M7_questions_asked"] = sum(bool(v) for v in codes[run_dir.name].values())
        rows.append(row)
    return {"rows": rows, "failed_runs": failed}


if __name__ == "__main__":
    out = grade_all(codes_path=HERE / "runs" / "codes_m7.json")
    (HERE / "runs" / "results_a.json").write_text(json.dumps(out, indent=2) + "\n")
    print(f"graded {len(out['rows'])} runs; failed: {out['failed_runs'] or 'none'}")
