import json
import sys
from pathlib import Path

import pytest

from runner import RateLimited, RunSpec, run_session

FAKE = Path(__file__).parent / "fake_agent.py"


@pytest.fixture
def fake(monkeypatch):
    def use(agent, mode):
        monkeypatch.setenv("FAKE_MODE", mode)
        monkeypatch.setenv("FAKE_FLAVOUR", agent)
        monkeypatch.setenv("SKILLEVAL_CLAUDE_BIN" if agent == "claude" else "SKILLEVAL_CODEX_BIN",
                           f"{sys.executable} {FAKE}")
    return use


def _run(tmp_path, agent, arm="on", timeout=60):
    d = tmp_path / "P1"
    d.mkdir(exist_ok=True)
    (d / "prompt.md").write_text("You are a helpful assistant.\nRule one.\n")
    (d / "answer_key.json").write_text(json.dumps({"domain": "support agent"}))
    spec = RunSpec(f"A-{agent}-{arm}-P1-r1", "A", agent, arm, "P1", 1)
    return run_session(spec, d, tmp_path / "runs", codex_model="gpt-x", work_root=tmp_path / "work",
                       frozen_check=lambda: None, timeout=timeout)


@pytest.mark.parametrize("agent", ["claude", "codex"])
def test_agent_that_waits_gets_the_apply_all_turn(tmp_path, fake, agent):
    fake(agent, "report_then_apply")
    meta = _run(tmp_path, agent)
    d = tmp_path / "runs" / "A" / f"A-{agent}-on-P1-r1" / "a1"
    assert (meta["status"], meta["gate_unchanged"], meta["turns"]) == ("ok", True, 2)
    assert (d / "after_t1.md").read_text() == (d / "before.md").read_text()
    assert "helpful assistant" not in (d / "after_t2.md").read_text()
    saved = json.loads((d / "meta.json").read_text())
    assert saved["turn"][1]["final_text"] == "applied" and saved["turn"][0]["session_id"]


@pytest.mark.parametrize("agent", ["claude", "codex"])
def test_agent_that_edits_immediately_fails_the_gate_and_gets_one_turn(tmp_path, fake, agent):
    fake(agent, "edit")
    meta = _run(tmp_path, agent)
    assert (meta["gate_unchanged"], meta["turns"]) == (False, 1)
    assert not (tmp_path / "runs" / "A" / f"A-{agent}-on-P1-r1" / "a1" / "after_t2.md").exists()


def test_timeout_is_recorded_not_raised(tmp_path, fake):
    fake("claude", "sleep")
    meta = _run(tmp_path, "claude", timeout=1)
    assert (meta["status"], meta["errors"], meta["turns"]) == ("error", ["timeout"], 1)


@pytest.mark.parametrize("agent", ["claude", "codex"])
def test_rate_limit_stops_the_batch(tmp_path, fake, agent):
    fake(agent, "limited")
    with pytest.raises(RateLimited):
        _run(tmp_path, agent)


def test_codex_without_pinned_model_refuses_to_run(tmp_path, fake):
    fake("codex", "report_then_apply")
    spec = RunSpec("x", "A", "codex", "on", "P1", 1)
    with pytest.raises(ValueError, match="not pinned"):
        run_session(spec, tmp_path, tmp_path / "runs", codex_model=None, frozen_check=lambda: None)
