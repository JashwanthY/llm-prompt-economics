"""Where did the extra output go? Content audit of zero-padding vs heavy-padding
files across three experiments. If the padded files carry MORE of what the
padding asked for (ARIA, labels, focus styles, try/catch, comments...), the
padding bought something the grader never measured. If the unpadded files
already carry it, the model was doing it anyway and the extra tokens are bulk.
Offline; no API calls."""
import json, pathlib, re, statistics as st, sys

ROOT = pathlib.Path(__file__).parent.parent
PAIRS = [  # (label, glob for zero padding, glob for heavy padding)
    ("dose quiz",   "dose/out/*__quiz__L0_none__*.html",   "dose/out/*__quiz__L3_heavy__*.html"),
    ("dose table",  "dose/out/*__table__L0_none__*.html",  "dose/out/*__table__L3_heavy__*.html"),
    ("compliance",  "compliance/out/*__L0_none__*.html",   "compliance/out/*__L3_heavy__*.html"),
    ("dashboard",   "diversity/out/*__minimal__*.html",    "diversity/out/*__padded__*.html"),
]
FEATURES = {  # name: regex, counted per file
    "aria attrs":        r"\saria-[a-z]+=",
    "role attrs":        r"\srole=",
    "aria-live":         r"aria-live",
    "<label":            r"<label\b",
    "focus styles":      r":focus(-visible)?\s*[,{]",
    "reduced-motion":    r"prefers-reduced-motion",
    "semantic tags":     r"<(main|section|header|footer|nav|article|aside)\b",
    "custom props":      r"--[a-z][\w-]*\s*:",
    "rem units":         r"\d(\.\d+)?rem\b",
    "try/catch":         r"\bcatch\s*\(",
    "addEventListener":  r"addEventListener\(",
    "inline onclick":    r"\son[a-z]+=",
    "const/let":         r"\b(const|let)\s",
    "var":               r"\bvar\s",
    "debounce/throttle": r"debounce|throttle",
    "JS comments":       r"^\s*//|/\*",
    "HTML comments":     r"<!--",
    "!important":        r"!important",
}

def sizes(s):
    css = sum(len(m) for m in re.findall(r"<style\b.*?</style>", s, re.S | re.I))
    js = sum(len(m) for m in re.findall(r"<script\b.*?</script>", s, re.S | re.I))
    return {"css chars": css, "js chars": js, "markup chars": len(s) - css - js, "total chars": len(s)}

def audit(files):
    rows = []
    for f in files:
        s = f.read_text(errors="replace")
        r = {k: len(re.findall(p, s, re.M | re.I)) for k, p in FEATURES.items()}
        r.update(sizes(s)); rows.append(r)
    return {k: st.mean(r[k] for r in rows) for k in rows[0]}, len(rows)

out = {}
for label, g0, g3 in PAIRS:
    a, n0 = audit(sorted(ROOT.glob(g0))); b, n3 = audit(sorted(ROOT.glob(g3)))
    out[label] = {"n": (n0, n3), "L0": a, "L3": b}
    print(f"\n=== {label}  (n={n0} zero-padding vs n={n3} heavy-padding) ===")
    print(f"  {'feature':18} {'L0':>8} {'L3':>8} {'ratio':>7}")
    for k in list(FEATURES) + ["css chars", "js chars", "markup chars", "total chars"]:
        ratio = (b[k] / a[k]) if a[k] else float("inf") if b[k] else 1.0
        flag = "  <- padding asked for this" if k in ("aria attrs","aria-live","<label","focus styles",
                "reduced-motion","semantic tags","custom props","rem units","try/catch",
                "addEventListener","const/let","debounce/throttle","JS comments") and ratio > 1.5 else ""
        print(f"  {k:18} {a[k]:8.1f} {b[k]:8.1f} {ratio:7.2f}{flag}")
(ROOT / "audit/content.json").write_text(json.dumps(out, indent=2))
