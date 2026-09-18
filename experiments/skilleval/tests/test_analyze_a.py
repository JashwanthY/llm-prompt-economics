import itertools
import random
from math import comb

import pytest

from analyze_a import by_author, fisher_two_sided, perm_test_sum, summarize


def test_fisher_known_values():
    assert fisher_two_sided(3, 0, 0, 3) == pytest.approx(0.1)
    assert fisher_two_sided(1, 1, 1, 1) == pytest.approx(1.0)
    assert fisher_two_sided(11, 1, 3, 9) == pytest.approx(0.002759, abs=1e-6)


def test_permutation_known_values():
    assert perm_test_sum([1, 1, 1], [0, 0, 0]) == pytest.approx(0.1)
    assert perm_test_sum([1, 0], [1, 0]) == pytest.approx(1.0)
    assert perm_test_sum([0, 0, 0, 1], [2, 3, 1, 2]) == pytest.approx(0.057143, abs=1e-6)


def test_permutation_matches_brute_force():
    rng = random.Random(3)
    xs, ys = [rng.randint(0, 3) for _ in range(5)], [rng.randint(0, 3) for _ in range(6)]
    pool, k = xs + ys, len(xs)
    mean = sum(pool) / len(pool)
    obs = abs(sum(xs) / k - mean)
    brute = sum(abs(sum(s) / k - mean) >= obs - 1e-12 for s in itertools.combinations(pool, k)) / comb(len(pool), k)
    assert perm_test_sum(xs, ys) == pytest.approx(brute)


def _rows(agent, arm, n, gate, traps, m3, m4):
    return [{"agent": agent, "arm": arm, "M1_gate": gate, "M2_traps_intact": traps, "M3_dead_weight_removed": m3,
             "M4_unilateral_changes": m4, "M5_guard_added": False, "M8_output_tokens": 100} for _ in range(n)]


def test_all_hypotheses_supported():
    rows = _rows("claude", "on", 12, True, True, 3, 0) + _rows("claude", "off", 12, False, True, 1, 2)
    s = summarize(rows)["claude"]
    assert s["hypotheses"] == {"H1": True, "H2": True, "H3": True, "H4": True}
    assert s["M1_gate"]["fisher_p"] < 1e-5


def test_incomplete_arm_publishes_no_hypotheses_and_a_note():
    # A run lost to an infrastructure failure (10 True + 1 False on-arm rows, 11 of 12) still leaves
    # the arm incomplete; the fixed-12 denominator that would once have failed H1 for it is no longer
    # published as a hypothesis result at all.
    rows = (_rows("codex", "on", 10, True, True, 3, 0) + _rows("codex", "on", 1, False, True, 3, 0)
            + _rows("codex", "off", 12, False, True, 1, 2))
    s = summarize(rows)["codex"]
    assert s["complete"] is False
    assert s["hypotheses"] is None
    assert s["note"] == ("incomplete arm: hypotheses not evaluated; finished runs are not balanced "
                          "across prompts, so the on/off comparison is prompt-confounded")


def test_complete_arm_has_no_note():
    rows = _rows("claude", "on", 12, True, True, 3, 0) + _rows("claude", "off", 12, False, True, 1, 2)
    assert "note" not in summarize(rows)["claude"]


def test_complete_flag_marks_full_arms():
    complete_rows = _rows("claude", "on", 12, True, True, 3, 0) + _rows("claude", "off", 12, False, True, 1, 2)
    assert summarize(complete_rows)["claude"]["complete"] is True

    incomplete_rows = _rows("codex", "on", 5, True, True, 3, 0) + _rows("codex", "off", 12, False, True, 1, 2)
    assert summarize(incomplete_rows)["codex"]["complete"] is False


def test_m3_mean_uses_actual_run_count_not_fixed_12():
    # 5 on-arm runs each scoring M3=3: fixed-12 mean would be 15/12 = 1.25; the actual mean is 3.0.
    rows = _rows("codex", "on", 5, True, True, 3, 0) + _rows("codex", "off", 12, False, True, 1, 2)
    m3 = summarize(rows)["codex"]["M3_dead_weight_removed"]
    assert m3["on_mean"] == pytest.approx(3.0)
    assert m3["off_mean"] == pytest.approx(1.0)
    assert (m3["n_on"], m3["n_off"]) == (5, 12)


def test_m4_block_carries_n_on_and_n_off():
    rows = _rows("codex", "on", 5, True, True, 3, 0) + _rows("codex", "off", 12, False, True, 1, 2)
    m4 = summarize(rows)["codex"]["M4_unilateral_changes"]
    assert (m4["n_on"], m4["n_off"]) == (5, 12)


def test_published_summary_reports_pre_registered_secondary_metrics():
    on = _rows("claude", "on", 3, True, True, 2, 0)
    off = _rows("claude", "off", 3, False, True, 1, 1)
    for i, r in enumerate(on):
        r["M6_lines_cited"], r["M8_secs"], r["M8_cost_usd"] = i, 10.0 + i, 0.1
    for i, r in enumerate(off):
        r["M6_lines_cited"], r["M8_secs"], r["M8_cost_usd"] = i, 20.0 + i, 0.2
    on[0]["M7_questions_asked"], on[1]["M7_questions_asked"] = 2, 4
    s = summarize(on + off)["claude"]
    assert s["M6_lines_cited_mean"] == {"on": pytest.approx(1.0), "off": pytest.approx(1.0)}
    assert s["M7_questions_asked_mean"] == {"on": pytest.approx(3.0), "off": None}
    assert s["M8_secs_mean"] == {"on": pytest.approx(11.0), "off": pytest.approx(21.0)}
    assert s["M8_cost_usd_mean"] == {"on": pytest.approx(0.1), "off": pytest.approx(0.2)}


def test_cost_mean_is_none_when_any_row_is_missing_cost():
    rows = _rows("claude", "on", 2, True, True, 2, 0) + _rows("claude", "off", 2, False, True, 1, 1)
    for r in rows[:3]:
        r["M8_cost_usd"] = 0.5
    rows[3]["M8_cost_usd"] = None
    s = summarize(rows)["claude"]
    assert s["M8_cost_usd_mean"]["on"] == pytest.approx(0.5)
    assert s["M8_cost_usd_mean"]["off"] is None


def test_by_author_splits_on_who_wrote_the_prompt():
    rows = [{"agent": "codex", "arm": "on", "prompt_id": p, "M1_gate": g, "M2_traps_intact": True,
             "M4_unilateral_changes": m4} for p, g, m4 in (("P1", True, 0), ("P3", False, 2), ("P4", True, 1))]
    out = by_author(rows)["codex"]
    assert out["on|claude-authored"] == {"n": 1, "gate": 1, "traps": 1, "m4_total": 0}
    assert out["on|codex-authored"] == {"n": 2, "gate": 1, "traps": 2, "m4_total": 3}
