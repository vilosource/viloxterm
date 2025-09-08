# Collapsible Sidebar Layout Specification

## Overview

This specification defines the layout for a PySide6-based desktop GUI application. The layout includes a fixed Activity Bar with icons, a collapsible Sidebar, a central Workspace area with split-and-tab functionality, and a Status Bar.

## Layout Components

### Activity Bar (Icons)

* Positioned on the far left side of the window.
* Implemented as a vertical `QToolBar`.
* Icon-only buttons (e.g., Explorer, Search, Git, Terminal, Settings).
* Fixed width (approx. 44–56 px).
* Non-movable and non-floatable.
* Each button focuses or toggles a corresponding Sidebar view.

### Sidebar (Collapsible)

* Positioned to the right of the Activity Bar.
* Implemented as a `QDockWidget` or a widget inside a `QSplitter`.
* Contains a `QStackedWidget` to display multiple tool panels:

  * File Explorer
  * Search Panel
  * Git Panel
  * Extensions or Settings
* Can be hidden/shown via a command or toolbar action.
* Last width is remembered when collapsed and restored when expanded.
* Optional: smooth hide/show animation using `QPropertyAnimation`.

### Workspace (Splits + Tabs)

* Central area of the application.
* Built on a **SplitTree** model using nested `QSplitter` objects.
* Supports **recursive splits**:

  * Vertical and horizontal splitting of panes.
  * Each split contains one or more Panes.
* Each **Pane** hosts a **TabContainer** implemented with `QTabWidget`.
* **Tabs** represent open **Views** (widgets) contributed by the application or plugins.

  * Examples: text editor, markdown preview, terminal, database browser, custom plugin UI.
* Tabs can be rearranged, moved between panes, or opened in a new split.
* Layout state is serializable to JSON for persistence and restored at startup.

### Status Bar

* Located at the bottom of the window.
* Spans the full width of the application.
* Displays status messages, notifications, and progress indicators.

## State Diagrams

### Expanded State

```
+-------------------------------------------------------------+
| [Icons] | [ Sidebar (collapsible) ] |     Workspace         |
|         |                           |  ┌─────────────────┐ |
|  A B C  |  ┌─────────────────────┐  |  │ Tab1 | Tab2 |   │ |
|  D E F  |  │  Tool View (tree)   │  |  │ ─────────────── │ |
|         |  │  or Search Panel    │  |  │ View (widget)  │ |
|         |  │  or Git Panel ...   │  |  └─────────────────┘ |
|         |  └─────────────────────┘  |                       |
+---------+---------------------------+-----------------------+
| Status Bar (messages, notifications, progress, etc.)        |
+-------------------------------------------------------------+
```

### Collapsed State

```
+-------------------------------------------------------------+
| [Icons] |                   Workspace                       |
|         |          ┌─────────────────┐                      |
|  A B C  |          │ Tab1 | Tab2 |   │                      |
|  D E F  |          │ ─────────────── │                      |
|         |          │ View (widget)  │                      |
|         |          └─────────────────┘                      |
+---------+---------------------------------------------------+
| Status Bar (messages, notifications, progress, etc.)        |
+-------------------------------------------------------------+
```

## Interaction

* **Toggle Sidebar**:

  * Triggered by toolbar icon or keyboard shortcut (e.g., `Ctrl+B`).
  * Collapses the Sidebar (width = 0) or restores it to last remembered width.
* **Activity Bar buttons**:

  * Activate corresponding view in the Sidebar.
  * Ensure Sidebar is shown if currently collapsed.
* **Workspace interactions**:

  * Split a pane horizontally or vertically.
  * Move tabs between panes.
  * Open a tab in a new split.
  * Close split (adopts tabs back into parent).

## Persistence

* Persist the following UI state with `QSettings`:

  * Sidebar visibility (shown/hidden).
  * Sidebar width when expanded.
  * Last selected Sidebar tool.
  * Workspace SplitTree layout (splits, panes, tabs).
  * Active tab per pane.
* Restore state on application startup.

## Enhancements (Optional)

* Auto-hide behavior (sidebar hides when focus moves to Workspace, shows on hover).
* Drag handle for resizing with double-click to reset width.
* Smooth animated transition between collapsed and expanded states.
* Tab context menus for actions (split, close others, move to new split).

