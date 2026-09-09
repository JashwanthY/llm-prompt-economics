"""Do rules cost because they ask for WORK, or because they add LENGTH?

The paper claimed "a line is billed when it asks for work, however phrased, and
free when it asks for restraint" on the strength of a comparison between the
compliance experiment and the dose ladder. Those two experiments do not use the
same task text -- the dose table prompt is 192 words and stricter, the
compliance one 152 -- and they ran in different sessions. The comparison was
confounded and the claim was not supported as it stood.

This settles it. One task text, used verbatim in all arms:

  bare        the task alone
  rules       plus five house rules that ask for WORK       (~82 words)
  restraint   plus restrictions of matched length asking for LESS

If cost tracks what a line asks for, `rules` is dear and `restraint` cheap at
equal length. If cost tracks length alone, the two cost the same.

Arms are interleaved within each trial so session drift lands on all three.
"""
import importlib.util
import pathlib

_s = importlib.util.spec_from_file_location(
    "dose_design", pathlib.Path(__file__).parent.parent / "dose" / "design.py")
_dose = importlib.util.module_from_spec(_s)
_s.loader.exec_module(_dose)

TASK = _dose.TASK_TABLE          # verbatim in every arm, no edits

RULES = """MANDATORY PROJECT CONVENTIONS. Follow every one:

1. Never write a hardcoded hex colour. Define all colours as CSS custom
   properties in :root and reference them with var(--name) everywhere.
2. Never use inline event handler attributes such as onclick or onchange.
   Attach every listener with addEventListener.
3. Every interactive element must carry a data-testid attribute.
4. Every id attribute must begin with the prefix "app-".
5. Never use innerHTML. Build DOM nodes with createElement and textContent.
"""

# Matched in length and imperative force, but every line REMOVES scope rather
# than adding it. Nothing here can be satisfied by writing more code.
RESTRAINT = """MANDATORY PROJECT CONVENTIONS. Follow every one:

1. Do not add any feature that was not asked for. Build exactly what is
   specified above and nothing beyond it.
2. Do not add explanatory comments, banners or documentation blocks.
3. Do not add animations, transitions or decorative visual effects.
4. Do not add defensive scaffolding for conditions the task does not mention.
5. Do not add configuration, theming or extension points, and no abstraction
   that the stated requirements do not force.
"""

ARMS = {"bare": "", "rules": RULES, "restraint": RESTRAINT}
MODELS = ["gpt-5.6-luna", "gpt-5.6-terra"]
EFFORT = "medium"
TRIALS = 3

PROMPT = lambda arm: (ARMS[arm] + ("\n" if ARMS[arm] else "") + TASK
                      + "\nOutput a complete, self-contained HTML file.")

SUPPORTED_IF = ("rules exceeds bare by >10% output tokens AND restraint stays "
                "within +/-10% of bare")

if __name__ == "__main__":
    print("PRE-REGISTERED: does cost track what a line asks for, or its length?")
    print(f"  task text: {len(TASK.split())} words, identical in all arms")
    for a, t in ARMS.items():
        print(f"  {a:10} +{len(t.split()):3} words")
    print(f"  {len(ARMS)} arms x {len(MODELS)} models x {TRIALS} trials = "
          f"{len(ARMS)*len(MODELS)*TRIALS} runs, interleaved")
    print(f"  supported if: {SUPPORTED_IF}")
