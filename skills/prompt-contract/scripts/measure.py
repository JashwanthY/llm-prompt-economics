"""Measure a prompt change: run a task N times under each variant, report the
deltas that matter -- output tokens, latency, artifact size -- with intervals.

Deliberately provider-agnostic. It shells out to a command you supply, so it
works with any model, any harness, any language. The command is run with
PROMPT_FILE and OUT_FILE in its environment; it must read the prompt, do the
work, and write the artifact.

  python3 measure.py --cmd './run.sh' \\
      --variant original=prompts/full.md --variant trimmed=prompts/trimmed.md \\
      --runs 3 --out runs/

Each run is timed by wall clock. Token counts are read from a JSON sidecar the
command may write next to OUT_FILE (`<OUT_FILE>.usage.json`, keys
input_tokens / output_tokens); without it, artifact size stands in and the
report says so rather than inventing numbers.
"""
import argparse, json, os, pathlib, random, statistics as st, subprocess, sys, time

def boot(vals, n=4000, seed=0):
    if len(vals) < 2:
        return (vals[0], vals[0]) if vals else (0.0, 0.0)
    rng = random.Random(seed)
    s = sorted(st.mean(rng.choices(vals, k=len(vals))) for _ in range(n))
    return s[int(.025 * n)], s[int(.975 * n)]


def run_one(cmd, prompt, out_path, timeout):
    env = {**os.environ, "PROMPT_FILE": str(prompt), "OUT_FILE": str(out_path)}
    t0 = time.time()
    p = subprocess.run(cmd, shell=True, env=env, capture_output=True, text=True, timeout=timeout)
    secs = time.time() - t0
    usage = pathlib.Path(str(out_path) + ".usage.json")
    u = json.loads(usage.read_text()) if usage.exists() else {}
    return {"secs": round(secs, 2),
            "in_tokens": u.get("input_tokens"), "out_tokens": u.get("output_tokens"),
            "chars": out_path.stat().st_size if out_path.exists() else 0,
            "ok": p.returncode == 0 and out_path.exists(),
            "stderr": p.stderr[-400:] if p.returncode else ""}


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cmd", required=True, help="command; reads $PROMPT_FILE, writes $OUT_FILE")
    ap.add_argument("--variant", action="append", required=True, metavar="NAME=PATH",
                    help="repeatable; the FIRST is the baseline everything is compared to")
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--out", default="runs")
    ap.add_argument("--ext", default="out")
    ap.add_argument("--timeout", type=int, default=900)
    a = ap.parse_args()

    variants = []
    for v in a.variant:
        name, _, path = v.partition("=")
        if not path or not pathlib.Path(path).exists():
            sys.exit(f"variant {name!r}: no such prompt file {path!r}")
        variants.append((name, pathlib.Path(path)))
    outdir = pathlib.Path(a.out); outdir.mkdir(parents=True, exist_ok=True)

    # Interleave: run trial 0 of every variant, then trial 1, and so on, so that
    # drift in API response time during the session lands on all variants
    # equally instead of on whichever ran last.
    results = {n: [] for n, _ in variants}
    for trial in range(a.runs):
        for name, prompt in variants:
            out_path = outdir / f"{name}__{trial}.{a.ext}"
            r = run_one(a.cmd, prompt, out_path, a.timeout)
            r.update(variant=name, trial=trial)
            results[name].append(r)
            flag = "" if r["ok"] else "  FAILED"
            print(f"  {name:12} trial {trial}  {r['secs']:6.1f}s  "
                  f"{(str(r['out_tokens']) + ' out tok') if r['out_tokens'] else str(r['chars']) + ' chars'}{flag}",
                  flush=True)
            if not r["ok"] and r["stderr"]:
                print(f"      {r['stderr'].splitlines()[-1][:160]}")
    (outdir / "measure.json").write_text(json.dumps(results, indent=2))

    base_name = variants[0][0]
    base = [r for r in results[base_name] if r["ok"]]
    if not base:
        sys.exit(f"baseline {base_name!r} produced no successful runs; nothing to compare")
    have_tokens = all(r["out_tokens"] is not None for v in results.values() for r in v if r["ok"])

    print(f"\n{'variant':12} {'n':>2} {'out tokens':>22} {'latency (s)':>22} {'size':>9}")
    rows = {}
    for name, _ in variants:
        ok = [r for r in results[name] if r["ok"]]
        if not ok:
            print(f"{name:12} {'0':>2}   all runs failed")
            continue
        tok = [r["out_tokens"] for r in ok] if have_tokens else None
        sec = [r["secs"] for r in ok]
        ch = [r["chars"] for r in ok]
        rows[name] = (tok, sec, ch)
        f = lambda v: f"{st.mean(v):7.0f} [{boot(v)[0]:.0f},{boot(v)[1]:.0f}]"
        print(f"{name:12} {len(ok):>2} {(f(tok) if tok else 'n/a (no usage sidecar)'):>22} "
              f"{st.mean(sec):8.1f} [{boot(sec)[0]:.1f},{boot(sec)[1]:.1f}]{'':>2} {st.mean(ch):9.0f}")

    print(f"\nversus {base_name}:")
    bt, bs, bc = rows[base_name]
    for name, _ in variants[1:]:
        if name not in rows:
            continue
        t, s, c = rows[name]
        parts = []
        if bt and t:
            parts.append(f"output tokens {st.mean(t)/st.mean(bt)-1:+.0%}")
        parts.append(f"latency {st.mean(s)/st.mean(bs)-1:+.0%}")
        parts.append(f"size {st.mean(c)/st.mean(bc)-1:+.0%}")
        print(f"  {name:12} " + "   ".join(parts))
    n = len(base)
    if n < 3:
        print(f"\n  Only {n} run(s) per variant. Treat these as indicative; intervals need 3+.")
    print("\n  These are cost numbers only. They say nothing about whether the output is\n"
          "  still correct -- run your own tests on the trimmed prompt before adopting it.")


if __name__ == "__main__":
    main()
