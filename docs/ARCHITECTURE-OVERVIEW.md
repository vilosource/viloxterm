# ViloxTerm Architecture Overview

## Current Architecture (Post-Refactor)

ViloxTerm follows a **Model-View-Command** architecture with clean separation of concerns and unidirectional data flow.

## Core Principles

### 1. Model-First Architecture
All state changes MUST flow through the model first:
```
User Action → Command → Model → Observer → UI Update
```

### 2. Clean Layer Separation
Dependencies flow in one direction only:
```
UI Layer → Service Layer → Model Layer
         ↖ Observer Events ↙
```

### 3. Single Source of Truth
- `WorkspaceModel` owns all workspace state
- UI components observe and react to model changes
- No business state in UI components

### 4. Command Pattern for Operations
All user actions go through commands for consistent validation and execution.

## Architecture Components

### Model Layer (`models/`)
- **WorkspaceModel** - Core workspace state (tabs, panes, tree structure)
- **WorkspaceState** - Application state container
- **Tab, Pane, TreeNode** - Domain entities
- Pure Python, no UI dependencies

### Command Layer (`core/commands/`)
- **CommandRegistry** - Central command registration and execution
- **CommandContext** - Execution context with model reference
- **Command Classes** - Business logic for state changes
- **CommandResult** - Standardized success/failure responses

### View Layer (`ui/`)
- **workspace.py** - Main workspace integration
- **workspace_view.py** - Pure view components (TabView, PaneView)
- **Widgets** - Reusable UI components
- Stateless, reactive to model changes

### Service Layer (`services/`)
- **WorkspaceService** - High-level workspace operations
- **ThemeService** - Theme management
- **TerminalServer** - Terminal backend
- Bridge between UI and Model layers

## Data Flow

### State Changes
1. User triggers action (keyboard shortcut, menu, button)
2. UI calls command via `CommandRegistry.execute()`
3. Command validates and modifies model
4. Model notifies observers
5. UI updates reactively

### Example: Split Pane
```python
# User presses Ctrl+\
→ Shortcut triggers command
→ CommandRegistry.execute("pane.split", context)
→ SplitPaneCommand.execute()
→ model.split_pane(pane_id, orientation)
→ model.notify_observers("pane_split", data)
→ WorkspaceView updates UI
```

## Key Design Decisions

### 1. Unified Model
- Single `WorkspaceModel` replaces dual model system
- Tree structure for panes directly in model
- Complete serialization support

### 2. Command Architecture
- All 147+ commands migrated to model-based execution
- Removed 201 service dependencies
- CommandStatus enum for clear success/failure

### 3. Pure Views
- Views are stateless renderers
- No business logic in UI components
- React to model changes via observers

### 4. Bridge Components
Limited bridge components for legitimate cross-layer needs:
- `terminal_server` - Terminal backend integration
- Event bus for decoupled communication

## Performance Metrics

- Command execution: <10ms
- Model updates: <1ms
- UI rendering: <16ms (60fps)
- State restoration: <100ms

## File Structure

```
packages/viloapp/src/viloapp/
├── models/
│   ├── workspace_model.py      # Core model (1023 lines)
│   └── compatibility.py        # Legacy compatibility
├── core/
│   └── commands/
│       ├── base.py             # Command infrastructure
│       ├── registry.py         # Command registry
│       └── builtin/           # Command implementations
├── ui/
│   ├── workspace.py           # Workspace integration (340 lines)
│   ├── workspace_view.py      # Pure views (506 lines)
│   └── widgets/              # Reusable components
└── services/
    ├── workspace_service.py   # High-level operations
    └── theme_service.py       # Theme management
```

## Migration Complete

The refactoring is 100% complete with:
- ✅ All commands migrated to model-based
- ✅ Dual model system eliminated
- ✅ Pure view layer implemented
- ✅ Clean architecture boundaries
- ✅ Full test coverage
- ✅ Performance targets met

## Future Enhancements

1. **Plugin System** - Full plugin architecture integration
2. **Advanced Navigation** - Vim-like navigation modes
3. **Multi-window** - Support for multiple windows
4. **Remote Development** - SSH and container support

## Quick Reference

### Common Commands
- `tab.create` - Create new tab
- `tab.close` - Close tab
- `pane.split` - Split pane (horizontal/vertical)
- `pane.close` - Close pane
- `pane.focus` - Focus specific pane
- `workspace.save` - Save workspace state
- `workspace.restore` - Restore workspace state

### Key Classes
- `WorkspaceModel` - Core model
- `CommandRegistry` - Command execution
- `CommandContext` - Execution context
- `TabView` - Tab rendering
- `PaneView` - Pane rendering

### Observer Events
- `tab_created`, `tab_closed`, `tab_switched`
- `pane_split`, `pane_closed`, `pane_focused`
- `widget_changed`, `state_changed`