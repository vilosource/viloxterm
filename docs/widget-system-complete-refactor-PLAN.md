# Widget System Complete Refactoring Plan

## Executive Summary

Complete the widget system refactoring to achieve true MVC architecture with perfect separation of concerns, enabling unlimited plugin extensibility without core modifications.

## North Star Principles Compliance

This plan strictly follows:
- **Rule 1**: One-Way Data Flow (UI → Command → Service → Model → Observer → UI)
- **Rule 2**: Single Entry Point (ALL operations through Commands)
- **Rule 3**: Layer Isolation (Models know nothing of UI)
- **Rule 4**: Business Logic in Services only
- **Rule 5**: No Implementation Details in Core
- **Rule 6**: Verification-First Refactoring

## Current State Analysis

### ✅ Completed
- WidgetType enum removed
- String-based widget IDs implemented
- Widget registry with dynamic discovery
- Default widget resolution system
- Widget metadata system

### ❌ Remaining Issues
1. **SplitPaneWidget** - Still a stub, needs to be pure view
2. **WidgetFactory** - Stub, needs to create from model
3. **PaneHeader** - Hardcoded widget types, needs registry integration
4. **Settings UI** - No UI for widget preferences
5. **Model Synchronization** - SplitPaneModel vs WorkspaceModel duality

## Phase 1: Prepare and Verify (Day 1)

### Task 1.1: Commit Current Changes
**Owner**: Developer
**Verification**: Clean git status
```bash
git add -A
git commit -m "feat: Complete widget defaults system with registry-based discovery

- Removed all hardcoded widget IDs from core
- Implemented registry-based default discovery
- Added user preference support
- Fixed workspace commands undefined variable bug
- Updated architecture documentation with refactoring process"
git tag checkpoint-widget-defaults
```

### Task 1.2: Establish Baseline Tests
**Owner**: Developer
**Files**: Create `test_widget_system_baseline.py`
```python
def test_all_commands_execute():
    """Baseline: All commands must execute without NameError."""
    for cmd in registry.get_all():
        execute_command(cmd)  # Must not raise NameError

def test_widget_creation():
    """Baseline: All registered widgets must be creatable."""
    for widget_id in app_widget_manager.get_available_widget_ids():
        widget = app_widget_manager.create_widget(widget_id, "test-instance")
        assert widget is not None

def test_app_startup():
    """Baseline: Application must start."""
    # Simulate app startup
```

### Task 1.3: Setup Continuous Monitoring
**Owner**: Developer
**Files**: Create `monitor_refactoring.sh`
```bash
#!/bin/bash
while true; do
    python -m py_compile packages/viloapp/src/**/*.py
    python test_widget_system_baseline.py
    sleep 2
done
```

## Phase 2: Complete Model Layer (Day 1-2)

### Task 2.1: Finalize WorkspaceModel as Single Source of Truth
**Owner**: Model Layer
**Files**: `models/workspace_model.py`
**North Star**: Rule 3 - Models have ZERO knowledge of UI

```python
class WorkspaceModel:
    """Single source of truth for workspace state."""

    def get_pane_tree(self, tab_id: str) -> PaneTree:
        """Get the complete tree structure for rendering."""
        # Already exists

    def get_available_widget_ids(self) -> list[str]:
        """Get widget IDs that can be used in panes."""
        # Delegate to app_widget_manager
        from viloapp.core.app_widget_manager import app_widget_manager
        return app_widget_manager.get_available_widget_ids()

    def change_pane_widget(self, pane_id: str, widget_id: str) -> bool:
        """Change the widget type of a pane."""
        # Validate widget_id exists
        if widget_id not in self.get_available_widget_ids():
            return False
        # Update pane
        pane = self.find_pane(pane_id)
        if pane:
            pane.widget_id = widget_id
            self._notify_observers("pane_widget_changed", {
                "pane_id": pane_id,
                "widget_id": widget_id
            })
            return True
        return False
```

### Task 2.2: Add Widget Preference Storage to Model
**Owner**: Model Layer
**Files**: `models/workspace_model.py`
```python
@dataclass
class WorkspaceState:
    # Existing fields...
    widget_preferences: dict[str, str] = field(default_factory=dict)
    # Maps context -> preferred widget_id
    # e.g., {"terminal": "plugin.awesome.terminal", "editor": "com.viloapp.editor"}

def set_widget_preference(self, context: str, widget_id: str):
    """Set user's preferred widget for a context."""
    self.state.widget_preferences[context] = widget_id
    self._notify_observers("preference_changed", {
        "context": context,
        "widget_id": widget_id
    })
```

## Phase 3: Service Layer Enhancement (Day 2)

### Task 3.1: Create Widget Management Service
**Owner**: Service Layer
**Files**: Create `services/widget_service.py`
**North Star**: Rule 4 - ALL business logic in Service layer

```python
class WidgetService:
    """Service for widget-related business logic."""

    def __init__(self, model: WorkspaceModel):
        self._model = model

    def get_widget_choices_for_pane(self, pane_id: str) -> list[WidgetChoice]:
        """Get available widget choices for a pane."""
        from viloapp.core.app_widget_manager import app_widget_manager

        choices = []
        for widget_id in app_widget_manager.get_available_widget_ids():
            metadata = app_widget_manager.get_widget(widget_id)
            if metadata and metadata.show_in_menu:
                choices.append(WidgetChoice(
                    widget_id=widget_id,
                    display_name=metadata.display_name,
                    category=metadata.category,
                    icon=metadata.icon
                ))

        # Sort by category and name
        choices.sort(key=lambda c: (c.category.value, c.display_name))
        return choices

    def can_change_widget_type(self, pane_id: str, widget_id: str) -> tuple[bool, str]:
        """Check if widget type can be changed."""
        # Business rules
        if not self._model.find_pane(pane_id):
            return False, "Pane not found"

        from viloapp.core.app_widget_manager import app_widget_manager
        if not app_widget_manager.is_widget_available(widget_id):
            return False, "Widget not available"

        # Check if current widget allows changes
        current_pane = self._model.find_pane(pane_id)
        current_metadata = app_widget_manager.get_widget(current_pane.widget_id)
        if current_metadata and not current_metadata.allow_type_change:
            return False, "Current widget doesn't allow type changes"

        return True, ""

    def change_pane_widget_type(self, pane_id: str, widget_id: str) -> OperationResult:
        """Change pane widget type with validation."""
        can_change, reason = self.can_change_widget_type(pane_id, widget_id)
        if not can_change:
            return OperationResult(success=False, error=reason)

        if self._model.change_pane_widget(pane_id, widget_id):
            return OperationResult(success=True)
        return OperationResult(success=False, error="Failed to change widget")
```

### Task 3.2: Integrate with Existing Services
**Owner**: Service Layer
**Files**: `services/workspace_service.py`
```python
class WorkspaceService:
    def __init__(self, model: WorkspaceModel, widget_service: WidgetService):
        self._model = model
        self._widget_service = widget_service  # Inject widget service
```

## Phase 4: Command Layer Updates (Day 2-3)

### Task 4.1: Create Widget Management Commands
**Owner**: Command Layer
**Files**: Create `core/commands/builtin/widget_commands.py`
**North Star**: Rule 2 - ALL operations through Commands

```python
@command(
    id="pane.changeWidgetType",
    title="Change Pane Widget Type",
    category="Pane",
    when="pane.focused"
)
def change_pane_widget_command(context: CommandContext) -> CommandResult:
    """Change the widget type of the active pane."""
    pane_id = context.parameters.get("pane_id")
    widget_id = context.parameters.get("widget_id")

    if not pane_id or not widget_id:
        return CommandResult(
            status=CommandStatus.FAILURE,
            message="Missing pane_id or widget_id"
        )

    widget_service = context.get_service(WidgetService)
    result = widget_service.change_pane_widget_type(pane_id, widget_id)

    if result.success:
        return CommandResult(status=CommandStatus.SUCCESS)
    return CommandResult(
        status=CommandStatus.FAILURE,
        message=result.error
    )

@command(
    id="settings.setDefaultWidget",
    title="Set Default Widget",
    category="Settings"
)
def set_default_widget_command(context: CommandContext) -> CommandResult:
    """Set the default widget for a context."""
    context_name = context.parameters.get("context")
    widget_id = context.parameters.get("widget_id")

    # Store in model
    context.model.set_widget_preference(context_name, widget_id)

    # Also update global settings
    from viloapp.core.settings.app_defaults import set_default_widget_for_context
    set_default_widget_for_context(context_name, widget_id)

    return CommandResult(status=CommandStatus.SUCCESS)
```

## Phase 5: Pure View Implementation (Day 3-4)

### Task 5.1: Rebuild SplitPaneWidget as Pure View
**Owner**: UI Layer
**Files**: `ui/widgets/split_pane_widget.py`
**North Star**: Rule 1 - View observes Model, no business logic

```python
class SplitPaneWidget(QWidget):
    """Pure view that renders pane tree from model."""

    def __init__(self, model: WorkspaceModel, tab_id: str, parent=None):
        super().__init__(parent)
        self._model = model
        self._tab_id = tab_id
        self._widget_instances = {}  # pane_id -> AppWidget

        # Setup UI
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)

        # Observe model
        model.add_observer(self._on_model_changed)

        # Initial render
        self._render_tree()

    def _on_model_changed(self, event: str, data: dict):
        """React to model changes."""
        if event == "tree_structure_changed" and data.get("tab_id") == self._tab_id:
            self._render_tree()
        elif event == "pane_widget_changed":
            self._update_pane_widget(data["pane_id"], data["widget_id"])
        elif event == "active_pane_changed":
            self._update_active_pane(data["pane_id"])

    def _render_tree(self):
        """Render the complete tree from model."""
        # Clear existing
        self._clear_widgets()

        # Get tree from model
        tab = self._model.get_tab(self._tab_id)
        if not tab:
            return

        # Recursively create widgets
        root_widget = self._create_node_widget(tab.tree.root)
        if root_widget:
            self._layout.addWidget(root_widget)

    def _create_node_widget(self, node: PaneNode) -> QWidget:
        """Create widget for a tree node."""
        if node.node_type == NodeType.LEAF:
            return self._create_pane_widget(node.pane)
        else:
            return self._create_split_widget(node)

    def _create_pane_widget(self, pane: Pane) -> QWidget:
        """Create widget for a pane."""
        from viloapp.core.app_widget_manager import app_widget_manager

        # Create app widget
        widget = app_widget_manager.create_widget(
            pane.widget_id,
            pane.id
        )

        if widget:
            self._widget_instances[pane.id] = widget

            # Wrap with header
            container = QWidget()
            layout = QVBoxLayout(container)
            layout.setContentsMargins(0, 0, 0, 0)

            # Create header (pure view)
            header = PaneHeader(pane.id, self._model, container)
            layout.addWidget(header)
            layout.addWidget(widget)

            return container

        return QWidget()  # Empty placeholder

    def _create_split_widget(self, node: PaneNode) -> QSplitter:
        """Create splitter for split node."""
        from PySide6.QtWidgets import QSplitter
        from PySide6.QtCore import Qt

        orientation = (
            Qt.Horizontal if node.orientation == Orientation.HORIZONTAL
            else Qt.Vertical
        )

        splitter = QSplitter(orientation)

        # Add children
        first = self._create_node_widget(node.first)
        second = self._create_node_widget(node.second)

        splitter.addWidget(first)
        splitter.addWidget(second)

        # Set ratio
        sizes = [int(1000 * node.ratio), int(1000 * (1 - node.ratio))]
        splitter.setSizes(sizes)

        return splitter

    def _clear_widgets(self):
        """Clear all widgets."""
        for widget in self._widget_instances.values():
            widget.deleteLater()
        self._widget_instances.clear()

        # Clear layout
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
```

### Task 5.2: Update PaneHeader to Use Registry
**Owner**: UI Layer
**Files**: `ui/widgets/pane_header.py`
**North Star**: No hardcoded widget types

```python
def _create_widget_type_menu(self) -> QMenu:
    """Create menu for changing widget type."""
    menu = QMenu("Change Widget Type", self)

    # Get choices from service (business logic)
    widget_service = ServiceLocator.get(WidgetService)
    choices = widget_service.get_widget_choices_for_pane(self._pane_id)

    # Group by category
    categories = {}
    for choice in choices:
        if choice.category not in categories:
            categories[choice.category] = []
        categories[choice.category].append(choice)

    # Add to menu
    for category, items in categories.items():
        menu.addSection(category.value.replace('_', ' ').title())
        for choice in items:
            action = QAction(choice.display_name, self)
            if choice.icon:
                action.setIcon(QIcon(choice.icon))

            # Use command to change type
            action.triggered.connect(
                lambda checked, wid=choice.widget_id: execute_command(
                    "pane.changeWidgetType",
                    {"pane_id": self._pane_id, "widget_id": wid}
                )
            )
            menu.addAction(action)

    return menu
```

## Phase 6: Settings UI Integration (Day 4)

### Task 6.1: Add Widget Preferences to Settings
**Owner**: UI Layer
**Files**: `ui/widgets/settings_app_widget.py`

```python
def _create_widget_preferences_section(self) -> QWidget:
    """Create widget preferences section."""
    section = QGroupBox("Default Widgets")
    layout = QFormLayout()

    # Get available contexts
    contexts = ["terminal", "editor", "file", "output"]

    for context in contexts:
        # Get current preference
        current = self._model.state.widget_preferences.get(context)
        if not current:
            current = app_widget_manager.get_default_widget_id(context)

        # Create combo box
        combo = QComboBox()

        # Add available widgets for this context
        for widget_id in app_widget_manager.get_widgets_for_context(context):
            metadata = app_widget_manager.get_widget(widget_id)
            if metadata:
                combo.addItem(metadata.display_name, widget_id)

        # Set current
        index = combo.findData(current)
        if index >= 0:
            combo.setCurrentIndex(index)

        # Connect to command
        combo.currentIndexChanged.connect(
            lambda idx, ctx=context, cmb=combo: execute_command(
                "settings.setDefaultWidget",
                {"context": ctx, "widget_id": cmb.currentData()}
            )
        )

        layout.addRow(f"Default {context.title()}:", combo)

    section.setLayout(layout)
    return section
```

## Phase 7: Factory Pattern Implementation (Day 4-5)

### Task 7.1: Rebuild WidgetFactory
**Owner**: UI Layer
**Files**: `ui/factories/widget_factory.py`
**North Star**: Factory creates from Model

```python
class WidgetFactory:
    """Factory that creates UI components from model."""

    @staticmethod
    def create_split_pane_widget(
        model: WorkspaceModel,
        tab_id: str,
        parent=None
    ) -> SplitPaneWidget:
        """Create split pane widget from model."""
        return SplitPaneWidget(model, tab_id, parent)

    @staticmethod
    def create_pane_header(
        pane_id: str,
        model: WorkspaceModel,
        parent=None
    ) -> PaneHeader:
        """Create pane header from model."""
        return PaneHeader(pane_id, model, parent)

    @staticmethod
    def create_app_widget(
        widget_id: str,
        instance_id: str
    ) -> Optional[AppWidget]:
        """Create app widget using registry."""
        from viloapp.core.app_widget_manager import app_widget_manager
        return app_widget_manager.create_widget(widget_id, instance_id)
```

## Phase 8: Testing and Validation (Day 5)

### Task 8.1: Create Comprehensive Test Suite
**Files**: Create `tests/test_widget_system_complete.py`

```python
class TestWidgetSystemComplete:
    """Comprehensive tests for complete widget system."""

    def test_no_hardcoded_widget_ids(self):
        """Ensure no hardcoded widget IDs in core."""
        # Scan all core files for hardcoded IDs

    def test_plugin_widget_first_class(self):
        """Plugin widgets work exactly like built-in."""
        # Register plugin widget
        # Use as default
        # Create in panes
        # Change types

    def test_mvc_separation(self):
        """Model, View, Controller properly separated."""
        # Model has no UI imports
        # View has no business logic
        # Commands use services

    def test_registry_based_discovery(self):
        """All widget discovery through registry."""
        # No direct widget class imports
        # Dynamic menu generation
        # Settings show all available

    def test_user_preferences_work(self):
        """User preferences properly stored and used."""
        # Set preference
        # Create new tab uses preference
        # Preference persists
```

### Task 8.2: Performance Validation
```python
def test_performance_requirements():
    """Ensure performance requirements met."""
    # Widget creation < 100ms
    # Registry lookup < 1ms
    # Preference lookup < 1ms
    # Tree rendering < 50ms
```

## Phase 9: Documentation and Migration (Day 5-6)

### Task 9.1: Update Architecture Documentation
- Update `ARCHITECTURE-NORTHSTAR.md` with examples
- Create `widget-system-COMPLETE.md`
- Update plugin developer guide

### Task 9.2: Create Migration Guide
```markdown
# Widget System Migration Guide

## For Plugin Developers
- Register your widget with metadata
- No core changes needed
- Can override built-in defaults

## For Core Developers
- Use registry for all widget operations
- Never hardcode widget IDs
- Always use commands for operations
```

## Verification Checklist

After each phase:
- [ ] Run static analysis (no undefined variables)
- [ ] Run test suite (all pass)
- [ ] Test app startup and basic operations
- [ ] Verify no hardcoded widget IDs
- [ ] Check MVC separation maintained
- [ ] Ensure commands work

## Success Metrics

1. **Zero hardcoded widget IDs** in core
2. **Plugin widgets** indistinguishable from built-in
3. **Pure MVC** - View knows nothing of business logic
4. **All operations** through commands
5. **User preferences** fully functional
6. **Performance** requirements met
7. **100% test coverage** for widget system

## Risk Mitigation

1. **Checkpoint after each phase** with git tags
2. **Continuous testing** during development
3. **Rollback strategy** prepared
4. **Incremental changes** with verification
5. **No big-bang changes** - gradual migration

## Timeline

- **Day 1**: Preparation and Model Layer
- **Day 2**: Service Layer and Commands
- **Day 3-4**: Pure View Implementation
- **Day 4**: Settings UI
- **Day 5**: Testing and Validation
- **Day 6**: Documentation and Release

Total: 6 days of focused development

## Next Steps

1. Review and approve this plan
2. Create git branch: `feature/widget-system-complete`
3. Begin with Phase 1: Preparation
4. Follow verification-first approach throughout