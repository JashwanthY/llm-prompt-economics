"""Study A prompt authoring (DESIGN.md §4.1): Claude Code writes P1-P2, Codex writes P3-P4.

Each author runs isolated and without the skill, in an empty folder outside any
git repository, from brief.md. Up to two attempts per prompt; the second attempt
receives the validator's problems. Everything is logged in prompts/Pn/authoring_log.md.
"""
import argparse
import json
import shutil
from datetime import datetime
from string import Template

from frozen import HERE, assert_frozen
from isolation import make_workdir
from runner import run_turn
from validate_key import validate

AUTHORS = {
    "P1": ("claude", "a customer-support agent for a subscription software company"),
    "P2": ("claude", "a coding agent working in a company's web application repository"),
    "P3": ("codex", "a research assistant that answers questions from retrieved internal documents"),
    "P4": ("codex", "a data-extraction pipeline that turns supplier invoices into a JSON record"),
}
PROMPTS = HERE / "prompts"


def author(pid, codex_model, codex_effort=None, attempts=2):
    agent, domain = AUTHORS[pid]
    brief = Template((HERE / "brief.md").read_text()).substitute(prompt_id=pid, domain=domain)
    out = PROMPTS / pid
    out.mkdir(parents=True, exist_ok=True)
    log = [f"# Authoring log — {pid}", "", f"- author: {agent}", f"- domain: {domain}", ""]
    problems = ["not attempted"]
    for n in range(1, attempts + 1):
        wd = make_workdir(f"author-{pid}-a{n}", agent, "off")
        message = brief if n == 1 else (brief + "\n\nYour previous files had these problems. Fix all of them:\n- "
                                        + "\n- ".join(problems))
        lines, result, secs, _ = run_turn(agent, wd, message, codex_model, codex_effort=codex_effort)
        (out / f"authoring_a{n}.events.jsonl").write_text("".join(f"{l}\n" for l in lines))
        if result.error or not (wd / "prompt.md").exists() or not (wd / "answer_key.json").exists():
            problems = [f"session error or missing files: {result.error}"]
        else:
            try:
                problems = validate((wd / "prompt.md").read_text(), json.loads((wd / "answer_key.json").read_text()))
            except json.JSONDecodeError as e:
                problems = [f"answer_key.json is not valid JSON: {e}"]
        stamp = datetime.now().isoformat(timespec="seconds")
        log.append(f"- {stamp} attempt {n} ({secs:.0f}s, model {result.model}): " + ("; ".join(problems) or "OK"))
        if not problems:
            shutil.copyfile(wd / "prompt.md", out / "prompt.md")
            shutil.copyfile(wd / "answer_key.json", out / "answer_key.json")
            break
    (out / "authoring_log.md").write_text("\n".join(log) + "\n")
    return problems


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("prompt_ids", nargs="+", choices=sorted(AUTHORS))
    frozen = assert_frozen()
    for pid in ap.parse_args().prompt_ids:
        left = author(pid, frozen["codex_model"], frozen["codex_reasoning_effort"])
        print(pid, "OK" if not left else f"FAILED after 2 attempts: {left}")
