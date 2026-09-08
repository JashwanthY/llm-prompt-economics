"""Pre-registered positive control: can this pipeline detect ANY prompt effect?

Every quality result in this study is a null obtained at ceiling. That is only
informative if the instrument is capable of registering a change at all. A null
from an instrument never shown to respond to anything is worth nothing, and it
is the first objection a reader should raise.

So: hold the task, the model, the grader and the reasoning effort fixed, and
remove from the prompt a fact the model CANNOT infer. Quality must fall. If it
does not, the instrument is blind and every null in the paper needs that caveat.

The cart task is used because it scored 100% on 80 checks at zero padding -- the
cleanest ceiling in the study, and therefore the hardest place to manufacture a
drop by accident.

Each ablation removes a proprietary PARAMETER while keeping the requirement to
display the value, so the model still knows what to output and simply cannot
know the number. This produces a graded drop rather than a missing element.
"""
import importlib.util
import pathlib

_spec = importlib.util.spec_from_file_location(
    "hard_design", pathlib.Path(__file__).parent.parent / "hard" / "design.py")
_hard = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_hard)

FULL = _hard.TASKS["cart"]
MODELS = _hard.MODELS
EFFORT = _hard.EFFORT
TRIALS = 2

# --- ablations -------------------------------------------------------------
_TIERS = """2. Volume discount on subtotal, highest applicable tier only:
   5% from $100, 10% from $250, 15% from $500."""
_TIERS_ABLATED = """2. Apply the standard volume discount to the subtotal,
   highest applicable tier only."""

_COUPON = """   SAVE10   - 10% off subtotal. It does NOT stack with a volume discount;
              whichever single discount is larger applies, never both.
   BULK5    - $5 off subtotal. This DOES stack with the volume discount.
   FREESHIP - shipping becomes 0. Always stacks."""
_COUPON_ABLATED = """   SAVE10   - a percentage off the subtotal.
   BULK5    - a fixed amount off the subtotal.
   FREESHIP - shipping becomes 0."""

_TAX = "5. Tax is 8.25% of the post-discount subtotal. Shipping is not taxed."
_TAX_ABLATED = "5. Tax is applied to the post-discount subtotal. Shipping is not taxed."


def _ablate(original, replacement):
    assert original in FULL, "ablation anchor missing from the task text"
    return FULL.replace(original, replacement)


ARMS = {
    "full":          FULL,
    "minus_tiers":   _ablate(_TIERS, _TIERS_ABLATED),
    "minus_coupon":  _ablate(_COUPON, _COUPON_ABLATED),
    "minus_tax":     _ablate(_TAX, _TAX_ABLATED),
}

# --- pre-registered prediction and success criterion -----------------------
# Stated before any run. The control SUCCEEDS if at least one ablated arm scores
# below 80%, i.e. falls out of the ceiling band the whole study is stuck in.
# Failure means the instrument cannot detect a prompt effect it was explicitly
# given one to detect, and every quality null in the paper is then uninformative.
SUCCESS_IF = "at least one ablated arm scores below 80%"
PREDICTIONS = {
    "minus_tiers":  "discount, tax and total checks fail across the tier scenarios",
    "minus_coupon": "the SAVE10 non-stacking and BULK5 stacking scenarios fail",
    "minus_tax":    "every tax and total check fails; subtotal and shipping unaffected",
}

PROMPT = lambda arm: (ARMS[arm] + "\nOutput a complete, self-contained HTML file. "
                      "No external scripts, stylesheets or fonts.")

if __name__ == "__main__":
    print("PRE-REGISTERED POSITIVE CONTROL")
    print(f"  task: cart (80 checks, scored 100% at zero padding)")
    print(f"  success criterion: {SUCCESS_IF}")
    for arm, text in ARMS.items():
        tag = "control" if arm == "full" else PREDICTIONS[arm]
        print(f"  {arm:14} {len(text.split()):4} words  -- {tag}")
    ablated = [a for a in ARMS if a != "full"]
    print(f"  {len(ablated)} ablated arms x {len(MODELS)} models x {TRIALS} trials = "
          f"{len(ablated)*len(MODELS)*TRIALS} runs")
    print("  full arm reuses the 4 existing zero-padding cart runs from hard/")
