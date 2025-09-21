# ViloxTerm Architecture Guide for Claude

## ⚠️ CRITICAL: Read This First

This codebase is undergoing a major architectural transformation. There are **two parallel models** that must be carefully managed. Read the architecture sections below before making any changes.

## North Star Principles

### 1. Model-First Architecture
**Principle**: All state changes MUST flow through the model first.
```
✅ CORRECT: User Action → Command → Model → Observer → UI Update
❌ WRONG:   User Action → UI Update → Maybe update model
```

### 2. Clean Layer Separation
**Principle**: Dependencies flow in one direction only.
```
UI Layer → Service Layer → Model Layer
         ↖ Observer Events ↙
```
- UI imports from services and models
- Services import from models only
- Models import nothing from UI or services

### 3. Single Source of Truth
**Principle**: The model owns all state. UI is purely reactive.
- WorkspaceModelImpl is the authoritative state source
- UI components observe and react to model changes
- Never store business state in UI components

### 4. Command Pattern for All Operations
**Principle**: All user actions go through commands.
```python
# Good: Command modifies model
execute_command("workbench.action.splitRight")

# Bad: Direct UI manipulation
split_widget.split_pane()
```

## ⚠️ Current Architecture Status

### The Dual Model Problem
**WARNING**: There are currently TWO models managing workspace state:

1. **WorkspaceModelImpl** (packages/viloapp/src/viloapp/models/workspace_model_impl.py)
   - The NEW clean architecture model
   - Lives in service layer
   - Used by commands
   - Contains tab and pane state

2. **SplitPaneModel** (packages/viloapp/src/viloapp/ui/widgets/split_pane_model.py)
   - The LEGACY UI model
   - Embedded in each SplitPaneWidget
   - Contains tree structure and AppWidgets
   - Still actively used by UI

**IMPORTANT**: Both models exist during migration. Changes must consider both until migration is complete.

### State Restoration Flow
**CRITICAL**: State restoration MUST go through the model:

```python
# CORRECT State Restoration:
1. Load state from disk (QSettings)
2. WorkspaceService.restore_state(state_dict)
3. WorkspaceModelImpl.restore_state(state_dict)
4. Model notifies observers
5. UI creates widgets reactively

# WRONG (but was previously done):
1. Load state from disk
2. UI directly creates widgets
3. Model remains empty
4. Commands fail with "No active pane"
```

## Known Issues and Pitfalls

### 1. Split Commands May Fail
**Issue**: Split commands query WorkspaceModelImpl which may be empty after state restoration.
**Check**: Ensure model is populated via restore_state() before any commands execute.

### 2. Circular Import with terminal_server
**Issue**: terminal_server is a "bridge component" that legitimately spans layers.
**Solution**: Use lazy loading pattern:
```python
@property
def terminal_server(self):
    if self._terminal_server_instance is None:
        from viloapp.services.terminal_server import terminal_server
        self._terminal_server_instance = terminal_server
    return self._terminal_server_instance
```

### 3. Widget Type Mapping
**Issue**: Saved state uses "text_editor" but model uses WidgetType.EDITOR
**Solution**: Map old names during restoration:
```python
widget_type_map = {
    "text_editor": WidgetType.EDITOR,
    "terminal": WidgetType.TERMINAL,
    # ...
}
```

### 4. Multiple Event Systems
**Issue**: Three event systems exist:
- Qt signals/slots (UI interactions)
- Model observers (state changes)
- Event bus (cross-cutting concerns)

**Guideline**:
- Use model observers for model→UI updates
- Use Qt signals for UI→UI communication
- Use event bus sparingly for service→UI requests

## Architecture Documentation

### Key Documents
- **docs/architecture-BRIDGES.md** - Explains bridge components
- **docs/architecture-fix-MODEL-SYNC-PLAN.md** - Model synchronization plan
- **docs/architecture-refactor-JOURNEY.md** - Complete refactoring chronicle
- **docs/architecture-refactor-RETROSPECTIVE.md** - Lessons learned

### Phase Status
✅ Phase 1-3: Core models, commands, services (COMPLETE)
✅ Phase 4: UI cleanup (COMPLETE)
✅ Phase 5: MVC implementation (COMPLETE)
✅ Phase 6: Circular dependency breaking (COMPLETE)
✅ Phase 7: Testing and validation (COMPLETE)
⚠️ Model-first restoration (PARTIAL - needs full SplitPaneModel migration)
❌ Complete model unification (NOT STARTED)

## When Making Changes

### Before Any Modification
1. **Check which model is affected** - WorkspaceModelImpl or SplitPaneModel?
2. **Trace the full flow** - From user action through command to model to UI
3. **Consider state restoration** - Will this work after app restart?
4. **Test the complete journey** - Not just runtime but startup and shutdown

### Adding New Features
1. Start with the model - add to WorkspaceModelImpl
2. Create/update commands
3. Connect observers
4. Only then update UI to react

### Fixing Bugs
1. Identify if it's a model sync issue
2. Check if state restoration is involved
3. Verify commands use the correct model
4. Ensure observers are connected

## Testing Checklist

When testing changes, verify:
- [ ] App starts with saved state
- [ ] Commands work after restoration
- [ ] Split operations function correctly
- [ ] Model and UI stay synchronized
- [ ] No circular import errors
- [ ] Performance remains <10ms for operations

## Common Commands for Testing

```bash
# Run the application
python packages/viloapp/src/viloapp/main.py

# Check logs for state issues
grep -E "No active pane|Failed to restore|model event" ~/.local/share/ViloxTerm/logs/viloxterm.log

# Monitor split operations
tail -f ~/.local/share/ViloxTerm/logs/viloxterm.log | grep -E "split|Split|active pane"
```

## Future Direction

### Immediate Priority
Complete migration to single model by:
1. Moving tree structure from SplitPaneModel to WorkspaceModelImpl
2. Making SplitPaneWidget a pure view component
3. Centralizing widget lifecycle in AppWidgetManager

### Long-term Goals
- Single unified model (WorkspaceModelImpl)
- Pure reactive UI
- Complete plugin system integration
- 100% command-driven operations

## Remember

**Every architectural decision must consider the full lifecycle:**
- Startup (state restoration)
- Runtime (user operations)
- Shutdown (state persistence)

**The architecture isn't just about clean code - it's about proper state management throughout the application lifecycle.**