"""Re-derive every numeric claim in paper-bloat/preprint.md from the raw logs.

Written because six separate defects in this study's own instruments each
produced a clean, plausible, wrong number. Run before any figure in the paper
is believed. Exits non-zero on the first mismatch. Experiment modules are
loaded by path because several directories share module names (design.py,
analyze.py) and a plain import resolves to whichever was inserted last.
"""
import collections, importlib.util, itertools, json, pathlib, random, re, statistics as st, sys
from math import comb

ROOT = pathlib.Path(__file__).parent


def load(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod


dose_design = load("dose_design", "dose/design.py")
compliance_check = load("compliance_check", "compliance/check.py")
dv = load("diversity_analyze", "diversity/analyze.py")
audit = load("audit_content", "audit/content.py") if False else None  # audit recomputed inline below
LEVELS = dose_design.LEVELS
MODELS = ("gpt-5.6-luna", "gpt-5.6-terra")

fails = []
def claim(cond, msg):
    print(("  OK    " if cond else "  WRONG ") + msg)
    if not cond:
        fails.append(msg)

def near(a, b, tol): return abs(a - b) <= tol
def pct(a, b): return b / a - 1

# ---------------------------------------------------------------- ladder
claim([len(v.split()) for v in LEVELS.values()] == [0, 68, 246, 811], "ladder is 0/68/246/811 words")

grades = {pathlib.Path(json.loads(l)["file"]).name: json.loads(l) for l in open(ROOT / "dose/grades.jsonl")}
dose = json.load(open(ROOT / "dose/runlog.json"))
by_lvl = collections.defaultdict(list)
for r in dose:
    r["grade"] = grades[f"{r['model']}__{r['task']}__{r['level']}__{r['trial']}.html"]
    by_lvl[r["level"]].append(r)
claim(all(len(v) == 12 for v in by_lvl.values()) and len(dose) == 48, "48 ladder runs, 12 per level")
mean = lambda rows, k: st.mean(r[k] for r in rows)
o0, o3 = mean(by_lvl["L0_none"], "out_tokens"), mean(by_lvl["L3_heavy"], "out_tokens")
s0, s3 = mean(by_lvl["L0_none"], "secs"), mean(by_lvl["L3_heavy"], "secs")
claim(near(o0, 3833, 1) and near(o3, 5428, 1), f"output tokens 3,833 -> 5,428 ({o0:.0f} -> {o3:.0f})")
claim(near(s0, 29.1, .05) and near(s3, 40.1, .05), f"latency 29.1 -> 40.1 ({s0:.1f} -> {s3:.1f})")
claim(near(pct(o0, o3), .42, .005), "+42% output tokens at L3")
claim(near(pct(s0, s3), .38, .005), "+38% latency at L3")
for lvl, wo, ws in (("L1_light", .08, .08), ("L2_mid", .26, .26)):
    claim(near(pct(o0, mean(by_lvl[lvl], "out_tokens")), wo, .006) and near(pct(s0, mean(by_lvl[lvl], "secs")), ws, .006),
          f"{lvl}: +{wo:.0%} tokens, +{ws:.0%} latency")
c0, c3 = mean(by_lvl["L0_none"], "chars"), mean(by_lvl["L3_heavy"], "chars")
claim(near(c0, 12143, 40) and near(c3, 18157, 40) and near(pct(c0, c3), .50, .01),
      f"file size 12.1k -> 18.2k, +50% ({c0:.0f} -> {c3:.0f}, {pct(c0, c3):+.0%})")
xs, ys = [r["out_tokens"] for r in dose], [r["secs"] for r in dose]
mx, my = st.mean(xs), st.mean(ys)
corr = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / (sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys)) ** .5
claim(corr > 0.8, f"output tokens explain most latency variance (r = {corr:.2f})")

# bootstrap intervals, seeded and in the same draw order as when first computed
random.seed(0)
def boot(vals, n=10000):
    s = sorted(st.mean(random.choices(vals, k=len(vals))) for _ in range(n))
    return s[int(.025 * n)], s[int(.975 * n)]
ci = {}
for lvl in LEVELS:
    ci[lvl] = (boot([r["out_tokens"] for r in by_lvl[lvl]]), boot([r["secs"] for r in by_lvl[lvl]]))
claim(near(ci["L0_none"][0][0], 3549, 8) and near(ci["L0_none"][0][1], 4105, 8), f"L0 token CI [3549, 4105] ({ci['L0_none'][0]})")
claim(near(ci["L3_heavy"][0][0], 5119, 8) and near(ci["L3_heavy"][0][1], 5701, 8), f"L3 token CI [5119, 5701] ({ci['L3_heavy'][0]})")
claim(near(ci["L0_none"][1][0], 26.6, .25) and near(ci["L0_none"][1][1], 31.6, .25), f"L0 latency CI [26.6, 31.6]")
claim(near(ci["L3_heavy"][1][0], 37.3, .25) and near(ci["L3_heavy"][1][1], 42.9, .25), f"L3 latency CI [37.3, 42.9]")

key = lambda r: (r["task"], r["model"], r["trial"])
lo, hi = {key(r): r for r in by_lvl["L0_none"]}, {key(r): r for r in by_lvl["L3_heavy"]}
d_out = [hi[k]["out_tokens"] - lo[k]["out_tokens"] for k in lo]
d_sec = [hi[k]["secs"] - lo[k]["secs"] for k in lo]
claim(len(d_out) == 12 and all(x > 0 for x in d_out) and all(x > 0 for x in d_sec), "all 12 paired L0->L3 deltas positive, both measures")
claim(near(st.mean(d_out), 1595, 1) and near(st.mean(d_sec), 11.0, .05), "paired deltas +1,595 tokens, +11.0 s")
cb_out, cb_sec = boot(d_out), boot(d_sec)
claim(near(cb_out[0], 1241, 8) and near(cb_out[1], 1989, 8), f"paired token CI [+1241, +1989] ({cb_out})")
claim(near(cb_sec[0], 8.7, .25) and near(cb_sec[1], 13.3, .25), f"paired latency CI [+8.7, +13.3] ({cb_sec})")
p_sign = sum(comb(12, i) for i in range(12, 13)) / 2 ** 12
claim(near(p_sign, 0.00024, 0.00002), f"one-sided sign test p = 0.00024 ({p_sign:.5f})")

perfect = sum(1 for r in dose if r["grade"]["passed"] == r["grade"]["total"])
bad = [r for r in dose if r["grade"]["passed"] < r["grade"]["total"]]
claim(perfect == 47 and len(bad) == 1 and bad[0]["level"] == "L0_none", "47 of 48 perfect; the single defect at zero guidance")
claim("closest" in str(bad[0]["grade"]["errors"]), "the defect is the RadioNodeList .closest error")
claim(max(sum(1 for r in by_lvl[l] if r["grade"]["passed"] < r["grade"]["total"]) for l in LEVELS) <= 1,
      "at most one failure in twelve runs per level (basis of the ~25% MDE statement)")

# ---------------------------------------------------------------- pilots
for d, model, want in (("bloat-pilot", "gpt-5.6-luna", .40), ("bloat-pilot", "gpt-5.6-terra", .51),
                       ("bloat-pilot-da", "gpt-5.6-luna", .45), ("bloat-pilot-da", "gpt-5.6-terra", .85)):
    lg = json.load(open(ROOT / d / "runlog.json"))
    a = collections.defaultdict(list)
    for r in lg: a[(r["model"], r["arm"])].append(r["secs"])
    claim(near(pct(st.mean(a[(model, "A_minimal")]), st.mean(a[(model, "B_padded")])), want, .006), f"{d} {model.split('-')[-1]} latency {want:+.0%}")
da = json.load(open(ROOT / "bloat-pilot-da/runlog.json"))
turns = collections.defaultdict(list)
for r in da: turns[r["arm"]].append(r["turns"])
claim(all(4 <= t <= 6 for v in turns.values() for t in v) and len(da) == 20, "agent-loop pilot: turns 4-6 in both arms, n=5 per cell")
claim(len(json.load(open(ROOT / "bloat-pilot/runlog.json"))) == 16, "direct pilot n=4 per cell (16 runs)")
bp = load("bloat_prompts", "bloat-pilot/prompts.py")
claim(len(bp.PADDING.split()) == 429, f"pilot guidance is 429 words ({len(bp.PADDING.split())})")
# The third-party skill pilot is withdrawn; experiments/longskill replaces it
# with an artifact composed for this study, at n=3 rather than n=1.
ls_ = json.load(open(ROOT / "longskill/runlog.json"))
lb = collections.defaultdict(list)
for r in ls_:
    lb[r["arm"]].append(r)
claim(len(ls_) == 12 and all(len(lb[a]) == 6 for a in ("contracts", "full")),
      "longskill: 12 interleaved runs, 6 per arm")
lm = lambda a, k: st.mean(x[k] for x in lb[a])
claim(near(pct(lm("contracts", "out_tokens"), lm("full", "out_tokens")), .04, .006), "skill scale +4% output tokens")
claim(near(pct(lm("contracts", "secs"), lm("full", "secs")), .03, .006), "skill scale +3% latency")
lp = {(x["arm"], x["model"], x["trial"]): x for x in ls_}
lk = sorted({(m_, t) for (_, m_, t) in lp})
claim(sum(lp[("full", *k)]["out_tokens"] > lp[("contracts", *k)]["out_tokens"] for k in lk) == 4,
      "skill scale: output rose in 4 of 6 paired cells")
for mod, want in (("gpt-5.6-luna", .11), ("gpt-5.6-terra", -.01)):
    f = lambda a: st.mean(x["out_tokens"] for x in lb[a] if x["model"] == mod)
    claim(near(pct(f("contracts"), f("full")), want, .006), f"skill scale {mod.split('-')[-1]} {want:+.0%}")
_ld = load("longskill_design", "longskill/design.py")
fw, cw = len(_ld.ARMS["full"].split()), len(_ld.ARMS["contracts"].split())
claim(fw == 5840 and cw == 1094, f"skill arms 5,840 vs 1,094 words ({fw} vs {cw})")
claim(_ld.TASK == dose_design.TASK_TABLE, "skill scale uses the dose table task verbatim")

# ---------------------------------------------------------------- compliance
cfiles = sorted((ROOT / "compliance/out").glob("*.html"))
cm = [(f, compliance_check.check(f)) for f in cfiles]
claim(len(cm) == 24, "24 compliance files")
claim(sum(x["hex"] for _, x in cm) == 1 and all("L1_light" in f.name for f, x in cm if x["hex"]), "one hex outside :root, at L1")
claim(sum(x["bad_id_prefix"] for _, x in cm) == 1 and all("L1_light" in f.name for f, x in cm if x["bad_id_prefix"]), "one unprefixed id, at L1")
claim(sum(x["inline_handlers"] + x["missing_testid"] + x["innerHTML"] for _, x in cm) == 0, "three rules never broken at any level")
clog = json.load(open(ROOT / "compliance/runlog.json"))
# The old cross-experiment rules-vs-guidance comparison is withdrawn: the
# compliance and dose table prompts are not the same text (152 vs 192 words) and
# the two ran in different sessions. experiments/rulescost replaces it with one
# identical task text across interleaved arms.
rc = json.load(open(ROOT / "rulescost/runlog.json"))
rb = collections.defaultdict(list)
for r in rc:
    rb[r["arm"]].append(r)
claim(len(rc) == 18 and all(len(rb[a]) == 6 for a in ("bare", "rules", "restraint")),
      "rulescost: 18 interleaved runs, 6 per arm")
rm = lambda a, k: st.mean(x[k] for x in rb[a])
b_o, b_s, b_c = rm("bare", "out_tokens"), rm("bare", "secs"), rm("bare", "chars")
claim(near(b_o, 4253, 1) and near(rm("rules", "out_tokens"), 5170, 1)
      and near(rm("restraint", "out_tokens"), 2949, 1), "rulescost tokens 4,253 / 5,170 / 2,949")
claim(near(pct(b_o, rm("rules", "out_tokens")), .22, .006), "rules +22% output tokens")
claim(near(pct(b_o, rm("restraint", "out_tokens")), -.31, .006), "restraint -31% output tokens")
claim(near(pct(b_s, rm("rules", "secs")), .17, .006) and near(pct(b_s, rm("restraint", "secs")), -.33, .006),
      "rules +17% latency, restraint -33% latency")
claim(near(pct(b_c, rm("rules", "chars")), .17, .006) and near(pct(b_c, rm("restraint", "chars")), -.32, .006),
      "rules +17% size, restraint -32% size")
rp = {(x["arm"], x["model"], x["trial"]): x["out_tokens"] for x in rc}
ks = sorted({(m_, t) for (_, m_, t) in rp})
claim(sum(rp[("rules", *k)] > rp[("bare", *k)] for k in ks) == 6
      and sum(rp[("restraint", *k)] < rp[("bare", *k)] for k in ks) == 6,
      "rules rose in 6/6 paired cells, restraint fell in 6/6")
for mod, wr, ws in (("gpt-5.6-luna", .19, -.27), ("gpt-5.6-terra", .24, -.34)):
    f = lambda a: st.mean(x["out_tokens"] for x in rb[a] if x["model"] == mod)
    claim(near(pct(f("bare"), f("rules")), wr, .006) and near(pct(f("bare"), f("restraint")), ws, .006),
          f"rulescost {mod.split('-')[-1]}: rules {wr:+.0%}, restraint {ws:+.0%}")
# Cross-check the per-model figures the prose quotes, since the earlier draft
# said -31% for luna where the data says -27% and no check caught it.
prose = (ROOT.parent / "paper-bloat/preprint.md").read_text()
claim("(+19%/\u221227% and +24%/\u221234%)" in prose,
      "prose quotes the measured per-model split (+19%/-27% and +24%/-34%)")

# the arms are matched in length -- this is what makes the contrast a test of
# what a line asks for rather than of how long it is
_rd = load("rulescost_design", "rulescost/design.py")
claim(abs(len(_rd.RULES.split()) - len(_rd.RESTRAINT.split())) <= 6,
      f"arms matched in length ({len(_rd.RULES.split())} vs {len(_rd.RESTRAINT.split())} words)")
claim(_rd.TASK == dose_design.TASK_TABLE, "rulescost uses the dose table task text verbatim")

# ---------------------------------------------------------------- content audit
FEAT = {"aria": r"\saria-[a-z]+=", "rem": r"\d(\.\d+)?rem\b", "props": r"--[a-z][\w-]*\s*:",
        "semantic": r"<(main|section|header|footer|nav|article|aside)\b", "rm": r"prefers-reduced-motion",
        "constlet": r"\b(const|let)\s", "ael": r"addEventListener\(", "onclick": r"\son[a-z]+=", "var": r"\bvar\s",
        "catch": r"\bcatch\s*\(", "comment": r"^\s*//|/\*"}
def feats(files):
    rows = []
    for f in files:
        s = f.read_text(errors="replace")
        rows.append({k: len(re.findall(p, s, re.M | re.I)) for k, p in FEAT.items()} |
                    {"js": sum(len(m) for m in re.findall(r"<script\b.*?</script>", s, re.S | re.I)),
                     # findall with a group returns the GROUP, not the match, so a
                     # backreferenced <(script|style)> pattern measures len("script").
                     "markup": len(s)
                               - sum(len(m) for m in re.findall(r"<style\b.*?</style>", s, re.S | re.I))
                               - sum(len(m) for m in re.findall(r"<script\b.*?</script>", s, re.S | re.I))})
    return {k: st.mean(r[k] for r in rows) for k in rows[0]}, [r["rm"] > 0 for r in rows]
dL0, rm0 = feats(sorted((ROOT / "dose/out").glob("*__L0_none__*.html")))
dL3, rm3 = feats(sorted((ROOT / "dose/out").glob("*__L3_heavy__*.html")))
claim(sum(rm0) == 0 and len(rm0) == 12 and sum(rm3) == 12, "reduced-motion in 0 of 12 L0 files and 12 of 12 L3 files")
for k, a, b, lbl in (("aria", 7.25, 14.08, "ARIA 7.3 -> 14.1"), ("rem", 4.83, 38.5, "rem 4.8 -> 38.5"),
                     ("props", 7.92, 18.75, "custom properties 7.9 -> 18.8"), ("semantic", 3.67, 7.25, "semantic 3.7 -> 7.3"),
                     ("constlet", 22.5, 36.5, "const/let 22.5 -> 36.5"), ("ael", 4.5, 4.58, "addEventListener 4.5 -> 4.6")):
    claim(near(dL0[k], a, .06) and near(dL3[k], b, .06), f"audit dose {lbl} ({dL0[k]:.2f} -> {dL3[k]:.2f})")
claim(all(dL0[k] == 0 and dL3[k] == 0 for k in ("onclick", "var", "catch", "comment")), "audit dose: no inline onclick, var, catch or comments at any level")
gL0, grm0 = feats(sorted((ROOT / "diversity/out").glob("*__minimal__*.html")))
gL3, grm3 = feats(sorted((ROOT / "diversity/out").glob("*__padded__*.html")))
claim(sum(grm0) == 0 and sum(grm3) == 12, "dashboard: reduced-motion 0 -> 12 of 12")
for k, a, b, lbl in (("aria", 2.5, 25.08, "ARIA 2.5 -> 25.1"), ("rem", 0.0, 81.17, "rem 0 -> 81.2"),
                     ("props", 12.33, 25.42, "custom properties 12.3 -> 25.4"), ("semantic", 8.83, 14.67, "semantic 8.8 -> 14.7"),
                     ("constlet", 7.25, 39.25, "const/let 7.3 -> 39.3"), ("ael", 0.58, 4.17, "addEventListener 0.6 -> 4.2")):
    claim(near(gL0[k], a, .06) and near(gL3[k], b, .06), f"audit dashboard {lbl} ({gL0[k]:.2f} -> {gL3[k]:.2f})")
claim(near(gL0["js"], 1272, 5) and near(gL3["js"], 7939, 5) and near(gL3["js"] / gL0["js"], 6.2, .1), f"dashboard JS 1,272 -> 7,939 chars, ~6x")
claim(0.99 <= gL3["markup"] / gL0["markup"] <= 1.02, f"dashboard markup flat ({gL0['markup']:.0f} -> {gL3['markup']:.0f})")

# ---------------------------------------------------------------- hard tasks, positive control
hard = [json.loads(l) for l in open(ROOT / "hard/grades.jsonl")]
hb = collections.defaultdict(list)
for d in hard: hb[d["task"]].append(d["passed"] / d["total"])
for task, want, checks in (("sheet", .955, 22), ("cart", 1.0, 80), ("form", .984, 31)):
    claim(near(st.mean(hb[task]), want, .0015) and [d["total"] for d in hard if d["task"] == task][0] == checks, f"hard/{task} {want:.1%} over {checks} checks")
claim(not any(.55 <= st.mean(v) <= .80 for v in hb.values()), "no hard task inside the 55-80% band")
pc = [json.loads(l) for l in open(ROOT / "poscontrol/grades.jsonl")]
pb = collections.defaultdict(list)
for d in pc: pb[d["arm"]].append(d)
score = lambda a: st.mean(d["passed"] / d["total"] for d in pb[a])
for a, w in (("full", 1.0), ("minus_tiers", .916), ("minus_coupon", .912), ("minus_tax", .738)):
    claim(near(score(a), w, .0015), f"positive control {a} = {w:.1%}")
claim(score("minus_tax") < .80, "positive-control criterion met")
names = {x for d in pb["minus_tax"] for x in d["failed"]}
kinds = collections.Counter(x.split()[-1] for x in names)
claim(set(kinds) == {"tax", "total"} and kinds["tax"] == 14 and kinds["total"] == 14, "minus_tax: only tax and total, all 14 of each")
claim(sum(1 for d in pb["minus_tax"] if d["failed"]) == 3, "minus_tax failed in 3 of 4 runs")
claim(near(100 * (score("full") - score("minus_tax")), 26.2, .2), "26-point drop")

# ---------------------------------------------------------------- diversity
feat = [json.loads(l) for l in open(ROOT / "diversity/features.jsonl")]
dg = collections.defaultdict(list)
for f in feat: dg[(f["arm"], f["model"])].append(f)
claim(len(dg) == 6 and all(len(v) == 6 for v in dg.values()), "diversity: 6 runs x 3 arms x 2 models")
def exact_p(arm, m):
    A, B = dg[(arm, m)], dg[("minimal", m)]; pool = A + B; n = len(A)
    sim = {(i, j): dv.similarity(pool[i], pool[j])["primary"] for i, j in itertools.combinations(range(len(pool)), 2)}
    h = lambda ids: st.mean(sim[(min(i, j), max(i, j))] for i, j in itertools.combinations(ids, 2))
    obs = h(range(n)) - h(range(n, len(pool)))
    hits = tot = 0
    for c in itertools.combinations(range(len(pool)), n):
        rest = [i for i in range(len(pool)) if i not in c]; tot += 1; hits += (h(c) - h(rest)) >= obs - 1e-12
    return obs, hits / tot
ps = {}
for arm in ("conservative", "padded"):
    for m in MODELS:
        ps[(arm, m)] = exact_p(arm, m)
claim(near(ps[("conservative", MODELS[0])][1], .977, .002) and near(ps[("conservative", MODELS[1])][1], .171, .002), "restriction vs minimal: exact p .977 (luna), .171 (terra)")
claim(near(ps[("padded", MODELS[0])][1], .962, .002) and near(ps[("padded", MODELS[1])][1], .060, .002), "bulk vs minimal: exact p .962 (luna), .060 (terra)")
pmin, pmax = min(v[1] for v in ps.values()), max(v[1] for v in ps.values())
claim(pmin > .05 and round(pmin, 2) == .06 and round(pmax, 2) == .98,
      f"convergence test inconclusive: p from .06 to .98 ({pmin:.4f}-{pmax:.4f})")
claim((ps[("padded", MODELS[0])][0] < 0) != (ps[("padded", MODELS[1])][0] < 0) and (ps[("conservative", MODELS[0])][0] < 0) != (ps[("conservative", MODELS[1])][0] < 0),
      "the two models move in opposite directions under both bulk and restriction")
for arm, w in (("minimal", 5), ("padded", 2), ("conservative", 2)):
    claim(dv.distinct(dg[(arm, MODELS[1])])["accent_hues"] == w, f"terra distinct accent hues {arm} = {w}")
lu = {arm: {k: dv.group_homogeneity(dg[(arm, MODELS[0])], k)[0] for k in ("struct", "hue", "feat")} for arm in ("minimal", "padded", "conservative")}
claim(all(lu["padded"][k] < lu["minimal"][k] for k in ("struct", "hue", "feat"))
      and lu["conservative"]["struct"] < lu["minimal"]["struct"]
      and lu["conservative"]["hue"] < lu["minimal"]["hue"]
      and abs(lu["conservative"]["feat"] - lu["minimal"]["feat"]) < 1e-9,
      "luna: less alike on every component under bulk; two of three under restriction, third unchanged")
dl = json.load(open(ROOT / "diversity/runlog.json"))
am = lambda arm, k: st.mean(r[k] for r in dl if r["arm"] == arm)
claim(near(pct(am("minimal", "out_tokens"), am("padded", "out_tokens")), .70, .006) and near(pct(am("minimal", "secs"), am("padded", "secs")), 1.04, .006), "bulk +70% tokens, +104% latency")
claim(near(pct(am("minimal", "out_tokens"), am("conservative", "out_tokens")), -.03, .006) and near(pct(am("minimal", "secs"), am("conservative", "secs")), .02, .006), "restriction -3% tokens, +2% latency")
claim(near(pct(am("minimal", "chars"), am("padded", "chars")), .76, .006) and near(pct(am("minimal", "chars"), am("conservative", "chars")), -.02, .006), "bulk +76% file size, restriction -2%")
claim(near(am("minimal", "out_tokens"), 5114, 1) and near(am("minimal", "secs"), 38.7, .05), "diversity minimal 5,114 tokens, 38.7 s")

# ---------------------------------------------------------------- totals
runs = {d: json.load(open(ROOT / d / "runlog.json")) for d in
        ("bloat-pilot", "bloat-pilot-da", "dose", "compliance", "hard", "poscontrol", "diversity", "rulescost", "longskill")}
total = sum(len(v) for v in runs.values())
claim(total == 198, f"198 runs total ({total})")
spend = sum(r.get("in_tokens", 0) for v in runs.values() for r in v) / 1e6 * 1.25 + sum(r.get("out_tokens", 0) for v in runs.values() for r in v) / 1e6 * 10
claim(near(spend, 18.12, .015), f"total spend $18.12 (${spend:.2f})")

print(f"\n{len(fails)} mismatch(es)")
sys.exit(1 if fails else 0)
