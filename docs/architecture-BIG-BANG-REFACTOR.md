# Big Bang Architecture Refactor - Burn It Down

## Philosophy
No compromises. No backward compatibility. No gradual migration. Delete everything wrong and rebuild it right.

## What Gets DELETED 🔥

### Immediate Deletions (Day 1)

```bash
# DELETE all dual model confusion
rm packages/viloapp/src/viloapp/ui/widgets/split_pane_model.py
rm packages/viloapp/src/viloapp/ui/widgets/split_pane_controller.py
rm packages/viloapp/src/viloapp/ui/widgets/split_pane_drag_handler.py
rm packages/viloapp/src/viloapp/ui/widgets/split_pane_view_helpers.py
rm packages/viloapp/src/viloapp/ui/widgets/split_pane_theme_manager.py

# DELETE redundant registries
rm packages/viloapp/src/viloapp/ui/widgets/widget_registry.py
rm packages/viloapp/src/viloapp/services/workspace_widget_registry.py

# DELETE legacy state management
rm packages/viloapp/src/viloapp/ui/widgets/widget_state.py
rm packages/viloapp/src/viloapp/controllers/state_controller.py

# DELETE circular dependency workarounds
# Remove all lazy loading hacks
# Remove all bridge component workarounds
```

### Code to Gut

```python
# In SplitPaneWidget - GUT EVERYTHING except shell
class SplitPaneWidget(QWidget):
    # DELETE all internal model
    # DELETE all state management
    # DELETE all direct manipulation
    # KEEP only render() method
```

```python
# In Workspace - GUT direct widget creation
class Workspace(QWidget):
    # DELETE add_editor_tab()
    # DELETE add_terminal_tab()
    # DELETE restore_state() - direct UI creation
    # KEEP only model observation
```

## What Gets BUILT 🏗️

### Day 1: Pure Model

```python
# packages/viloapp/src/viloapp/models/workspace_model.py
class WorkspaceModel:
    """THE ONLY SOURCE OF TRUTH"""

    def __init__(self):
        self.state = WorkspaceState()
        self.observers = []
        self.command_history = []

    # Every operation goes through model
    def execute(self, operation: Operation) -> Result:
        result = operation.apply(self.state)
        self._notify_observers(result.changes)
        return result

class WorkspaceState:
    """Complete state - no external dependencies"""
    tabs: List[Tab]
    active_tab: str

class Tab:
    """Complete tab state"""
    id: str
    name: str
    tree: PaneTree  # Full tree structure HERE
    active_pane: str

class PaneTree:
    """The tree structure that was scattered"""
    root: PaneNode

    def split(self, pane_id: str, orientation: str) -> str:
        # Tree manipulation in model
        pass

    def close(self, pane_id: str) -> bool:
        # Tree rebalancing in model
        pass

class PaneNode:
    """Single node representation"""
    type: NodeType
    id: str
    # For splits
    orientation: Optional[str]
    ratio: float
    first: Optional[PaneNode]
    second: Optional[PaneNode]
    # For leaves
    pane: Optional[Pane]

class Pane:
    """Complete pane state"""
    id: str
    widget_type: str
    widget_state: dict
    focused: bool
```

### Day 2: Pure Commands

```python
# packages/viloapp/src/viloapp/commands/all_commands.py
class Command:
    """Base for all operations"""
    def execute(self, model: WorkspaceModel, context: Context) -> Result:
        pass

class SplitPaneCommand(Command):
    def execute(self, model: WorkspaceModel, context: Context) -> Result:
        pane_id = context.active_pane
        orientation = context.params.get('orientation')

        # Direct model manipulation
        new_pane_id = model.split_pane(pane_id, orientation)
        return Result(success=True, new_pane=new_pane_id)

# DELETE all UI-touching commands
# DELETE all service-layer indirection
# Commands go STRAIGHT to model
```

### Day 3: Pure Views

```python
# packages/viloapp/src/viloapp/ui/views/workspace_view.py
class WorkspaceView(QWidget):
    """Pure view - zero state, zero logic"""

    def __init__(self, model: WorkspaceModel):
        super().__init__()
        self.model = model
        model.add_observer(self.render)
        self.render()

    def render(self):
        """Complete re-render from model"""
        # Clear everything
        self._clear_all()

        # Rebuild from model
        for tab in self.model.state.tabs:
            self._render_tab(tab)

    def _render_tab(self, tab: Tab):
        """Pure rendering"""
        tab_widget = TabView(tab)
        self.add_tab(tab_widget)

class TabView(QWidget):
    """Renders a single tab"""
    def __init__(self, tab: Tab):
        super().__init__()
        self.render_tree(tab.tree)

    def render_tree(self, tree: PaneTree):
        """Render the tree structure"""
        self._render_node(tree.root)

    def _render_node(self, node: PaneNode):
        if node.type == NodeType.SPLIT:
            splitter = QSplitter(
                Qt.Horizontal if node.orientation == 'horizontal' else Qt.Vertical
            )
            splitter.addWidget(self._render_node(node.first))
            splitter.addWidget(self._render_node(node.second))
            return splitter
        else:
            return PaneView(node.pane)

class PaneView(QWidget):
    """Pure pane rendering"""
    def __init__(self, pane: Pane):
        super().__init__()
        widget = WidgetFactory.create(pane.widget_type, pane.widget_state)
        layout = QVBoxLayout(self)
        layout.addWidget(widget)
```

### Day 4: Single Widget Factory

```python
# packages/viloapp/src/viloapp/widgets/factory.py
class WidgetFactory:
    """Single place for widget creation"""

    @staticmethod
    def create(widget_type: str, state: dict) -> QWidget:
        if widget_type == "terminal":
            return TerminalWidget(state)
        elif widget_type == "editor":
            return EditorWidget(state)
        # ... etc

# DELETE AppWidgetManager
# DELETE widget_registry
# DELETE all other factories
```

## The New Flow

```
User Action
    ↓
Qt Event Handler
    ↓
Command Lookup
    ↓
Command.execute(model, context)
    ↓
Model.mutate()
    ↓
Model.notify_observers()
    ↓
View.render()
```

## Implementation Plan

### Day 1: The Purge
```bash
# Morning: DELETE everything wrong
git checkout -b big-bang-refactor
rm -rf [all files listed above]

# Afternoon: Disable everything that breaks
# Comment out all broken imports
# App won't run - that's OK
```

### Day 2: Model Foundation
```bash
# Morning: Build complete model
mkdir -p packages/viloapp/src/viloapp/newarch/
touch packages/viloapp/src/viloapp/newarch/model.py

# Implement:
- WorkspaceModel
- WorkspaceState
- Tab, PaneTree, PaneNode, Pane
- All operations in model

# Afternoon: Test model in isolation
python -c "from viloapp.newarch.model import WorkspaceModel; m = WorkspaceModel(); m.create_tab(); m.split_pane()"
```

### Day 3: Command Layer
```bash
# Morning: Pure commands
touch packages/viloapp/src/viloapp/newarch/commands.py

# Every user action as command
- No UI references
- No service calls
- Direct model manipulation

# Afternoon: Command tests
# Test every command against model
```

### Day 4: View Layer
```bash
# Morning: Pure views
touch packages/viloapp/src/viloapp/newarch/views.py

# Implement:
- WorkspaceView
- TabView
- PaneView
- Pure rendering from model

# Afternoon: Connect everything
# Model → View observation
# Commands → Model execution
```

### Day 5: Make It Run
```bash
# Morning: New main.py
touch packages/viloapp/src/viloapp/main_new.py

# Wire everything:
model = WorkspaceModel()
view = WorkspaceView(model)
commander = Commander(model)
app.run()

# Afternoon: Fix what breaks
# But DON'T compromise architecture
```

## What We're NOT Doing

- ❌ NO backward compatibility
- ❌ NO migration paths
- ❌ NO adapter patterns
- ❌ NO feature flags
- ❌ NO gradual rollout
- ❌ NO preserving old code
- ❌ NO workarounds
- ❌ NO compromises

## Success Criteria

After 5 days:
- ✅ Single model (WorkspaceModel)
- ✅ Zero UI state
- ✅ All operations through commands
- ✅ Pure views from model
- ✅ No circular dependencies
- ✅ No lazy loading hacks
- ✅ One widget factory
- ✅ One registry (if any)

## The Nuclear Option

If things get messy:

```bash
# Start completely fresh
mkdir viloapp-clean
cd viloapp-clean

# Copy ONLY what's good
cp ../viloapp/packages/viloapp/src/viloapp/main.py .
cp ../viloapp/packages/viloapp/src/viloapp/models/base.py .

# Build from scratch
# Import nothing old
# Reference nothing legacy
```

## Why This Will Work

1. **No Technical Debt** - Starting clean
2. **No Confusion** - One way to do things
3. **No Compromises** - Architecture is pure
4. **Fast Development** - No working around old code
5. **Easy Testing** - Everything is simple

## Risks

1. **App broken for days** - Accept it
2. **Some features lost** - Rebuild them right
3. **User data migration** - Write converter once
4. **Plugins break** - They need updating anyway

## The Commitment

This requires:
- 5 days of focused work
- Zero distractions
- No feature requests
- No bug fixes
- Just architecture

## Let's Do It

Ready to burn it down? Here's the first command:

```bash
# Create branch for destruction
git checkout -b burn-it-down

# Start deleting
rm packages/viloapp/src/viloapp/ui/widgets/split_pane_model.py

# Commit the purge
git commit -m "🔥 BURN: Delete SplitPaneModel forever"
```

The question is: **Are you ready to burn it all down and rebuild it right?**

No half measures. No compromises. Clean architecture or nothing.