"""Compliance run, through LangChain Deep Agents."""
import os, pathlib, sys, json, time
ENV = "/path/to/your/.env"
for line in open(ENV, encoding="utf-8", errors="replace"):
    line = line.strip().lstrip("﻿")
    if line and not line.startswith("#") and "=" in line:
        k, _, v = line.partition("=")
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
from design import LEVELS, MODELS, TRIALS, EFFORT, PROMPT
from langchain_openai import ChatOpenAI
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend

OUT = HERE / "out"; OUT.mkdir(exist_ok=True)
logf = HERE / "runlog.json"
log = json.loads(logf.read_text()) if logf.exists() else []
done = {(r["model"], r["level"], r["trial"]) for r in log}

for model_id in MODELS:
    for level, pad in LEVELS.items():
        for t in range(TRIALS):
            target = OUT / f"{model_id}__{level}__{t}.html"
            if (model_id, level, t) in done or target.exists():
                continue
            agent = create_deep_agent(
                model=ChatOpenAI(model=model_id, reasoning_effort=EFFORT,
                                 use_responses_api=True),
                system_prompt=PROMPT(pad),
                backend=FilesystemBackend(root_dir=str(OUT), virtual_mode=False))
            t0 = time.time()
            try:
                res = agent.invoke({"messages": [{"role": "user", "content":
                    f"Write the finished HTML file to exactly this absolute path: "
                    f"{target}\nWrite the file, then reply with just: DONE"}]},
                    config={"configurable": {"thread_id": f"{model_id}-{level}-{t}"},
                            "recursion_limit": 50})
                msgs = res["messages"]; err = None
            except Exception as e:
                msgs = []; err = str(e)[:200]
            relocated = False
            if not target.exists():
                for cand in list(pathlib.Path.home().rglob(target.name))[:3]:
                    if cand.is_file() and cand.resolve() != target.resolve():
                        target.write_bytes(cand.read_bytes()); cand.unlink()
                        try: cand.parent.rmdir()
                        except OSError: pass
                        relocated = True; break
            ti = to = 0
            for m in msgs:
                u = getattr(m, "usage_metadata", None) or {}
                ti += u.get("input_tokens", 0); to += u.get("output_tokens", 0)
            rec = {"model": model_id, "level": level, "trial": t,
                   "exists": target.exists(),
                   "chars": target.stat().st_size if target.exists() else 0,
                   "in_tokens": ti, "out_tokens": to,
                   "secs": round(time.time()-t0, 1), "error": err, "relocated": relocated}
            log.append(rec); print(json.dumps(rec), flush=True)
            logf.write_text(json.dumps(log, indent=2))
tin = sum(r["in_tokens"] for r in log); tout = sum(r["out_tokens"] for r in log)
print(f"\n{len(log)} runs | {tin} in / {tout} out | est ${tin/1e6*1.25 + tout/1e6*10:.2f}")
