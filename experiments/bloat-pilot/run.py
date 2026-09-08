"""Generate quizzes under both prompt arms, pinned reasoning, save each file.

Direct model calls -- no agent loop -- so the only difference between arms is
the prompt text itself.
"""
import os, pathlib, sys, json, time

# Credentials come from OPENAI_API_KEY, or from a .env file named by
# OPENAI_ENV_FILE. The loader strips CRLF, because a .env saved with Windows
# line endings leaves a trailing \r on the key and the API rejects it with no
# useful error.
ENV = os.environ.get("OPENAI_ENV_FILE", "")
if ENV and pathlib.Path(ENV).exists():
    for line in open(ENV, encoding="utf-8", errors="replace"):
        line = line.strip().lstrip("\ufeff")
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
if not os.environ.get("OPENAI_API_KEY"):
    raise SystemExit("set OPENAI_API_KEY, or OPENAI_ENV_FILE to a .env containing it")
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from prompts import ARMS
from openai import OpenAI

client = OpenAI()
OUT = pathlib.Path(__file__).parent / "out"; OUT.mkdir(exist_ok=True)
MODELS = ["gpt-5.6-luna", "gpt-5.6-terra"]
TRIALS = int(sys.argv[1]) if len(sys.argv) > 1 else 6
EFFORT = "medium"

log = []
for model in MODELS:
    for arm, prompt in ARMS.items():
        for t in range(TRIALS):
            f = OUT / f"{model}__{arm}__{t}.html"
            if f.exists():
                continue
            t0 = time.time()
            r = client.responses.create(
                model=model,
                input=prompt,
                reasoning={"effort": EFFORT},   # pinned identically for every arm
            )
            html = r.output_text
            if "<!DOCTYPE" in html:
                html = html[html.index("<!DOCTYPE"):]
            f.write_text(html, encoding="utf-8")
            rec = {"model": model, "arm": arm, "trial": t, "chars": len(html),
                   "out_tokens": r.usage.output_tokens, "in_tokens": r.usage.input_tokens,
                   "secs": round(time.time() - t0, 1)}
            log.append(rec)
            print(json.dumps(rec), flush=True)

(OUT.parent / "runlog.json").write_text(json.dumps(log, indent=2))
tin = sum(r["in_tokens"] for r in log); tout = sum(r["out_tokens"] for r in log)
print(f"\n{len(log)} generations | {tin} in / {tout} out | est ${tin/1e6*1.25 + tout/1e6*10:.2f}")
