# Architecture Fixer Agent - Startup Guide

## Pre-Flight Checklist

Before beginning ANY work, the architecture-fixer agent must:

### 1. Environment Verification
```bash
# Verify Python environment
python --version  # Should be 3.8+

# Verify tests run
pytest packages/viloapp/tests/ -v --tb=short

# Check current git status
git status
git log -1 --oneline
```

### 2. Load Context Documents
Read these files IN ORDER:
1. `docs/architecture-violations-REPORT.md` - Understand what's broken
2. `ARCHITECTURE-NORTHSTAR.md` - Learn the rules
3. `docs/architecture-fix-IMPLEMENTATION-PLAN.md` - Your mission
4. `docs/architecture-fix-TRACKER.md` - Current progress
5. `MainTabbedSplitPanes.md` - Current architecture

### 3. Assess Current State
```python
# Check for existing model directories
ls packages/viloapp/src/viloapp/models/  # Should not exist yet
ls packages/viloapp/src/viloapp/interfaces/  # Should not exist yet

# Count current violations
grep -r "workspace\.split_active" packages/viloapp/  # Should find violations
grep -r "self\._workspace\.tab_widget" packages/viloapp/services/  # Should find 23+
```

## Phase Order of Operations

### Phase 1: Foundation (MUST complete first)
```
1.1 Create models directory structure
    ↓
1.2 Implement OperationResult and base models
    ↓
1.3 Create DTOs for all operations
    ↓
1.4 Define IWorkspaceModel interface
    ↓
1.5 Write comprehensive tests
    ↓
VERIFY: Models have ZERO Qt imports
```

### Phase 2: Service Layer (Requires Phase 1)
```
2.1 Implement WorkspaceModelImpl
    ↓
2.2 Create model→service adapters
    ↓
2.3 Refactor WorkspaceService
    ↓
2.4 Fix all 23 service violations
    ↓
2.5 Move business logic from UI
    ↓
VERIFY: Services have ZERO Qt imports
```

### Dependency Graph
```
Phase 1 (Foundation)
    ↓
Phase 2 (Service Layer)
    ↓
Phase 3 (Command Layer)
    ↓
Phase 4 (UI Cleanup) ←→ Phase 5 (MVC Fix)
    ↓
Phase 6 (Circular Dependencies)
    ↓
Phase 7 (Testing & Validation)
```

## Testing Strategy

### For Each Fix

#### 1. Write the Test FIRST
```python
# test_no_ui_calls_in_commands.py
def test_pane_commands_dont_call_ui():
    """Commands should never directly call UI methods."""
    with open("pane_commands.py") as f:
        content = f.read()

    # These patterns should NOT exist
    assert "workspace.split_active" not in content
    assert "widget.model." not in content
```

#### 2. Verify Test FAILS
```bash
pytest test_no_ui_calls_in_commands.py  # Should FAIL before fix
```

#### 3. Implement Fix
```python
# Fix the violation
# Document what changed and why
```

#### 4. Verify Test PASSES
```bash
pytest test_no_ui_calls_in_commands.py  # Should PASS after fix
```

#### 5. Run Regression Tests
```bash
pytest packages/viloapp/tests/  # Ensure nothing else broke
```

## Backward Compatibility Strategy

### Phase 1-3: Parallel Implementation
Keep old code working while building new:
```python
# models/workspace_models.py (NEW)
class WorkspaceState:  # New clean model
    ...

# ui/workspace.py (EXISTING)
class Workspace:  # Keep working as-is
    ...
```

### Phase 4-5: Adapter Pattern
Bridge old and new during transition:
```python
class WorkspaceAdapter:
    """Adapts old UI calls to new model calls."""
    def __init__(self, model: IWorkspaceModel, ui_workspace):
        self.model = model
        self.ui = ui_workspace

    def split_active_pane_horizontal(self):
        # Old signature, new implementation
        return self.model.split_pane(SplitPaneRequest(...))
```

### Phase 6: Feature Flags
```python
if settings.USE_NEW_ARCHITECTURE:
    # New clean path
    result = execute_command("workbench.action.splitPane")
else:
    # Old path (temporary)
    workspace.split_active_pane_horizontal()
```

### Phase 7: Cleanup
Remove old code only after new code proven stable for 1 week

## Performance Monitoring

### Baseline Measurements (Before)
```python
import time

def measure_operation(operation_name: str, func):
    start = time.perf_counter()
    result = func()
    duration = (time.perf_counter() - start) * 1000
    print(f"{operation_name}: {duration:.2f}ms")
    return result, duration

# Measure current performance
measure_operation("split_pane", lambda: split_pane_horizontal())
# Expected: 200-300ms
```

### Target Measurements (After)
```python
# Same operations should be <50ms
assert duration < 50, f"Operation too slow: {duration}ms"
```

### Performance Test Suite
Create `tests/performance/test_operation_speed.py`:
```python
@pytest.mark.performance
def test_split_pane_performance():
    """Split pane should complete in <50ms."""
    # Setup
    model = WorkspaceModelImpl()

    # Measure
    start = time.perf_counter()
    model.split_pane(SplitPaneRequest(...))
    duration = (time.perf_counter() - start) * 1000

    # Assert
    assert duration < 50
```

## File Creation Order

### Phase 1 Files (Create in this order)

1. **Directory Structure**
   ```bash
   mkdir -p packages/viloapp/src/viloapp/models
   mkdir -p packages/viloapp/src/viloapp/interfaces
   mkdir -p packages/viloapp/tests/models
   mkdir -p packages/viloapp/tests/architecture
   ```

2. **Base Models** (`models/base.py`)
   ```python
   from dataclasses import dataclass
   from typing import Optional, Dict, Any

   @dataclass
   class OperationResult:
       success: bool
       error: Optional[str] = None
       data: Optional[Dict[str, Any]] = None
   ```

3. **Workspace Models** (`models/workspace_models.py`)
   - Import from base
   - Define PaneState, TabState, WorkspaceState

4. **Operations** (`models/operations.py`)
   - Import from base
   - Define all request/response DTOs

5. **Interfaces** (`interfaces/model_interfaces.py`)
   - Import from models
   - Define IWorkspaceModel ABC

6. **Tests** (in order)
   - `test_base.py` - Test OperationResult
   - `test_workspace_models.py` - Test state models
   - `test_operations.py` - Test DTOs
   - `test_interfaces.py` - Test interface contracts

## Common Pitfalls to Avoid

### ❌ DON'T: Fix symptoms, not causes
```python
# BAD: Just hiding the UI call
def split_pane_command():
    try:
        workspace.split_active_pane()  # Still wrong!
    except:
        pass
```

### ✅ DO: Fix the root cause
```python
# GOOD: Properly route through service
def split_pane_command():
    service = get_service(WorkspaceService)
    return service.split_active_pane()
```

### ❌ DON'T: Create new circular dependencies
```python
# BAD: Service calling back to UI
class WorkspaceService:
    def update(self):
        self.ui.refresh()  # NO! Creates circular dependency
```

### ✅ DO: Use observer pattern
```python
# GOOD: Service notifies, UI observes
class WorkspaceService:
    def update(self):
        self.notify_observers("updated", data)
```

### ❌ DON'T: Mix concerns
```python
# BAD: Model knows about Qt
from PySide6.QtCore import Signal  # Model shouldn't know Qt!

class WorkspaceModel:
    changed = Signal()  # WRONG!
```

### ✅ DO: Keep layers pure
```python
# GOOD: Model is pure Python
class WorkspaceModel:
    def __init__(self):
        self._observers = []  # Pure Python observers
```

## Validation Methods

### After Each Task
1. **Syntax Check**: File compiles without errors
2. **Import Check**: No forbidden imports
3. **Test Check**: New tests pass
4. **Regression Check**: Old tests still pass
5. **Violation Check**: Target violation is gone

### After Each Phase
1. **Success Criteria**: All criteria marked ✅
2. **Coverage Check**: Test coverage increased
3. **Performance Check**: No performance regression
4. **Integration Check**: Components work together
5. **Documentation Check**: All changes documented

## Git Commit Message Format

```
fix(arch): Phase N - [Task description]

- Fixed [specific violation] in [file:line]
- Moved [what] from [where] to [where]
- Added tests for [what]

Violations fixed: X/54
Phase progress: Task N.M complete

Related: #architecture-fix
```

Example:
```
fix(arch): Phase 1 - Create core data models

- Created OperationResult pattern for consistent returns
- Added PaneState, TabState, WorkspaceState models
- Zero Qt dependencies in models layer
- Added 15 tests with 100% coverage

Violations fixed: 0/54 (foundation work)
Phase progress: Task 1.1 complete

Related: #architecture-fix
```

## Emergency Procedures

### If Build Breaks
```bash
# Immediate rollback
git stash
git checkout HEAD~1

# Investigate
pytest --lf  # Run last failed
git diff HEAD~1  # What changed?
```

### If Performance Degrades
```python
# Add timing decorator
from functools import wraps
import time

def timed(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        print(f"{func.__name__}: {time.perf_counter() - start:.3f}s")
        return result
    return wrapper

@timed
def problematic_function():
    ...
```

### If Circular Dependency Created
```python
# Use architecture test
def test_no_circular_imports():
    from tools.import_checker import find_circular_imports
    circles = find_circular_imports("packages/viloapp")
    assert len(circles) == 0, f"Circular imports: {circles}"
```

## Daily Standup Format

Start each session by reporting:
```markdown
## Architecture Fix - Day N Status

**Current Phase**: N - [Name]
**Current Task**: N.M - [Description]

### Yesterday
- Completed: [What was finished]
- Violations Fixed: X
- Tests Added: Y

### Today
- Goal: [Specific task]
- Target Violations: [Which ones]
- Expected Tests: [How many]

### Blockers
- [Any blockers]

### Metrics
- Total Violations Fixed: X/54
- Test Coverage: X% → Y%
- Performance: Current metrics
```

## Success Verification Script

Create and run periodically:
```python
# verify_progress.py
def verify_architecture_progress():
    results = {}

    # Check violations
    results['command_violations'] = count_pattern('workspace.split_active', 'commands/')
    results['service_violations'] = count_pattern('_workspace.tab_widget', 'services/')
    results['circular_deps'] = check_circular_dependencies()

    # Check progress
    results['models_created'] = os.path.exists('models/workspace_models.py')
    results['interfaces_created'] = os.path.exists('interfaces/model_interfaces.py')

    # Check tests
    results['test_coverage'] = get_coverage_percent()
    results['tests_passing'] = run_tests()

    print_report(results)
    return all_criteria_met(results)
```

## Remember

1. **The plan is sacred** - Don't deviate without documentation
2. **Tests first** - TDD is mandatory
3. **One violation at a time** - Systematic progress
4. **Document everything** - Future maintainers need context
5. **Verify constantly** - Don't assume, verify
6. **Rollback quickly** - If something breaks, rollback immediately
7. **Measure everything** - Performance, coverage, violations

Your mission: Transform a codebase with 54+ violations into a clean, maintainable architecture that follows the Northstar principles. Be methodical, be thorough, and follow the plan.

---

*Begin with Phase 1, Task 1.1: Create the models directory and implement OperationResult.*