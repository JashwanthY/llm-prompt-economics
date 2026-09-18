import json

import run_batch
from run_batch import is_finished, main


def _meta(root, run_id, n, status):
    d = root / "A" / run_id / f"a{n}"
    d.mkdir(parents=True)
    (d / "meta.json").write_text(json.dumps({"status": status}))


def test_finished_after_one_ok_or_two_errors(tmp_path):
    _meta(tmp_path, "r1", 1, "ok")
    assert is_finished("r1", root=tmp_path)
    _meta(tmp_path, "r2", 1, "error")
    assert not is_finished("r2", root=tmp_path)
    _meta(tmp_path, "r2", 2, "error")
    assert is_finished("r2", root=tmp_path)
    assert not is_finished("never-run", root=tmp_path)


def test_single_agent_batch_only_probes_that_agent(monkeypatch):
    recorded = {}

    def fake_check_isolation(model, log_path, effort, agents=("claude", "codex")):
        recorded["agents"] = agents
        return True

    monkeypatch.setattr(run_batch, "check_isolation", fake_check_isolation)
    monkeypatch.setattr(run_batch, "make_schedule", lambda: [])
    monkeypatch.setattr(run_batch, "assert_frozen",
                         lambda: {"codex_model": "gpt-x", "codex_reasoning_effort": None})

    main(limit=0, agent="claude")
    assert recorded["agents"] == ("claude",)

    main(limit=0)
    assert recorded["agents"] == ("claude", "codex")
