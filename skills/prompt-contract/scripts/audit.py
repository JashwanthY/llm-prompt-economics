"""Measure which directives in a prompt actually changed the model's output.

This script holds no opinion about what any line means. It cannot read a prompt
and it does not try: deciding that "use rem units" is generic advice while
"aria-label equal to its action_id" is a project requirement is a judgement
about meaning, and the agent running this skill makes it. Two earlier versions
tried to make that call mechanically and both failed in the dangerous direction
-- see references/why-no-keyword-matching.md.

What is left here is the part a model should NOT do by eye: counting how often a
feature appears across a pile of generated artifacts, normalising for their
size, and comparing two arms. That is arithmetic, and arithmetic belongs in a
script.

  lines  <prompt>              number the directive lines, so you can cite them
  report <prompt> --probes ... bucket each probe from output you already have

A probe is written by the agent, for this prompt, and looks like:

  [{"line": 17,
    "feature": "reduced-motion support",
    "pattern": "prefers-reduced-motion"}]

`pattern` is counted in the generated artifacts -- not in the prompt. Set
"inverted": true when ABSENCE is compliance (e.g. "no inline styles").
"""
import argparse, glob, json, pathlib, re, statistics as st, sys

DENSITY = 10_000       # counts are compared per 10KB of artifact
AMPLIFIED_AT = 1.25    # on/off density ratio above which the line is doing work
PRESENT_AT = 0.5       # per-10KB density below which a signal counts as absent


def directives(text):
    """Split a prompt into candidate directive lines, dropping structure.

    Purely structural -- fences, headings, table rows and fragments go, and
    everything else stays. No line is judged here."""
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


def cmd_lines(args):
    lines = directives(pathlib.Path(args.prompt).read_text())
    print(f"{args.prompt}: {len(lines)} directive lines\n")
    for ln, s in lines:
        print(f"  L{ln:<5} {s}")
    print("\n  Classify these yourself against the taxonomy in SKILL.md.")
    print("  This script did not judge them and has no opinion to offer.")


def load_probes(path):
    try:
        probes = json.loads(pathlib.Path(path).read_text())
    except (OSError, json.JSONDecodeError) as e:
        sys.exit(f"--probes {path}: {e}")
    if not isinstance(probes, list) or not probes:
        sys.exit(f"--probes {path}: expected a non-empty JSON list of probes")
    for i, p in enumerate(probes):
        missing = {"feature", "pattern"} - set(p)
        if missing:
            sys.exit(f"probe {i}: missing {', '.join(sorted(missing))}")
        try:
            p["_rx"] = re.compile(p["pattern"], re.M | re.I)
        except re.error as e:
            sys.exit(f"probe {p['feature']!r}: bad pattern -- {e}")
    return probes


def count(probe, text):
    n = len(probe["_rx"].findall(text))
    return (0 if n else 1) if probe.get("inverted") else n


# Padded output is simply bigger, so a raw count rises with file size even when
# behaviour has not changed. An earlier version compared raw counts and called
# `rem` units "already-followed, delete" on an off=4.8 -> on=38.5 signal, which
# would have advised deleting the line responsible for most of the rem usage.
def densities(probe, texts):
    return [count(probe, t) / max(len(t), 1) * DENSITY for t in texts]


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


VERDICT = {
    "already-followed": "DELETE -- same density with or without your line",
    "ignored": "DELETE -- absent either way; the model does not do this",
    "amplified": "KEEP if you want more of it -- your line multiplies what you get",
    "only-when-asked": "KEEP if you want the feature -- absent entirely without your line",
    "present-without-it": "candidate only -- add --on to see if your line multiplies it",
    "absent-without-it": "candidate only -- add --on to see if your line produces it"}
ORDER = {k: i for i, k in enumerate(
    ["already-followed", "ignored", "amplified", "only-when-asked",
     "present-without-it", "absent-without-it"])}


def read_all(pattern, what):
    files = [pathlib.Path(p).read_text(errors="replace") for p in sorted(glob.glob(pattern))]
    if not files:
        sys.exit(f"no files matched --{what} {pattern!r}")
    return files


def cmd_report(args):
    probes = load_probes(args.probes)
    off_files = read_all(args.off, "off")
    on_files = read_all(args.on, "on") if args.on else None

    print(f"{'='*72}\nAUDIT  off-arm: {len(off_files)} files"
          + (f"   on-arm: {len(on_files)} files" if on_files
             else "   (no on-arm: only 'already-followed' is decidable)"))
    print("=" * 72)

    rows = []
    for p in probes:
        b, off, on = bucket(densities(p, off_files),
                            densities(p, on_files) if on_files else None)
        rows.append((b, p.get("line"), p["feature"], off, on))
    rows.sort(key=lambda r: (ORDER[r[0]], r[2]))

    cur = None
    for b, ln, feat, off, on in rows:
        if b != cur:
            cur = b
            print(f"\n  {b.upper()}  ({VERDICT[b]})")
        det = (f"{off:.1f}->{on:.1f}/10KB  x{on/off:.1f}" if on is not None and off > 0
               else f"{off:.1f}->{on:.1f}/10KB" if on is not None else f"{off:.1f}/10KB")
        loc = f"L{ln}" if ln is not None else "--"
        print(f"    {loc:<6} {feat[:30]:30} {det}")

    dead = [r for r in rows if r[0] in ("already-followed", "ignored")]
    keep = [r for r in rows if r[0] in ("amplified", "only-when-asked")]
    decided = len(dead) + len(keep)
    print(f"\n  {len(dead)} of {len(rows)} probed directives are doing nothing.")
    print(f"  {len(keep)} are buying a feature -- keep them if you want what they buy.")
    if decided and on_files:
        print(f"\n  DEAD WEIGHT: {100*len(dead)/decided:.0f}% of decided directives "
              f"({len(dead)}/{decided}).")
    elif not on_files:
        print("\n  No on-arm supplied, so nothing is decided -- these are candidates.")
    print("\n  Nothing was deleted. This measures whether directives were FOLLOWED,")
    print("  never whether the result is CORRECT. Re-run your own tests.")


p = argparse.ArgumentParser(description=__doc__,
                            formatter_class=argparse.RawDescriptionHelpFormatter)
sub = p.add_subparsers(dest="cmd", required=True)
c = sub.add_parser("lines", help="number the directive lines"); c.add_argument("prompt")
c.set_defaults(fn=cmd_lines)
r = sub.add_parser("report", help="bucket probes against generated output")
r.add_argument("prompt"); r.add_argument("--probes", required=True)
r.add_argument("--off", required=True); r.add_argument("--on")
r.set_defaults(fn=cmd_report)
a = p.parse_args(); a.fn(a)
