import tomllib

from isolation import SKILL_SUBDIR, claude_cmd, codex_cmd, make_workdir


def _src(tmp_path):
    p = tmp_path / "src.md"
    p.write_text("You are a helpful assistant.\n")
    return p


def _skill(tmp_path):
    s = tmp_path / "SKILL.md"
    s.write_text("skill")
    return s


def test_on_arm_places_skill_only_in_its_own_agents_folder(tmp_path):
    for agent, other in (("claude", "codex"), ("codex", "claude")):
        wd = make_workdir(f"r-{agent}", agent, "on", _src(tmp_path), root=tmp_path / "w", skill=_skill(tmp_path))
        assert (wd / SKILL_SUBDIR[agent] / "SKILL.md").read_text() == "skill"
        assert not (wd / SKILL_SUBDIR[other]).exists()
        assert (wd / "prompt.md").read_text() == "You are a helpful assistant.\n"


def test_off_arm_has_no_skill_and_the_directory_is_reset(tmp_path):
    root, skill = tmp_path / "w", _skill(tmp_path)
    make_workdir("r1", "claude", "on", _src(tmp_path), root=root, skill=skill)
    wd = make_workdir("r1", "claude", "off", _src(tmp_path), root=root, skill=skill)
    assert not (wd / ".claude").exists() and not (wd / ".agents").exists()


def test_workdir_without_prompt_is_empty(tmp_path):
    wd = make_workdir("author", "codex", "off", root=tmp_path / "w", skill=_skill(tmp_path))
    assert list(wd.iterdir()) == []


def test_claude_cmd_is_isolated_and_resumable(monkeypatch):
    monkeypatch.delenv("SKILLEVAL_CLAUDE_BIN", raising=False)
    cmd = claude_cmd("Clean it up.")
    assert cmd[:3] == ["claude", "-p", "Clean it up."]
    assert cmd[cmd.index("--model") + 1] == "sonnet"
    assert cmd[cmd.index("--setting-sources") + 1] == "project"
    assert "--strict-mcp-config" in cmd and cmd[cmd.index("--permission-mode") + 1] == "acceptEdits"
    assert cmd[cmd.index("--tools") + 1:cmd.index("--tools") + 7] == ["Read", "Edit", "Write", "Glob", "Grep", "Skill"]
    assert "--resume" not in cmd
    assert claude_cmd("apply all", resume="s-1")[-2:] == ["--resume", "s-1"]


def test_codex_cmd_disables_personal_skills_and_mcp_servers(tmp_path, monkeypatch):
    monkeypatch.delenv("SKILLEVAL_CODEX_BIN", raising=False)
    home = tmp_path / "skills"
    (home / "alpha").mkdir(parents=True)
    (home / "alpha" / "SKILL.md").write_text("x")
    cmd = codex_cmd("Clean it up.", "gpt-x", effort="medium", homes=(str(home),))
    assert cmd[:4] == ["npx", "-y", "@openai/codex@0.154.0", "exec"]
    assert cmd[-1] == "Clean it up." and cmd[cmd.index("-m") + 1] == "gpt-x"
    assert "model_reasoning_effort=medium" in cmd
    cfg = next(c for c in cmd if c.startswith("skills.config="))
    entries = tomllib.loads("x = " + cfg.split("=", 1)[1])["x"]
    assert entries and all(e["enabled"] is False for e in entries)
    assert "--ignore-user-config" in cmd
    assert not any(c.startswith("mcp_servers.") for c in cmd)
    assert codex_cmd("apply all", "gpt-x", resume="t-1", homes=(str(home),))[-3:] == ["resume", "t-1", "apply all"]
    assert "-m" not in codex_cmd("probe", None, homes=(str(home),))
