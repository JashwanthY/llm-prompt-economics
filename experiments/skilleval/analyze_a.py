"""Study A hypotheses H1-H4 (DESIGN.md §4.4) from runs/results_a.json. Agents are never pooled.

Thresholds use a fixed denominator of 12 per agent and arm, so a run lost to two
infrastructure failures counts against the hypothesis (DEVIATIONS.md). Writes
runs/summary_a.json.
"""
import collections
import json
from math import comb

from frozen import HERE


def fisher_two_sided(a, b, c, d):
    """Two-sided Fisher's exact test for [[a, b], [c, d]] (rows: arms; columns: yes, no)."""
    n1, n2, k = a + b, c + d, a + c
    total = comb(n1 + n2, k)

    def p(x):
        return comb(n1, x) * comb(n2, k - x) / total

    observed = p(a)
    return min(1.0, sum(p(x) for x in range(max(0, k - n2), min(k, n1) + 1) if p(x) <= observed * (1 + 1e-9)))


def perm_test_sum(xs, ys):
    """Exact two-sided permutation test on the difference in means of small non-negative integers.

    Counts, over every way of choosing len(xs) of the pooled values, the subsets whose
    mean is at least as far from the pooled mean as xs's is, using the distribution of
    subset sums rather than enumerating subsets.
    """
    pool, k = list(xs) + list(ys), len(xs)
    ways = [collections.Counter() for _ in range(k + 1)]
    ways[0][0] = 1
    for v in pool:
        for j in range(k, 0, -1):
            for s, c in list(ways[j - 1].items()):
                ways[j][s + v] += c
    mean = sum(pool) / len(pool)
    observed = abs(sum(xs) / k - mean)
    extreme = sum(c for s, c in ways[k].items() if abs(s / k - mean) >= observed - 1e-12)
    return extreme / comb(len(pool), k)


INCOMPLETE_NOTE = ("incomplete arm: hypotheses not evaluated; finished runs are not balanced across "
                    "prompts, so the on/off comparison is prompt-confounded")


def summarize(rows, n_per_arm=12):
    out = {}
    for agent in sorted({r["agent"] for r in rows}):
        on = [r for r in rows if r["agent"] == agent and r["arm"] == "on"]
        off = [r for r in rows if r["agent"] == agent and r["arm"] == "off"]

        def yes(rs, m):
            return sum(bool(r[m]) for r in rs)

        def binary(m):
            y_on, y_off = yes(on, m), yes(off, m)
            return {"on": y_on, "off": y_off, "n_on": len(on), "n_off": len(off),
                    "fisher_p": fisher_two_sided(y_on, len(on) - y_on, y_off, len(off) - y_off)}

        def mean_of(rs, key):
            vals = [r[key] for r in rs if key in r and r[key] is not None]
            return sum(vals) / len(vals) if vals else None

        def cost_mean(rs):
            if not rs or any(r.get("M8_cost_usd") is None for r in rs):
                return None
            return sum(r["M8_cost_usd"] for r in rs) / len(rs)

        m3_on, m3_off = [r["M3_dead_weight_removed"] for r in on], [r["M3_dead_weight_removed"] for r in off]
        m4_on, m4_off = [r["M4_unilateral_changes"] for r in on], [r["M4_unilateral_changes"] for r in off]
        complete = len(on) == n_per_arm and len(off) == n_per_arm
        hypotheses = {
            "H1": yes(on, "M1_gate") >= 11,
            "H2": yes(on, "M2_traps_intact") >= 11,
            "H3": sum(v == 0 for v in m4_on) >= 10 and sum(m4_on) < sum(m4_off),
            "H4": sum(m3_on) / n_per_arm >= 2.0,
        }
        cell = {
            "skill_invoked": {"on": sum(bool(r.get("skill_invoked")) for r in on),
                              "off": sum(bool(r.get("skill_invoked")) for r in off)},
            "M1_gate": binary("M1_gate"),
            "M2_traps_intact": binary("M2_traps_intact"),
            "M3_dead_weight_removed": {"on_mean": sum(m3_on) / max(len(on), 1),
                                       "off_mean": sum(m3_off) / max(len(off), 1),
                                       "n_on": len(on), "n_off": len(off),
                                       "perm_p": perm_test_sum(m3_on, m3_off) if m3_on and m3_off else None},
            "M4_unilateral_changes": {"on_total": sum(m4_on), "off_total": sum(m4_off),
                                      "on_zero": sum(v == 0 for v in m4_on),
                                      "n_on": len(on), "n_off": len(off),
                                      "perm_p": perm_test_sum(m4_on, m4_off) if m4_on and m4_off else None},
            "M5_guard_added": {"on": yes(on, "M5_guard_added"), "off": yes(off, "M5_guard_added")},
            "M6_lines_cited_mean": {"on": mean_of(on, "M6_lines_cited"), "off": mean_of(off, "M6_lines_cited")},
            "M7_questions_asked_mean": {"on": mean_of(on, "M7_questions_asked"),
                                        "off": mean_of(off, "M7_questions_asked")},
            "M8_output_tokens_mean": {"on": sum(r["M8_output_tokens"] for r in on) / max(len(on), 1),
                                      "off": sum(r["M8_output_tokens"] for r in off) / max(len(off), 1)},
            "M8_secs_mean": {"on": mean_of(on, "M8_secs"), "off": mean_of(off, "M8_secs")},
            "M8_cost_usd_mean": {"on": cost_mean(on), "off": cost_mean(off)},
            "complete": complete,
            "hypotheses": hypotheses if complete else None,
        }
        if not complete:
            cell["note"] = INCOMPLETE_NOTE
        out[agent] = cell
    return out


AUTHOR = {"P1": "claude", "P2": "claude", "P3": "codex", "P4": "codex"}


def by_author(rows):
    """Descriptive split by which agent wrote the prompt (DESIGN.md §4.1)."""
    out = {}
    for r in rows:
        cell = out.setdefault(r["agent"], {}).setdefault(
            f"{r['arm']}|{AUTHOR[r['prompt_id']]}-authored", {"n": 0, "gate": 0, "traps": 0, "m4_total": 0})
        cell["n"] += 1
        cell["gate"] += bool(r["M1_gate"])
        cell["traps"] += bool(r["M2_traps_intact"])
        cell["m4_total"] += r["M4_unilateral_changes"]
    return out


if __name__ == "__main__":
    results = json.loads((HERE / "runs" / "results_a.json").read_text())
    summary = {"failed_runs": results["failed_runs"], "agents": summarize(results["rows"]),
               "by_author": by_author(results["rows"])}
    (HERE / "runs" / "summary_a.json").write_text(json.dumps(summary, indent=2) + "\n")
    for agent, s in summary["agents"].items():
        print(agent, s["hypotheses"], "| gate on/off", s["M1_gate"]["on"], s["M1_gate"]["off"],
              "| M4 on/off", s["M4_unilateral_changes"]["on_total"], s["M4_unilateral_changes"]["off_total"])
