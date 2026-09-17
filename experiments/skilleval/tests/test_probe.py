import json
import sys
from pathlib import Path

from probe import check_isolation, personal_skill_names

FAKE = Path(__file__).parent / "fake_agent.py"


def _fake(monkeypatch, mode):
    monkeypatch.setenv("FAKE_MODE", mode)
    for var in ("SKILLEVAL_CLAUDE_BIN", "SKILLEVAL_CODEX_BIN"):
        monkeypatch.setenv(var, f"{sys.executable} {FAKE}")


def test_personal_skill_names_excludes_prompt_contract(tmp_path):
    for name in ("alpha", "prompt-contract"):
        (tmp_path / name).mkdir()
        (tmp_path / name / "SKILL.md").write_text("x")
    assert personal_skill_names([tmp_path]) == {"alpha"}


def test_clean_probe_passes_and_is_logged(tmp_path, monkeypatch):
    _fake(monkeypatch, "probe")
    log = tmp_path / "probes.jsonl"
    for agent in ("claude", "codex"):
        monkeypatch.setenv("FAKE_FLAVOUR", agent)
        assert check_isolation("gpt-x", log, agents=(agent,), dirs=[], root=tmp_path / "w")
    rows = [json.loads(l) for l in log.read_text().splitlines()]
    assert len(rows) == 4 and all(r["good"] for r in rows)


def test_skill_visible_in_off_arm_fails(tmp_path, monkeypatch):
    _fake(monkeypatch, "leak")
    monkeypatch.setenv("FAKE_FLAVOUR", "codex")
    assert not check_isolation("gpt-x", tmp_path / "probes.jsonl", agents=("codex",), dirs=[], root=tmp_path / "w")


def test_personal_skill_visible_fails(tmp_path, monkeypatch):
    _fake(monkeypatch, "probe")
    monkeypatch.setenv("FAKE_FLAVOUR", "claude")
    (tmp_path / "mine" / "code-review").mkdir(parents=True)
    (tmp_path / "mine" / "code-review" / "SKILL.md").write_text("x")
    assert not check_isolation("gpt-x", tmp_path / "probes.jsonl", agents=("claude",),
                               dirs=[tmp_path / "mine"], root=tmp_path / "w")
