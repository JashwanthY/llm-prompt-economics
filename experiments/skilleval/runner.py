"""Run one skill-evaluation session: turn 1, then "apply all" if prompt.md is untouched.

Every turn runs with stdin closed (an open stdin makes `codex exec` wait forever)
and a hard timeout, in a working directory outside any git repository. Artifacts
are copied to <out_root>/<study>/<run_id>/a<attempt>/ and the directory removed.
"""
import json
import re
import shutil
import subprocess
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from events import parse_claude, parse_codex
from frozen import assert_frozen
from isolation import claude_cmd, codex_cmd, make_workdir

TURN1 = ("This is our {domain} system prompt: prompt.md. It's getting long and expensive, "
         "and the model sometimes ignores parts of it. Clean it up.")
TURN2 = "apply all"
TIMEOUT = 900
RATE_LIMIT = re.compile(r"(?i)rate.?limit|usage limit|limit reached|quota|too many requests|\b429\b")


class RateLimited(RuntimeError):
    pass


@dataclass
class RunSpec:
    run_id: str
    study: str
    agent: str
    arm: str
    prompt_id: str
    rep: int


def run_turn(agent, wd, message, codex_model=None, resume=None, codex_effort=None, timeout=TIMEOUT):
    cmd = claude_cmd(message, resume) if agent == "claude" else codex_cmd(message, codex_model, resume, codex_effort)
    start = time.monotonic()
    try:
        p = subprocess.run(cmd, cwd=wd, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=timeout)
        lines, stderr, code = p.stdout.splitlines(), p.stderr, p.returncode
    except subprocess.TimeoutExpired as e:
        out = e.stdout.decode(errors="replace") if isinstance(e.stdout, bytes) else (e.stdout or "")
        lines, stderr, code = out.splitlines(), "", None
    secs = time.monotonic() - start
    result = (parse_claude if agent == "claude" else parse_codex)(lines)
    if code is None:
        result.error = "timeout"
    elif code != 0 and result.error is None:
        result.error = f"exit {code}: {stderr[-300:]}"
    if result.error and RATE_LIMIT.search(f"{result.error}\n{stderr[-2000:]}"):
        raise RateLimited(result.error)
    return lines, result, secs, stderr


def _read(path):
    return path.read_bytes() if path.exists() else b""


def _files(wd):
    return sorted(str(p.relative_to(wd)) for p in wd.rglob("*")
                  if p.is_file() and not str(p.relative_to(wd)).startswith((".claude", ".agents")))


def run_session(spec, prompt_dir, out_root, codex_model=None, codex_effort=None, attempt=1,
                work_root=None, frozen_check=assert_frozen, timeout=TIMEOUT):
    frozen_check()
    if spec.agent == "codex" and not codex_model:
        raise ValueError("codex_model is not pinned in frozen.json")
    prompt_dir = Path(prompt_dir)
    domain = json.loads((prompt_dir / "answer_key.json").read_text())["domain"]
    wd = make_workdir(f"{spec.run_id}-a{attempt}", spec.agent, spec.arm, prompt_dir / "prompt.md", root=work_root)
    before = _read(wd / "prompt.md")

    turns = []
    lines, result, secs, _ = run_turn(spec.agent, wd, TURN1.format(domain=domain), codex_model,
                                      codex_effort=codex_effort, timeout=timeout)
    turns.append((lines, result, secs, _read(wd / "prompt.md")))
    files_after_t1 = _files(wd)
    unchanged = turns[0][3] == before
    if unchanged and result.error is None and result.session_id:
        lines, r2, secs2, _ = run_turn(spec.agent, wd, TURN2, codex_model, resume=result.session_id,
                                       codex_effort=codex_effort, timeout=timeout)
        turns.append((lines, r2, secs2, _read(wd / "prompt.md")))

    dest = Path(out_root) / spec.study / spec.run_id / f"a{attempt}"
    shutil.rmtree(dest, ignore_errors=True)
    dest.mkdir(parents=True)
    (dest / "before.md").write_bytes(before)
    for i, (ls, _r, _s, after) in enumerate(turns, 1):
        (dest / f"after_t{i}.md").write_bytes(after)
        (dest / f"t{i}.events.jsonl").write_text("".join(f"{l}\n" for l in ls))
    errors = [r.error for _l, r, _s, _a in turns if r.error]
    meta = {
        **asdict(spec), "attempt": attempt, "status": "error" if errors else "ok", "errors": errors,
        "gate_unchanged": unchanged, "turns": len(turns), "files_after_t1": files_after_t1,
        "turn": [{"session_id": r.session_id, "model": r.model, "secs": round(s, 1),
                  "input_tokens": r.input_tokens, "output_tokens": r.output_tokens,
                  "reasoning_tokens": r.reasoning_tokens, "cost_usd": r.cost_usd,
                  "tool_calls": r.tool_calls, "skills": r.skills, "final_text": r.final_text}
                 for _l, r, s, _a in turns],
    }
    (dest / "meta.json").write_text(json.dumps(meta, indent=2) + "\n")
    shutil.rmtree(wd, ignore_errors=True)
    return meta
