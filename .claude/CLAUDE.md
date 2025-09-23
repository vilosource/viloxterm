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

## ⚠️ CRITICAL: Refactoring Process Requirements

### When Refactoring (Removing/Renaming Symbols)

**MANDATORY STEPS** - Do not skip any of these:

1. **Find ALL Usages First**
```bash
# Use multiple tools to ensure completeness
grep -r "WidgetType" packages/viloapp/src --include="*.py"
rg "widget_type|widget_id|widgetType" --type py
find packages/viloapp -name "*.py" -exec grep -l "WidgetType" {} \;
```

2. **Create Verification Script**
```python
# verify_refactoring.py - Run this continuously
import subprocess
import sys

def check_undefined_vars():
    """Check for undefined variables."""
    result = subprocess.run(
        ['python', '-m', 'py_compile'] + glob.glob('packages/viloapp/src/**/*.py', recursive=True),
        capture_output=True, text=True
    )

    if 'NameError' in result.stderr or 'undefined' in result.stderr:
        print("❌ UNDEFINED VARIABLES FOUND!")
        print(result.stderr)
        return False
    return True

def check_variable_consistency():
    """Ensure consistent variable naming."""
    # Count occurrences of different patterns
    patterns = ['widget_type', 'widget_id', 'widgetType']
    for pattern in patterns:
        count = subprocess.run(
            ['grep', '-r', pattern, 'packages/viloapp/src', '--include=*.py'],
            capture_output=True
        ).stdout.count(b'\n')
        print(f"{pattern}: {count} occurrences")

if __name__ == "__main__":
    if not check_undefined_vars():
        sys.exit(1)
    check_variable_consistency()
```

3. **Run Continuous Validation**
```bash
# Keep this running in a terminal during ALL refactoring
while true; do
    clear
    echo "=== Checking for undefined variables ==="
    python verify_refactoring.py

    echo "\n=== Running quick test ==="
    python test_workspace_command_fix.py

    sleep 2
done
```

4. **Test EVERY Command After Changes**
```python
# test_all_commands.py - Must pass before considering refactoring complete
from viloapp.core.commands.registry import command_registry

for cmd_id in command_registry.get_all_commands():
    try:
        # Create minimal context and execute
        context = create_minimal_context()
        result = execute_command(cmd_id, context)
        print(f"✅ {cmd_id}")
    except NameError as e:
        print(f"❌ {cmd_id}: {e}")
        sys.exit(1)
```

### Red Flags That MUST Stop You

🚨 **STOP if you see any of these:**

1. **Any undefined variable error**
```python
NameError: name 'widget_type' is not defined  # STOP!
```

2. **Mixed variable names for same concept**
```python
widget_id = get_default_widget_type()  # Inconsistent!
if widget_type == "terminal":  # Different variable!
```

3. **Tests that only mock, don't execute**
```python
@patch("WorkspaceService")  # Mocking hides real errors!
def test_command(mock):
    pass  # This test won't catch NameError!
```

4. **Can't find all usages with grep/ast**
```bash
# If grep doesn't find it, you're not looking hard enough
grep -r "pattern" .  # Too few results? Check aliases!
```

5. **Changing multiple files without testing between**
```bash
# WRONG: Change 10 files then test
# RIGHT: Change 1 file, test, commit, repeat
```

### Refactoring Checklist

**Before starting:**
- [ ] All tests pass
- [ ] No undefined variables (pyflakes/mypy clean)
- [ ] Created list of ALL symbols being changed
- [ ] Found ALL usages with automated tools
- [ ] Have verification script ready

**During refactoring:**
- [ ] Running continuous validation loop
- [ ] Testing after EVERY file change
- [ ] Using consistent variable names
- [ ] Committing incrementally
- [ ] Checking for undefined variables continuously

**After refactoring:**
- [ ] All tests pass
- [ ] All commands execute without NameError
- [ ] No undefined variables in entire codebase
- [ ] Variable names are consistent
- [ ] Application starts and runs normally

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
- [ ] **No undefined variables** (run pyflakes)
- [ ] **All commands execute** (run test_all_commands.py)
- [ ] **Tests use real code, not just mocks**
- [ ] **Variable naming is consistent**

## Common Commands for Testing

```bash
# Run the application
python packages/viloapp/src/viloapp/main.py

# Check for undefined variables (CRITICAL!)
python -m pyflakes packages/viloapp/src
python -m py_compile packages/viloapp/src/**/*.py

# Test all commands work
python test_all_commands.py

# Check logs for state issues
grep -E "No active pane|Failed to restore|model event" ~/.local/share/ViloxTerm/logs/viloxterm.log

# Monitor split operations
tail -f ~/.local/share/ViloxTerm/logs/viloxterm.log | grep -E "split|Split|active pane"

# Check variable naming consistency
grep -r "widget_type" packages/viloapp/src --include="*.py" | wc -l
grep -r "widget_id" packages/viloapp/src --include="*.py" | wc -l
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

## Plugin Architecture Principles

### Core Must Not Know Implementations
- Core defines interfaces and patterns
- No specific widget IDs in core
- No hardcoded plugin names
- Use runtime discovery

### Widget ID Conventions
- Built-in: `com.viloapp.<name>`
- Plugins: `plugin.<plugin_id>.<widget_name>`
- These are CONVENTIONS not constants

### Extensibility Rules
- Adding new widgets must NEVER require modifying core files
- Widget IDs are owned by the widgets themselves
- Use registries for runtime discovery
- Core modules define patterns, not instances

## Remember

**Every architectural decision must consider the full lifecycle:**
- Startup (state restoration)
- Runtime (user operations)
- Shutdown (state persistence)

**The architecture isn't just about clean code - it's about proper state management throughout the application lifecycle.**