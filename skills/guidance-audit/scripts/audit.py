"""Audit a system prompt: which of its generic lines are doing anything?

Three buckets, decided by running the task WITHOUT the guidance and looking at
what the model does anyway:

  already-followed  the model does it unprompted  -> the line is dead weight
  ignored           the model never does it       -> the line is dead weight
  only-when-asked   the line is why you get it    -> keep IF you want the feature

The third bucket is a feature you are buying, not waste. This tool reports; it
never deletes. Deciding whether you want reduced-motion support is a product
question, not a prompt question.

Commands
  classify <prompt>                     free, static: split contract / restraint / guidance
  report   <prompt> --off '<glob>'      free: bucket the lines using output you already have
  measure  <prompt> --task <file>       costs money: runs the task with guidance removed

`report` is the honest core: `measure` only produces the files that `report` reads.
"""
import argparse, glob, json, pathlib, re, statistics as st, sys

HERE = pathlib.Path(__file__).parent
SIGS = json.loads((HERE.parent / "references/signatures.json").read_text())

# A line that asks the model to do LESS costs nothing to include (measured:
# -3% output tokens, +2% latency, n=6 per model -- but with opposite signs per
# model, so this is "no detectable cost", not "provably free").
RESTRAINT = re.compile(
    r"\b(never|do not|don't|avoid|refrain|omit|exclude|must not|prefer not)\b", re.I)
WORK = re.compile(r"\b(use|add|include|ensure|write|provide|apply|set|define|"
                  r"implement|support|handle|render|show|display)\b", re.I)

# Deliberately NOT trying to auto-detect project-specific "contract" lines.
# An earlier version did, with a regex for identifier-ish tokens, and classified
# 46 of 61 lines of pure generic guidance as contract because
# "prefers-reduced-motion" is hyphenated. Anything the signature library does not
# recognise is returned as "review" -- the honest answer, since a false
# "contract" hides a deletable line and a false "guidance" risks advising the
# deletion of a project requirement.


def directives(text):
    """Split a prompt into candidate directive lines, dropping structure."""
    out, in_fence = [], False
    for i, raw in enumerate(text.splitlines(), 1):
        s = raw.strip()
        if s.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence or not s:
            continue
        if s.startswith("#") or s.startswith("---") or s.startswith("|"):
            continue
        s = re.sub(r"^[-*+]\s+|^\d+[.)]\s+", "", s)
        if len(s.split()) < 3:
            continue
        out.append((i, s))
    return out


def classify_line(s, sig):
    """guidance if the signature library recognises it; restraint if it asks for
    less and not for more; otherwise review by hand."""
    if sig:
        return "guidance"
    if RESTRAINT.search(s) and not WORK.search(s):
        return "restraint"
    return "review"


def _kw(k):
    """Whole-token match. Plain substring search matched "aria" inside
    "variable", "let" inside "complete", "const" inside "constraint" and "rem"
    inside "remove" -- which labelled project-specific contract lines as generic
    guidance, the one direction that could advise deleting a real requirement."""
    return re.compile(r"(?<![\w-])" + re.escape(k) + r"(?![\w-])", re.I)


for _sig in SIGS["signatures"]:
    _sig["_kw"] = [_kw(k) for k in _sig["keywords"]]


def match_signature(s):
    best = None
    for sig in SIGS["signatures"]:
        hits = sum(1 for rx in sig["_kw"] if rx.search(s))
        if hits and (best is None or hits > best[0]):
            best = (hits, sig)
    return best[1] if best else None


def count(sig, text):
    n = len(re.findall(sig["regex"], text, re.M | re.I))
    return (0 if n else 1) if sig.get("inverted") else n


def cmd_classify(args):
    lines = directives(pathlib.Path(args.prompt).read_text())
    groups = {"guidance": [], "restraint": [], "review": []}
    sigs = {}
    for ln, s in lines:
        sig = match_signature(s)
        k = classify_line(s, sig)
        groups[k].append((ln, s))
        if sig:
            sigs[ln] = sig
    print(f"{args.prompt}: {len(lines)} directive lines\n")
    print(f"  guidance   {len(groups['guidance']):4}  recognised generic directive -- AUDITABLE")
    print(f"  restraint  {len(groups['restraint']):4}  asks for less -- no detectable cost")
    print(f"  review     {len(groups['review']):4}  unrecognised -- judge by hand, bias toward keeping\n")
    for ln, s in groups["guidance"]:
        sg = sigs[ln]
        print(f"  L{ln:<5} [{sg['id']:22}] prior: {sg['observed']:16} {s[:56]}")
    if groups["review"]:
        print(f"\n  {len(groups['review'])} lines have no mechanical signature. These may be project")
        print("  requirements the model cannot infer, or guidance this library does not know.")
        print("  The audit says nothing about them; do not delete on its say-so.")
    groups["_sigs"] = sigs
    return groups


# Padded output is simply bigger, so a raw count rises with file size even when
# the model's behaviour has not changed. Counts are therefore compared per 10KB.
# The first version of this compared raw counts and called `rem` units
# "already-followed, delete" on an off=4.8 -> on=38.5 signal, which would have
# advised deleting the line responsible for most of the rem usage.
DENSITY = 10_000
AMPLIFIED_AT = 1.25    # on/off density ratio above which the line is doing work
PRESENT_AT = 0.5       # per-10KB density below which we treat a signal as absent


def densities(sig, texts):
    return [count(sig, t) / max(len(t), 1) * DENSITY for t in texts]


def bucket(off_d, on_d=None):
    off = st.mean(off_d) if off_d else 0.0
    if on_d is None:
        return ("present-without-it" if off >= PRESENT_AT else "absent-without-it"), off, None
    on = st.mean(on_d)
    if off < PRESENT_AT and on < PRESENT_AT:
        return "ignored", off, on
    if off < PRESENT_AT:
        return "only-when-asked", off, on
    return ("amplified" if on / off >= AMPLIFIED_AT else "already-followed"), off, on


def cmd_report(args):
    groups = cmd_classify(args)
    off_files = [pathlib.Path(p).read_text(errors="replace") for p in sorted(glob.glob(args.off))]
    on_files = [pathlib.Path(p).read_text(errors="replace") for p in sorted(glob.glob(args.on))] if args.on else None
    if not off_files:
        sys.exit(f"no files matched --off {args.off!r}")
    print(f"\n{'='*72}\nAUDIT  off-arm: {len(off_files)} files"
          + (f"   on-arm: {len(on_files)} files" if on_files else "   (no on-arm: only 'already-followed' is decidable)"))
    print("=" * 72)
    seen, rows = set(), []
    for ln, s in groups["guidance"]:
        sig = groups["_sigs"].get(ln)
        if not sig or sig["id"] in seen:
            continue
        seen.add(sig["id"])
        b, off, on = bucket(densities(sig, off_files),
                            densities(sig, on_files) if on_files else None)
        rows.append((b, sig["id"], ln, off, on, s))
    order = {"already-followed": 0, "ignored": 1, "amplified": 2, "only-when-asked": 3,
             "present-without-it": 4, "absent-without-it": 5}
    rows.sort(key=lambda r: (order[r[0]], r[1]))
    verdict = {
        "already-followed": "DELETE -- same density with or without your line",
        "ignored": "DELETE -- absent either way; the model does not do this",
        "amplified": "KEEP if you want more of it -- your line multiplies what you get",
        "only-when-asked": "KEEP if you want the feature -- absent entirely without your line",
        "present-without-it": "candidate only -- add --on to see if your line multiplies it",
        "absent-without-it": "candidate only -- add --on to see if your line produces it"}
    cur = None
    for b, sid, ln, off, on, s in rows:
        if b != cur:
            cur = b
            print(f"\n  {b.upper()}  ({verdict[b]})")
        det = (f"{off:.1f}->{on:.1f}/10KB  x{on/off:.1f}" if on is not None and off > 0
               else f"{off:.1f}->{on:.1f}/10KB" if on is not None else f"{off:.1f}/10KB")
        print(f"    L{ln:<5} {sid:22} {det:18} {s[:48]}")
    n_del = sum(1 for r in rows if r[0] in ("already-followed", "ignored"))
    n_keep = sum(1 for r in rows if r[0] in ("amplified", "only-when-asked"))
    print(f"\n  {n_del} of {len(rows)} audited directives are doing nothing -- delete those.")
    print(f"  {n_keep} are buying you something -- keep them if you want what they buy.")
    print("  Nothing was deleted. Decide each KEEP line on whether you want that feature,")
    print("  then re-run your own tests -- this tool does not check correctness.")


def cmd_measure(args):
    sys.exit("measure: not wired in this build.\n"
             "Generate the off-arm yourself -- run your task with the generic guidance\n"
             "removed, 3 times, save the outputs -- then:\n"
             f"  python3 {pathlib.Path(__file__).name} report {args.prompt} --off 'out/off_*.html'")


p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
sub = p.add_subparsers(dest="cmd", required=True)
c = sub.add_parser("classify"); c.add_argument("prompt"); c.set_defaults(fn=cmd_classify)
r = sub.add_parser("report"); r.add_argument("prompt"); r.add_argument("--off", required=True)
r.add_argument("--on"); r.set_defaults(fn=cmd_report)
m = sub.add_parser("measure"); m.add_argument("prompt"); m.add_argument("--task"); m.set_defaults(fn=cmd_measure)
a = p.parse_args(); a.fn(a)
