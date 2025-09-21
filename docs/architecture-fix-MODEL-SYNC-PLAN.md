# Model Synchronization Architecture Fix

## Problem Statement

The application has two parallel, unsynchronized models:
- **WorkspaceModelImpl**: Clean architecture model in service layer (empty on startup)
- **SplitPaneModel**: Legacy model in UI widgets (contains actual state)

This causes split commands to fail because they operate on the empty WorkspaceModelImpl.

## Root Cause

During state restoration:
1. UI directly creates widgets without going through the model
2. WorkspaceModelImpl is never populated with existing state
3. Commands fail because model has no panes

## Solution Architecture

### Phase 1: Model-First State Restoration

**Goal**: Make WorkspaceModelImpl the single source of truth

1. **Modify state restoration flow**:
   ```
   MainWindow.restore_state()
   → Load saved state from QSettings
   → Parse workspace state JSON
   → Call WorkspaceService.restore_state(state_data)
   → WorkspaceModelImpl populates from state
   → Model notifies UI observers
   → UI creates widgets based on model
   ```

2. **Add restore_state to WorkspaceModelImpl**:
   - Parse saved state structure
   - Create TabState objects with panes
   - Populate model's internal state
   - Notify observers for each tab/pane

### Phase 2: UI Reacts to Model

**Goal**: UI becomes purely reactive to model changes

1. **Workspace listens to model events**:
   - "tab_added" → Create new tab with SplitPaneWidget
   - "pane_split" → Update SplitPaneWidget structure
   - "pane_closed" → Remove pane from display

2. **SplitPaneWidget becomes a view**:
   - Remove internal SplitPaneModel
   - Read structure from WorkspaceModelImpl
   - Only handle display and user interaction

### Phase 3: Unify Widget Creation

**Goal**: All widgets created through model operations

1. **Widget creation flow**:
   ```
   User Action → Command → WorkspaceService
   → WorkspaceModelImpl.split_pane()
   → Model updates state
   → Model notifies observers
   → UI creates AppWidget via factory
   → Widget registered in AppWidgetManager
   ```

2. **AppWidget lifecycle**:
   - Created by model operations
   - Registered in AppWidgetManager
   - Owned by model (PaneState)
   - Displayed by UI (SplitPaneWidget)

## Implementation Steps

### Step 1: Add State Restoration to Model

```python
# In WorkspaceModelImpl
def restore_state(self, state_dict: dict) -> OperationResult:
    """Restore workspace state from saved data."""
    tabs_data = state_dict.get("tabs", [])
    for tab_data in tabs_data:
        # Create tab in model
        self._restore_tab(tab_data)

    # Set active tab
    if "current_tab" in state_dict:
        self._state.active_tab_index = state_dict["current_tab"]

    # Notify UI to sync
    self._notify("state_restored", state_dict)
```

### Step 2: Route State Through Service

```python
# In WorkspaceService
def restore_state(self, state_dict: dict) -> bool:
    """Restore workspace state through model."""
    if self._model:
        result = self._model.restore_state(state_dict)
        return result.success
    return False
```

### Step 3: Update UI State Restoration

```python
# In Workspace
def restore_state(self, state: dict):
    """Restore workspace state through model."""
    # Don't create UI directly, route through service
    workspace_service = ServiceLocator.get(WorkspaceService)
    if workspace_service:
        workspace_service.restore_state(state)
    # UI will be updated via observer callbacks
```

### Step 4: Make SplitPaneWidget Model-Aware

Instead of having its own SplitPaneModel, SplitPaneWidget should:
1. Receive tab_id in constructor
2. Query WorkspaceModelImpl for pane structure
3. Update display when model notifies changes

## Benefits

1. **Single Source of Truth**: WorkspaceModelImpl owns all state
2. **Clean Separation**: Model → Service → UI layers properly separated
3. **Command Pattern Works**: Commands operate on populated model
4. **Predictable State**: All state changes go through model
5. **Plugin-Friendly**: Plugins can observe/modify model cleanly

## Risks and Mitigations

**Risk**: Large refactor might break existing functionality
**Mitigation**: Implement incrementally, maintain backward compatibility

**Risk**: Performance impact from observer notifications
**Mitigation**: Batch notifications, use efficient data structures

**Risk**: Complex state synchronization
**Mitigation**: Clear state flow, comprehensive logging

## Success Criteria

1. Split commands work after state restoration
2. Single model contains all workspace state
3. UI updates reactively to model changes
4. No direct UI state manipulation
5. Clean separation between layers