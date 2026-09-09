"""A dose point far above the ladder ceiling, on a skill we can publish.

The guidance ladder tops out at 811 words. Real skills run to thousands. The
only artifact at that dose available to us belonged to another author and is not
ours to redistribute, so `build_variants.py` composes an equivalent: a house
design-system skill of the same shape, written for this study.

  full       ~5,840 words, ~46% of lines inside code fences
  contracts  ~1,094 words, no fences, every project-specific requirement kept

The manipulation is the same as the ladder's: the contracts variant keeps
everything the model cannot infer -- component names, class prefixes, data
attributes, the state machine, event names -- and drops the code templates and
the generic engineering guidance. Both arms are then given the identical task.
"""
import importlib.util
import pathlib

HERE = pathlib.Path(__file__).parent
_s = importlib.util.spec_from_file_location(
    "dose_design", HERE.parent / "dose" / "design.py")
_dose = importlib.util.module_from_spec(_s)
_s.loader.exec_module(_dose)

TASK = _dose.TASK_TABLE          # verbatim, both arms

ARMS = {
    "contracts": (HERE / "contracts.md").read_text(),
    "full": (HERE / "full.md").read_text(),
}
MODELS = ["gpt-5.6-luna", "gpt-5.6-terra"]
EFFORT = "medium"
TRIALS = 3

PROMPT = lambda arm: (ARMS[arm] + "\n\n---\n\n" + TASK
                      + "\nOutput a complete, self-contained HTML file.")

if __name__ == "__main__":
    print("PRE-REGISTERED: a skill-scale dose point")
    for a, t in ARMS.items():
        print(f"  {a:10} {len(t.split()):5} words")
    print(f"  ratio: full is {len(ARMS['full'].split())/len(ARMS['contracts'].split()):.1f}x the contracts variant")
    print(f"  {len(ARMS)} arms x {len(MODELS)} models x {TRIALS} trials = "
          f"{len(ARMS)*len(MODELS)*TRIALS} runs, interleaved")
