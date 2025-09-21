# Architecture Fix Implementation Plan

## Overview

This plan details the systematic approach to fix all 54+ architectural violations in ViloxTerm's tab and pane system. The fixes are organized into 7 phases over 7 weeks, with clear dependencies and success criteria.

## Guiding Principles

1. **No Breaking Changes**: All fixes must maintain backward compatibility during transition
2. **Incremental Progress**: Each phase must be independently deployable
3. **Test-Driven**: Write tests before fixing violations
4. **Clear Boundaries**: Enforce strict layer separation
5. **Single Source of Truth**: One model, many views

## Phase 1: Foundation - Data Models and Contracts (Week 1)

### Goal
Establish clear data contracts between layers without breaking existing code.

### Tasks

#### 1.1 Create Core Data Models

**File**: `packages/viloapp/src/viloapp/models/workspace_models.py`
```python
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from enum import Enum

class OperationResult:
    """Standard result for all operations."""
    success: bool
    error: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

@dataclass
class PaneState:
    """Pure data representation of a pane."""
    id: str
    widget_type: str
    widget_state: Dict[str, Any]
    is_active: bool

@dataclass
class TabState:
    """Pure data representation of a tab."""
    id: str
    name: str
    pane_tree: Dict[str, Any]  # Serialized tree structure
    active_pane_id: str

@dataclass
class WorkspaceState:
    """Pure data representation of workspace."""
    tabs: List[TabState]
    active_tab_index: int

    def can_close_tab(self, index: int) -> OperationResult:
        """Business rule: Can't close last tab."""
        if len(self.tabs) <= 1:
            return OperationResult(False, "Cannot close the last remaining tab")
        return OperationResult(True)
```

#### 1.2 Create Operation DTOs

**File**: `packages/viloapp/src/viloapp/models/operations.py`
```python
@dataclass
class SplitPaneRequest:
    pane_id: str
    orientation: str  # "horizontal" or "vertical"
    ratio: float = 0.5

@dataclass
class ClosePaneRequest:
    pane_id: str
    force: bool = False

@dataclass
class TabOperationRequest:
    operation: str  # "add", "close", "rename", "duplicate"
    tab_index: Optional[int] = None
    tab_name: Optional[str] = None
    tab_type: Optional[str] = None
```

#### 1.3 Create Model Interfaces

**File**: `packages/viloapp/src/viloapp/interfaces/model_interfaces.py`
```python
from abc import ABC, abstractmethod

class IWorkspaceModel(ABC):
    """Interface for workspace model - no Qt dependencies."""

    @abstractmethod
    def get_state(self) -> WorkspaceState:
        pass

    @abstractmethod
    def add_tab(self, name: str, type: str) -> OperationResult:
        pass

    @abstractmethod
    def close_tab(self, index: int) -> OperationResult:
        pass

    @abstractmethod
    def split_pane(self, request: SplitPaneRequest) -> OperationResult:
        pass
```

### Success Criteria
- [ ] All data models created and tested
- [ ] No existing code broken
- [ ] Models have zero Qt dependencies

## Phase 2: Service Layer Refactoring (Week 2)

### Goal
Move all business logic to services, working with pure data models.

### Tasks

#### 2.1 Create WorkspaceModel Implementation

**File**: `packages/viloapp/src/viloapp/models/workspace_model_impl.py`
```python
class WorkspaceModelImpl(IWorkspaceModel):
    """Pure data model for workspace - no UI dependencies."""

    def __init__(self):
        self._state = WorkspaceState(tabs=[], active_tab_index=0)
        self._observers = []

    def add_observer(self, callback):
        self._observers.append(callback)

    def _notify(self, event_type: str, data: Any):
        for observer in self._observers:
            observer(event_type, data)

    def add_tab(self, name: str, type: str) -> OperationResult:
        # Pure business logic
        tab = TabState(id=generate_id(), name=name, ...)
        self._state.tabs.append(tab)
        self._notify("tab_added", tab)
        return OperationResult(True, data={"tab_id": tab.id})
```

#### 2.2 Refactor WorkspaceService

**Changes to**: `packages/viloapp/src/viloapp/services/workspace_service.py`

```python
class WorkspaceService(Service):
    def __init__(self, model: IWorkspaceModel):
        self._model = model  # Work with model, not UI
        self._widget_registry = WorkspaceWidgetRegistry()

    def split_active_pane(self, orientation: str) -> OperationResult:
        # Work with model
        state = self._model.get_state()
        active_tab = state.tabs[state.active_tab_index]

        request = SplitPaneRequest(
            pane_id=active_tab.active_pane_id,
            orientation=orientation
        )

        # Business logic validation
        if not self._can_split_pane(state, request):
            return OperationResult(False, "Cannot split pane")

        # Update model
        result = self._model.split_pane(request)

        # Model will notify observers (including UI)
        return result
```

#### 2.3 Fix Service Managers

**Changes to**: `packages/viloapp/src/viloapp/services/workspace_pane_manager.py`

Remove ALL direct UI access:
```python
# DELETE these lines:
# widget = self._workspace.get_current_split_widget()
# widget.split_horizontal(widget.active_pane_id)

# REPLACE with:
def split_active_pane(self, orientation: str) -> OperationResult:
    state = self._model.get_state()
    # Work with pure data
    return self._model.split_pane(SplitPaneRequest(...))
```

### Success Criteria
- [ ] Services work with IWorkspaceModel interface
- [ ] No service accesses UI widgets directly
- [ ] All business logic moved to services
- [ ] Services return OperationResult, not direct values

## Phase 3: Command Layer Fix (Week 3)

### Goal
Make commands the single entry point, calling only services.

### Tasks

#### 3.1 Fix Pane Commands

**Changes to**: `packages/viloapp/src/viloapp/core/commands/builtin/pane_commands.py`

```python
@command(id="workbench.action.splitPaneHorizontal")
def split_pane_horizontal_command(context: CommandContext) -> CommandResult:
    # Get service
    workspace_service = context.get_service(WorkspaceService)
    if not workspace_service:
        return CommandResult(success=False, error="WorkspaceService not available")

    # Call service method ONLY
    result = workspace_service.split_active_pane("horizontal")

    # Convert OperationResult to CommandResult
    return CommandResult(
        success=result.success,
        error=result.error,
        value=result.data
    )

# DELETE all lines like:
# workspace.split_active_pane_horizontal()  # Remove UI calls
# split_widget.model.change_pane_type()     # Remove model access
```

#### 3.2 Create Command Router

**File**: `packages/viloapp/src/viloapp/core/commands/router.py`
```python
class CommandRouter:
    """Ensures all UI operations go through commands."""

    @staticmethod
    def split_pane(orientation: str) -> CommandResult:
        return execute_command(
            f"workbench.action.splitPane{orientation.title()}",
            orientation=orientation
        )

    # Single point for all operations
```

### Success Criteria
- [ ] Commands ONLY call service methods
- [ ] No command accesses UI or model directly
- [ ] All operations have corresponding commands
- [ ] CommandRouter provides single entry point

## Phase 4: UI Layer Cleanup (Week 4)

### Goal
Remove business logic from UI, make it purely presentational.

### Tasks

#### 4.1 Remove Duplicate Methods from Workspace

**Changes to**: `packages/viloapp/src/viloapp/ui/workspace.py`

```python
# DELETE these methods entirely:
def split_active_pane_horizontal(self): ...  # Lines 612-626
def split_active_pane_vertical(self): ...     # Lines 627-641
def close_active_pane(self): ...              # Lines 642-666

# They duplicate service functionality
```

#### 4.2 Make UI Observe Model Changes

```python
class Workspace(QWidget):
    def __init__(self, model: IWorkspaceModel):
        self._model = model
        self._model.add_observer(self._on_model_changed)

    def _on_model_changed(self, event_type: str, data: Any):
        if event_type == "tab_added":
            self._add_tab_widget(data)
        elif event_type == "pane_split":
            self._update_pane_display(data)
        # React to model changes only
```

#### 4.3 Remove Business Logic MessageBoxes

```python
# BEFORE (workspace.py:354-360):
if self.tab_widget.count() <= 1:
    QMessageBox.information(...)  # Business logic in UI

# AFTER:
def close_tab(self, index: int):
    result = execute_command("file.closeTab", index=index)
    if not result.success:
        self._show_error(result.error)  # UI decides how to show
```

### Success Criteria
- [ ] No business logic in UI components
- [ ] UI observes model changes
- [ ] All operations go through commands
- [ ] MessageBoxes only for UI concerns

## Phase 5: MVC Pattern Fix (Week 5)

### Goal
Implement proper MVC with dependency injection.

### Tasks

#### 5.1 Dependency Injection for SplitPaneWidget

**Changes to**: `packages/viloapp/src/viloapp/ui/widgets/split_pane_widget.py`

```python
class SplitPaneWidget(QWidget):
    def __init__(self, model: SplitPaneModel, controller: SplitPaneController, parent=None):
        super().__init__(parent)
        # Injected, not created
        self.model = model
        self.controller = controller

        # Set up observers
        self.model.model_changed.connect(self._on_model_changed)

    def _on_model_changed(self):
        # React to model changes
        self.refresh_view()
```

#### 5.2 Create Widget Factory

**File**: `packages/viloapp/src/viloapp/ui/factories/widget_factory.py`
```python
class WidgetFactory:
    """Creates and wires up MVC components."""

    @staticmethod
    def create_split_pane_widget(initial_type: WidgetType) -> SplitPaneWidget:
        # Create model
        model = SplitPaneModel(initial_type)

        # Create controller with model
        controller = SplitPaneController(model)

        # Create view with both
        view = SplitPaneWidget(model, controller)

        # Wire up additional connections
        controller.set_view(view)

        return view
```

### Success Criteria
- [ ] Model and controller injected into views
- [ ] Views observe model changes
- [ ] Controllers handle all business logic
- [ ] Factory pattern for widget creation

## Phase 6: Eliminate Circular Dependencies (Week 6)

### Goal
Establish strict one-way data flow.

### Tasks

#### 6.1 Remove Service→UI Calls

**Current circular pattern**:
```
UI → Service → UI (circular!)
```

**Fixed pattern**:
```python
# UI initiates
execute_command("splitPane")
    → Command calls Service
        → Service updates Model
            → Model notifies observers
                → UI updates from notification
```

#### 6.2 Create Event Bus

**File**: `packages/viloapp/src/viloapp/core/events/event_bus.py`
```python
class EventBus:
    """Decouples layers through events."""

    def publish(self, event_type: str, data: Any):
        # Notify all subscribers
        for subscriber in self._subscribers[event_type]:
            subscriber(data)

    def subscribe(self, event_type: str, callback):
        self._subscribers[event_type].append(callback)
```

#### 6.3 Update Service Layer

```python
class WorkspaceService:
    def split_active_pane(self, orientation: str) -> OperationResult:
        # Update model
        result = self._model.split_pane(...)

        if result.success:
            # Publish event instead of calling UI
            self._event_bus.publish("pane_split", result.data)

        return result  # Return result, don't call UI
```

### Success Criteria
- [ ] No circular dependencies
- [ ] Clear one-way data flow
- [ ] Event-based communication
- [ ] All layers independently testable

## Phase 7: Testing and Validation (Week 7)

### Goal
Comprehensive testing to ensure fixes work correctly.

### Tasks

#### 7.1 Unit Tests for Each Layer

**Model Tests**:
```python
def test_workspace_model_add_tab():
    model = WorkspaceModelImpl()
    result = model.add_tab("Test", "editor")
    assert result.success
    assert len(model.get_state().tabs) == 1
```

**Service Tests**:
```python
def test_workspace_service_split_pane():
    mock_model = Mock(IWorkspaceModel)
    service = WorkspaceService(mock_model)
    result = service.split_active_pane("horizontal")
    mock_model.split_pane.assert_called_once()
```

#### 7.2 Integration Tests

```python
def test_full_split_flow():
    # Create real components
    model = WorkspaceModelImpl()
    service = WorkspaceService(model)

    # Execute command
    result = execute_command("workbench.action.splitPaneHorizontal")

    # Verify model state
    state = model.get_state()
    assert len(state.tabs[0].panes) == 2
```

#### 7.3 Performance Tests

```python
def test_split_performance():
    # Measure operation time
    start = time.time()
    execute_command("workbench.action.splitPaneHorizontal")
    duration = time.time() - start

    # Should be under 50ms (was 200-300ms)
    assert duration < 0.05
```

### Success Criteria
- [ ] 80%+ unit test coverage
- [ ] All critical paths have integration tests
- [ ] Performance improved by 4x
- [ ] No regressions in functionality

## Implementation Schedule

| Week | Phase | Focus | Risk |
|------|-------|-------|------|
| 1 | Foundation | Data models, DTOs | Low |
| 2 | Service Layer | Business logic migration | Medium |
| 3 | Command Layer | Single entry point | Medium |
| 4 | UI Cleanup | Remove business logic | High |
| 5 | MVC Fix | Dependency injection | High |
| 6 | Circular Deps | One-way data flow | High |
| 7 | Testing | Validation & performance | Low |

## Risk Mitigation

### High-Risk Changes (Weeks 4-6)
- Create feature flags to toggle between old/new implementation
- Maintain backward compatibility adapters
- Incremental rollout with monitoring
- Keep old code paths until new ones proven stable

### Rollback Plan
- Each phase tagged in git
- Automated tests must pass before proceeding
- Feature flags allow instant rollback
- Old code removed only after 2 weeks stable

## Success Metrics

### Quantitative
- [ ] Zero circular dependencies (from 3)
- [ ] 80%+ unit test coverage (from ~0%)
- [ ] <50ms operation latency (from 200-300ms)
- [ ] Zero direct UI calls in services (from 23)
- [ ] Single path per operation (from 3+)

### Qualitative
- [ ] Clear architectural boundaries
- [ ] Easy to understand data flow
- [ ] New features easier to add
- [ ] Bugs easier to diagnose
- [ ] Onboarding time reduced

## Conclusion

This plan systematically addresses all 54+ architectural violations through:
1. **Clear data contracts** (Phase 1)
2. **Proper service layer** (Phase 2)
3. **Command pattern** (Phase 3)
4. **Clean UI layer** (Phase 4)
5. **Proper MVC** (Phase 5)
6. **One-way data flow** (Phase 6)
7. **Comprehensive testing** (Phase 7)

The incremental approach ensures the system remains functional throughout the refactoring, with clear rollback points if issues arise.

Total estimated effort: **7 weeks** with 1-2 developers.