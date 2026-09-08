"""Re-verify every numeric claim in paper-bloat/preprint.md against raw data.

Written because three separate measurement bugs in this study each produced a
clean, plausible, wrong number. Run this before any change to the paper's
figures is believed. Exits non-zero on the first mismatch.
"""
import collections, json, pathlib, random, statistics as st, sys
from math import comb

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

# Paired L0->L3 within each task/model/trial cell, with the sign test the paper
# quotes. Seeded so the reported interval is reproducible.
random.seed(0)
def boot(vals, n=10000):
    s = sorted(st.mean(random.choices(vals, k=len(vals))) for _ in range(n))
    return s[int(.025 * n)], s[int(.975 * n)]
kf = lambda r: (r["task"], r["model"], r["trial"])
lo_ = {kf(r): r for _, r in by_dose["L0_none"]}
hi_ = {kf(r): r for _, r in by_dose["L3_heavy"]}
dt = [(hi_[k]["out_tokens"] - lo_[k]["out_tokens"], hi_[k]["secs"] - lo_[k]["secs"])
      for k in lo_ if k in hi_]
d_out, d_sec, n_p = [x[0] for x in dt], [x[1] for x in dt], len(dt)
claim(n_p == 12 and all(x > 0 for x in d_out) and all(x > 0 for x in d_sec),
      "all 12 paired L0->L3 deltas are positive in both measures")
sign_p = sum(comb(n_p, i) for i in range(n_p, n_p + 1)) / 2 ** n_p
claim(abs(sign_p - 0.00024) < 0.00002, f"sign test p = 0.00024 ({sign_p:.5f})")
claim(abs(st.mean(d_out) - 1595) < 1, f"paired output delta +1,595 ({st.mean(d_out):.0f})")
claim(abs(st.mean(d_sec) - 11.0) < 0.05, f"paired latency delta +11.0s ({st.mean(d_sec):.1f})")

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

runs = {d: json.load(open(ROOT / d / "runlog.json"))
        for d in ("bloat-pilot", "bloat-pilot-da", "dose", "compliance", "hard",
                  "poscontrol", "diversity")}
total = sum(len(v) for v in runs.values())
claim(total == 168, f"168 runs total ({total})")
spend = sum(r.get("in_tokens", 0) for v in runs.values() for r in v) / 1e6 * 1.25 \
      + sum(r.get("out_tokens", 0) for v in runs.values() for r in v) / 1e6 * 10
claim(abs(spend - 14.37) < 0.02, f"total spend $14.37 (${spend:.2f})")

# diversity: pre-registered tests, the exploratory collapse, and the cost split
sys.path.insert(0, str(ROOT / "diversity"))
import analyze as dv
dfe = [json.loads(l) for l in open(ROOT / "diversity/features.jsonl")]
dg = collections.defaultdict(list)
for f in dfe:
    dg[(f["arm"], f["model"])].append(f)
claim(all(len(v) == 6 for v in dg.values()) and len(dg) == 6, "diversity: 6 runs x 3 arms x 2 models")
for arm, model, want in (("minimal", "gpt-5.6-luna", .578), ("minimal", "gpt-5.6-terra", .306),
                         ("padded", "gpt-5.6-luna", .473), ("padded", "gpt-5.6-terra", .457),
                         ("conservative", "gpt-5.6-luna", .478), ("conservative", "gpt-5.6-terra", .402)):
    got = dv.group_homogeneity(dg[(arm, model)])[0]
    claim(abs(got - want) < .0015, f"diversity homogeneity {arm}/{model.split('-')[-1]} = {want:.3f} ({got:.3f})")
import math
def fisher(arm):
    ps = []
    for m in ("gpt-5.6-luna", "gpt-5.6-terra"):
        ps.append(dv.permutation_p(dg[(arm, m)], dg[("minimal", m)], n=10000)[1])
    chi = -2 * sum(math.log(max(p, 1e-12)) for p in ps)
    return ps, math.exp(-chi / 2) * (1 + chi / 2)
ps, fp = fisher("conservative")
claim(abs(fp - .463) < .01 and fp > .05, f"diversity validation Fisher p = .46, not supported ({fp:.3f})")
ps, fp = fisher("padded")
claim(abs(fp - .222) < .01 and fp > .05, f"diversity H1 Fisher p = .22, not supported ({fp:.3f})")
for arm, want in (("minimal", 5), ("padded", 2), ("conservative", 2)):
    got = dv.distinct(dg[(arm, "gpt-5.6-terra")])["accent_hues"]
    claim(got == want, f"terra distinct accent hues, {arm} = {want} ({got})")
dl = runs["diversity"]
def arm_mean(arm, k): return st.mean(r[k] for r in dl if r["arm"] == arm)
o0, s0 = arm_mean("minimal", "out_tokens"), arm_mean("minimal", "secs")
claim(abs(arm_mean("padded", "out_tokens") / o0 - 1.70) < .01, "diversity bulk +70% output tokens")
claim(abs(arm_mean("padded", "secs") / s0 - 2.04) < .01, "diversity bulk +104% latency")
claim(abs(arm_mean("conservative", "out_tokens") / o0 - 0.97) < .01, "diversity restriction -3% output tokens")
claim(abs(arm_mean("conservative", "secs") / s0 - 1.02) < .01, "diversity restriction +2% latency")
claim(abs(arm_mean("padded", "chars") / arm_mean("minimal", "chars") - 1.76) < .01, "diversity bulk +76% HTML size")

# positive control: criterion met, and for the predicted reason
pc = [json.loads(l) for l in open(ROOT / "poscontrol/grades.jsonl")]
pby = collections.defaultdict(list)
for d in pc:
    pby[d["arm"]].append(d)
score = lambda arm: st.mean(d["passed"] / d["total"] for d in pby[arm])
for arm, want in (("full", 1.000), ("minus_tiers", 0.916), ("minus_coupon", 0.912),
                  ("minus_tax", 0.738)):
    claim(abs(score(arm) - want) < 0.0015, f"poscontrol {arm} = {want:.1%} ({score(arm):.1%})")
claim(score("minus_tax") < 0.80, "positive-control criterion met (an arm below 80%)")
# 14 DISTINCT tax checks and 14 distinct total checks exist; three of the four
# runs failed all of them, so occurrences are 42 each. The claim is about which
# KINDS failed, so count distinct names, not occurrences.
failed_names = {x for d in pby["minus_tax"] for x in d["failed"]}
kinds = collections.Counter(x.split()[-1] for x in failed_names)
claim(set(kinds) == {"tax", "total"} and kinds["tax"] == 14 and kinds["total"] == 14,
      f"minus_tax failed ONLY tax and total checks, all 14 of each ({dict(kinds)})")
runs_failing = sum(1 for d in pby["minus_tax"] if d["failed"])
claim(runs_failing == 3, f"minus_tax failed in 3 of 4 runs ({runs_failing})")

# hard-task calibration: no task inside the pre-registered band
import subprocess
hard = [json.loads(l) for l in open(ROOT / "hard/grades.jsonl")]
by = collections.defaultdict(list)
for d in hard:
    by[d["task"]].append(d["passed"] / d["total"])
for task, want, checks in (("sheet", 0.955, 22), ("cart", 1.000, 80), ("form", 0.984, 31)):
    got = st.mean(by[task])
    claim(abs(got - want) < 0.005 and
          [d["total"] for d in hard if d["task"] == task][0] == checks,
          f"hard/{task} scores {want:.1%} over {checks} checks ({got:.1%})")
claim(not any(0.55 <= st.mean(v) <= 0.80 for v in by.values()),
      "no hard task falls inside the 55-80% admission band")

print(f"\n{len(fails)} mismatch(es)")
sys.exit(1 if fails else 0)
