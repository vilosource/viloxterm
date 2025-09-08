# Flexible Split Architecture with Mixed Widgets

## Overview

This document describes the flexible split pane architecture for the ViloApp. The application features multiple root-level tabs, each containing a content area that can be recursively split into panes. Each pane can host different types of widgets, creating a highly customizable workspace.

## Core Concepts

### Multi-Tab Design
- The application supports **multiple tabs** at the root level (e.g., "Development", "Debug", "Database", etc.)
- Each tab maintains its own independent split layout and widget configuration
- Tabs can be added, closed (except the last one), and switched between
- Each tab preserves its split state when switching

### Content Panes
- Each tab's content area can be split into multiple **content panes**
- Panes can host different types of widgets (Editor, Terminal, File Explorer, etc.)
- Panes can be recursively split horizontally or vertically
- Each pane has a unique ID for tracking and management
- Pane content can be replaced with different widget types dynamically

### Splitting Operations
- **Split Right**: Creates a horizontal splitter, dividing the pane into left and right sections
- **Split Down**: Creates a vertical splitter, dividing the pane into top and bottom sections
- Splits are recursive - any pane can be further split
- New panes are created with placeholder content initially

### Closing Behavior
- Right-click on any pane to access the context menu with "Close Pane" option
- When a pane is closed:
  - Its sibling pane(s) expand to fill the available space
  - The parent splitter collapses if only one child remains
  - The last remaining pane cannot be closed (prevents empty workspace)

## Visual Examples

### Multiple Tabs with Different Layouts
```
┌──────────────────────────────────────────────┐
│  [Development*] [Debug] [Database] [+]       │
│┌──────────────┬─────────────────────────────┐│
││              │                             ││
││   Editor     │      Terminal               ││
││  (main.py)   │   (bash session)            ││
││              │                             ││
│└──────────────┴─────────────────────────────┘│
└──────────────────────────────────────────────┘
```

### Complex Split with Mixed Widgets
```
┌──────────────────────────────────────────────┐
│  [Development*] [Debug] [Database] [+]       │
│┌──────────────┬─────────────────────────────┐│
││   Editor     │      Terminal               ││
││  (main.py)   │   (bash session)            ││
││              ├─────────────────────────────┤│
││              │    File Explorer            ││
││              │  (project tree)             ││
│└──────────────┴─────────────────────────────┘│
└──────────────────────────────────────────────┘
```

### Debug Tab Layout
```
┌──────────────────────────────────────────────┐
│  [Development] [Debug*] [Database] [+]       │
│┌───────────────┬──────────────┬─────────────┐│
││               │              │             ││
││  Variables    │   Editor     │   Output    ││
││   Viewer      │  (debug.py)  │   Console   ││
││               │              │             ││
│├───────────────┴──────────────┴─────────────┤│
││            Call Stack Viewer               ││
││         (debugging session)                ││
│└────────────────────────────────────────────┘│
└──────────────────────────────────────────────┘
```

## Tree Structure

The internal structure uses nested splitters with different widget types:

```
Root TabWidget
├── Tab 1: Development
│   └── HSplitter
│       ├── Editor Widget (main.py)
│       └── VSplitter
│           ├── Terminal Widget (bash)
│           └── FileExplorer Widget
├── Tab 2: Debug  
│   └── VSplitter
│       ├── HSplitter
│       │   ├── Variables Widget
│       │   ├── Editor Widget (debug.py)
│       │   └── Console Widget
│       └── CallStack Widget
└── Tab 3: Database
    └── VSplitter
        ├── SQLEditor Widget
        └── HSplitter
            ├── SchemaTree Widget
            └── TableView Widget
```

## Container Collapse Rules

When a pane is closed, the system follows these rules:

1. **Multiple Children**: If the parent splitter has 2+ children, simply remove the closed pane
2. **Single Child Remaining**: If only one child remains after closing:
   - Replace the parent splitter with the remaining child widget
   - The remaining child takes the full space of the former splitter
3. **Last Pane**: The last remaining pane in the workspace cannot be closed

## Implementation Details

### Key Components

1. **MainWindow**: Contains the root tab widget with multiple tabs
2. **TabWorkspace**: Content area for each tab that manages splits
3. **ContentPane**: Base class for pane content
4. **WidgetFactory**: Creates different widget types for panes
5. **SplitManager**: Manages the tree of splitters and panes per tab
6. **ContextMenu**: Provides split, open, replace, and close operations

### Signals and Slots

- `split_horizontal_requested(pane_id)`: Request to split a pane horizontally
- `split_vertical_requested(pane_id)`: Request to split a pane vertically
- `close_pane_requested(pane_id)`: Request to close a pane
- `pane_activated(pane_id)`: Notify when a pane becomes active

### Pane Identification

Each pane has a unique ID following the pattern:
- Root: `pane_root`
- After splits: `pane_1`, `pane_2`, `pane_3`, etc.

## Available Widget Types

The application supports various widget types that can be loaded into panes:

1. **Editor Widget** - Code editing with syntax highlighting
2. **Terminal Widget** - Command line interface  
3. **File Explorer** - File/folder tree view
4. **Output Console** - Program output display
5. **Variables Viewer** - Debug variable inspection
6. **Call Stack** - Debug call stack display
7. **Search Results** - Find/replace results
8. **Markdown Preview** - Rendered markdown
9. **Empty/Placeholder** - Default empty pane

### Widget State Management

Each pane maintains its widget type and state:

```python
{
    "pane_id": "pane_123",
    "widget_type": "editor",
    "widget_state": {
        "file_path": "/src/main.py",
        "cursor_position": [45, 12],
        "scroll_position": 120
    }
}
```

## User Interactions

### Context Menu (Right-Click)
- **Split Right**: Create horizontal split
- **Split Down**: Create vertical split  
- **Open →**: Submenu to open widget type in new split
- **Replace With →**: Submenu to replace current pane content
- **Close Pane**: Remove this pane (if not the last one)

### Keyboard Shortcuts (Future)
- `Ctrl+\`: Split right
- `Ctrl+Shift+\`: Split down
- `Ctrl+W`: Close current pane

## Benefits of Simplified Architecture

1. **Reduced Complexity**: No tab management within panes
2. **Clear Mental Model**: One workspace, multiple views
3. **Predictable Behavior**: Consistent splitting and closing rules
4. **Better Performance**: Fewer widgets to manage
5. **Simpler State Management**: Single tab state + pane tree

## Migration from Multi-Tab Architecture

The previous architecture allowed multiple tabs per pane. The simplified version:
- Removes `TabContainer` from split panes
- Uses `ContentPane` widgets directly
- Moves tab functionality to root level only
- Simplifies close behavior (no confirmation dialogs)

## Future Enhancements

- Drag-and-drop to rearrange panes
- Save/restore split layouts
- Minimum pane size constraints
- Pane resizing animations
- Named workspace layouts