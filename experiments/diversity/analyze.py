"""Diversity metric, pairwise within arm and model, with permutation tests.

Usage:
  python3 analyze.py features.jsonl          -- experiment groups by arm/model
  (validate.py imports the functions to check the metric on existing data)
"""
import collections, colorsys, difflib, itertools, json, random, re, statistics as st, sys

HEX = re.compile(r"#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})(?![0-9a-fA-F])")
RGB = re.compile(r"rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)")
HSL = re.compile(r"hsla?\(\s*([\d.]+)(?:deg)?\s*,\s*([\d.]+)%\s*,\s*([\d.]+)%")
FONT = re.compile(r"font-family\s*:\s*([^;}]+)", re.I)


def hues(css):
    """Chromatic hue bins (12 x 30 deg) declared anywhere in the CSS."""
    cols = []
    for h in HEX.findall(css):
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        cols.append(tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)))
    for r, g, b in RGB.findall(css):
        cols.append((int(r) / 255, int(g) / 255, int(b) / 255))
    for h, s, l in HSL.findall(css):
        cols.append(colorsys.hls_to_rgb(float(h) / 360, float(l) / 100, float(s) / 100))
    bins = collections.Counter()
    for r, g, b in cols:
        h, l, s = colorsys.rgb_to_hls(r, g, b)
        if s >= 0.20 and 0.15 <= l <= 0.85:          # chromatic, not grey/black/white
            bins[int(h * 12) % 12] += 1
    return bins


def fonts(css):
    out = set()
    for m in FONT.findall(css):
        first = m.split(",")[0].strip().strip("'\"").lower()
        if first and not first.startswith("var("):
            out.add(first)
    return out


def layout(feat):
    css, c = feat["css"], feat["counts"]
    radius = [int(x) for x in re.findall(r"border-radius\s*:\s*(\d+)px", css)]
    return {
        "grid": bool(re.search(r"display\s*:\s*grid|grid-template", css)),
        "flex": bool(re.search(r"display\s*:\s*flex", css)),
        "aside": c["aside"] > 0,
        "nav": c["nav"] > 0,
        "chart": "svg" if c["svg"] else ("canvas" if c["canvas"] else "none"),
        "table": c["table"] > 0,
        "gradient": "gradient(" in css,
        "shadow": "box-shadow" in css,
        "radius": "none" if not radius else ("small" if max(radius) <= 6 else
                  "medium" if max(radius) <= 14 else "large"),
    }


def similarity(a, b):
    s_struct = difflib.SequenceMatcher(None, a["tags"], b["tags"], autojunk=False).ratio()
    ha, hb = set(hues(a["css"])), set(hues(b["css"]))
    s_hue = 1.0 if not (ha | hb) else len(ha & hb) / len(ha | hb)
    la, lb = layout(a), layout(b)
    s_feat = sum(la[k] == lb[k] for k in la) / len(la)
    return {"primary": (s_struct + s_hue) / 2, "struct": s_struct, "hue": s_hue, "feat": s_feat}


def group_homogeneity(feats, key="primary"):
    pairs = [similarity(a, b)[key] for a, b in itertools.combinations(feats, 2)]
    return st.mean(pairs) if pairs else float("nan"), pairs


def permutation_p(group_a, group_b, key="primary", n=10000, seed=0):
    """One-sided: is homogeneity(a) - homogeneity(b) larger than chance relabelling?"""
    obs = group_homogeneity(group_a, key)[0] - group_homogeneity(group_b, key)[0]
    pool = group_a + group_b
    na = len(group_a)
    rng = random.Random(seed)
    # cache pairwise sims once; permutations only re-partition indices
    idx = list(range(len(pool)))
    sim = {}
    for i, j in itertools.combinations(idx, 2):
        sim[(i, j)] = similarity(pool[i], pool[j])[key]
    def homog(ids):
        ps = [sim[(min(i, j), max(i, j))] for i, j in itertools.combinations(ids, 2)]
        return st.mean(ps)
    hits = 0
    for _ in range(n):
        rng.shuffle(idx)
        d = homog(idx[:na]) - homog(idx[na:])
        if d >= obs - 1e-12:
            hits += 1
    return obs, hits / n


def distinct(feats):
    acc = collections.Counter()
    for f in feats:
        h = hues(f["css"])
        acc[h.most_common(1)[0][0] if h else "none"] += 1
    return {
        "accent_hues": len(acc),
        "font_families": len(set().union(*(fonts(f["css"]) for f in feats))),
        "layout_vectors": len({tuple(sorted(layout(f).items())) for f in feats}),
    }


if __name__ == "__main__":
    feats = [json.loads(l) for l in open(sys.argv[1])]
    sys.path.insert(0, __file__.rsplit("/", 1)[0])
    from design import MODELS, PERMUTATIONS
    groups = collections.defaultdict(list)
    for f in feats:
        groups[(f["arm"], f["model"])].append(f)
    print(f"{'arm':13} {'model':14} {'n':>2} {'homog':>6} {'struct':>6} {'hue':>6} "
          f"{'feat':>6}   {'accents':>7} {'fonts':>5} {'layouts':>7}")
    for (arm, model), fs in sorted(groups.items()):
        h = {k: group_homogeneity(fs, k)[0] for k in ("primary", "struct", "hue", "feat")}
        d = distinct(fs)
        print(f"{arm:13} {model:14} {len(fs):>2} {h['primary']:6.3f} {h['struct']:6.3f} "
              f"{h['hue']:6.3f} {h['feat']:6.3f}   {d['accent_hues']:>7} "
              f"{d['font_families']:>5} {d['layout_vectors']:>7}")
    print("\nPre-registered tests (one-sided permutation, within model, pooled by "
          "averaging p across models via Fisher):")
    import math
    for arm, label in (("conservative", "METRIC VALIDATION"), ("padded", "H1")):
        ps, obs_all = [], []
        for m in MODELS:
            obs, p = permutation_p(groups[(arm, m)], groups[("minimal", m)], n=PERMUTATIONS)
            ps.append(p); obs_all.append(obs)
            print(f"  {label:17} {arm:13} vs minimal  {m:14} delta {obs:+.3f}  p={p:.4f}")
        chi = -2 * sum(math.log(max(p, 1e-12)) for p in ps)
        # Fisher's method, 2 tests -> chi-square with 4 df: survival = e^{-x/2}(1 + x/2)
        fisher = math.exp(-chi / 2) * (1 + chi / 2)
        print(f"  {label:17} {arm:13} combined (Fisher)                  p={fisher:.4f}  "
              f"{'SUPPORTED' if fisher < .05 else 'not supported'}")
