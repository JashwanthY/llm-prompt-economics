"""Compose a synthetic production-style skill and a contracts-only variant.

The study needed a dose point far above the 811-word ladder ceiling. The only
one available was a real skill belonging to another author, which is not ours to
publish. This generates an equivalent: a house design-system skill of the same
shape -- long, heavy with code fences, mixing project-specific contract with
generic engineering advice -- written for this study and freely redistributable.

Target shape, matched to a real production skill:
  full        ~843 lines, ~6,300 words, ~55% of lines inside code fences
  contracts   ~150 lines, ~1,350 words, no fences, contract prose only

The contracts variant keeps every project-specific requirement and drops the
fences and the generic guidance. That is the manipulation.
"""
import pathlib

COMPONENTS = [
    ("DataGrid", "tabular records with sorting and pagination", "grid", "rows"),
    ("FilterBar", "faceted filtering above a grid", "filterbar", "facets"),
    ("Pager", "page navigation for a grid", "pager", "pages"),
    ("StatTile", "a single headline number with a delta", "stattile", "value"),
    ("Toolbar", "actions that apply to the current view", "toolbar", "actions"),
    ("EmptyState", "what shows when a collection has no members", "empty", "message"),
    ("Badge", "a short status token", "badge", "label"),
    ("Drawer", "a panel that slides over the current view", "drawer", "panel"),
    ("Toast", "a transient confirmation", "toast", "message"),
    ("ExportMenu", "download actions for the current selection", "export", "formats"),
]

GENERIC = [
    ("Accessibility", [
        "Write semantic HTML. Prefer `<main>`, `<section>`, `<header>` and `<footer>` to nested `<div>` elements.",
        "Headings must descend in order without skipping a level.",
        "Every form control needs an associated `<label>`.",
        "Colour contrast must meet WCAG AA.",
        "Every interactive element must be reachable by keyboard and show a visible focus indicator.",
        "Do not rely on colour alone to convey meaning.",
        "Use `aria-live` regions to announce content that changes without a navigation.",
        "Ensure the tab order follows the visual order.",
        "Respect `prefers-reduced-motion` for any animation.",
        "The interface must remain usable at 200% zoom.",
    ]),
    ("CSS conventions", [
        "Keep specificity flat and avoid deep descendant selectors.",
        "Avoid `!important`.",
        "Use CSS custom properties for any value that repeats, and define them once at the top.",
        "Prefer `rem` units for typography so text scales with user preferences.",
        "Use flexbox or grid for layout rather than floats.",
        "Group related declarations together.",
        "Ensure the layout is responsive and works at narrow viewport widths.",
    ]),
    ("JavaScript conventions", [
        "Use `const` and `let` rather than `var`.",
        "Prefer strict equality.",
        "Attach listeners with `addEventListener` rather than inline handler attributes.",
        "Keep functions small and focused on a single responsibility.",
        "Give variables descriptive names and avoid magic numbers.",
        "Cache DOM lookups rather than querying repeatedly inside a loop.",
        "Prefer `map`, `filter` and `reduce` where they express intent more clearly than an index loop.",
    ]),
    ("Performance", [
        "Minimise reflows and repaints.",
        "Debounce or throttle handlers that fire frequently.",
        "Prefer `transform` and `opacity` for animation because they avoid layout.",
        "Batch DOM reads together and DOM writes together.",
        "Keep the critical rendering path short and avoid blocking the main thread.",
    ]),
    ("Robustness", [
        "Validate input before using it.",
        "Fail gracefully rather than throwing.",
        "Guard against empty states and boundary conditions.",
        "Do not assume an element exists before querying it.",
        "Consider what happens when a collection is empty, has one member, and has many.",
    ]),
    ("Maintainability", [
        "Comment anything non-obvious, but never comment what the code already says plainly.",
        "Keep a single source of truth and derive everything else from it.",
        "Re-derive the view from state rather than patching the view incrementally.",
        "Initialise state explicitly rather than relying on `undefined`.",
        "Prefer clarity over cleverness.",
    ]),
]


def contract_lines(name, purpose, slug, payload):
    return [
        f"- The root element MUST carry `class=\"ds-{slug}\"` and `data-component=\"{name}\"`.",
        f"- Every `id` inside a {name} MUST begin with `ds-{slug}-`.",
        f"- The {payload} container MUST carry `data-role=\"{slug}-{payload}\"`.",
        f"- Colours MUST be referenced as `var(--ds-*)`; never write a literal colour inside a {name}.",
        f"- A {name} MUST NOT be constructed with `innerHTML`; build nodes with `createElement`.",
        f"- Interactive elements inside a {name} MUST carry `data-testid`.",
        f"- The {name} title element MUST be `id=\"ds-{slug}-title\"` and referenced by `aria-labelledby`.",
        f"- A {name} MUST render its empty state rather than collapsing to zero height.",
    ]


def states(name, slug, payload):
    return [
        f"### {name} states", "",
        f"A {name} is always in exactly one of four states, and the state MUST be",
        f"exposed as `data-state` on the root so the audit pipeline can read it.", "",
        f"- `loading` — the {payload} are being fetched. Render the skeleton, not a spinner.",
        f"- `ready` — the {payload} are present and the component is interactive.",
        f"- `empty` — the request succeeded and returned nothing. Render the EmptyState child.",
        f"- `error` — the request failed. Render the message and a retry control.", "",
        f"Transitions are one-way from `loading`; a {name} never returns to `loading`",
        f"once it has reached `ready`. Re-fetching updates in place and keeps the",
        f"previous {payload} visible until the new ones arrive.", "",
    ]


def behaviour(name, slug, payload):
    return [
        f"### {name} behaviour", "",
        f"Mutations to {payload} go through the component's `update` method and never",
        f"touch the DOM directly. The component owns its subtree; callers own the state.",
        f"When state changes, re-derive the subtree from state rather than patching it.", "",
        f"- `update(next)` replaces the {payload} and returns the component.",
        f"- `destroy()` removes listeners and detaches the root.",
        f"- Events are dispatched on the root as `ds:{slug}:change`, with the new value",
        f"  on `event.detail.value`. Callers listen on the root, never on children.", "",
        f"A {name} MUST NOT read global state, query outside its own subtree, or",
        f"register a listener on `document` or `window`. Anything it needs is passed in.", "",
    ]


def accessibility_notes(name, slug):
    return [
        f"### {name} accessibility", "",
        f"- The root is a landmark and MUST be labelled by `ds-{slug}-title`.",
        f"- Controls follow the visual order in the tab sequence.",
        f"- Changes that happen without a navigation are announced in the component's",
        f"  own `aria-live=\"polite\"` region, never a page-level one.",
        f"- Disabled controls explain why they are disabled in their accessible name.", "",
    ]


def pitfalls(name, slug, payload):
    return [
        f"### {name} pitfalls", "",
        f"- Do not nest a {name} inside another {name}. The audit pipeline flattens",
        f"  `data-component` and will report both as malformed.",
        f"- Do not reuse a {slug} id across two instances on one page. Suffix them.",
        f"- Do not render {payload} the caller has not supplied. An absent value is the",
        f"  `empty` state, not an invitation to invent placeholder content.",
        f"- Do not animate the transition into `error`. It reads as a success.", "",
    ]
def fence(name, slug, payload):
    """Code templates. In a real skill these are the bulk of the file, and they
    are the part a contracts-only variant drops."""
    return [
        "```html",
        f'<section class="ds-{slug}" data-component="{name}" data-state="ready"',
        f'         aria-labelledby="ds-{slug}-title">',
        f'  <header class="ds-{slug}__head">',
        f'    <h2 class="ds-{slug}__title" id="ds-{slug}-title"></h2>',
        f'    <div class="ds-{slug}__actions" data-role="{slug}-actions"></div>',
        "  </header>",
        f'  <div class="ds-{slug}__body" data-role="{slug}-{payload}"></div>',
        f'  <p class="ds-{slug}__live" aria-live="polite" hidden></p>',
        f'  <footer class="ds-{slug}__foot"></footer>',
        "</section>",
        "```",
        "",
        "```javascript",
        f"function create{name}(host, state) {{",
        "  const root = document.createElement('section');",
        f"  root.className = 'ds-{slug}';",
        f"  root.dataset.component = '{name}';",
        "  root.dataset.state = state.items ? 'ready' : 'empty';",
        f"  root.setAttribute('aria-labelledby', 'ds-{slug}-title');",
        "",
        "  const title = document.createElement('h2');",
        f"  title.id = 'ds-{slug}-title';",
        "  title.textContent = state.title;",
        "  root.appendChild(title);",
        "",
        "  const body = document.createElement('div');",
        f"  body.dataset.role = '{slug}-{payload}';",
        "  root.appendChild(body);",
        "",
        "  const live = document.createElement('p');",
        "  live.setAttribute('aria-live', 'polite');",
        "  live.hidden = true;",
        "  root.appendChild(live);",
        "",
        "  host.appendChild(root);",
        "  return {",
        "    root,",
        f"    update(next) {{ render{name}(body, next); announce(live, next); return this; }},",
        "    destroy() { root.remove(); },",
        "  };",
        "}",
        "",
        f"function render{name}(body, next) {{",
        "  body.replaceChildren();",
        f"  for (const item of next.{payload} ?? []) {{",
        "    const node = document.createElement('div');",
        "    node.textContent = String(item);",
        f"    node.dataset.testid = '{slug}-item';",
        "    body.appendChild(node);",
        "  }",
        "}",
        "```",
        "",
    ]


def build():
    full = ["---", "name: house-design-system",
            "description: >", "  House component conventions for internal dashboards.",
            "---", "", "# House Design System", "",
            "Every dashboard in this codebase is assembled from the components below.",
            "The conventions here are not suggestions; downstream tooling parses the",
            "class names and data attributes, and a component that deviates will not be",
            "picked up by the audit pipeline.", "",
            "## Global contract", "",
            "- All colours are defined once in `:root` as `--ds-*` custom properties.",
            "- Every component root carries `data-component` naming the component.",
            "- Every `id` in the document begins with `ds-`.",
            "- No inline event handler attributes anywhere in the output.",
            "- No `innerHTML` anywhere in the output.",
            "- Every interactive element carries `data-testid`.", ""]
    contracts = list(full[:6]) + ["# House Design System", "",
            "## Global contract", ""] + full[16:23] + [""]

    for name, purpose, slug, payload in COMPONENTS:
        head = [f"## {name}", "", f"A {name} renders {purpose}.", ""]
        cl = contract_lines(name, purpose, slug, payload)
        rich = (states(name, slug, payload) + behaviour(name, slug, payload)
                + pitfalls(name, slug, payload))
        full += head + cl + [""] + rich + fence(name, slug, payload)
        # The contracts variant keeps every project-specific requirement --
        # including the state machine and the event names, which no model could
        # guess -- and drops only the code fences and the generic guidance.
        contracts += head + cl + [""]

    full += ["## Engineering guidance", ""]
    for section, items in GENERIC:
        full += [f"### {section}", ""] + [f"- {i}" for i in items] + [""]

    full += ["## Compliance checklist", "",
             "Before returning output, verify every item:", ""]
    full += [f"- [ ] {n} root carries `data-component` and `ds-` prefixed ids." for n, _, _, _ in COMPONENTS]
    full += ["- [ ] No literal colours outside `:root`.",
             "- [ ] No inline handlers, no `innerHTML`.",
             "- [ ] Every interactive element has `data-testid`.", ""]
    contracts += ["## Compliance checklist", "",
                  "- [ ] No literal colours outside `:root`.",
                  "- [ ] No inline handlers, no `innerHTML`.",
                  "- [ ] Every interactive element has `data-testid`.",
                  "- [ ] Every id begins with `ds-`.", ""]
    return "\n".join(full), "\n".join(contracts)


def profile(text):
    lines = text.splitlines()
    fenced, inf = 0, False
    for l in lines:
        if l.strip().startswith("```"):
            inf = not inf; fenced += 1; continue
        if inf: fenced += 1
    return {"lines": len(lines), "words": len(text.split()),
            "lines_in_code_fences": fenced,
            "headings": sum(1 for l in lines if l.startswith("#"))}


if __name__ == "__main__":
    here = pathlib.Path(__file__).parent
    full, contracts = build()
    (here / "full.md").write_text(full)
    (here / "contracts.md").write_text(contracts)
    import json
    for n, t in (("full", full), ("contracts", contracts)):
        print(f"  {n:10} {profile(t)}")
    (here / "PROFILE.json").write_text(json.dumps(
        {"full": profile(full), "contracts": profile(contracts)}, indent=2))
