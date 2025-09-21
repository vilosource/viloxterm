# MainTabbedSplitPanes.md - Definitive Architecture Documentation

## Executive Summary

This document serves as the definitive source of truth for ViloxTerm's tabbed interface and split pane system. Based on thorough code analysis, it documents the **actual implementation** including architectural patterns, violations, and the true flow of operations.

**Key Finding**: While the architecture aims for MVC separation and command pattern, there are significant violations that create circular dependencies and mix concerns between layers.

## Architecture Overview

### Layer Structure
```
┌─────────────────────────────────────────────┐
│           Command Layer                     │
│  (Commands → WorkspaceService → UI/Model)   │
├─────────────────────────────────────────────┤
│           Service Layer                     │
│  (WorkspaceService, Managers)               │
├─────────────────────────────────────────────┤
│           UI Layer                          │
│  (Workspace, SplitPaneWidget, PaneContent)  │
├─────────────────────────────────────────────┤
│           Model Layer                       │
│  (SplitPaneModel, Tree Structure)           │
└─────────────────────────────────────────────┘
```

## Tab System Implementation

### Core Components

1. **Workspace** (`workspace.py`) - Main tab container
   - Uses QTabWidget for tab management
   - Each tab contains one SplitPaneWidget
   - Manages tab lifecycle (add, close, rename, duplicate)

2. **WorkspaceTab** - Data container
   ```python
   class WorkspaceTab:
       name: str
       split_widget: SplitPaneWidget
       metadata: dict  # Stores widget_id for singleton widgets
   ```

3. **Tab Operations Flow**
   ```
   User Action → Command → WorkspaceService → Workspace → QTabWidget
                    ↓              ↓
                CommandResult   Notification
   ```

### Tab Management Features
- **Tab Types**: Editor, Terminal, Output, Custom AppWidgets
- **Operations**: Add, Close, Rename, Duplicate, Close Others, Close to Right
- **State**: Persisted via `save_state()`/`restore_state()`

## Split Pane System Architecture

### Model Layer (`split_pane_model.py`)

**Pure Data Structure** - Tree-based representation
```python
SplitNode (orientation, ratio)
    ├── LeafNode (contains AppWidget)
    └── LeafNode or SplitNode
```

**Key Responsibilities**:
- Tree structure management
- AppWidget lifecycle (creation, cleanup)
- Active pane tracking
- State serialization

**IMPORTANT**: Model **owns** the AppWidgets. They are created and destroyed here.

### View Layer (`split_pane_widget.py`, `PaneContent`)

**Visual Representation**
- `SplitPaneWidget`: Main widget coordinating the split view
- `PaneContent`: Wrapper for AppWidgets (adds borders, headers)
- QSplitter widgets for visual splitting

**Key Responsibilities**:
- Render tree structure as Qt widgets
- Handle drag/resize operations
- Forward user interactions to controller
- Visual feedback (active pane highlighting)

### Controller Layer (`split_pane_controller.py`)

**Business Logic Coordination**
- Processes widget actions (split, close, focus)
- Manages state transitions
- Coordinates model updates with view refreshes
- Handles terminal close callbacks

## Command Pattern Implementation

### Intended Flow
```
User Action → execute_command() → Command Function → Service → UI/Model
```

### Actual Implementation (with violations)

#### Tab Commands (Mostly Correct)
```python
# workspace.py - Context menu
execute_command("workbench.action.renameTab", tab_index=index)
    ↓
# tab_commands.py
@command(id="workbench.action.renameTab")
def rename_tab_command(context):
    workspace_service.start_rename_tab(index)
```

#### Pane Commands (VIOLATION PATTERN)
```python
# pane_commands.py - The command
@command(id="workbench.action.splitPaneHorizontal")
def split_pane_horizontal_command(context):
    # VIOLATION: Command directly calls UI method
    workspace.split_active_pane_horizontal()
```

```python
# workspace.py - The UI method
def split_active_pane_horizontal(self):
    # VIOLATION: Circular dependency - UI calls Service
    workspace_service.split_active_pane("horizontal")
    # Fallback: Direct widget manipulation
    widget.split_horizontal(widget.active_pane_id)
```

## Operation Flows

### Split Pane Operation (Actual Flow)

1. **User Action**: Right-click pane → "Split Horizontal"

2. **Context Menu** (`split_pane_widget.py:204`)
   ```python
   execute_command("workbench.action.splitPaneHorizontal", pane=self)
   ```

3. **Command** (`pane_commands.py:24`)
   ```python
   workspace.split_active_pane_horizontal()  # VIOLATION: Direct UI call
   ```

4. **Workspace UI** (`workspace.py:612`)
   ```python
   workspace_service.split_active_pane("horizontal")  # Circular call to service
   # OR fallback:
   widget.split_horizontal(widget.active_pane_id)  # Direct widget manipulation
   ```

5. **Service** (`workspace_service.py:372`)
   ```python
   self._pane_manager.split_active_pane(orientation)
   ```

6. **Pane Manager** (`workspace_pane_manager.py:41`)
   ```python
   widget.split_horizontal(widget.active_pane_id)  # Back to UI widget
   ```

7. **SplitPaneWidget** (`split_pane_widget.py:808`)
   ```python
   self.controller.split_horizontal(pane_id)
   ```

8. **Controller** (`split_pane_controller.py:176`)
   ```python
   self._split_pane_internal(pane_id, params)
   ```

9. **Model** (`split_pane_model.py:307`)
   ```python
   # Finally! Actual business logic
   new_leaf = LeafNode(widget_type=leaf.widget_type)
   split = SplitNode(orientation=orientation)
   # Tree manipulation...
   ```

**Problem**: 9 layers for what should be 3-4 layers!

### Close Pane Operation

Similar circular pattern:
```
Command → Workspace.close_active_pane() → WorkspaceService.close_active_pane()
→ PaneManager → SplitPaneWidget → Controller → Model
```

### Widget Action Routing

**Correct Pattern** (from AppWidget up):
```python
# AppWidget emits signal
self.action_requested.emit("split", {"orientation": "horizontal"})
    ↓
# SplitPaneWidget connects and forwards
widget.action_requested.connect(lambda: self.handle_widget_action())
    ↓
# Controller processes
controller.handle_widget_action(leaf_id, action, params)
    ↓
# Model updates
model.split_pane(pane_id, orientation)
```

## Architectural Violations and Anti-patterns

### 1. Command Pattern Violations

**Problem**: Commands call UI methods directly instead of services
```python
# VIOLATION in pane_commands.py
workspace.split_active_pane_horizontal()  # Should call service method
```

**Impact**: Breaks command pattern, creates tight coupling

### 2. Circular Dependencies

**Problem**: UI → Service → UI circular calls
```python
# workspace.py
def split_active_pane_horizontal(self):
    workspace_service.split_active_pane()  # UI calls Service

# workspace_service.py
def split_active_pane(self):
    widget.split_horizontal()  # Service calls UI
```

**Impact**: Violates layer separation, makes testing difficult

### 3. Business Logic in UI Layer

**Problem**: Workspace contains business decisions
```python
# workspace.py:354 - Business logic in UI
if self.tab_widget.count() <= 1:
    QMessageBox.information(...)  # Mixing business rule with UI
    return
```

**Should be**: Service layer determines if operation is valid

### 4. Inconsistent State Management

**Problem**: State tracked in multiple places
- Tab indices in WorkspaceWidgetRegistry
- Active pane in SplitPaneModel
- Tab data in Workspace.tabs dict

**Impact**: State synchronization issues

### 5. Direct Widget Manipulation

**Problem**: Multiple paths to same operation
```python
# Path 1: Through commands
execute_command("workbench.action.splitPaneHorizontal")

# Path 2: Direct method calls
widget.split_horizontal(pane_id)

# Path 3: Through service
workspace_service.split_active_pane("horizontal")
```

**Impact**: Inconsistent behavior, difficult to track operations

### 6. MVC Violations in SplitPaneWidget

**Problem**: View directly creates and manipulates model
```python
# split_pane_widget.py - View creating model
self.model = SplitPaneModel(initial_widget_type)
self.controller = SplitPaneController(self.model)
```

**Should be**: Model injected into view, controller orchestrates

## Correct MVC Implementation (What Should Be)

### Proper Command Flow
```
Command → Service (business logic) → Model (data update) → View (presentation)
                                           ↓
                                    Signal/Observer → View Update
```

### Proper Layer Responsibilities

**Model**: Pure data, no UI knowledge
- Tree structure
- Widget registry
- State persistence

**View**: Pure presentation, no business logic
- Render model state
- Capture user input
- Forward events (not process)

**Controller/Service**: All business logic
- Validate operations
- Coordinate updates
- Manage state transitions

## AppWidget System

### Lifecycle Management

**Creation Flow**:
```
SplitPaneModel.create_app_widget()
    → AppWidgetManager.create_widget()
        → Factory or Class instantiation
            → Widget initialization (may be async)
                → set_ready() when complete
```

**State Transitions**:
```
CREATED → INITIALIZING → READY ←→ SUSPENDED
                ↓                      ↓
              ERROR              DESTROYING → DESTROYED
```

### Widget Communication

**Correct**: Signals bubble up through tree
```python
AppWidget → action_requested signal
          → PaneContent (forwards)
          → SplitPaneWidget (handles)
          → Controller (processes)
          → Model (updates)
```

## Recommendations for Fixing Violations

### 1. Fix Command Pattern
```python
# pane_commands.py - CORRECT
@command(id="workbench.action.splitPaneHorizontal")
def split_pane_horizontal_command(context):
    # Call service, not UI
    return workspace_service.split_active_pane("horizontal")
```

### 2. Remove Circular Dependencies
```python
# workspace.py - REMOVE these methods
# def split_active_pane_horizontal(self)  # Delete
# def split_active_pane_vertical(self)    # Delete
# def close_active_pane(self)             # Delete
```

### 3. Move Business Logic to Service
```python
# workspace_service.py
def can_close_tab(self, index):
    """Business logic for tab closing"""
    return self.get_tab_count() > 1

def can_close_pane(self, pane_id):
    """Business logic for pane closing"""
    return self.get_pane_count() > 1
```

### 4. Consolidate State Management
- Single source of truth in Model layer
- Views observe model changes
- No duplicate state tracking

### 5. Enforce Single Path Operations
- All operations go through commands
- Commands call services
- Services update models
- Models notify views

## Testing Implications

Current architecture makes testing difficult due to:
- Circular dependencies prevent unit testing
- UI/Business logic mixing requires GUI for testing
- Multiple paths to operations cause inconsistent test results

With proper separation:
- Model: Unit testable (no UI dependencies)
- Service: Unit testable (mock model/view)
- View: Widget testing (mock model)
- Commands: Integration tests

## Conclusion

The ViloxTerm tabbed split pane system has a **well-intentioned architecture** that attempts MVC and command patterns, but suffers from **significant violations** that undermine these patterns. The tree-based split pane model is elegant, but the layers above it create unnecessary complexity through circular dependencies and mixed responsibilities.

**Priority Fixes**:
1. Remove UI methods that duplicate service functionality
2. Fix commands to call services, not UI
3. Move all business logic from UI to service layer
4. Establish clear, one-way data flow

The architecture would benefit from strict enforcement of layer boundaries and removal of "convenience" methods that bypass proper channels.