import json

import pytest

from frozen import FrozenMismatch, assert_frozen, record_prompts, sha256


def _setup(tmp_path):
    skill = tmp_path / "SKILL.md"
    skill.write_text("v1")
    frozen = tmp_path / "frozen.json"
    frozen.write_text(json.dumps({"skill_sha256": sha256(skill)}))
    prompts = tmp_path / "prompts"
    (prompts / "P1").mkdir(parents=True)
    (prompts / "P1" / "prompt.md").write_text("prompt")
    (prompts / "P1" / "answer_key.json").write_text("{}")
    return skill, frozen, prompts


def test_passes_when_nothing_changed(tmp_path):
    skill, frozen, prompts = _setup(tmp_path)
    record_prompts(frozen, prompts)
    assert assert_frozen(frozen, skill, prompts)["skill_sha256"] == sha256(skill)


def test_raises_when_skill_edited(tmp_path):
    skill, frozen, prompts = _setup(tmp_path)
    skill.write_text("v2")
    with pytest.raises(FrozenMismatch, match="SKILL.md changed"):
        assert_frozen(frozen, skill, prompts)


def test_raises_when_recorded_answer_key_edited(tmp_path):
    skill, frozen, prompts = _setup(tmp_path)
    record_prompts(frozen, prompts)
    (prompts / "P1" / "answer_key.json").write_text('{"edited": true}')
    with pytest.raises(FrozenMismatch, match="P1/answer_key.json changed"):
        assert_frozen(frozen, skill, prompts)


def test_record_prompts_keeps_other_fields(tmp_path):
    skill, frozen, prompts = _setup(tmp_path)
    data = record_prompts(frozen, prompts)
    assert data["skill_sha256"] == sha256(skill)
    assert set(data["prompts"]["P1"]) == {"prompt", "answer_key"}
