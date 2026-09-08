"""Pre-registered design: does instruction bulk or restriction collapse output
diversity?

The hypothesis is not that instructions make the model WRONG -- three
experiments have shown correctness sits at ceiling. It is that instructions
make the model GENERIC: given room, repeated runs of the same brief diverge into
different designs; given a heavy or restrictive prompt, they converge on one.

Two things people put in skills are separated so each can be blamed alone:

  MINIMAL       the brief only                                     (baseline)
  PADDED        the brief + 811 words of generic engineering       (BULK, no restriction)
                guidance, verbatim from the dose experiment, which
                never names a colour, font, card or layout
  CONSERVATIVE  the brief + ~90 words of restrictive design         (RESTRICTION, no bulk)
                pressure in the style of real skills, which also
                never names a colour, font or layout

No arm mechanically determines anything the metric measures. If an arm said
"use blue" and the metric counted blues, the result would be a tautology; every
arm here leaves every measured choice to the model.

Everything below is fixed before any run.
"""
import importlib.util
import pathlib

_spec = importlib.util.spec_from_file_location(
    "dose_design", pathlib.Path(__file__).parent.parent / "dose" / "design.py")
_dose = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_dose)

MODELS = ["gpt-5.6-luna", "gpt-5.6-terra"]
EFFORT = "medium"
TRIALS = 6          # per arm per model; diversity is measured ACROSS trials,
                    # so 6 gives 15 within-group pairs

BRIEF = """Build a single self-contained HTML file: an analytics dashboard for a small
online shop.

It must show:
- Total revenue for the month, and the change versus last month
- Order count for the week
- The five best-selling products with units sold
- A recent-activity feed of the last eight events (orders, refunds, reviews)
- A revenue-over-time chart for the last 30 days, drawn without any external
  library

Use realistic sample data of your own. No external scripts, stylesheets, fonts
or images.
"""

CONSERVATIVE = """
DESIGN CONVENTIONS. These are mandatory.
- ALWAYS follow established dashboard conventions. Do NOT experiment with
  unconventional layouts.
- NEVER add decorative elements that do not serve a function.
- Prioritise clarity and consistency over visual interest. The result MUST look
  conventional and professional.
- Use restraint with colour. Do NOT use bold, unusual or expressive palettes.
- Do NOT deviate from standard, widely used UI patterns. Familiarity is the goal.
- Keep typography plain and conventional.
- Avoid any visual choice a conservative enterprise reviewer would question.
"""

ARMS = {
    "minimal":      BRIEF,
    "padded":       BRIEF + _dose.LEVELS["L3_heavy"],
    "conservative": BRIEF + CONSERVATIVE,
}

PROMPT = lambda arm: ARMS[arm] + "\nOutput a complete, self-contained HTML file."

# --- pre-registered metric --------------------------------------------------
# For every pair of runs in the same arm and model, similarity is the mean of
#   S_struct  difflib ratio over the rendered DOM tag sequence (tag:depth)
#   S_hue     Jaccard over the set of chromatic hue bins (12 x 30 degrees)
#             declared in the file's CSS
# Group homogeneity = mean pairwise similarity. Higher = more alike.
#
# Secondary, reported but not the test: distinct accent hues, distinct font
# families, distinct layout-feature vectors, per arm and model.
PRIMARY = "mean of S_struct and S_hue, averaged over within-arm within-model pairs"

# --- pre-registered predictions and criteria --------------------------------
# Metric validation (must hold or the H1 result is uninterpretable):
#   CONSERVATIVE homogeneity > MINIMAL homogeneity, one-sided permutation p < .05
# The hypothesis (the user's claim, applied to bulk that never mentions design):
#   H1: PADDED homogeneity > MINIMAL homogeneity, one-sided permutation p < .05
PERMUTATIONS = 10000

if __name__ == "__main__":
    print("PRE-REGISTERED DIVERSITY DESIGN")
    for a, t in ARMS.items():
        print(f"  {a:13} {len(t.split()):4} words")
    n = len(ARMS) * len(MODELS) * TRIALS
    print(f"  {len(ARMS)} arms x {len(MODELS)} models x {TRIALS} trials = {n} runs")
    print(f"  primary: {PRIMARY}")
    print("  validation: conservative > minimal   |   H1: padded > minimal")
