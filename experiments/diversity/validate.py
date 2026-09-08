"""Check the diversity metric on existing data before any money is spent.

  1. a file against itself scores exactly 1.0
  2. repeated runs of the SAME brief (quiz vs quiz, table vs table, from the
     dose experiment) score more alike than runs of DIFFERENT briefs
  3. same-brief runs are not already at 1.0 -- there must be headroom for
     the experiment to detect further convergence
"""
import itertools, json, pathlib, statistics as st, subprocess, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from analyze import similarity, group_homogeneity

HERE = pathlib.Path(__file__).parent
feats = {}
for f in sorted((HERE.parent / "dose/out").glob("*.html")):
    out = subprocess.run(["node", str(HERE / "features.js"), str(f)],
                         capture_output=True, text=True)
    if out.stdout.startswith("{"):
        d = json.loads(out.stdout); d["task"] = f.stem.split("__")[1]; feats[f.name] = d
    else:
        print("  extractor failed:", f.name, out.stderr[:120])
print(f"extracted {len(feats)} of 48 dose files")

ok = lambda c, m: print(("  OK    " if c else "  FAIL  ") + m)
any_f = next(iter(feats.values()))
s = similarity(any_f, any_f)
ok(abs(s["primary"] - 1.0) < 1e-9, f"identity -> {s['primary']:.3f}")

quiz = [d for d in feats.values() if d["task"] == "quiz"]
table = [d for d in feats.values() if d["task"] == "table"]
wq, _ = group_homogeneity(quiz); wt, _ = group_homogeneity(table)
between = st.mean(similarity(a, b)["primary"] for a in quiz for b in table)
print(f"  within quiz {wq:.3f}   within table {wt:.3f}   between {between:.3f}")
ok(wq > between and wt > between, "same brief more alike than different briefs")
ok(wq < 0.95 and wt < 0.95, "headroom: same-brief runs are not already at ~1.0")
for k in ("struct", "hue", "feat"):
    a = group_homogeneity(quiz, k)[0]; b = group_homogeneity(table, k)[0]
    c = st.mean(similarity(x, y)[k] for x in quiz for y in table)
    print(f"        {k:6} within quiz {a:.3f}  within table {b:.3f}  between {c:.3f}")
