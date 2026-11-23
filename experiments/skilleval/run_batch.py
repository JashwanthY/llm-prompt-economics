"""Run pending Study A sessions in schedule order, up to --limit, resumably.

A run is finished when one attempt is "ok" or two attempts errored. A rate limit
stops the batch without recording an attempt, so rerunning resumes the order.
"""
import argparse
import json

from frozen import HERE, assert_frozen
from probe import check_isolation
from runner import RateLimited, RunSpec, run_session
from schedule import make_schedule, make_schedule_a2

RUNS = HERE / "runs"
PROMPTS = HERE / "prompts"


def attempts(run_id, study="A", root=RUNS):
    d = root / study / run_id
    return [json.loads(m.read_text()) for m in sorted(d.glob("a*/meta.json"))] if d.exists() else []


def is_finished(run_id, study="A", root=RUNS):
    done = attempts(run_id, study, root)
    return any(m["status"] == "ok" for m in done) or len(done) >= 2


def main(limit, agent=None, study="A"):
    frozen = assert_frozen()
    model, effort = frozen["codex_model"], frozen["codex_reasoning_effort"]
    RUNS.mkdir(exist_ok=True)
    if study == "A2":  # DESIGN_A2.md: Claude Code only
        agent = "claude"
    probe_agents = (agent,) if agent else ("claude", "codex")
    if not check_isolation(model, RUNS / "probes.jsonl", effort, agents=probe_agents):
        print("isolation probe failed -- see runs/probes.jsonl; nothing was run")
        return 3
    schedule = make_schedule_a2() if study == "A2" else make_schedule()
    ran = 0
    for run in schedule:
        if ran >= limit:
            break
        if (agent and run["agent"] != agent) or is_finished(run["run_id"], study):
            continue
        spec = RunSpec(**run)
        attempt = len(attempts(spec.run_id, study)) + 1
        try:
            meta = run_session(spec, PROMPTS / spec.prompt_id, RUNS, model, effort, attempt)
        except RateLimited as e:
            print(f"rate limited at {spec.run_id}: {e} -- stopped; rerun later to resume")
            return 2
        print(f"{spec.run_id} a{attempt}: {meta['status']} gate={meta['gate_unchanged']} turns={meta['turns']} "
              f"out={sum(t['output_tokens'] for t in meta['turn'])} {meta['errors'] or ''}")
        ran += 1
    left = sum(not is_finished(r["run_id"], study) for r in schedule)
    print(f"{ran} session(s) this batch; {left} of {len(schedule)} still pending")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--limit", type=int, default=4)
    ap.add_argument("--agent", choices=["claude", "codex"])
    ap.add_argument("--study", choices=["A", "A2"], default="A")
    a = ap.parse_args()
    raise SystemExit(main(a.limit, a.agent, a.study))
