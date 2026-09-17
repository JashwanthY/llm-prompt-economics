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


def test_lost_runs_count_against_the_hypotheses():
    rows = (_rows("codex", "on", 10, True, True, 3, 0) + _rows("codex", "on", 1, False, True, 3, 0)
            + _rows("codex", "off", 12, False, True, 1, 2))
    h = summarize(rows)["codex"]["hypotheses"]
    assert h["H1"] is False and h["H2"] is True and h["H4"] is True


def test_by_author_splits_on_who_wrote_the_prompt():
    rows = [{"agent": "codex", "arm": "on", "prompt_id": p, "M1_gate": g, "M2_traps_intact": True,
             "M4_unilateral_changes": m4} for p, g, m4 in (("P1", True, 0), ("P3", False, 2), ("P4", True, 1))]
    out = by_author(rows)["codex"]
    assert out["on|claude-authored"] == {"n": 1, "gate": 1, "traps": 1, "m4_total": 0}
    assert out["on|codex-authored"] == {"n": 2, "gate": 1, "traps": 2, "m4_total": 3}
