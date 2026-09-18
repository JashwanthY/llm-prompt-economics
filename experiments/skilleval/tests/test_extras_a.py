import json

import pytest

from extras_a import init_skills_tally, m4_selectivity, word_retention

L = [
    "You are a helpful assistant.",        # 1 restated_capability - not ambiguous
    "Be careful with dates.",               # 2 vague_contract - ambiguous
    "Keep replies under 80 words.",         # 3 work_order_unclear - ambiguous
    "Explain every policy in full detail.", # 4 other - not ambiguous
    "End every message with a sign-off.",   # 5 other - not ambiguous
    "Never reveal internal notes.",         # 6 restriction - not ambiguous
]
BEFORE = "\n".join(L) + "\n"
KEY = {
    "planted": [
        {"category": "restated_capability", "line": 1},
        {"category": "vague_contract", "line": 2},
        {"category": "work_order_unclear", "line": 3},
        {"category": "restriction", "line": 6},
    ],
}


def _write_run(runs, prompts, run_id, prompt_id, before, end, turns=1, attempt=1):
    d = runs / run_id / f"a{attempt}"
    d.mkdir(parents=True)
    (d / "before.md").write_text(before)
    (d / ("after_t2.md" if turns == 2 else "after_t1.md")).write_text(end)
    (prompts / prompt_id).mkdir(parents=True, exist_ok=True)
    (prompts / prompt_id / "answer_key.json").write_text(json.dumps(KEY))


def test_m4_selectivity_separates_ambiguous_from_other_lines(tmp_path):
    runs, prompts = tmp_path / "runs", tmp_path / "prompts"
    # Change line 2 (ambiguous) and line 5 (other); leave the rest untouched.
    end = "\n".join([L[0], "Ambiguity resolved: use the customer's local timezone.", L[2], L[3],
                     "Sign off with the agent's first name only.", L[5]]) + "\n"
    _write_run(runs, prompts, "R1", "P1", BEFORE, end)
    row = {"run_id": "R1", "agent": "claude", "arm": "on", "prompt_id": "P1", "attempt": 1, "turns": 1}
    out = m4_selectivity([row], runs=runs, prompts=prompts)
    on = out["claude"]["on"]
    assert (on["ambiguous_changed"], on["ambiguous_total"]) == (1, 2)
    assert (on["other_changed"], on["other_total"]) == (1, 4)
    assert on["ambiguous_fraction"] == pytest.approx(0.5)
    assert on["other_fraction"] == pytest.approx(0.25)
    assert on["ratio"] == pytest.approx(2.0)


def test_m4_selectivity_handles_an_arm_with_no_runs(tmp_path):
    runs, prompts = tmp_path / "runs", tmp_path / "prompts"
    _write_run(runs, prompts, "R1", "P1", BEFORE, BEFORE)
    row = {"run_id": "R1", "agent": "claude", "arm": "on", "prompt_id": "P1", "attempt": 1, "turns": 1}
    off = m4_selectivity([row], runs=runs, prompts=prompts)["claude"]["off"]
    assert off == {"ambiguous_changed": 0, "ambiguous_total": 0, "ambiguous_fraction": None,
                   "other_changed": 0, "other_total": 0, "other_fraction": None, "ratio": None}


def test_word_retention_means_the_ratio_per_arm():
    rows = [
        {"agent": "claude", "arm": "on", "words_before": 100, "words_after": 60},
        {"agent": "claude", "arm": "on", "words_before": 200, "words_after": 100},
        {"agent": "claude", "arm": "off", "words_before": 100, "words_after": 95},
    ]
    out = word_retention(rows)["claude"]
    assert out["on"]["mean_retention"] == pytest.approx((0.6 + 0.5) / 2)
    assert out["on"]["n"] == 2
    assert out["off"]["mean_retention"] == pytest.approx(0.95)


def test_word_retention_skips_rows_missing_word_counts():
    rows = [{"agent": "codex", "arm": "on", "words_before": 0, "words_after": 0}]
    out = word_retention(rows)["codex"]["on"]
    assert out == {"mean_retention": None, "n": 0}


def _write_meta(runs, run_id, attempt, skills):
    d = runs / run_id / f"a{attempt}"
    d.mkdir(parents=True)
    (d / "meta.json").write_text(json.dumps({"turn": [{"skills": skills}]}))


def test_init_skills_tally_counts_prompt_contract_and_diffs_the_arms(tmp_path):
    runs = tmp_path / "runs"
    _write_meta(runs, "on1", 1, ["prompt-contract", "claude-api", "run"])
    _write_meta(runs, "on2", 1, ["prompt-contract", "claude-api"])
    _write_meta(runs, "off1", 1, ["claude-api", "run"])
    rows = [
        {"run_id": "on1", "agent": "claude", "arm": "on", "attempt": 1},
        {"run_id": "on2", "agent": "claude", "arm": "on", "attempt": 1},
        {"run_id": "off1", "agent": "claude", "arm": "off", "attempt": 1},
    ]
    out = init_skills_tally(rows, runs=runs)["claude"]
    assert out["on"] == {"n_runs": 2, "n_with_skills_data": 2, "n_with_prompt_contract": 2,
                         "skills_seen": ["claude-api", "prompt-contract", "run"]}
    assert out["off"] == {"n_runs": 1, "n_with_skills_data": 1, "n_with_prompt_contract": 0,
                          "skills_seen": ["claude-api", "run"]}
    assert out["only_in_on"] == ["prompt-contract"]
    assert out["only_in_off"] == []


def test_init_skills_tally_skips_runs_with_no_skills_data(tmp_path):
    runs = tmp_path / "runs"
    _write_meta(runs, "on1", 1, None)
    rows = [{"run_id": "on1", "agent": "codex", "arm": "on", "attempt": 1}]
    out = init_skills_tally(rows, runs=runs)["codex"]["on"]
    assert out == {"n_runs": 1, "n_with_skills_data": 0, "n_with_prompt_contract": 0, "skills_seen": []}
