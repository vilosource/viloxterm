# ViloxTerm Architecture Northstar Guide

## The Sacred Rules of Architecture

This document defines the **inviolable architectural principles** that MUST be followed by all developers working on ViloxTerm. These rules exist to prevent the architectural decay that led to 54+ violations requiring a 7-week fix.

**Violation of these rules requires explicit architectural review and approval.**

---

## 🚨 THE CARDINAL RULES (Never Break These)

### Rule 1: One-Way Data Flow
```
User Input → Command → Service → Model → View (via Observer)
```
- **NEVER** create circular dependencies
- **NEVER** have Service call UI methods
- **NEVER** have UI call Service then Service call UI

### Rule 2: Single Entry Point
- **ALL** user operations MUST go through Commands
- **NO** direct widget manipulation from outside
- **NO** multiple paths to the same operation

### Rule 3: Layer Isolation
- **Commands** can ONLY call Services
- **Services** can ONLY work with Models
- **UI** can ONLY observe Models and execute Commands
- **Models** have ZERO knowledge of UI or Services

### Rule 4: Business Logic Location
- **ALL** business logic in Service layer
- **NO** business rules in UI components
- **NO** validation MessageBoxes in UI layer
- **NO** "if can_close" checks in UI

---

## 📋 LAYER RESPONSIBILITIES

### Command Layer (`/core/commands/`)
**Purpose**: Entry point for all operations

✅ **DO**:
```python
@command(id="workbench.action.splitPane")
def split_pane_command(context: CommandContext) -> CommandResult:
    service = context.get_service(WorkspaceService)
    result = service.split_pane(orientation)
    return CommandResult(success=result.success, error=result.error)
```

❌ **DON'T**:
```python
# NEVER access UI directly
workspace.split_active_pane_horizontal()  # VIOLATION!

# NEVER access widget internals
widget.model.change_pane_type()  # VIOLATION!
```

### Service Layer (`/services/`)
**Purpose**: Business logic and orchestration

✅ **DO**:
```python
class WorkspaceService:
    def __init__(self, model: IWorkspaceModel):
        self._model = model  # Work with interfaces

    def can_close_tab(self, index: int) -> bool:
        return self._model.get_tab_count() > 1  # Business rule
```

❌ **DON'T**:
```python
# NEVER access UI widgets
self._workspace.tab_widget.currentIndex()  # VIOLATION!

# NEVER call UI methods
self._workspace.add_editor_tab()  # VIOLATION!

# NEVER access widget internals
widget.model.pane_indices.items()  # VIOLATION!
```

### Model Layer (`/models/`)
**Purpose**: Pure data and state management

✅ **DO**:
```python
class WorkspaceModel:
    def __init__(self):
        self._state = WorkspaceState()
        self._observers = []

    def add_tab(self, name: str) -> OperationResult:
        # Pure logic, no UI knowledge
        tab = TabState(name=name)
        self._state.tabs.append(tab)
        self._notify_observers("tab_added", tab)
        return OperationResult(success=True)
```

❌ **DON'T**:
```python
# NEVER import Qt/UI modules
from PySide6.QtWidgets import QWidget  # VIOLATION!

# NEVER reference UI components
if self.tab_widget.count() > 0:  # VIOLATION!
```

### UI Layer (`/ui/`)
**Purpose**: Pure presentation and user interaction

✅ **DO**:
```python
class Workspace(QWidget):
    def __init__(self, model: IWorkspaceModel):
        self._model = model
        model.add_observer(self._on_model_changed)

    def _on_split_requested(self):
        # Use commands for operations
        execute_command("workbench.action.splitPane")

    def _on_model_changed(self, event: str, data: Any):
        # React to model changes
        if event == "tab_added":
            self._create_tab_widget(data)
```

❌ **DON'T**:
```python
# NEVER implement business logic
if self.tab_widget.count() <= 1:  # VIOLATION!
    QMessageBox.information("Cannot close last tab")

# NEVER call services directly (except through commands)
workspace_service.split_pane()  # VIOLATION!

# NEVER create your own Model/Controller
self.model = SplitPaneModel()  # VIOLATION! Should be injected
```

---

## 🏗️ ARCHITECTURAL PATTERNS

### Pattern 1: Dependency Injection
**Always inject dependencies, never create them**

✅ **GOOD**:
```python
class SplitPaneWidget(QWidget):
    def __init__(self, model: ISplitPaneModel, controller: IController):
        self.model = model  # Injected
        self.controller = controller  # Injected
```

❌ **BAD**:
```python
class SplitPaneWidget(QWidget):
    def __init__(self):
        self.model = SplitPaneModel()  # Created internally - VIOLATION!
        self.controller = Controller(self.model)  # Tight coupling!
```

### Pattern 2: Observer Pattern
**Models notify, Views observe**

✅ **GOOD**:
```python
# Model notifies
self._notify_observers("state_changed", new_state)

# View observes
model.add_observer(self._on_model_changed)
```

❌ **BAD**:
```python
# Model directly updates view - VIOLATION!
self.view.update_display(new_state)

# View polls model - VIOLATION!
if self.model.has_changed():
    self.refresh()
```

### Pattern 3: Command Pattern
**All operations through commands**

✅ **GOOD**:
```python
# Context menu action
action.triggered.connect(
    lambda: execute_command("workbench.action.splitPane")
)
```

❌ **BAD**:
```python
# Direct method call - VIOLATION!
action.triggered.connect(self.split_pane_horizontal)

# Multiple paths - VIOLATION!
# Path 1: via command
# Path 2: direct widget.split()
# Path 3: via service
```

### Pattern 4: Result Pattern
**Always return structured results**

✅ **GOOD**:
```python
def split_pane(self, orientation: str) -> OperationResult:
    if not self.can_split():
        return OperationResult(success=False, error="Cannot split")
    # ... do split
    return OperationResult(success=True, data={"pane_id": new_id})
```

❌ **BAD**:
```python
def split_pane(self, orientation: str) -> bool:  # What failed? Why?
    return False

def split_pane(self, orientation: str):  # No error handling!
    self.do_split()
```

---

## 🔍 CODE REVIEW CHECKLIST

Before approving any PR, verify:

### Commands
- [ ] Only calls Service methods?
- [ ] No UI access?
- [ ] No Model direct access?
- [ ] Returns CommandResult?

### Services
- [ ] Works with Model interfaces only?
- [ ] No Qt/PySide imports?
- [ ] No UI widget access?
- [ ] Returns OperationResult?
- [ ] Contains ALL business logic?

### Models
- [ ] Pure data structures?
- [ ] No UI dependencies?
- [ ] Notifies observers?
- [ ] Serializable state?

### UI Components
- [ ] NO business logic?
- [ ] Dependencies injected?
- [ ] Only observes Model?
- [ ] Only executes Commands?
- [ ] NO direct Service calls?

### General
- [ ] No circular dependencies?
- [ ] Single path for operation?
- [ ] Proper error handling?
- [ ] Unit testable?

---

## 🚫 FORBIDDEN PATTERNS

### 1. The Circular Service Pattern
```python
# FORBIDDEN!
class Workspace:
    def split_pane(self):
        service.split_pane()  # UI → Service

class WorkspaceService:
    def split_pane(self):
        workspace.do_split()  # Service → UI (VIOLATION!)
```

### 2. The Business MessageBox
```python
# FORBIDDEN!
class UIComponent:
    def close_tab(self):
        if self.tab_count() <= 1:
            QMessageBox.show("Cannot close")  # Business logic in UI!
```

### 3. The Model Creator
```python
# FORBIDDEN!
class View:
    def __init__(self):
        self.model = Model()  # View creates Model (VIOLATION!)
```

### 4. The Direct Access
```python
# FORBIDDEN!
class Command:
    def execute(self):
        widget.model.do_something()  # Command → Model directly!
```

### 5. The Multi-Path
```python
# FORBIDDEN!
# Three ways to do the same thing:
execute_command("split")
service.split()
widget.split()
```

---

## ✅ APPROVED PATTERNS

### 1. The Command Flow
```python
# APPROVED
User Action
    → execute_command("operation")
        → Command.execute()
            → Service.operation()
                → Model.update()
                    → Observer notification
                        → View.refresh()
```

### 2. The Error Bubble
```python
# APPROVED
Model.operation() → OperationResult(success=False, error="Reason")
    ↓
Service.operation() → Adds context
    ↓
Command.execute() → CommandResult(success=False, error="User message")
    ↓
UI.handle_result() → Shows error appropriately
```

### 3. The Factory Pattern
```python
# APPROVED
class WidgetFactory:
    @staticmethod
    def create_split_widget() -> SplitWidget:
        model = Model()
        controller = Controller(model)
        view = SplitWidget(model, controller)
        return view
```

---

## 📊 ARCHITECTURE DECISION RECORDS

### ADR-001: No Service-to-UI Calls
**Decision**: Services must NEVER call UI methods directly
**Reason**: Creates circular dependencies, breaks testability
**Alternative**: Use observer pattern for UI updates

### ADR-002: Single Command Entry
**Decision**: All operations must go through Commands
**Reason**: Multiple paths lead to inconsistent behavior
**Alternative**: None - this is mandatory

### ADR-003: Model Injection
**Decision**: Models must be injected into Views, not created
**Reason**: Enables testing, prevents tight coupling
**Alternative**: Factory pattern for complex creation

### ADR-004: Business Logic in Services
**Decision**: ALL business logic must be in Service layer
**Reason**: UI should be swappable without losing logic
**Alternative**: None - strict separation required

---

## 🔧 ENFORCEMENT TOOLS

### Pre-commit Hooks
```bash
# .pre-commit-config.yaml
- id: check-architecture
  name: Check Architecture Rules
  entry: python scripts/check_architecture.py
  language: python
  files: \.py$
```

### Architecture Tests
```python
# tests/architecture/test_no_circular_deps.py
def test_no_service_imports_ui():
    service_files = glob("**/services/*.py")
    for file in service_files:
        content = read_file(file)
        assert "from viloapp.ui" not in content
        assert "from PySide6" not in content
```

### CI Pipeline Checks
```yaml
# .github/workflows/architecture.yml
- name: Architecture Compliance
  run: |
    python scripts/check_layer_violations.py
    python scripts/check_circular_dependencies.py
    python scripts/check_command_pattern.py
```

---

## 📚 REQUIRED READING

Before working on ViloxTerm architecture:

1. **MainTabbedSplitPanes.md** - Current architecture documentation
2. **architecture-violations-REPORT.md** - What went wrong and why
3. **architecture-fix-IMPLEMENTATION-PLAN.md** - How we're fixing it
4. This document - The rules going forward

---

## 🤝 ARCHITECTURE REVIEW PROCESS

### When Review is Required
- Adding new commands
- Creating new services
- Modifying data flow
- Adding UI/Service interactions
- Creating new models

### Review Checklist
1. Does it follow one-way data flow?
2. Are responsibilities correctly placed?
3. Is it testable in isolation?
4. Does it use existing patterns?
5. Are there any circular dependencies?

### Approval Required From
- Tech Lead for service changes
- Architecture Owner for pattern changes
- Team consensus for new patterns

---

## 💡 QUICK REFERENCE

### Where Does This Logic Go?

| Logic Type | Location | Example |
|------------|----------|---------|
| Can user perform action? | Service | `can_close_tab()` |
| Validation rules | Service | `validate_tab_name()` |
| State changes | Model | `add_tab()` |
| User feedback | UI | Show error dialog |
| Operation orchestration | Service | Coordinate multiple models |
| Data transformation | Service/Model | Format for display |
| Event handling | UI → Command | Button click → execute_command |
| Business rules | Service | Minimum tabs = 1 |
| Visual rules | UI | Tab width = 100px |

### Common Mistakes to Avoid

❌ **"It's just a simple check"** - Business logic always goes in Service
❌ **"I'll refactor it later"** - Violations multiply exponentially
❌ **"It's more convenient this way"** - Convenience creates tech debt
❌ **"The service is right there"** - Use commands, not direct calls
❌ **"It's only one MessageBox"** - Business logic creep starts small

---

## 📝 SIGN-OFF

By contributing to ViloxTerm, you acknowledge that you have:
- [ ] Read this Northstar Guide
- [ ] Understand the layer responsibilities
- [ ] Will follow the cardinal rules
- [ ] Will request review when unsure
- [ ] Will reject PRs that violate these rules

**Remember**: These rules exist because we learned the hard way. 54+ violations took 7 weeks to fix. Don't be the person who creates the 55th.

---

*"Architecture is not about perfection, it's about consistency. A consistently followed decent architecture beats a sporadically followed perfect one."*

**Document Version**: 1.0
**Last Updated**: 2024
**Enforcement Level**: MANDATORY