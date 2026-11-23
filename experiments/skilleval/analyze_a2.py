"""Study A2 (DESIGN_A2.md §5): replication R of H1-H4, and K1-K5 (skill content vs stop instruction).

Grades runs/A2 with Study A's grader unchanged, writes runs/results_a2.json and
runs/summary_a2.json. Fixed denominator of 12 per arm, as Study A.
Usage: python3 analyze_a2.py
"""
import itertools
import json
from math import comb

from analyze_a import summarize
from frozen import HERE
from grade_a import grade_all

N = 12


def fisher_greater(a, b, c, d):
    """One-sided Fisher exact p for [[a, b], [c, d]]: P(first-row yes count >= a)."""
    n1, n2, k = a + b, c + d, a + c
    total = comb(n1 + n2, k)
    return sum(comb(n1, x) * comb(n2, k - x) for x in range(a, min(k, n1) + 1)) / total


def perm_one_sided(xs, ys, direction):
    """Exact permutation p on the sum of xs among all equal-size splits of the pooled values.

    direction "greater": P(sum >= observed); "less": P(sum <= observed); "two": |mean diff| >= observed.
    """
    pool, k = list(xs) + list(ys), len(xs)
    obs, mean = sum(xs), sum(pool) / len(pool)
    hits = total = 0
    for idx in itertools.combinations(range(len(pool)), k):
        s = sum(pool[i] for i in idx)
        total += 1
        if direction == "greater":
            hits += s >= obs - 1e-9
        elif direction == "less":
            hits += s <= obs + 1e-9
        else:
            hits += abs(s / k - mean) >= abs(obs / k - mean) - 1e-9
    return hits / total


def holm(ps):
    order = sorted(ps, key=ps.get)
    adj, running = {}, 0.0
    for i, name in enumerate(order):
        running = max(running, min(1.0, (len(order) - i) * ps[name]))
        adj[name] = running
    return adj


def main():
    graded = grade_all(runs=HERE / "runs" / "A2", codes_path=HERE / "runs" / "codes_m7_a2.json")
    (HERE / "runs" / "results_a2.json").write_text(json.dumps(graded, indent=2) + "\n")
    rows = graded["rows"]
    arm = {a: [r for r in rows if r["arm"] == a] for a in ("off", "on", "instr")}
    yes = lambda rs, m: sum(bool(r[m]) for r in rs)  # noqa: E731

    rep = summarize([r for r in rows if r["arm"] in ("on", "off")])["claude"]
    on, ins = arm["on"], arm["instr"]
    p = {
        "K2": fisher_greater(yes(on, "M2_traps_intact"), N - yes(on, "M2_traps_intact"),
                             yes(ins, "M2_traps_intact"), N - yes(ins, "M2_traps_intact")),
        "K3": fisher_greater(yes(on, "M5_guard_added"), N - yes(on, "M5_guard_added"),
                             yes(ins, "M5_guard_added"), N - yes(ins, "M5_guard_added")),
        "K4": perm_one_sided([r["M3_dead_weight_removed"] for r in on],
                             [r["M3_dead_weight_removed"] for r in ins], "greater"),
        "K5": perm_one_sided([r["M4_unilateral_changes"] for r in on],
                             [r["M4_unilateral_changes"] for r in ins], "less"),
    }
    adj = holm(p)
    direction = {
        "K2": yes(on, "M2_traps_intact") > yes(ins, "M2_traps_intact"),
        "K3": yes(on, "M5_guard_added") > yes(ins, "M5_guard_added"),
        "K4": sum(r["M3_dead_weight_removed"] for r in on) > sum(r["M3_dead_weight_removed"] for r in ins),
        "K5": sum(r["M4_unilateral_changes"] for r in on) < sum(r["M4_unilateral_changes"] for r in ins),
    }
    per_arm = {a: {"n": len(rs), "M1_gate": yes(rs, "M1_gate"), "M2_traps_intact": yes(rs, "M2_traps_intact"),
                   "M3_mean": round(sum(r["M3_dead_weight_removed"] for r in rs) / max(len(rs), 1), 3),
                   "M4_total": sum(r["M4_unilateral_changes"] for r in rs),
                   "M5_guard_added": yes(rs, "M5_guard_added"),
                   "M6_mean": round(sum(r["M6_lines_cited"] for r in rs) / max(len(rs), 1), 2),
                   "M7_mean": (round(sum(r["M7_questions_asked"] for r in rs) / len(rs), 2)
                               if rs and all("M7_questions_asked" in r for r in rs) else None),
                   "skill_invoked": sum(bool(r["skill_invoked"]) for r in rs),
                   "M8_output_tokens_mean": round(sum(r["M8_output_tokens"] for r in rs) / max(len(rs), 1)),
                   "M8_secs_mean": round(sum(r["M8_secs"] for r in rs) / max(len(rs), 1), 1),
                   "M8_cost_usd_mean": (round(sum(r["M8_cost_usd"] for r in rs) / len(rs), 4)
                                        if rs and all(r["M8_cost_usd"] is not None for r in rs) else None)}
               for a, rs in arm.items()}
    summary = {
        "failed_runs": graded["failed_runs"],
        "complete": all(len(rs) == N for rs in arm.values()),
        "per_arm": per_arm,
        "R_replication": {"hypotheses": rep["hypotheses"], "M1_fisher_p": rep["M1_gate"]["fisher_p"],
                          "M2_fisher_p": rep["M2_traps_intact"]["fisher_p"],
                          "M4_perm_p": rep["M4_unilateral_changes"]["perm_p"]},
        "K1_instr_holds_gate": yes(ins, "M1_gate") >= 11,
        "K": {k: {"p_one_sided": round(p[k], 6), "p_holm": round(adj[k], 6), "direction_as_predicted": direction[k],
                  "supported": direction[k] and adj[k] < 0.05} for k in p},
        "cost_on_vs_instr_perm_p_two_sided": round(perm_one_sided([r["M8_output_tokens"] for r in on],
                                                                  [r["M8_output_tokens"] for r in ins], "two"), 6),
    }
    summary["content_adds_value"] = any(v["supported"] for v in summary["K"].values())
    (HERE / "runs" / "summary_a2.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
