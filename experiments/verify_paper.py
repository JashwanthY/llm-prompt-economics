"""Re-verify every numeric claim in paper-bloat/preprint.md against raw data.

Written because three separate measurement bugs in this study each produced a
clean, plausible, wrong number. Run this before any change to the paper's
figures is believed. Exits non-zero on the first mismatch.
"""
import collections, json, pathlib, statistics as st, sys

ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, str(ROOT / "dose"))
sys.path.insert(0, str(ROOT / "compliance"))
from design import LEVELS                      # noqa: E402  (dose ladder)
import check as compliance_check               # noqa: E402

fails = []
def claim(cond, msg):
    print(("  OK    " if cond else "  WRONG ") + msg)
    if not cond:
        fails.append(msg)

claim([len(v.split()) for v in LEVELS.values()] == [0, 68, 246, 811],
      "padding ladder is 0/68/246/811 words")

grades = {pathlib.Path(json.loads(l)["file"]).name: json.loads(l)
          for l in open(ROOT / "dose/grades.jsonl")}
log = json.load(open(ROOT / "dose/runlog.json"))
by_dose = collections.defaultdict(list)
for r in log:
    key = f"{r['model']}__{r['task']}__{r['level']}__{r['trial']}.html"
    by_dose[r["level"]].append((grades[key], r))

base = None
for lvl in LEVELS:
    rows = by_dose[lvl]
    o = st.mean(r["out_tokens"] for _, r in rows)
    s = st.mean(r["secs"] for _, r in rows)
    base = base or (o, s)
    print(f"    {lvl:10} n={len(rows):2} out={o:6.0f} ({o/base[0]-1:+.0%}) "
          f"secs={s:5.1f} ({s/base[1]-1:+.0%})")
    if lvl == "L3_heavy":
        claim(abs(o / base[0] - 1.42) < 0.005, "+42% output tokens at L3")
        claim(abs(s / base[1] - 1.38) < 0.005, "+38% latency at L3")
claim(all(len(v) == 12 for v in by_dose.values()), "n=12 per dose")

allg = [d for rows in by_dose.values() for d, _ in rows]
perfect = sum(1 for d in allg if d["passed"] == d["total"])
claim(perfect == 47 and len(allg) == 48, f"47 of 48 outputs perfect ({perfect}/{len(allg)})")
bad = [d for d in allg if d["passed"] < d["total"]]
claim(len(bad) == 1 and "L0_none" in bad[0]["file"],
      "the single defect occurred at zero padding")

for d, model, want in [("bloat-pilot", "gpt-5.6-luna", 0.40),
                       ("bloat-pilot", "gpt-5.6-terra", 0.51),
                       ("bloat-pilot-da", "gpt-5.6-luna", 0.45),
                       ("bloat-pilot-da", "gpt-5.6-terra", 0.85)]:
    lg = json.load(open(ROOT / d / "runlog.json"))
    a = collections.defaultdict(list)
    for r in lg:
        a[(r["model"], r["arm"])].append(r["secs"])
    lo, hi = st.mean(a[(model, "A_minimal")]), st.mean(a[(model, "B_padded")])
    claim(abs((hi / lo - 1) - want) < 0.005, f"{d} {model} latency {want:+.0%}")

ms = [compliance_check.check(p) for p in sorted((ROOT / "compliance/out").glob("*.html"))]
claim(len(ms) == 24, "24 compliance files")
claim(sum(x["hex"] for x in ms) == 1, "1 hex-outside-:root violation")
claim(sum(x["inline_handlers"] + x["missing_testid"] + x["bad_id_prefix"]
          + x["innerHTML"] for x in ms) == 1, "1 other-rule violation in total")
claim(sum(sum(x[k] for x in ms) == 0
          for k in ("inline_handlers", "missing_testid", "innerHTML")) == 3,
      "three rules never broken at any dose")

total = sum(len(json.load(open(ROOT / d / "runlog.json")))
            for d in ("bloat-pilot", "bloat-pilot-da", "dose", "compliance"))
claim(total == 108, f"108 runs total ({total})")

print(f"\n{len(fails)} mismatch(es)")
sys.exit(1 if fails else 0)
