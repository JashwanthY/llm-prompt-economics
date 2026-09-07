"""Pre-registered compliance design. Fixed BEFORE any run.

Five explicit, mechanically checkable rules, stated ONCE near the top of the
prompt -- then padding after. This mirrors the real case: the lesson skill
states "never hardcode hex values" on line 37 of 844, and the shipped output
contained 87 hex literals.

The rules are deliberately arbitrary-but-checkable, the way a house style is:
nothing here is inferable, so following them is purely a matter of holding the
instruction while doing the work.
"""

RULES = """MANDATORY PROJECT CONVENTIONS. These are house rules for this codebase.
Follow every one:

1. Never write a hardcoded hex colour. Define all colours as CSS custom
   properties in :root and reference them with var(--name) everywhere.
2. Never use inline event handler attributes such as onclick or onchange.
   Attach every listener with addEventListener.
3. Every interactive element must carry a data-testid attribute.
4. Every id attribute must begin with the prefix "app-".
5. Never use innerHTML. Build DOM nodes with createElement and textContent.
"""

TASK = """Build a single self-contained HTML file: a sortable, filterable data table.

Requirements:
- Embed a dataset of 24 employee records as a JS array, each with: name,
  department (Engineering/Sales/Support/Design), salary (number),
  startDate (ISO date string), active (boolean). Invent plausible values.
- A table with a header row. Clicking a column header sorts by that column,
  ascending then descending. Show the current sort direction.
- A text input that filters rows by name or department as the user types.
- A checkbox "Active only" that filters to active records, combinable with the text filter.
- Pagination at 10 rows per page with Previous/Next and "Page X of Y".
  Previous disabled on page 1; Next disabled on the last page.
- A line reading "Showing A-B of C" reflecting current filters.
- An "Export CSV" button that exports the currently filtered rows.
- No external libraries, no frameworks, no CDN links. Vanilla HTML/CSS/JS only.
"""

import importlib.util, pathlib
# Load the dose ladder by path: both modules are named design.py, so a plain
# import resolves to this file and self-imports.
_spec = importlib.util.spec_from_file_location(
    "dose_design", pathlib.Path(__file__).parent.parent / "dose" / "design.py")
_dose = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_dose)
LEVELS = _dose.LEVELS               # identical ladder: 0 / 68 / 246 / 811 words

MODELS = ["gpt-5.6-luna", "gpt-5.6-terra"]
TRIALS = 3
EFFORT = "medium"
PROMPT = lambda pad: RULES + "\n" + TASK + pad + "\nOutput a complete, self-contained HTML file."
