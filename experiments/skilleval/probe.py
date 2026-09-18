"""Skills probe run at the start of every batch (DESIGN.md §3).

Each agent and arm is asked to list its skills. The probe passes only if
prompt-contract is visible exactly in the skill arm and none of the author's
personal skills is visible in either arm. Every result is appended to probes.jsonl.
Codex's bundled skills in ~/.codex/skills/.system/ count as shipped, like
Claude Code's built-ins, and are not treated as personal.
"""
import json
from datetime import datetime
from pathlib import Path

from isolation import make_workdir
from runner import run_turn

PROBE = "List every skill available to you, names only, comma-separated. If none, reply NONE. No other text."
PERSONAL_SKILL_DIRS = [Path.home() / ".claude" / "skills", Path.home() / ".agents" / "skills",
                       Path.home() / ".codex" / "skills"]
SHIPPED_SKILL_DIRS = [Path.home() / ".codex" / "skills" / ".system"]


def personal_skill_names(dirs, shipped_dirs=()):
    names = {p.parent.name for d in dirs for p in Path(d).glob("*/SKILL.md")} - {"prompt-contract"}
    shipped = {p.parent.name for d in shipped_dirs for p in Path(d).glob("*/SKILL.md")}
    return names - shipped


def probe(agent, arm, codex_model=None, codex_effort=None, root=None):
    wd = make_workdir(f"probe-{agent}-{arm}", agent, arm, root=root)
    _lines, result, _secs, _err = run_turn(agent, wd, PROBE, codex_model, codex_effort=codex_effort, timeout=300)
    names = sorted({n.strip() for n in result.final_text.split(",") if n.strip() and n.strip() != "NONE"})
    return names, result.error


def check_isolation(codex_model, log_path, codex_effort=None, agents=("claude", "codex"),
                    dirs=PERSONAL_SKILL_DIRS, shipped_dirs=SHIPPED_SKILL_DIRS, root=None):
    personal = personal_skill_names(dirs, shipped_dirs)
    ok = True
    with open(log_path, "a") as log:
        for agent in agents:
            for arm in ("off", "on"):
                names, error = probe(agent, arm, codex_model, codex_effort, root)
                bare = {n.split(":")[-1] for n in names}
                has_skill = "prompt-contract" in bare
                leaked = sorted(personal & bare)
                good = error is None and has_skill == (arm == "on") and not leaked
                log.write(json.dumps({"time": datetime.now().isoformat(timespec="seconds"), "agent": agent,
                                      "arm": arm, "names": names, "leaked": leaked, "error": error,
                                      "good": good}) + "\n")
                ok = ok and good
    return ok
