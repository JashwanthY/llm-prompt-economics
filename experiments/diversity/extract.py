"""Render every diversity output through features.js and label it with the
arm, model and trial parsed from its filename, producing features.jsonl for
analyze.py. Kept separate from the metric so extraction failures are visible
rather than silently shrinking a group."""
import json, pathlib, subprocess, sys

HERE = pathlib.Path(__file__).parent
rows, failed = [], []
for f in sorted((HERE / "out").glob("*.html")):
    model, arm, trial = f.stem.split("__")
    out = subprocess.run(["node", str(HERE / "features.js"), str(f)],
                         capture_output=True, text=True)
    if not out.stdout.startswith("{"):
        failed.append((f.name, out.stderr.strip()[:160])); continue
    d = json.loads(out.stdout)
    d.update(model=model, arm=arm, trial=int(trial))
    rows.append(d)
(HERE / "features.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n")
print(f"extracted {len(rows)} files; {len(failed)} failed")
for name, err in failed:
    print("  FAILED", name, err)
sys.exit(1 if failed else 0)
