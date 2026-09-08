"""Bloat pilot, run through LangChain Deep Agents.

Same two arms as before (identical task; B adds only general web advice), but
the agent has the full Deep Agents harness -- planning, filesystem tools, and
its own loop -- rather than a single API call.
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
HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "bloat-pilot"))
from prompts import ARMS

from langchain_openai import ChatOpenAI
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend

OUT = HERE / "out"; OUT.mkdir(exist_ok=True)
MODELS = ["gpt-5.6-luna", "gpt-5.6-terra"]
TRIALS = int(sys.argv[1]) if len(sys.argv) > 1 else 1
EFFORT = "medium"

logf = HERE / "runlog.json"
log = json.loads(logf.read_text()) if logf.exists() else []

for model_id in MODELS:
    for arm, task in ARMS.items():
        for t in range(TRIALS):
            name = f"{model_id}__{arm}__{t}.html"
            target = OUT / name
            if target.exists():
                continue
            # reasoning_effort with tools requires the Responses API on gpt-5.6
            model = ChatOpenAI(model=model_id, reasoning_effort=EFFORT,
                               use_responses_api=True)
            agent = create_deep_agent(
                model=model,
                system_prompt=task,
                backend=FilesystemBackend(root_dir=str(OUT), virtual_mode=False),
            )
            t0 = time.time()
            res = agent.invoke(
                {"messages": [{"role": "user", "content":
                    f"Write the finished HTML file to exactly this absolute path: "
                    f"{target}\nWrite the file, then reply with just: DONE"}]},
                config={"configurable": {"thread_id": f"{model_id}-{arm}-{t}"},
                        "recursion_limit": 50},
            )
            secs = round(time.time() - t0, 1)
            msgs = res["messages"]
            usage = {"in": 0, "out": 0}
            for m in msgs:
                u = (getattr(m, "usage_metadata", None) or {})
                usage["in"] += u.get("input_tokens", 0)
                usage["out"] += u.get("output_tokens", 0)
            rec = {"model": model_id, "arm": arm, "trial": t,
                   "exists": target.exists(),
                   "chars": target.stat().st_size if target.exists() else 0,
                   "turns": len(msgs), "in_tokens": usage["in"],
                   "out_tokens": usage["out"], "secs": secs}
            log.append(rec); print(json.dumps(rec), flush=True)
            logf.write_text(json.dumps(log, indent=2))

tin = sum(r["in_tokens"] for r in log); tout = sum(r["out_tokens"] for r in log)
print(f"\n{len(log)} runs | {tin} in / {tout} out | est ${tin/1e6*1.25 + tout/1e6*10:.2f}")
