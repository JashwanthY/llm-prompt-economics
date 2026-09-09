---
name: house-design-system
description: >
  House component conventions for internal dashboards.
---

# House Design System

## Global contract

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

## Compliance checklist

- [ ] No literal colours outside `:root`.
- [ ] No inline handlers, no `innerHTML`.
- [ ] Every interactive element has `data-testid`.
- [ ] Every id begins with `ds-`.
