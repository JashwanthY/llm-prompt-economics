"""Aggregate compliance by dose. Reports per-rule violation rates and cost."""
import json, pathlib, statistics as st, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from check import check
from design import LEVELS, MODELS

HERE = pathlib.Path(__file__).parent
log = {(r["model"], r["level"], r["trial"]): r
       for r in json.loads((HERE / "runlog.json").read_text())}
WORDS = {k: len(v.split()) for k, v in LEVELS.items()}
RULES = [("hex", "R1 hex literals"), ("inline_handlers", "R2 inline handlers"),
         ("missing_testid", "R3 missing data-testid"), ("bad_id_prefix", "R4 bad id prefix"),
         ("innerHTML", "R5 innerHTML")]

print(f"{'model':14} {'dose':10} {'n':>2} {'kept/5':>7} "
      + " ".join(f"{lbl.split()[0]:>4}" for _, lbl in RULES)
      + f" {'out_tok':>8} {'secs':>6}")
rows = []
for m in MODELS:
    for lvl in LEVELS:
        ms = [check(p) for t in range(3)
              if (p := HERE / "out" / f"{m}__{lvl}__{t}.html").exists()]
        if not ms:
            continue
        rs = [log.get((m, lvl, t)) for t in range(3)]
        rs = [r for r in rs if r]
        kept = st.mean(x["rules_kept"] for x in ms)
        broke = [sum(1 for x in ms if x[k] > 0) for k, _ in RULES]
        row = dict(model=m, level=lvl, words=WORDS[lvl], n=len(ms), kept=kept,
                   broke=broke,
                   out=st.mean(r["out_tokens"] for r in rs) if rs else 0,
                   secs=st.mean(r["secs"] for r in rs) if rs else 0,
                   viol=st.mean(sum(x[k] for k, _ in RULES) for x in ms))
        rows.append(row)
        print(f"{m:14} {lvl:10} {len(ms):>2} {kept:>7.2f} "
              + " ".join(f"{b:>4}" for b in broke)
              + f" {row['out']:>8.0f} {row['secs']:>6.1f}")

print("\nPooled across both models:")
print(f"{'dose':10} {'words':>5} {'n':>2} {'rules kept /5':>13} {'total violations':>17}")
for lvl in LEVELS:
    sub = [r for r in rows if r["level"] == lvl]
    if not sub:
        continue
    n = sum(r["n"] for r in sub)
    kept = sum(r["kept"] * r["n"] for r in sub) / n
    viol = sum(r["viol"] * r["n"] for r in sub) / n
    print(f"{lvl:10} {WORDS[lvl]:>5} {n:>2} {kept:>13.2f} {viol:>17.1f}")
