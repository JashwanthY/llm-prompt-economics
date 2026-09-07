"""Two prompts. Same task, same required behaviour. B adds only general
web-development advice any current model already applies unprompted -- no new
requirement, no new constraint, no information the model lacks.

If B scores worse than A, redundant instruction costs output quality.
"""

TASK = """Build a single self-contained HTML file: an interactive 5-question quiz.

Requirements:
- 5 questions, 4 options each, one selection per question
- A progress indicator showing how many questions are answered (e.g. "3 of 5 answered")
  that updates live as the learner selects options
- The Submit button is DISABLED until all 5 questions are answered, then enabled
- On submit: show "You scored N/5", and for each wrong question show the question text,
  the option the learner chose, and the correct option
- A Retry button that clears all selections, resets the progress indicator, re-disables
  Submit, hides the results, and lets the learner take the quiz again from scratch
- Keyboard accessible: options selectable with the keyboard
- No external libraries, no frameworks, no CDN links. Vanilla HTML/CSS/JS only.
- Output ONLY the HTML file contents, starting with <!DOCTYPE html>. No commentary.
"""

# Padding: 100% general knowledge. Nothing here is project-specific, and nothing
# adds a requirement. A competent model does all of it unprompted.
PADDING = """
General web development guidance to follow:

Write semantic HTML. Use <main>, <section>, <header>, <footer>, <nav> and <article>
where they apply rather than nesting <div> elements. Headings must descend in order
without skipping levels. Every form control needs an associated <label>. Use the
<fieldset> and <legend> elements to group related radio inputs together.

Accessibility matters. Ensure colour contrast meets WCAG AA, which is 4.5:1 for body
text and 3:1 for large text. Every interactive element must be reachable by keyboard
and must show a visible focus indicator. Do not remove focus outlines without
providing a replacement. Use aria-live regions to announce dynamic content changes.
Add aria-label or aria-labelledby where the visible text is insufficient. Ensure the
tab order follows the visual order of the page. Do not rely on colour alone to convey
meaning. Provide text alternatives for any non-text content.

Structure your CSS carefully. Prefer a consistent naming convention such as BEM, where
blocks, elements and modifiers are named predictably. Avoid deep descendant selectors
because they raise specificity and make overrides difficult. Keep specificity flat.
Avoid !important. Group related declarations. Use CSS custom properties for values that
repeat, such as colours and spacing units. Define them once at the top of the stylesheet.
Prefer rem units for typography so text scales with user preferences. Use a modern
layout method such as flexbox or grid rather than floats or absolute positioning.
Ensure the layout is responsive and works at narrow viewport widths. Use relative units
and avoid fixed pixel widths that break on small screens. Consider a mobile-first
approach where base styles target small screens and media queries add complexity.

Write clean JavaScript. Use const and let rather than var. Prefer strict equality.
Use addEventListener rather than inline onclick attributes. Keep functions small and
focused on a single responsibility. Give variables descriptive names. Avoid global
variables where a local scope will do. Handle edge cases explicitly. Validate input
before using it. Avoid magic numbers by naming constants. Do not mutate function
arguments. Prefer array methods such as map, filter and reduce over manual index loops
where they express the intent more clearly. Cache DOM lookups rather than querying
repeatedly inside loops. Batch DOM updates to avoid layout thrashing.

Consider performance. Minimise reflows and repaints. Avoid unnecessary work in event
handlers that fire frequently. Defer non-critical work. Keep the critical rendering
path short. Avoid blocking the main thread.

Consider maintainability. Comment anything non-obvious, but do not comment what the
code already says plainly. Keep the file organised with styles first, then markup,
then behaviour. Be consistent in formatting and indentation throughout.
"""

ARMS = {"A_minimal": TASK, "B_padded": TASK + "\n" + PADDING}
