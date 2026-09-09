---
name: house-design-system
description: >
  House component conventions for internal dashboards.
---

# House Design System

Every dashboard in this codebase is assembled from the components below.
The conventions here are not suggestions; downstream tooling parses the
class names and data attributes, and a component that deviates will not be
picked up by the audit pipeline.

## Global contract

- All colours are defined once in `:root` as `--ds-*` custom properties.
- Every component root carries `data-component` naming the component.
- Every `id` in the document begins with `ds-`.
- No inline event handler attributes anywhere in the output.
- No `innerHTML` anywhere in the output.
- Every interactive element carries `data-testid`.

## DataGrid

A DataGrid renders tabular records with sorting and pagination.

- The root element MUST carry `class="ds-grid"` and `data-component="DataGrid"`.
- Every `id` inside a DataGrid MUST begin with `ds-grid-`.
- The rows container MUST carry `data-role="grid-rows"`.
- Colours MUST be referenced as `var(--ds-*)`; never write a literal colour inside a DataGrid.
- A DataGrid MUST NOT be constructed with `innerHTML`; build nodes with `createElement`.
- Interactive elements inside a DataGrid MUST carry `data-testid`.
- The DataGrid title element MUST be `id="ds-grid-title"` and referenced by `aria-labelledby`.
- A DataGrid MUST render its empty state rather than collapsing to zero height.

### DataGrid states

A DataGrid is always in exactly one of four states, and the state MUST be
exposed as `data-state` on the root so the audit pipeline can read it.

- `loading` — the rows are being fetched. Render the skeleton, not a spinner.
- `ready` — the rows are present and the component is interactive.
- `empty` — the request succeeded and returned nothing. Render the EmptyState child.
- `error` — the request failed. Render the message and a retry control.

Transitions are one-way from `loading`; a DataGrid never returns to `loading`
once it has reached `ready`. Re-fetching updates in place and keeps the
previous rows visible until the new ones arrive.

### DataGrid behaviour

Mutations to rows go through the component's `update` method and never
touch the DOM directly. The component owns its subtree; callers own the state.
When state changes, re-derive the subtree from state rather than patching it.

- `update(next)` replaces the rows and returns the component.
- `destroy()` removes listeners and detaches the root.
- Events are dispatched on the root as `ds:grid:change`, with the new value
  on `event.detail.value`. Callers listen on the root, never on children.

A DataGrid MUST NOT read global state, query outside its own subtree, or
register a listener on `document` or `window`. Anything it needs is passed in.

### DataGrid pitfalls

- Do not nest a DataGrid inside another DataGrid. The audit pipeline flattens
  `data-component` and will report both as malformed.
- Do not reuse a grid id across two instances on one page. Suffix them.
- Do not render rows the caller has not supplied. An absent value is the
  `empty` state, not an invitation to invent placeholder content.
- Do not animate the transition into `error`. It reads as a success.

```html
<section class="ds-grid" data-component="DataGrid" data-state="ready"
         aria-labelledby="ds-grid-title">
  <header class="ds-grid__head">
    <h2 class="ds-grid__title" id="ds-grid-title"></h2>
    <div class="ds-grid__actions" data-role="grid-actions"></div>
  </header>
  <div class="ds-grid__body" data-role="grid-rows"></div>
  <p class="ds-grid__live" aria-live="polite" hidden></p>
  <footer class="ds-grid__foot"></footer>
</section>
```

```javascript
function createDataGrid(host, state) {
  const root = document.createElement('section');
  root.className = 'ds-grid';
  root.dataset.component = 'DataGrid';
  root.dataset.state = state.items ? 'ready' : 'empty';
  root.setAttribute('aria-labelledby', 'ds-grid-title');

  const title = document.createElement('h2');
  title.id = 'ds-grid-title';
  title.textContent = state.title;
  root.appendChild(title);

  const body = document.createElement('div');
  body.dataset.role = 'grid-rows';
  root.appendChild(body);

  const live = document.createElement('p');
  live.setAttribute('aria-live', 'polite');
  live.hidden = true;
  root.appendChild(live);

  host.appendChild(root);
  return {
    root,
    update(next) { renderDataGrid(body, next); announce(live, next); return this; },
    destroy() { root.remove(); },
  };
}

function renderDataGrid(body, next) {
  body.replaceChildren();
  for (const item of next.rows ?? []) {
    const node = document.createElement('div');
    node.textContent = String(item);
    node.dataset.testid = 'grid-item';
    body.appendChild(node);
  }
}
```

## FilterBar

A FilterBar renders faceted filtering above a grid.

- The root element MUST carry `class="ds-filterbar"` and `data-component="FilterBar"`.
- Every `id` inside a FilterBar MUST begin with `ds-filterbar-`.
- The facets container MUST carry `data-role="filterbar-facets"`.
- Colours MUST be referenced as `var(--ds-*)`; never write a literal colour inside a FilterBar.
- A FilterBar MUST NOT be constructed with `innerHTML`; build nodes with `createElement`.
- Interactive elements inside a FilterBar MUST carry `data-testid`.
- The FilterBar title element MUST be `id="ds-filterbar-title"` and referenced by `aria-labelledby`.
- A FilterBar MUST render its empty state rather than collapsing to zero height.

### FilterBar states

A FilterBar is always in exactly one of four states, and the state MUST be
exposed as `data-state` on the root so the audit pipeline can read it.

- `loading` — the facets are being fetched. Render the skeleton, not a spinner.
- `ready` — the facets are present and the component is interactive.
- `empty` — the request succeeded and returned nothing. Render the EmptyState child.
- `error` — the request failed. Render the message and a retry control.

Transitions are one-way from `loading`; a FilterBar never returns to `loading`
once it has reached `ready`. Re-fetching updates in place and keeps the
previous facets visible until the new ones arrive.

### FilterBar behaviour

Mutations to facets go through the component's `update` method and never
touch the DOM directly. The component owns its subtree; callers own the state.
When state changes, re-derive the subtree from state rather than patching it.

- `update(next)` replaces the facets and returns the component.
- `destroy()` removes listeners and detaches the root.
- Events are dispatched on the root as `ds:filterbar:change`, with the new value
  on `event.detail.value`. Callers listen on the root, never on children.

A FilterBar MUST NOT read global state, query outside its own subtree, or
register a listener on `document` or `window`. Anything it needs is passed in.

### FilterBar pitfalls

- Do not nest a FilterBar inside another FilterBar. The audit pipeline flattens
  `data-component` and will report both as malformed.
- Do not reuse a filterbar id across two instances on one page. Suffix them.
- Do not render facets the caller has not supplied. An absent value is the
  `empty` state, not an invitation to invent placeholder content.
- Do not animate the transition into `error`. It reads as a success.

```html
<section class="ds-filterbar" data-component="FilterBar" data-state="ready"
         aria-labelledby="ds-filterbar-title">
  <header class="ds-filterbar__head">
    <h2 class="ds-filterbar__title" id="ds-filterbar-title"></h2>
    <div class="ds-filterbar__actions" data-role="filterbar-actions"></div>
  </header>
  <div class="ds-filterbar__body" data-role="filterbar-facets"></div>
  <p class="ds-filterbar__live" aria-live="polite" hidden></p>
  <footer class="ds-filterbar__foot"></footer>
</section>
```

```javascript
function createFilterBar(host, state) {
  const root = document.createElement('section');
  root.className = 'ds-filterbar';
  root.dataset.component = 'FilterBar';
  root.dataset.state = state.items ? 'ready' : 'empty';
  root.setAttribute('aria-labelledby', 'ds-filterbar-title');

  const title = document.createElement('h2');
  title.id = 'ds-filterbar-title';
  title.textContent = state.title;
  root.appendChild(title);

  const body = document.createElement('div');
  body.dataset.role = 'filterbar-facets';
  root.appendChild(body);

  const live = document.createElement('p');
  live.setAttribute('aria-live', 'polite');
  live.hidden = true;
  root.appendChild(live);

  host.appendChild(root);
  return {
    root,
    update(next) { renderFilterBar(body, next); announce(live, next); return this; },
    destroy() { root.remove(); },
  };
}

function renderFilterBar(body, next) {
  body.replaceChildren();
  for (const item of next.facets ?? []) {
    const node = document.createElement('div');
    node.textContent = String(item);
    node.dataset.testid = 'filterbar-item';
    body.appendChild(node);
  }
}
```

## Pager

A Pager renders page navigation for a grid.

- The root element MUST carry `class="ds-pager"` and `data-component="Pager"`.
- Every `id` inside a Pager MUST begin with `ds-pager-`.
- The pages container MUST carry `data-role="pager-pages"`.
- Colours MUST be referenced as `var(--ds-*)`; never write a literal colour inside a Pager.
- A Pager MUST NOT be constructed with `innerHTML`; build nodes with `createElement`.
- Interactive elements inside a Pager MUST carry `data-testid`.
- The Pager title element MUST be `id="ds-pager-title"` and referenced by `aria-labelledby`.
- A Pager MUST render its empty state rather than collapsing to zero height.

### Pager states

A Pager is always in exactly one of four states, and the state MUST be
exposed as `data-state` on the root so the audit pipeline can read it.

- `loading` — the pages are being fetched. Render the skeleton, not a spinner.
- `ready` — the pages are present and the component is interactive.
- `empty` — the request succeeded and returned nothing. Render the EmptyState child.
- `error` — the request failed. Render the message and a retry control.

Transitions are one-way from `loading`; a Pager never returns to `loading`
once it has reached `ready`. Re-fetching updates in place and keeps the
previous pages visible until the new ones arrive.

### Pager behaviour

Mutations to pages go through the component's `update` method and never
touch the DOM directly. The component owns its subtree; callers own the state.
When state changes, re-derive the subtree from state rather than patching it.

- `update(next)` replaces the pages and returns the component.
- `destroy()` removes listeners and detaches the root.
- Events are dispatched on the root as `ds:pager:change`, with the new value
  on `event.detail.value`. Callers listen on the root, never on children.

A Pager MUST NOT read global state, query outside its own subtree, or
register a listener on `document` or `window`. Anything it needs is passed in.

### Pager pitfalls

- Do not nest a Pager inside another Pager. The audit pipeline flattens
  `data-component` and will report both as malformed.
- Do not reuse a pager id across two instances on one page. Suffix them.
- Do not render pages the caller has not supplied. An absent value is the
  `empty` state, not an invitation to invent placeholder content.
- Do not animate the transition into `error`. It reads as a success.

```html
<section class="ds-pager" data-component="Pager" data-state="ready"
         aria-labelledby="ds-pager-title">
  <header class="ds-pager__head">
    <h2 class="ds-pager__title" id="ds-pager-title"></h2>
    <div class="ds-pager__actions" data-role="pager-actions"></div>
  </header>
  <div class="ds-pager__body" data-role="pager-pages"></div>
  <p class="ds-pager__live" aria-live="polite" hidden></p>
  <footer class="ds-pager__foot"></footer>
</section>
```

```javascript
function createPager(host, state) {
  const root = document.createElement('section');
  root.className = 'ds-pager';
  root.dataset.component = 'Pager';
  root.dataset.state = state.items ? 'ready' : 'empty';
  root.setAttribute('aria-labelledby', 'ds-pager-title');

  const title = document.createElement('h2');
  title.id = 'ds-pager-title';
  title.textContent = state.title;
  root.appendChild(title);

  const body = document.createElement('div');
  body.dataset.role = 'pager-pages';
  root.appendChild(body);

  const live = document.createElement('p');
  live.setAttribute('aria-live', 'polite');
  live.hidden = true;
  root.appendChild(live);

  host.appendChild(root);
  return {
    root,
    update(next) { renderPager(body, next); announce(live, next); return this; },
    destroy() { root.remove(); },
  };
}

function renderPager(body, next) {
  body.replaceChildren();
  for (const item of next.pages ?? []) {
    const node = document.createElement('div');
    node.textContent = String(item);
    node.dataset.testid = 'pager-item';
    body.appendChild(node);
  }
}
```

## StatTile

A StatTile renders a single headline number with a delta.

- The root element MUST carry `class="ds-stattile"` and `data-component="StatTile"`.
- Every `id` inside a StatTile MUST begin with `ds-stattile-`.
- The value container MUST carry `data-role="stattile-value"`.
- Colours MUST be referenced as `var(--ds-*)`; never write a literal colour inside a StatTile.
- A StatTile MUST NOT be constructed with `innerHTML`; build nodes with `createElement`.
- Interactive elements inside a StatTile MUST carry `data-testid`.
- The StatTile title element MUST be `id="ds-stattile-title"` and referenced by `aria-labelledby`.
- A StatTile MUST render its empty state rather than collapsing to zero height.

### StatTile states

A StatTile is always in exactly one of four states, and the state MUST be
exposed as `data-state` on the root so the audit pipeline can read it.

- `loading` — the value are being fetched. Render the skeleton, not a spinner.
- `ready` — the value are present and the component is interactive.
- `empty` — the request succeeded and returned nothing. Render the EmptyState child.
- `error` — the request failed. Render the message and a retry control.

Transitions are one-way from `loading`; a StatTile never returns to `loading`
once it has reached `ready`. Re-fetching updates in place and keeps the
previous value visible until the new ones arrive.

### StatTile behaviour

Mutations to value go through the component's `update` method and never
touch the DOM directly. The component owns its subtree; callers own the state.
When state changes, re-derive the subtree from state rather than patching it.

- `update(next)` replaces the value and returns the component.
- `destroy()` removes listeners and detaches the root.
- Events are dispatched on the root as `ds:stattile:change`, with the new value
  on `event.detail.value`. Callers listen on the root, never on children.

A StatTile MUST NOT read global state, query outside its own subtree, or
register a listener on `document` or `window`. Anything it needs is passed in.

### StatTile pitfalls

- Do not nest a StatTile inside another StatTile. The audit pipeline flattens
  `data-component` and will report both as malformed.
- Do not reuse a stattile id across two instances on one page. Suffix them.
- Do not render value the caller has not supplied. An absent value is the
  `empty` state, not an invitation to invent placeholder content.
- Do not animate the transition into `error`. It reads as a success.

```html
<section class="ds-stattile" data-component="StatTile" data-state="ready"
         aria-labelledby="ds-stattile-title">
  <header class="ds-stattile__head">
    <h2 class="ds-stattile__title" id="ds-stattile-title"></h2>
    <div class="ds-stattile__actions" data-role="stattile-actions"></div>
  </header>
  <div class="ds-stattile__body" data-role="stattile-value"></div>
  <p class="ds-stattile__live" aria-live="polite" hidden></p>
  <footer class="ds-stattile__foot"></footer>
</section>
```

```javascript
function createStatTile(host, state) {
  const root = document.createElement('section');
  root.className = 'ds-stattile';
  root.dataset.component = 'StatTile';
  root.dataset.state = state.items ? 'ready' : 'empty';
  root.setAttribute('aria-labelledby', 'ds-stattile-title');

  const title = document.createElement('h2');
  title.id = 'ds-stattile-title';
  title.textContent = state.title;
  root.appendChild(title);

  const body = document.createElement('div');
  body.dataset.role = 'stattile-value';
  root.appendChild(body);

  const live = document.createElement('p');
  live.setAttribute('aria-live', 'polite');
  live.hidden = true;
  root.appendChild(live);

  host.appendChild(root);
  return {
    root,
    update(next) { renderStatTile(body, next); announce(live, next); return this; },
    destroy() { root.remove(); },
  };
}

function renderStatTile(body, next) {
  body.replaceChildren();
  for (const item of next.value ?? []) {
    const node = document.createElement('div');
    node.textContent = String(item);
    node.dataset.testid = 'stattile-item';
    body.appendChild(node);
  }
}
```

## Toolbar

A Toolbar renders actions that apply to the current view.

- The root element MUST carry `class="ds-toolbar"` and `data-component="Toolbar"`.
- Every `id` inside a Toolbar MUST begin with `ds-toolbar-`.
- The actions container MUST carry `data-role="toolbar-actions"`.
- Colours MUST be referenced as `var(--ds-*)`; never write a literal colour inside a Toolbar.
- A Toolbar MUST NOT be constructed with `innerHTML`; build nodes with `createElement`.
- Interactive elements inside a Toolbar MUST carry `data-testid`.
- The Toolbar title element MUST be `id="ds-toolbar-title"` and referenced by `aria-labelledby`.
- A Toolbar MUST render its empty state rather than collapsing to zero height.

### Toolbar states

A Toolbar is always in exactly one of four states, and the state MUST be
exposed as `data-state` on the root so the audit pipeline can read it.

- `loading` — the actions are being fetched. Render the skeleton, not a spinner.
- `ready` — the actions are present and the component is interactive.
- `empty` — the request succeeded and returned nothing. Render the EmptyState child.
- `error` — the request failed. Render the message and a retry control.

Transitions are one-way from `loading`; a Toolbar never returns to `loading`
once it has reached `ready`. Re-fetching updates in place and keeps the
previous actions visible until the new ones arrive.

### Toolbar behaviour

Mutations to actions go through the component's `update` method and never
touch the DOM directly. The component owns its subtree; callers own the state.
When state changes, re-derive the subtree from state rather than patching it.

- `update(next)` replaces the actions and returns the component.
- `destroy()` removes listeners and detaches the root.
- Events are dispatched on the root as `ds:toolbar:change`, with the new value
  on `event.detail.value`. Callers listen on the root, never on children.

A Toolbar MUST NOT read global state, query outside its own subtree, or
register a listener on `document` or `window`. Anything it needs is passed in.

### Toolbar pitfalls

- Do not nest a Toolbar inside another Toolbar. The audit pipeline flattens
  `data-component` and will report both as malformed.
- Do not reuse a toolbar id across two instances on one page. Suffix them.
- Do not render actions the caller has not supplied. An absent value is the
  `empty` state, not an invitation to invent placeholder content.
- Do not animate the transition into `error`. It reads as a success.

```html
<section class="ds-toolbar" data-component="Toolbar" data-state="ready"
         aria-labelledby="ds-toolbar-title">
  <header class="ds-toolbar__head">
    <h2 class="ds-toolbar__title" id="ds-toolbar-title"></h2>
    <div class="ds-toolbar__actions" data-role="toolbar-actions"></div>
  </header>
  <div class="ds-toolbar__body" data-role="toolbar-actions"></div>
  <p class="ds-toolbar__live" aria-live="polite" hidden></p>
  <footer class="ds-toolbar__foot"></footer>
</section>
```

```javascript
function createToolbar(host, state) {
  const root = document.createElement('section');
  root.className = 'ds-toolbar';
  root.dataset.component = 'Toolbar';
  root.dataset.state = state.items ? 'ready' : 'empty';
  root.setAttribute('aria-labelledby', 'ds-toolbar-title');

  const title = document.createElement('h2');
  title.id = 'ds-toolbar-title';
  title.textContent = state.title;
  root.appendChild(title);

  const body = document.createElement('div');
  body.dataset.role = 'toolbar-actions';
  root.appendChild(body);

  const live = document.createElement('p');
  live.setAttribute('aria-live', 'polite');
  live.hidden = true;
  root.appendChild(live);

  host.appendChild(root);
  return {
    root,
    update(next) { renderToolbar(body, next); announce(live, next); return this; },
    destroy() { root.remove(); },
  };
}

function renderToolbar(body, next) {
  body.replaceChildren();
  for (const item of next.actions ?? []) {
    const node = document.createElement('div');
    node.textContent = String(item);
    node.dataset.testid = 'toolbar-item';
    body.appendChild(node);
  }
}
```

## EmptyState

A EmptyState renders what shows when a collection has no members.

- The root element MUST carry `class="ds-empty"` and `data-component="EmptyState"`.
- Every `id` inside a EmptyState MUST begin with `ds-empty-`.
- The message container MUST carry `data-role="empty-message"`.
- Colours MUST be referenced as `var(--ds-*)`; never write a literal colour inside a EmptyState.
- A EmptyState MUST NOT be constructed with `innerHTML`; build nodes with `createElement`.
- Interactive elements inside a EmptyState MUST carry `data-testid`.
- The EmptyState title element MUST be `id="ds-empty-title"` and referenced by `aria-labelledby`.
- A EmptyState MUST render its empty state rather than collapsing to zero height.

### EmptyState states

A EmptyState is always in exactly one of four states, and the state MUST be
exposed as `data-state` on the root so the audit pipeline can read it.

- `loading` — the message are being fetched. Render the skeleton, not a spinner.
- `ready` — the message are present and the component is interactive.
- `empty` — the request succeeded and returned nothing. Render the EmptyState child.
- `error` — the request failed. Render the message and a retry control.

Transitions are one-way from `loading`; a EmptyState never returns to `loading`
once it has reached `ready`. Re-fetching updates in place and keeps the
previous message visible until the new ones arrive.

### EmptyState behaviour

Mutations to message go through the component's `update` method and never
touch the DOM directly. The component owns its subtree; callers own the state.
When state changes, re-derive the subtree from state rather than patching it.

- `update(next)` replaces the message and returns the component.
- `destroy()` removes listeners and detaches the root.
- Events are dispatched on the root as `ds:empty:change`, with the new value
  on `event.detail.value`. Callers listen on the root, never on children.

A EmptyState MUST NOT read global state, query outside its own subtree, or
register a listener on `document` or `window`. Anything it needs is passed in.

### EmptyState pitfalls

- Do not nest a EmptyState inside another EmptyState. The audit pipeline flattens
  `data-component` and will report both as malformed.
- Do not reuse a empty id across two instances on one page. Suffix them.
- Do not render message the caller has not supplied. An absent value is the
  `empty` state, not an invitation to invent placeholder content.
- Do not animate the transition into `error`. It reads as a success.

```html
<section class="ds-empty" data-component="EmptyState" data-state="ready"
         aria-labelledby="ds-empty-title">
  <header class="ds-empty__head">
    <h2 class="ds-empty__title" id="ds-empty-title"></h2>
    <div class="ds-empty__actions" data-role="empty-actions"></div>
  </header>
  <div class="ds-empty__body" data-role="empty-message"></div>
  <p class="ds-empty__live" aria-live="polite" hidden></p>
  <footer class="ds-empty__foot"></footer>
</section>
```

```javascript
function createEmptyState(host, state) {
  const root = document.createElement('section');
  root.className = 'ds-empty';
  root.dataset.component = 'EmptyState';
  root.dataset.state = state.items ? 'ready' : 'empty';
  root.setAttribute('aria-labelledby', 'ds-empty-title');

  const title = document.createElement('h2');
  title.id = 'ds-empty-title';
  title.textContent = state.title;
  root.appendChild(title);

  const body = document.createElement('div');
  body.dataset.role = 'empty-message';
  root.appendChild(body);

  const live = document.createElement('p');
  live.setAttribute('aria-live', 'polite');
  live.hidden = true;
  root.appendChild(live);

  host.appendChild(root);
  return {
    root,
    update(next) { renderEmptyState(body, next); announce(live, next); return this; },
    destroy() { root.remove(); },
  };
}

function renderEmptyState(body, next) {
  body.replaceChildren();
  for (const item of next.message ?? []) {
    const node = document.createElement('div');
    node.textContent = String(item);
    node.dataset.testid = 'empty-item';
    body.appendChild(node);
  }
}
```

## Badge

A Badge renders a short status token.

- The root element MUST carry `class="ds-badge"` and `data-component="Badge"`.
- Every `id` inside a Badge MUST begin with `ds-badge-`.
- The label container MUST carry `data-role="badge-label"`.
- Colours MUST be referenced as `var(--ds-*)`; never write a literal colour inside a Badge.
- A Badge MUST NOT be constructed with `innerHTML`; build nodes with `createElement`.
- Interactive elements inside a Badge MUST carry `data-testid`.
- The Badge title element MUST be `id="ds-badge-title"` and referenced by `aria-labelledby`.
- A Badge MUST render its empty state rather than collapsing to zero height.

### Badge states

A Badge is always in exactly one of four states, and the state MUST be
exposed as `data-state` on the root so the audit pipeline can read it.

- `loading` — the label are being fetched. Render the skeleton, not a spinner.
- `ready` — the label are present and the component is interactive.
- `empty` — the request succeeded and returned nothing. Render the EmptyState child.
- `error` — the request failed. Render the message and a retry control.

Transitions are one-way from `loading`; a Badge never returns to `loading`
once it has reached `ready`. Re-fetching updates in place and keeps the
previous label visible until the new ones arrive.

### Badge behaviour

Mutations to label go through the component's `update` method and never
touch the DOM directly. The component owns its subtree; callers own the state.
When state changes, re-derive the subtree from state rather than patching it.

- `update(next)` replaces the label and returns the component.
- `destroy()` removes listeners and detaches the root.
- Events are dispatched on the root as `ds:badge:change`, with the new value
  on `event.detail.value`. Callers listen on the root, never on children.

A Badge MUST NOT read global state, query outside its own subtree, or
register a listener on `document` or `window`. Anything it needs is passed in.

### Badge pitfalls

- Do not nest a Badge inside another Badge. The audit pipeline flattens
  `data-component` and will report both as malformed.
- Do not reuse a badge id across two instances on one page. Suffix them.
- Do not render label the caller has not supplied. An absent value is the
  `empty` state, not an invitation to invent placeholder content.
- Do not animate the transition into `error`. It reads as a success.

```html
<section class="ds-badge" data-component="Badge" data-state="ready"
         aria-labelledby="ds-badge-title">
  <header class="ds-badge__head">
    <h2 class="ds-badge__title" id="ds-badge-title"></h2>
    <div class="ds-badge__actions" data-role="badge-actions"></div>
  </header>
  <div class="ds-badge__body" data-role="badge-label"></div>
  <p class="ds-badge__live" aria-live="polite" hidden></p>
  <footer class="ds-badge__foot"></footer>
</section>
```

```javascript
function createBadge(host, state) {
  const root = document.createElement('section');
  root.className = 'ds-badge';
  root.dataset.component = 'Badge';
  root.dataset.state = state.items ? 'ready' : 'empty';
  root.setAttribute('aria-labelledby', 'ds-badge-title');

  const title = document.createElement('h2');
  title.id = 'ds-badge-title';
  title.textContent = state.title;
  root.appendChild(title);

  const body = document.createElement('div');
  body.dataset.role = 'badge-label';
  root.appendChild(body);

  const live = document.createElement('p');
  live.setAttribute('aria-live', 'polite');
  live.hidden = true;
  root.appendChild(live);

  host.appendChild(root);
  return {
    root,
    update(next) { renderBadge(body, next); announce(live, next); return this; },
    destroy() { root.remove(); },
  };
}

function renderBadge(body, next) {
  body.replaceChildren();
  for (const item of next.label ?? []) {
    const node = document.createElement('div');
    node.textContent = String(item);
    node.dataset.testid = 'badge-item';
    body.appendChild(node);
  }
}
```

## Drawer

A Drawer renders a panel that slides over the current view.

- The root element MUST carry `class="ds-drawer"` and `data-component="Drawer"`.
- Every `id` inside a Drawer MUST begin with `ds-drawer-`.
- The panel container MUST carry `data-role="drawer-panel"`.
- Colours MUST be referenced as `var(--ds-*)`; never write a literal colour inside a Drawer.
- A Drawer MUST NOT be constructed with `innerHTML`; build nodes with `createElement`.
- Interactive elements inside a Drawer MUST carry `data-testid`.
- The Drawer title element MUST be `id="ds-drawer-title"` and referenced by `aria-labelledby`.
- A Drawer MUST render its empty state rather than collapsing to zero height.

### Drawer states

A Drawer is always in exactly one of four states, and the state MUST be
exposed as `data-state` on the root so the audit pipeline can read it.

- `loading` — the panel are being fetched. Render the skeleton, not a spinner.
- `ready` — the panel are present and the component is interactive.
- `empty` — the request succeeded and returned nothing. Render the EmptyState child.
- `error` — the request failed. Render the message and a retry control.

Transitions are one-way from `loading`; a Drawer never returns to `loading`
once it has reached `ready`. Re-fetching updates in place and keeps the
previous panel visible until the new ones arrive.

### Drawer behaviour

Mutations to panel go through the component's `update` method and never
touch the DOM directly. The component owns its subtree; callers own the state.
When state changes, re-derive the subtree from state rather than patching it.

- `update(next)` replaces the panel and returns the component.
- `destroy()` removes listeners and detaches the root.
- Events are dispatched on the root as `ds:drawer:change`, with the new value
  on `event.detail.value`. Callers listen on the root, never on children.

A Drawer MUST NOT read global state, query outside its own subtree, or
register a listener on `document` or `window`. Anything it needs is passed in.

### Drawer pitfalls

- Do not nest a Drawer inside another Drawer. The audit pipeline flattens
  `data-component` and will report both as malformed.
- Do not reuse a drawer id across two instances on one page. Suffix them.
- Do not render panel the caller has not supplied. An absent value is the
  `empty` state, not an invitation to invent placeholder content.
- Do not animate the transition into `error`. It reads as a success.

```html
<section class="ds-drawer" data-component="Drawer" data-state="ready"
         aria-labelledby="ds-drawer-title">
  <header class="ds-drawer__head">
    <h2 class="ds-drawer__title" id="ds-drawer-title"></h2>
    <div class="ds-drawer__actions" data-role="drawer-actions"></div>
  </header>
  <div class="ds-drawer__body" data-role="drawer-panel"></div>
  <p class="ds-drawer__live" aria-live="polite" hidden></p>
  <footer class="ds-drawer__foot"></footer>
</section>
```

```javascript
function createDrawer(host, state) {
  const root = document.createElement('section');
  root.className = 'ds-drawer';
  root.dataset.component = 'Drawer';
  root.dataset.state = state.items ? 'ready' : 'empty';
  root.setAttribute('aria-labelledby', 'ds-drawer-title');

  const title = document.createElement('h2');
  title.id = 'ds-drawer-title';
  title.textContent = state.title;
  root.appendChild(title);

  const body = document.createElement('div');
  body.dataset.role = 'drawer-panel';
  root.appendChild(body);

  const live = document.createElement('p');
  live.setAttribute('aria-live', 'polite');
  live.hidden = true;
  root.appendChild(live);

  host.appendChild(root);
  return {
    root,
    update(next) { renderDrawer(body, next); announce(live, next); return this; },
    destroy() { root.remove(); },
  };
}

function renderDrawer(body, next) {
  body.replaceChildren();
  for (const item of next.panel ?? []) {
    const node = document.createElement('div');
    node.textContent = String(item);
    node.dataset.testid = 'drawer-item';
    body.appendChild(node);
  }
}
```

## Toast

A Toast renders a transient confirmation.

- The root element MUST carry `class="ds-toast"` and `data-component="Toast"`.
- Every `id` inside a Toast MUST begin with `ds-toast-`.
- The message container MUST carry `data-role="toast-message"`.
- Colours MUST be referenced as `var(--ds-*)`; never write a literal colour inside a Toast.
- A Toast MUST NOT be constructed with `innerHTML`; build nodes with `createElement`.
- Interactive elements inside a Toast MUST carry `data-testid`.
- The Toast title element MUST be `id="ds-toast-title"` and referenced by `aria-labelledby`.
- A Toast MUST render its empty state rather than collapsing to zero height.

### Toast states

A Toast is always in exactly one of four states, and the state MUST be
exposed as `data-state` on the root so the audit pipeline can read it.

- `loading` — the message are being fetched. Render the skeleton, not a spinner.
- `ready` — the message are present and the component is interactive.
- `empty` — the request succeeded and returned nothing. Render the EmptyState child.
- `error` — the request failed. Render the message and a retry control.

Transitions are one-way from `loading`; a Toast never returns to `loading`
once it has reached `ready`. Re-fetching updates in place and keeps the
previous message visible until the new ones arrive.

### Toast behaviour

Mutations to message go through the component's `update` method and never
touch the DOM directly. The component owns its subtree; callers own the state.
When state changes, re-derive the subtree from state rather than patching it.

- `update(next)` replaces the message and returns the component.
- `destroy()` removes listeners and detaches the root.
- Events are dispatched on the root as `ds:toast:change`, with the new value
  on `event.detail.value`. Callers listen on the root, never on children.

A Toast MUST NOT read global state, query outside its own subtree, or
register a listener on `document` or `window`. Anything it needs is passed in.

### Toast pitfalls

- Do not nest a Toast inside another Toast. The audit pipeline flattens
  `data-component` and will report both as malformed.
- Do not reuse a toast id across two instances on one page. Suffix them.
- Do not render message the caller has not supplied. An absent value is the
  `empty` state, not an invitation to invent placeholder content.
- Do not animate the transition into `error`. It reads as a success.

```html
<section class="ds-toast" data-component="Toast" data-state="ready"
         aria-labelledby="ds-toast-title">
  <header class="ds-toast__head">
    <h2 class="ds-toast__title" id="ds-toast-title"></h2>
    <div class="ds-toast__actions" data-role="toast-actions"></div>
  </header>
  <div class="ds-toast__body" data-role="toast-message"></div>
  <p class="ds-toast__live" aria-live="polite" hidden></p>
  <footer class="ds-toast__foot"></footer>
</section>
```

```javascript
function createToast(host, state) {
  const root = document.createElement('section');
  root.className = 'ds-toast';
  root.dataset.component = 'Toast';
  root.dataset.state = state.items ? 'ready' : 'empty';
  root.setAttribute('aria-labelledby', 'ds-toast-title');

  const title = document.createElement('h2');
  title.id = 'ds-toast-title';
  title.textContent = state.title;
  root.appendChild(title);

  const body = document.createElement('div');
  body.dataset.role = 'toast-message';
  root.appendChild(body);

  const live = document.createElement('p');
  live.setAttribute('aria-live', 'polite');
  live.hidden = true;
  root.appendChild(live);

  host.appendChild(root);
  return {
    root,
    update(next) { renderToast(body, next); announce(live, next); return this; },
    destroy() { root.remove(); },
  };
}

function renderToast(body, next) {
  body.replaceChildren();
  for (const item of next.message ?? []) {
    const node = document.createElement('div');
    node.textContent = String(item);
    node.dataset.testid = 'toast-item';
    body.appendChild(node);
  }
}
```

## ExportMenu

A ExportMenu renders download actions for the current selection.

- The root element MUST carry `class="ds-export"` and `data-component="ExportMenu"`.
- Every `id` inside a ExportMenu MUST begin with `ds-export-`.
- The formats container MUST carry `data-role="export-formats"`.
- Colours MUST be referenced as `var(--ds-*)`; never write a literal colour inside a ExportMenu.
- A ExportMenu MUST NOT be constructed with `innerHTML`; build nodes with `createElement`.
- Interactive elements inside a ExportMenu MUST carry `data-testid`.
- The ExportMenu title element MUST be `id="ds-export-title"` and referenced by `aria-labelledby`.
- A ExportMenu MUST render its empty state rather than collapsing to zero height.

### ExportMenu states

A ExportMenu is always in exactly one of four states, and the state MUST be
exposed as `data-state` on the root so the audit pipeline can read it.

- `loading` — the formats are being fetched. Render the skeleton, not a spinner.
- `ready` — the formats are present and the component is interactive.
- `empty` — the request succeeded and returned nothing. Render the EmptyState child.
- `error` — the request failed. Render the message and a retry control.

Transitions are one-way from `loading`; a ExportMenu never returns to `loading`
once it has reached `ready`. Re-fetching updates in place and keeps the
previous formats visible until the new ones arrive.

### ExportMenu behaviour

Mutations to formats go through the component's `update` method and never
touch the DOM directly. The component owns its subtree; callers own the state.
When state changes, re-derive the subtree from state rather than patching it.

- `update(next)` replaces the formats and returns the component.
- `destroy()` removes listeners and detaches the root.
- Events are dispatched on the root as `ds:export:change`, with the new value
  on `event.detail.value`. Callers listen on the root, never on children.

A ExportMenu MUST NOT read global state, query outside its own subtree, or
register a listener on `document` or `window`. Anything it needs is passed in.

### ExportMenu pitfalls

- Do not nest a ExportMenu inside another ExportMenu. The audit pipeline flattens
  `data-component` and will report both as malformed.
- Do not reuse a export id across two instances on one page. Suffix them.
- Do not render formats the caller has not supplied. An absent value is the
  `empty` state, not an invitation to invent placeholder content.
- Do not animate the transition into `error`. It reads as a success.

```html
<section class="ds-export" data-component="ExportMenu" data-state="ready"
         aria-labelledby="ds-export-title">
  <header class="ds-export__head">
    <h2 class="ds-export__title" id="ds-export-title"></h2>
    <div class="ds-export__actions" data-role="export-actions"></div>
  </header>
  <div class="ds-export__body" data-role="export-formats"></div>
  <p class="ds-export__live" aria-live="polite" hidden></p>
  <footer class="ds-export__foot"></footer>
</section>
```

```javascript
function createExportMenu(host, state) {
  const root = document.createElement('section');
  root.className = 'ds-export';
  root.dataset.component = 'ExportMenu';
  root.dataset.state = state.items ? 'ready' : 'empty';
  root.setAttribute('aria-labelledby', 'ds-export-title');

  const title = document.createElement('h2');
  title.id = 'ds-export-title';
  title.textContent = state.title;
  root.appendChild(title);

  const body = document.createElement('div');
  body.dataset.role = 'export-formats';
  root.appendChild(body);

  const live = document.createElement('p');
  live.setAttribute('aria-live', 'polite');
  live.hidden = true;
  root.appendChild(live);

  host.appendChild(root);
  return {
    root,
    update(next) { renderExportMenu(body, next); announce(live, next); return this; },
    destroy() { root.remove(); },
  };
}

function renderExportMenu(body, next) {
  body.replaceChildren();
  for (const item of next.formats ?? []) {
    const node = document.createElement('div');
    node.textContent = String(item);
    node.dataset.testid = 'export-item';
    body.appendChild(node);
  }
}
```

## Engineering guidance

### Accessibility

- Write semantic HTML. Prefer `<main>`, `<section>`, `<header>` and `<footer>` to nested `<div>` elements.
- Headings must descend in order without skipping a level.
- Every form control needs an associated `<label>`.
- Colour contrast must meet WCAG AA.
- Every interactive element must be reachable by keyboard and show a visible focus indicator.
- Do not rely on colour alone to convey meaning.
- Use `aria-live` regions to announce content that changes without a navigation.
- Ensure the tab order follows the visual order.
- Respect `prefers-reduced-motion` for any animation.
- The interface must remain usable at 200% zoom.

### CSS conventions

- Keep specificity flat and avoid deep descendant selectors.
- Avoid `!important`.
- Use CSS custom properties for any value that repeats, and define them once at the top.
- Prefer `rem` units for typography so text scales with user preferences.
- Use flexbox or grid for layout rather than floats.
- Group related declarations together.
- Ensure the layout is responsive and works at narrow viewport widths.

### JavaScript conventions

- Use `const` and `let` rather than `var`.
- Prefer strict equality.
- Attach listeners with `addEventListener` rather than inline handler attributes.
- Keep functions small and focused on a single responsibility.
- Give variables descriptive names and avoid magic numbers.
- Cache DOM lookups rather than querying repeatedly inside a loop.
- Prefer `map`, `filter` and `reduce` where they express intent more clearly than an index loop.

### Performance

- Minimise reflows and repaints.
- Debounce or throttle handlers that fire frequently.
- Prefer `transform` and `opacity` for animation because they avoid layout.
- Batch DOM reads together and DOM writes together.
- Keep the critical rendering path short and avoid blocking the main thread.

### Robustness

- Validate input before using it.
- Fail gracefully rather than throwing.
- Guard against empty states and boundary conditions.
- Do not assume an element exists before querying it.
- Consider what happens when a collection is empty, has one member, and has many.

### Maintainability

- Comment anything non-obvious, but never comment what the code already says plainly.
- Keep a single source of truth and derive everything else from it.
- Re-derive the view from state rather than patching the view incrementally.
- Initialise state explicitly rather than relying on `undefined`.
- Prefer clarity over cleverness.

## Compliance checklist

Before returning output, verify every item:

- [ ] DataGrid root carries `data-component` and `ds-` prefixed ids.
- [ ] FilterBar root carries `data-component` and `ds-` prefixed ids.
- [ ] Pager root carries `data-component` and `ds-` prefixed ids.
- [ ] StatTile root carries `data-component` and `ds-` prefixed ids.
- [ ] Toolbar root carries `data-component` and `ds-` prefixed ids.
- [ ] EmptyState root carries `data-component` and `ds-` prefixed ids.
- [ ] Badge root carries `data-component` and `ds-` prefixed ids.
- [ ] Drawer root carries `data-component` and `ds-` prefixed ids.
- [ ] Toast root carries `data-component` and `ds-` prefixed ids.
- [ ] ExportMenu root carries `data-component` and `ds-` prefixed ids.
- [ ] No literal colours outside `:root`.
- [ ] No inline handlers, no `innerHTML`.
- [ ] Every interactive element has `data-testid`.
