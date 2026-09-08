"""Diversity runner, through LangChain Deep Agents like every other experiment."""
import json, os, pathlib, sys, time

ENV = "/path/to/your/.env"
for line in open(ENV, encoding="utf-8", errors="replace"):
    line = line.strip().lstrip("﻿")
    if line and not line.startswith("#") and "=" in line:
        k, _, v = line.partition("=")
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
from design import ARMS, MODELS, TRIALS, EFFORT, PROMPT   # noqa: E402
from langchain_openai import ChatOpenAI                   # noqa: E402
from deepagents import create_deep_agent                  # noqa: E402
from deepagents.backends import FilesystemBackend         # noqa: E402

OUT = HERE / "out"; OUT.mkdir(exist_ok=True)
LOGF = HERE / "runlog.json"
log = json.loads(LOGF.read_text()) if LOGF.exists() else []
done = {(r["model"], r["arm"], r["trial"]) for r in log}

# Interleave arms so any drift in API latency over the session lands on every
# arm equally rather than on whichever one ran last.
for trial in range(TRIALS):
    for arm in ARMS:
        for model_id in MODELS:
            target = OUT / f"{model_id}__{arm}__{trial}.html"
            if (model_id, arm, trial) in done or target.exists():
                continue
            agent = create_deep_agent(
                model=ChatOpenAI(model=model_id, reasoning_effort=EFFORT,
                                 use_responses_api=True),
                system_prompt=PROMPT(arm),
                backend=FilesystemBackend(root_dir=str(OUT), virtual_mode=False))
            t0 = time.time()
            try:
                res = agent.invoke(
                    {"messages": [{"role": "user", "content":
                        f"Write the finished HTML file to exactly this absolute "
                        f"path: {target}\nWrite the file, then reply with just: DONE"}]},
                    config={"configurable": {"thread_id": f"{model_id}-{arm}-{trial}"},
                            "recursion_limit": 50})
                msgs, err = res["messages"], None
            except Exception as e:
                msgs, err = [], str(e)[:200]
            relocated = False
            if not target.exists():
                for cand in list(pathlib.Path.home().rglob(target.name))[:3]:
                    if cand.is_file() and cand.resolve() != target.resolve():
                        target.write_bytes(cand.read_bytes()); cand.unlink()
                        relocated = True; break
            ti = to = 0
            for m in msgs:
                u = getattr(m, "usage_metadata", None) or {}
                ti += u.get("input_tokens", 0); to += u.get("output_tokens", 0)
            rec = {"model": model_id, "arm": arm, "trial": trial,
                   "exists": target.exists(),
                   "chars": target.stat().st_size if target.exists() else 0,
                   "in_tokens": ti, "out_tokens": to,
                   "secs": round(time.time() - t0, 1), "error": err, "relocated": relocated}
            log.append(rec); print(json.dumps(rec), flush=True)
            LOGF.write_text(json.dumps(log, indent=2))

ti = sum(r["in_tokens"] for r in log); to = sum(r["out_tokens"] for r in log)
print(f"\n{len(log)} runs | est ${ti/1e6*1.25 + to/1e6*10:.2f}")
