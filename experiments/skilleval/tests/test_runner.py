import json
import sys
from pathlib import Path

import pytest

from runner import RateLimited, RunSpec, codex_served_model, run_session

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


def test_codex_model_is_read_from_its_own_session_log(tmp_path, fake):
    fake("codex", "report_then_apply")
    sessions = tmp_path / "codex-sessions"
    sessions.mkdir(parents=True, exist_ok=True)
    (sessions / "rollout-2026-01-01T00-00-00-t-1.jsonl").write_text("\n".join(json.dumps(e) for e in [
        {"type": "session_meta", "payload": {"session_id": "t-1"}},
        {"type": "turn_context", "payload": {"model": "gpt-test"}},
    ]) + "\n")
    meta = _run(tmp_path, "codex")
    assert meta["turn"][0]["model"] == "gpt-test"
    assert meta["turn"][0]["requested_model"] == "gpt-x"


def test_codex_served_model_returns_none_for_unknown_thread(tmp_path):
    sessions = tmp_path / "sessions"
    sessions.mkdir()
    (sessions / "rollout-2026-01-01T00-00-00-other.jsonl").write_text("\n".join(json.dumps(e) for e in [
        {"type": "session_meta", "payload": {"session_id": "other-thread"}},
        {"type": "turn_context", "payload": {"model": "gpt-other"}},
    ]) + "\n")
    assert codex_served_model("t-1", sessions_root=sessions) is None
