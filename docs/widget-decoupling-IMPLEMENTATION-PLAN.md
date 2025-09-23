# Widget System Decoupling Implementation Plan

## Overview

Complete removal of the hardcoded `WidgetType` enum and replacement with string-based widget IDs. This is a breaking change that will touch 57+ files but will permanently fix the plugin extensibility problem.

## Core Principle

**No backward compatibility with the enum system**. We're making a clean break to avoid years of technical debt.

## Phase 1: Rip Out the Enum (Day 1)

### Task 1.1: Delete WidgetType Enum
**Files to modify**:
- `packages/viloapp/src/viloapp/models/workspace_model.py`
  - Delete the WidgetType enum completely
  - Change `widget_type: WidgetType` to `widget_id: str` in Pane dataclass
  - Update all methods to use widget_id instead of widget_type

### Task 1.2: Fix Model Methods
**Location**: `packages/viloapp/src/viloapp/models/workspace_model.py`
```python
@dataclass
class Pane:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    widget_id: str = "viloapp.terminal"  # Default to terminal
    # Remove: widget_type: WidgetType = WidgetType.TERMINAL

def create_tab(self, name: str, widget_id: str = "viloapp.terminal"):
    # No more WidgetType parameter

def change_pane_widget(self, pane_id: str, widget_id: str):
    # Direct string usage
```

### Task 1.3: Define Standard Widget IDs
**Create**: `packages/viloapp/src/viloapp/core/widget_ids.py`
```python
# Standard widget identifiers
TERMINAL = "viloapp.terminal"
EDITOR = "viloapp.editor"
OUTPUT = "viloapp.output"
SETTINGS = "viloapp.settings"
FILE_EXPLORER = "viloapp.file_explorer"

# For migration from old saves
LEGACY_MAP = {
    "terminal": TERMINAL,
    "editor": EDITOR,
    "text_editor": EDITOR,
    "output": OUTPUT,
    "settings": SETTINGS,
    "file_explorer": FILE_EXPLORER,
    "custom": "plugin.unknown"
}
```

## Phase 2: Update All Commands (Day 1-2)

### Task 2.1: Mass Update Command Files
**Pattern for all command files**:
```python
# OLD
from viloapp.models.workspace_model import WidgetType
context.model.create_tab(name, WidgetType.TERMINAL)

# NEW
from viloapp.core.widget_ids import TERMINAL
context.model.create_tab(name, TERMINAL)
```

**Files to update**:
- `core/commands/builtin/file_commands.py` - Replace all WidgetType.EDITOR with EDITOR
- `core/commands/builtin/terminal_commands.py` - Replace all WidgetType.TERMINAL with TERMINAL
- `core/commands/builtin/settings_commands.py` - Replace all WidgetType.SETTINGS with SETTINGS
- `core/commands/builtin/workspace_commands.py` - Update split commands
- `core/commands/builtin/debug_commands.py` - Update debug commands
- `core/commands/builtin/theme_commands.py` - Update theme editor creation

### Task 2.2: Fix When-Context System
**Location**: `core/commands/when_context.py`
```python
# OLD
variables["editorFocus"] = active_pane.widget_type in [WidgetType.EDITOR, WidgetType.TEXT_EDITOR]

# NEW
from viloapp.core.widget_ids import EDITOR
variables["editorFocus"] = active_pane.widget_id == EDITOR
variables["terminalFocus"] = active_pane.widget_id == TERMINAL
variables["explorerFocus"] = active_pane.widget_id == FILE_EXPLORER
```

## Phase 3: Update UI Layer (Day 2)

### Task 3.1: Fix AppWidget Base Class
**Location**: `ui/widgets/app_widget.py`
```python
class AppWidget(QWidget):
    def __init__(self, widget_id: str, instance_id: str, parent=None):
        super().__init__(parent)
        self.widget_id = widget_id
        self.instance_id = instance_id
        # Delete all widget_type references
```

### Task 3.2: Update Workspace Views
**Location**: `ui/workspace_view.py`
```python
# Fix WidgetFactory
class WidgetFactory:
    @staticmethod
    def create(widget_id: str, pane_id: str) -> QWidget:
        # Remove all WidgetType references
        # Use widget_id directly

# Fix PaneView
def _create_header(self):
    # Display widget_id or extract display name
    type_label = QLabel(self.pane.widget_id.split('.')[-1].replace('_', ' ').title())
```

### Task 3.3: Update Workspace Integration
**Location**: `ui/workspace.py`
```python
from viloapp.core.widget_ids import TERMINAL, EDITOR, OUTPUT

def create_new_tab(self, name: str = "New Tab", widget_type: str = "terminal"):
    # Map old string types to widget IDs for compatibility
    widget_id = LEGACY_MAP.get(widget_type.lower(), f"unknown.{widget_type}")
    context.model.create_tab(name, widget_id)
```

## Phase 4: Fix Widget Manager (Day 2-3)

### Task 4.1: Refactor AppWidgetManager
**Location**: `core/app_widget_manager.py`
```python
class AppWidgetManager:
    def __init__(self):
        self._factories: Dict[str, Callable] = {}  # widget_id -> factory
        # Delete _type_mapping completely

    def register_factory(self, widget_id: str, factory: Callable):
        self._factories[widget_id] = factory

    def create_widget(self, widget_id: str, instance_id: str) -> Optional[AppWidget]:
        if widget_id in self._factories:
            return self._factories[widget_id](instance_id)
        # Try plugin system
        return self._create_plugin_widget(widget_id, instance_id)
```

### Task 4.2: Update Widget Registration
**Location**: `core/app_widget_registry.py`
```python
# Update all registrations
manager.register_factory(
    TERMINAL,
    lambda instance_id: TerminalAppWidget(TERMINAL, instance_id)
)

manager.register_factory(
    EDITOR,
    lambda instance_id: EditorAppWidget(EDITOR, instance_id)
)
# ... etc for all widgets
```

## Phase 5: Fix Plugin System (Day 3)

### Task 5.1: Update Plugin Bridge
**Location**: `core/plugin_system/widget_bridge.py`
```python
class PluginAppWidgetAdapter(AppWidget):
    def __init__(self, plugin_widget, qt_widget, instance_id: str):
        # Use plugin's actual widget ID
        widget_id = f"plugin.{plugin_widget.get_widget_id()}"
        super().__init__(widget_id, instance_id)
        # Remove ALL widget type guessing/forcing
```

### Task 5.2: Update Service Adapters
**Location**: `core/plugin_system/service_adapters.py`
- Remove all WidgetType imports
- Use widget IDs directly
- Update workspace adapter methods

## Phase 6: Fix Persistence (Day 3-4)

### Task 6.1: Update Serialization
**Location**: `models/workspace_model.py`
```python
def to_dict(self) -> dict:
    return {
        "id": self.id,
        "widget_id": self.widget_id,  # Save widget ID
        # Remove widget_type completely
    }
```

### Task 6.2: Update Deserialization with Migration
**Location**: `models/workspace_model.py`
```python
@classmethod
def from_dict(cls, data: dict) -> "Pane":
    # Handle old saves that have widget_type
    if "widget_id" in data:
        widget_id = data["widget_id"]
    elif "widget_type" in data:
        # Migrate old format
        old_type = data["widget_type"]
        widget_id = LEGACY_MAP.get(old_type, f"unknown.{old_type}")
    else:
        widget_id = TERMINAL  # Default

    return cls(id=data.get("id"), widget_id=widget_id)
```

## Phase 7: Update All Tests (Day 4-5)

### Task 7.1: Mass Test Update
**Pattern for all test files**:
```python
# OLD
from viloapp.models.workspace_model import WidgetType
widget = create_widget(WidgetType.TERMINAL)

# NEW
from viloapp.core.widget_ids import TERMINAL
widget = create_widget(TERMINAL)
```

**Files to update** (all 30+ test files):
- `tests/unit/test_app_widget_manager.py`
- `tests/unit/test_workspace_commands.py`
- `tests/gui/test_split_pane_widget_lifecycle.py`
- ... etc

### Task 7.2: Remove Widget Type Test Fixtures
- Delete any fixtures that create WidgetType mocks
- Update test helpers to use widget IDs

## Phase 8: Create Widget Metadata System (Day 5)

### Task 8.1: Widget Metadata Registry
**Create**: `packages/viloapp/src/viloapp/core/widget_metadata.py`
```python
@dataclass
class WidgetMetadata:
    widget_id: str
    display_name: str
    icon: Optional[str] = None
    category: str = "general"
    capabilities: Set[str] = field(default_factory=set)

class WidgetMetadataRegistry:
    _instance = None

    def __init__(self):
        self._metadata: Dict[str, WidgetMetadata] = {}
        self._register_builtin()

    def _register_builtin(self):
        self.register(WidgetMetadata(
            widget_id=TERMINAL,
            display_name="Terminal",
            icon="terminal",
            category="terminal",
            capabilities={"shell", "command_execution"}
        ))
        # ... register all built-in widgets

    def register(self, metadata: WidgetMetadata):
        self._metadata[metadata.widget_id] = metadata

    def get_display_name(self, widget_id: str) -> str:
        if widget_id in self._metadata:
            return self._metadata[widget_id].display_name
        # Fallback: extract from ID
        return widget_id.split('.')[-1].replace('_', ' ').title()

widget_metadata_registry = WidgetMetadataRegistry()
```

### Task 8.2: Update UI to Use Metadata
**Location**: `ui/workspace_view.py`, `ui/widgets/pane_header.py`
```python
from viloapp.core.widget_metadata import widget_metadata_registry

# In PaneView._create_header
display_name = widget_metadata_registry.get_display_name(self.pane.widget_id)
type_label = QLabel(display_name)
```

## Phase 9: Final Cleanup (Day 5-6)

### Task 9.1: Remove All WidgetType Imports
```bash
# Find and remove all remaining imports
grep -r "from.*WidgetType" packages/
grep -r "import.*WidgetType" packages/
```

### Task 9.2: Delete Compatibility Stub
**Delete**: `packages/viloapp/src/viloapp/ui/widgets/widget_registry.py`
- This stub file is no longer needed

### Task 9.3: Update Documentation
- Update ARCHITECTURE-OVERVIEW.md
- Update command-architecture-FINAL.md
- Create widget-system-ARCHITECTURE.md

## Implementation Script

```bash
#!/bin/bash
# Automated replacement script

# Step 1: Replace WidgetType.TERMINAL with TERMINAL
find packages -name "*.py" -exec sed -i 's/WidgetType\.TERMINAL/TERMINAL/g' {} \;

# Step 2: Replace WidgetType.EDITOR with EDITOR
find packages -name "*.py" -exec sed -i 's/WidgetType\.EDITOR/EDITOR/g' {} \;
find packages -name "*.py" -exec sed -i 's/WidgetType\.TEXT_EDITOR/EDITOR/g' {} \;

# Step 3: Replace WidgetType.SETTINGS with SETTINGS
find packages -name "*.py" -exec sed -i 's/WidgetType\.SETTINGS/SETTINGS/g' {} \;

# Step 4: Replace WidgetType.OUTPUT with OUTPUT
find packages -name "*.py" -exec sed -i 's/WidgetType\.OUTPUT/OUTPUT/g' {} \;

# Step 5: Replace WidgetType.FILE_EXPLORER with FILE_EXPLORER
find packages -name "*.py" -exec sed -i 's/WidgetType\.FILE_EXPLORER/FILE_EXPLORER/g' {} \;

# Step 6: Update imports
find packages -name "*.py" -exec sed -i 's/from viloapp.models.workspace_model import WidgetType/from viloapp.core.widget_ids import TERMINAL, EDITOR, OUTPUT, SETTINGS, FILE_EXPLORER/g' {} \;

# Step 7: Fix widget_type to widget_id
find packages -name "*.py" -exec sed -i 's/widget_type=/widget_id=/g' {} \;
find packages -name "*.py" -exec sed -i 's/\.widget_type/.widget_id/g' {} \;
```

## Validation Checklist

- [ ] App starts without errors
- [ ] Can create tabs with all widget types
- [ ] Can split panes
- [ ] Plugin widgets show correct names (not "CUSTOM")
- [ ] Old saves load correctly (migration works)
- [ ] New saves use widget_id
- [ ] Commands work with all widgets
- [ ] Tests pass
- [ ] No WidgetType enum remains in codebase

## Why This Approach Is Better

1. **Clean Break**: No years of maintaining deprecated code
2. **Immediate Benefits**: Plugins get first-class support right away
3. **Simpler Code**: No dual-system complexity
4. **Faster**: 5-6 days instead of weeks
5. **Clear Migration**: Old saves are converted on load, done

## Risks and Mitigation

| Risk | Mitigation |
|------|------------|
| Break existing saves | Migration in from_dict handles old format |
| Plugin breakage | Plugins already use IWidget interface, not affected |
| Miss some references | Use grep/sed scripts for systematic replacement |
| Test failures | Fix tests as part of the change |

## Order of Implementation

1. **Create widget_ids.py** with constants
2. **Run replacement script** for bulk changes
3. **Fix compilation errors** systematically
4. **Update tests** to use new system
5. **Add metadata registry** for display names
6. **Test thoroughly** with real plugins
7. **Update documentation**

This aggressive approach will completely solve the widget coupling problem in less than a week, with no technical debt carried forward.