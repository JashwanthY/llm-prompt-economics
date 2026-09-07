"""Pre-registered design. Levels and tasks fixed BEFORE any run.

Four padding doses x two tasks. Padding is cumulative and is entirely general
web-development knowledge: it adds no requirement, no constraint, and nothing
the model could not already do. Only the dose changes.
"""

TASK_QUIZ = """Build a single self-contained HTML file: an interactive 5-question quiz.

Requirements:
- 5 questions, 4 options each, one selection per question
- A progress indicator showing how many questions are answered that updates live
- The Submit button is DISABLED until all 5 questions are answered, then enabled
- On submit: show "You scored N/5", and for each wrong question show the question text,
  the option the learner chose, and the correct option
- A Retry button that clears all selections, resets the progress indicator, re-disables
  Submit, hides the results, and lets the learner take the quiz again from scratch
- Keyboard accessible: options selectable with the keyboard
- No external libraries, no frameworks, no CDN links. Vanilla HTML/CSS/JS only.
"""

# Deliberately harder: more moving parts, more state, more room to fail. Chosen
# because the quiz sat at 100% in both arms, leaving no headroom to detect a
# quality difference in either direction.
TASK_TABLE = """Build a single self-contained HTML file: a sortable, filterable data table.

Requirements:
- Embed this dataset directly in the file as a JS array of 24 employee records, each with:
  name, department (one of Engineering/Sales/Support/Design), salary (number),
  startDate (ISO date string), active (boolean). Invent plausible values.
- Render a table with a header row. Clicking any column header sorts by that column,
  ascending on first click, descending on second. Show the current sort direction.
- A text input that filters rows by name or department as the user types (case-insensitive)
- A checkbox "Active only" that filters to active records, combinable with the text filter
- Pagination: 10 rows per page, with Previous/Next buttons and a "Page X of Y" indicator.
  Previous is disabled on page 1; Next is disabled on the last page. Filtering resets to page 1.
- A row-count line reading "Showing A-B of C" that reflects the current filters
- An "Export CSV" button that builds a CSV of the CURRENTLY FILTERED rows and triggers a
  download via a Blob. Values containing commas must be quoted.
- No external libraries, no frameworks, no CDN links. Vanilla HTML/CSS/JS only.
"""

_L1 = """
General web development guidance to follow:

Write semantic HTML. Use <main>, <section>, <header> and <footer> where they apply rather
than nesting <div> elements. Headings must descend in order without skipping levels. Every
form control needs an associated <label>. Ensure colour contrast meets WCAG AA. Every
interactive element must be reachable by keyboard and must show a visible focus indicator.
Do not rely on colour alone to convey meaning.
"""

_L2 = """
Structure your CSS carefully. Prefer a consistent naming convention such as BEM, where blocks,
elements and modifiers are named predictably. Avoid deep descendant selectors because they
raise specificity and make overrides difficult. Keep specificity flat. Avoid !important. Group
related declarations. Use CSS custom properties for values that repeat, such as colours and
spacing units. Define them once at the top of the stylesheet. Prefer rem units for typography
so text scales with user preferences. Use a modern layout method such as flexbox or grid
rather than floats. Ensure the layout is responsive and works at narrow viewport widths.

Write clean JavaScript. Use const and let rather than var. Prefer strict equality. Use
addEventListener rather than inline onclick attributes. Keep functions small and focused on a
single responsibility. Give variables descriptive names. Avoid global variables where a local
scope will do. Handle edge cases explicitly. Avoid magic numbers by naming constants. Prefer
array methods such as map, filter and reduce over manual index loops where they express intent
more clearly. Cache DOM lookups rather than querying repeatedly inside loops.
"""

_L3 = """
Consider performance throughout. Minimise reflows and repaints. Avoid unnecessary work in event
handlers that fire frequently; debounce or throttle where appropriate. Defer non-critical work.
Keep the critical rendering path short. Avoid blocking the main thread. Prefer transform and
opacity for animation because they avoid layout. Batch DOM writes together and reads together.

Consider maintainability. Comment anything non-obvious, but do not comment what the code already
says plainly. Keep the file organised with styles first, then markup, then behaviour. Be
consistent in formatting and indentation throughout. Prefer clarity over cleverness. A future
reader should be able to follow the control flow without holding the whole file in their head.

Consider accessibility beyond the basics. Use aria-live regions to announce dynamic content
changes. Add aria-label or aria-labelledby where visible text is insufficient. Ensure the tab
order follows the visual order. Provide text alternatives for non-text content. Ensure that any
state conveyed visually is also exposed to assistive technology. Test that the interface remains
usable at 200% zoom. Respect prefers-reduced-motion for any animation.

Consider robustness. Validate input before using it. Fail gracefully rather than throwing.
Guard against empty states and boundary conditions. Do not assume an element exists before
querying it. Consider what happens when a collection is empty, when it has one item, and when
it has many. Prefer defensive defaults over silent failure.
"""

_L4 = """
Consider the broader engineering context. Prefer composition over inheritance. Keep coupling
low and cohesion high. A module should do one thing and expose a small surface. Name things
for what they mean in the domain, not for how they are implemented. Avoid abbreviations that
a newcomer would have to decode. Consistent naming across a file is worth more than a clever
name in one place.

Think about state. Keep a single source of truth and derive everything else from it rather
than storing the same fact twice. Two copies of a value will eventually disagree. When state
changes, re-derive the view from the state instead of patching the view incrementally. Make
invalid states unrepresentable where the language allows it. Initialise state explicitly
rather than relying on undefined.

Think about errors. Distinguish between conditions you expect and conditions that indicate a
bug. Expected conditions belong in normal control flow; bugs should be loud. Do not swallow
errors silently. An empty catch block is almost always wrong. When you do catch, catch
narrowly and handle specifically. Prefer returning a result over throwing across a wide
boundary.

Think about the user. Interfaces should make the next action obvious. Disabled controls should
explain why they are disabled. Destructive actions should be reversible or confirmed. Loading
and empty states deserve as much design attention as the populated state. Feedback should be
immediate; if something takes time, say so. Never leave the user guessing whether their input
registered.

Think about testing. Code that is easy to test is usually well structured. Pure functions are
easier to reason about than functions that reach out into the world. Separate the part that
decides from the part that acts. Keep side effects at the edges. If a function is hard to
name, it is probably doing too much.

Think about the reader. The person maintaining this code may be you in six months with no
memory of writing it. Optimise for their comprehension over your convenience today. Leave the
code in a state where the next change is easy to make safely.
"""

LEVELS = {
    "L0_none":  "",
    "L1_light": _L1,
    "L2_mid":   _L1 + _L2,
    "L3_heavy": _L1 + _L2 + _L3 + _L4,
}
TASKS = {"quiz": TASK_QUIZ, "table": TASK_TABLE}
MODELS = ["gpt-5.6-luna", "gpt-5.6-terra"]
TRIALS = 3
EFFORT = "medium"
