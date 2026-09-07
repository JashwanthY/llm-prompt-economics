"""Pre-registered design: tasks calibrated to sit OFF ceiling.

The dose and compliance experiments both failed to test the harm hypothesis for
the same reason: their tasks were easy enough that both models scored ~100% with
no padding at all, so there was no room for a decrease to show. That is an
unmeasurable result, not a null one.

This experiment fixes the instrument. Three candidate tasks are written to be
hard -- many interacting constraints, exact checkable outputs, edge cases that
must hold simultaneously -- then CALIBRATED at zero padding before the ladder is
run. Only tasks that land in the band below are carried forward.

Everything here is fixed before any model call.
"""
import importlib.util
import pathlib

# --- pre-registered calibration rule ---------------------------------------
# A task is admitted only if its pooled zero-padding score falls in this band.
# Above it there is no room to fall (the failure this experiment exists to fix);
# below it the task is too hard to attribute a further drop to padding.
BAND = (0.55, 0.80)
TRIALS_FOR = {"calibrate": 2,   # per model, per task, at L0 only
              "ladder": 3}     # per model, per dose, for admitted tasks

MODELS = ["gpt-5.6-luna", "gpt-5.6-terra"]
EFFORT = "medium"

# The dose ladder is reused verbatim so results are comparable to the earlier
# experiment. Loaded by path because both modules are named design.py and a
# plain import resolves to this file.
_spec = importlib.util.spec_from_file_location(
    "dose_design", pathlib.Path(__file__).parent.parent / "dose" / "design.py")
_dose = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_dose)
LEVELS = _dose.LEVELS      # 0 / 68 / 246 / 811 words

# --- candidate tasks --------------------------------------------------------
# Each states many constraints that must hold AT THE SAME TIME, and produces
# exact values a grader can assert rather than prose a grader must interpret.

TASK_SHEET = """Build a single self-contained HTML file: a miniature spreadsheet.

A 4x4 grid of editable cells addressed A1 through D4. Each cell is an <input>
with id "cell-A1", "cell-B3" and so on.

Rules, all of which must hold together:
1. A cell whose value starts with "=" is a formula. Otherwise it is a literal
   number (treat blank or non-numeric as 0).
2. Formulas support + - * / with * and / binding tighter than + and -,
   parentheses, cell references, and SUM(A1:A4) over a rectangular range.
3. The grid displays COMPUTED values, not formula text. Show each computed
   value in a <span id="out-A1"> next to its input, rounded to 2 decimals
   (so 1/3 shows "0.33", and 5 shows "5.00").
4. Editing any cell recomputes every cell that depends on it, transitively.
5. A formula that participates in a reference cycle must display exactly
   "#CYCLE" in its output span, and must not hang the page.
6. Division by zero displays exactly "#DIV/0".
7. A reference to a cell outside A1:D4 displays exactly "#REF".
8. A button with id "app-undo" reverts the single most recent cell edit,
   including its recomputation. Repeated presses walk further back.
"""

TASK_CART = """Build a single self-contained HTML file: a checkout pricing engine.

Fixed catalogue, rendered as rows with a quantity <input>:
  Widget  $24.99   id "qty-widget"
  Gadget  $79.50   id "qty-gadget"
  Doohickey $12.25 id "qty-doohickey"

A coupon <input id="app-coupon"> and an "Apply" button id "app-apply".

Compute and display, each in its own span, all rounded to 2 decimals and
prefixed with "$":
  id "out-subtotal", "out-discount", "out-shipping", "out-tax", "out-total"

Rules, all of which must hold together:
1. Subtotal is the sum of price x quantity.
2. Volume discount on subtotal, highest applicable tier only:
   5% from $100, 10% from $250, 15% from $500.
3. Coupon codes, case-insensitive:
   SAVE10   - 10% off subtotal. It does NOT stack with a volume discount;
              whichever single discount is larger applies, never both.
   BULK5    - $5 off subtotal. This DOES stack with the volume discount.
   FREESHIP - shipping becomes 0. Always stacks.
   Any other code is rejected: show exactly "Invalid coupon" in
   <span id="out-coupon-error"> and apply nothing.
4. Shipping is $8.00 flat, or $0.00 when the post-discount subtotal is $75.00
   or more, or when FREESHIP is applied.
5. Tax is 8.25% of the post-discount subtotal. Shipping is not taxed.
6. Total is post-discount subtotal + shipping + tax.
7. Discount shown is the total amount removed, as a positive number.
8. Every value updates immediately when any quantity changes.
9. Quantities are clamped to integers >= 0; typing a negative or junk value
   is treated as 0 without throwing.
"""

TASK_FORM = """Build a single self-contained HTML file: a registration form with
cross-field validation.

Fields, each an input with the given id:
  app-username, app-email, app-password, app-confirm, app-dob, app-phone

A submit <button id="app-submit">.

Rules, all of which must hold together:
1. Every field shows its error in <span id="err-username"> and so on, with the
   EXACT text given below. When a field is valid its error span is empty.
2. Username: 3-16 characters, letters/digits/underscore only. Errors:
   "Username is required" when empty,
   "Username must be 3-16 characters" when the length is wrong,
   "Username may only contain letters, digits and underscore" otherwise.
   These usernames are taken: admin, root, test. For those show
   "Username is already taken".
3. Email must contain a single "@" with a non-empty local part and a domain
   containing a dot. Error: "Enter a valid email address".
4. Password: at least 10 characters, and must contain an uppercase letter, a
   lowercase letter, a digit and a symbol. Error lists ONLY what is missing,
   in that order, as "Password needs: uppercase, digit" (comma-separated).
   When it is only too short: "Password must be at least 10 characters".
   When it is both too short and missing classes, show the length error only.
5. Confirm must equal password. Error: "Passwords do not match".
6. Date of birth must make the user at least 18 years old today. Error:
   "You must be at least 18".
7. Phone must be exactly 10 digits after stripping spaces, dashes and
   parentheses. Error: "Enter a 10-digit phone number".
8. Errors for every invalid field appear simultaneously, not one at a time.
9. The submit button is disabled whenever any field is invalid, and enabled
   only when all are valid.
"""

TASKS = {"sheet": TASK_SHEET, "cart": TASK_CART, "form": TASK_FORM}

PROMPT = lambda task, pad: (
    TASKS[task] + pad + "\nOutput a complete, self-contained HTML file. "
    "No external scripts, stylesheets or fonts.")

if __name__ == "__main__":
    print("PRE-REGISTERED HARD-TASK DESIGN")
    print(f"  admit band at zero padding: {BAND[0]:.0%}-{BAND[1]:.0%}")
    for name, body in TASKS.items():
        rules = sum(1 for l in body.splitlines()
                    if l.strip()[:2].rstrip(".").isdigit())
        print(f"  {name:6} {len(body.split()):4} words, {rules} numbered rules")
    calib = len(TASKS) * len(MODELS) * TRIALS_FOR["calibrate"]
    print(f"  calibration: {len(TASKS)} tasks x {len(MODELS)} models "
          f"x {TRIALS_FOR['calibrate']} trials = {calib} runs at L0")
    print(f"  ladder (per admitted task): {len(LEVELS)} doses x {len(MODELS)} "
          f"models x {TRIALS_FOR['ladder']} trials = {len(LEVELS)*len(MODELS)*TRIALS_FOR['ladder']} runs")
