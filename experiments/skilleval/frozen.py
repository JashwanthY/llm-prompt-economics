"""Pin everything a skill-evaluation result depends on, and refuse to run if it drifts.

`freeze()` writes frozen.json before the first real run. `assert_frozen()` runs at
the start of every session: a skill or authored prompt that no longer matches its
recorded hash stops the run instead of quietly measuring something else.
"""
import argparse
import hashlib
import json
import subprocess
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
SKILL = REPO / "skills" / "prompt-contract" / "SKILL.md"
FROZEN = HERE / "frozen.json"
PROMPTS_ROOT = HERE / "prompts"
CODEX_PKG = ["npx", "-y", "@openai/codex@0.154.0"]
BOLT_COMMIT = "2e254ac19a69"


class FrozenMismatch(RuntimeError):
    pass


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _last_line(cmd):
    r = subprocess.run(cmd, cwd=REPO, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=300)
    lines = [l.strip() for l in r.stdout.splitlines() if l.strip()]
    return lines[-1] if lines else ""


def freeze(codex_model=None, codex_effort=None, path=FROZEN):
    path = Path(path)
    old = json.loads(path.read_text()) if path.exists() else {}
    rel = str(SKILL.relative_to(REPO))
    data = {
        "written": date.today().isoformat(),
        "repo_commit": _last_line(["git", "rev-parse", "--short=12", "HEAD"]),
        "skill_path": rel,
        "skill_commit": _last_line(["git", "log", "-1", "--format=%h", "--abbrev=12", "--", rel]),
        "skill_sha256": sha256(SKILL),
        "claude_code_version": _last_line(["claude", "--version"]),
        "claude_model_flag": "sonnet",
        "codex_version": _last_line(CODEX_PKG + ["--version"]),
        "codex_model": codex_model,
        "codex_reasoning_effort": codex_effort,
        "bolt_commit": BOLT_COMMIT,
    }
    if "prompts" in old:
        data["prompts"] = old["prompts"]
    path.write_text(json.dumps(data, indent=2) + "\n")
    return data


def record_prompts(path=FROZEN, prompts_root=PROMPTS_ROOT):
    path = Path(path)
    data = json.loads(path.read_text())
    data["prompts"] = {
        d.name: {"prompt": sha256(d / "prompt.md"), "answer_key": sha256(d / "answer_key.json")}
        for d in sorted(Path(prompts_root).iterdir())
        if (d / "answer_key.json").exists()
    }
    path.write_text(json.dumps(data, indent=2) + "\n")
    return data


def assert_frozen(path=FROZEN, skill=SKILL, prompts_root=PROMPTS_ROOT):
    data = json.loads(Path(path).read_text())
    now = sha256(skill)
    if now != data["skill_sha256"]:
        raise FrozenMismatch(f"{Path(skill).name} changed since freeze: {now[:12]} != {data['skill_sha256'][:12]}")
    for pid, hashes in data.get("prompts", {}).items():
        for field, name in (("prompt", "prompt.md"), ("answer_key", "answer_key.json")):
            if sha256(Path(prompts_root) / pid / name) != hashes[field]:
                raise FrozenMismatch(f"{pid}/{name} changed since it was recorded")
    return data


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    init = sub.add_parser("init", help="write frozen.json (keeps recorded prompt hashes)")
    init.add_argument("--codex-model")
    init.add_argument("--codex-effort")
    sub.add_parser("record-prompts", help="record hashes of prompts/P*/ in frozen.json")
    a = ap.parse_args()
    out = freeze(a.codex_model, a.codex_effort) if a.cmd == "init" else record_prompts()
    print(json.dumps(out, indent=2))
