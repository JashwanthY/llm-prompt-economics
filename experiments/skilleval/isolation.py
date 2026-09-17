"""Build the working directory and the exact command for one isolated agent turn.

Both arms get the agent as shipped, built-in skills included. The only difference
between arms is whether prompt-contract sits in the working directory's skill
folder. Personal settings, plugins, hooks, MCP servers and skills are excluded:
Claude Code by --setting-sources project and --strict-mcp-config, Codex by
disabling each personal skill and MCP server for the run. Both were verified by
probe on 2026-09-17 (DESIGN.md §3).
"""
import glob
import json
import os
import shlex
import shutil
from pathlib import Path

from frozen import CODEX_PKG, SKILL

CLAUDE_TOOLS = ["Read", "Edit", "Write", "Glob", "Grep", "Skill"]  # Skill: how Claude Code loads any skill, in both arms
CODEX_MCP_SERVERS = ["langchain_lates_documentation", "playwright", "node_repl", "computer-use"]
CODEX_SKILL_HOMES = ("~/.agents/skills", "~/.codex/skills")
SKILL_SUBDIR = {"claude": ".claude/skills/prompt-contract", "codex": ".agents/skills/prompt-contract"}


def work_root():
    return Path(os.environ.get("SKILLEVAL_WORK") or Path(os.environ.get("TMPDIR", "/tmp")) / "skilleval")


def make_workdir(run_id, agent, arm, prompt_src=None, root=None, skill=SKILL):
    wd = Path(root or work_root()) / run_id
    shutil.rmtree(wd, ignore_errors=True)
    wd.mkdir(parents=True)
    if prompt_src is not None:
        shutil.copyfile(prompt_src, wd / "prompt.md")
    if arm == "on":
        dest = wd / SKILL_SUBDIR[agent]
        dest.mkdir(parents=True)
        shutil.copyfile(skill, dest / "SKILL.md")
    return wd


def claude_cmd(message, resume=None, tools=CLAUDE_TOOLS):
    cmd = shlex.split(os.environ.get("SKILLEVAL_CLAUDE_BIN", "claude")) + [
        "-p", message, "--model", "sonnet", "--setting-sources", "project", "--strict-mcp-config",
        "--permission-mode", "acceptEdits", "--output-format", "stream-json", "--verbose", "--tools", *tools,
    ]
    return cmd + (["--resume", resume] if resume else [])


def codex_skill_disables(homes=CODEX_SKILL_HOMES):
    paths = set()
    for home in homes:
        for p in glob.glob(os.path.join(os.path.expanduser(home), "*", "SKILL.md")):
            paths.update((p, os.path.realpath(p)))
    return "[" + ", ".join("{path = %s, enabled = false}" % json.dumps(p) for p in sorted(paths)) + "]"


def codex_cmd(message, model=None, resume=None, effort=None, homes=CODEX_SKILL_HOMES):
    base = shlex.split(os.environ["SKILLEVAL_CODEX_BIN"]) if os.environ.get("SKILLEVAL_CODEX_BIN") else list(CODEX_PKG)
    cmd = base + ["exec", "--json", "--skip-git-repo-check", "--sandbox", "workspace-write",
                  "-c", "skills.config=" + codex_skill_disables(homes)]
    for name in CODEX_MCP_SERVERS:
        cmd += ["-c", f"mcp_servers.{name}.enabled=false"]
    if model:
        cmd += ["-m", model]
    if effort:
        cmd += ["-c", f"model_reasoning_effort={effort}"]
    return cmd + (["resume", resume, message] if resume else [message])
