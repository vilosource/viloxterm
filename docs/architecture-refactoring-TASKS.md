# Model-View-Command Architecture Refactoring Tasks

## Overview
This document tracks the complete refactoring from service-based architecture to Model-View-Command pattern.

## Current State Analysis

### ✅ Completed (Task 1)
- **Unified CommandContext**: Single model-based CommandContext in `base.py`
- **Command Infrastructure**: Base classes moved to proper locations
- **Import Structure**: All imports updated to use `base.py`
- **Code Organization**: Command classes distributed to appropriate builtin files

### ⚠️ Critical Issues Discovered

#### 1. Double Command System Implementation
- **LegacyCommand**: 135+ decorator-based commands using `@command` decorator
- **Command ABC**: 12 class-based commands implementing Command interface
- **Problem**: Two parallel systems with no integration

#### 2. Broken Command Execution
- **Issue**: `workspace.py` calls `command_registry.execute()` but method doesn't exist
- **Impact**: Command classes are defined but never executed
- **Location**: `/ui/workspace.py` lines 84, 209, 231, 278, 297, 315

#### 3. Service Dependencies
- **Count**: 131 `get_service()` calls, 205 service references total
- **Services**: WorkspaceService, ThemeService, StateService, PluginService, TerminalService
- **Files**: All 17 builtin command files still use services

#### 4. Missing Model Methods
```python
# Methods needed but not implemented:
- focus_next_pane()
- focus_previous_pane()
- save_state()
- load_state()
- add_observer()
- remove_observer()
- notify_observers()
```

## Task Breakdown

### Task 2: Fix Command Execution Infrastructure
**Priority**: CRITICAL - Application is broken without this

#### Files to Modify:
- `/core/commands/registry.py` - Add execute() method
- `/core/commands/executor.py` - Check if this should handle execution

#### Implementation Details:
```python
def execute(self, command_id: str, context: CommandContext, **kwargs) -> CommandResult:
    """Execute a command by ID, handling both LegacyCommand and Command classes."""
    # 1. Check if it's a registered LegacyCommand
    legacy_cmd = self.get_command(command_id)
    if legacy_cmd:
        context.update_args(**kwargs)
        return legacy_cmd.execute(context)

    # 2. Check if it's a Command class
    # Need to add command class registry
    command_class = self.get_command_class(command_id)
    if command_class:
        cmd = command_class(**kwargs)
        return cmd.execute(context)

    # 3. Command not found
    return CommandResult(
        status=CommandStatus.FAILURE,
        message=f"Command not found: {command_id}"
    )
```

#### Command Registration Mapping:
```python
# Map command IDs to Command classes
COMMAND_CLASSES = {
    "tab.create": CreateTabCommand,
    "tab.close": CloseTabCommand,
    "tab.rename": RenameTabCommand,
    "tab.switch": SwitchTabCommand,
    "pane.split": SplitPaneCommand,
    "pane.close": ClosePaneCommand,
    "pane.focus": FocusPaneCommand,
    "pane.changeWidget": ChangeWidgetTypeCommand,
    "navigate.up": NavigatePaneCommand,
    "navigate.down": NavigatePaneCommand,
    "navigate.left": NavigatePaneCommand,
    "navigate.right": NavigatePaneCommand,
}
```

### Task 3: Add Missing Model Methods
**Priority**: HIGH - Required for commands to work

#### File to Modify:
- `/models/workspace_model.py`

#### Methods to Add:
```python
def focus_next_pane(self) -> bool:
    """Focus the next pane in tab order."""
    tab = self.state.get_active_tab()
    if not tab:
        return False

    panes = tab.tree.root.get_all_panes()
    if len(panes) <= 1:
        return False

    current_idx = next((i for i, p in enumerate(panes) if p.id == tab.active_pane_id), -1)
    next_idx = (current_idx + 1) % len(panes)

    tab.active_pane_id = panes[next_idx].id
    self.notify_observers("pane_focused", {"pane_id": panes[next_idx].id})
    return True

def focus_previous_pane(self) -> bool:
    """Focus the previous pane in tab order."""
    # Similar implementation but (current_idx - 1) % len(panes)

def save_state(self) -> dict:
    """Serialize model state for persistence."""
    return {
        "tabs": [tab.to_dict() for tab in self.state.tabs],
        "active_tab_id": self.state.active_tab_id,
        "metadata": self.state.metadata
    }

def load_state(self, state: dict) -> bool:
    """Load model state from persistence."""
    try:
        self.state.tabs = [Tab.from_dict(t) for t in state["tabs"]]
        self.state.active_tab_id = state.get("active_tab_id")
        self.state.metadata = state.get("metadata", {})
        self.notify_observers("state_loaded", {})
        return True
    except Exception as e:
        logger.error(f"Failed to load state: {e}")
        return False
```

### Task 4: Implement Observer Pattern
**Priority**: HIGH - Required for UI updates

#### Files to Modify:
- `/models/workspace_model.py` - Add observer support
- `/models/workspace_state.py` - Add observer list

#### Implementation:
```python
class WorkspaceModel:
    def __init__(self):
        self.state = WorkspaceState()
        self._observers = []

    def add_observer(self, callback):
        """Add an observer callback."""
        if callback not in self._observers:
            self._observers.append(callback)

    def remove_observer(self, callback):
        """Remove an observer callback."""
        if callback in self._observers:
            self._observers.remove(callback)

    def notify_observers(self, event: str, data: dict):
        """Notify all observers of a change."""
        for observer in self._observers:
            try:
                observer(event, data)
            except Exception as e:
                logger.error(f"Observer error: {e}")
```

### Task 5: Service Removal Strategy
**Priority**: MEDIUM - Can be done incrementally

#### Phase 1 - Simple Commands (No External Dependencies)
**Files**: `navigation_commands.py`, `view_commands.py`, `edit_commands.py`
- Replace WorkspaceService with direct model calls
- Remove StateService, use model.state directly

#### Phase 2 - Complex Commands (External Dependencies)
**Files**: `terminal_commands.py`, `theme_commands.py`, `plugin_commands.py`
- Keep service for external integration only
- Move business logic to model

#### Example Migration:
```python
# BEFORE (service-based)
def split_pane_command(context: CommandContext) -> CommandResult:
    workspace_service = context.get_service(WorkspaceService)
    new_pane_id = workspace_service.split_active_pane("horizontal")

# AFTER (model-based)
def split_pane_command(context: CommandContext) -> CommandResult:
    pane = context.get_active_pane()
    new_pane_id = context.model.split_pane(pane.id, "horizontal")
```

### Task 6: Command Migration Plan
**Priority**: MEDIUM - Can be done incrementally

#### High-Value Commands to Migrate First:
1. **Tab Commands** (most used):
   - `workbench.action.duplicateTab` → DuplicateTabCommand
   - `workbench.action.closeOtherTabs` → CloseOtherTabsCommand

2. **Pane Commands** (complex logic):
   - `workbench.action.focusNextPane` → FocusNextPaneCommand
   - `workbench.action.focusPreviousPane` → FocusPreviousPaneCommand

3. **Workspace Commands** (state management):
   - `workbench.action.saveLayout` → SaveLayoutCommand
   - `workbench.action.restoreLayout` → RestoreLayoutCommand

### Task 7: Performance Monitoring
**Priority**: LOW - After functionality complete

#### Metrics to Track:
- Command execution time
- Model update time
- Observer notification time
- UI update lag

#### Implementation:
```python
import time

def measure_performance(func):
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = (time.perf_counter() - start) * 1000
        if elapsed > 1:  # Log if > 1ms
            logger.warning(f"{func.__name__} took {elapsed:.2f}ms")
        return result
    return wrapper
```

### Task 8: Final Cleanup
**Priority**: LOW - After all migrations complete

#### Items to Clean:
1. Delete `/core/commands/workspace_commands.py.backup`
2. Remove duplicate Command class definitions in builtin files
3. Remove deprecated get_service() methods from CommandContext
4. Clean up unused imports
5. Update all docstrings to reflect new architecture

## Testing Strategy

### Unit Tests Required:
- [ ] CommandRegistry.execute() with both command types
- [ ] Model observer notification system
- [ ] Command class instantiation and execution
- [ ] Model method implementations (focus_next_pane, etc.)

### Integration Tests Required:
- [ ] Tab creation/deletion flow
- [ ] Pane splitting/closing flow
- [ ] State persistence and restoration
- [ ] UI update via observers

## Success Criteria

### Immediate (Blocking):
- ✅ Application starts without errors
- ✅ Commands execute successfully
- ✅ UI updates when model changes

### Short-term:
- ✅ All 135 decorator commands still work
- ✅ Command classes execute properly
- ✅ No service dependencies in simple commands

### Long-term:
- ✅ 100% commands use model directly
- ✅ All state changes go through model
- ✅ UI is purely reactive (no business logic)
- ✅ Command execution < 1ms
- ✅ Zero UI state storage

## File Reference

### Core Files:
- `/core/commands/base.py` - Command base classes
- `/core/commands/registry.py` - Command registry (needs execute())
- `/core/commands/decorators.py` - Command decorators
- `/models/workspace_model.py` - Core model (needs methods)
- `/models/workspace_state.py` - State storage
- `/ui/workspace.py` - Main UI integration

### Command Files:
- `/core/commands/builtin/tab_commands.py` - Tab Command classes
- `/core/commands/builtin/pane_commands.py` - Pane Command classes
- `/core/commands/builtin/*.py` - 17 files with decorator commands

## Notes

### Architecture Decisions:
1. **Keep both systems during transition** - Don't break existing functionality
2. **Model is source of truth** - All state lives in WorkspaceModel
3. **Commands are stateless** - Create new instance per execution
4. **Services for external only** - Terminal, file system, network

### Migration Order:
1. Fix critical infrastructure (execute method)
2. Add missing model methods
3. Implement observer pattern
4. Migrate simple commands
5. Migrate complex commands
6. Remove service layer
7. Performance optimization
8. Cleanup

### Risk Mitigation:
- Keep LegacyCommand wrapper working
- Test each migration thoroughly
- Migrate incrementally, not big bang
- Keep backup of working state