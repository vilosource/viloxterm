# Big Bang Refactor - Execution Tracker

## Status: NOT STARTED
**Start Date:** TBD
**Target Completion:** 5 days from start
**Branch:** `burn-it-down`

---

## Day 1: THE PURGE 🔥

### Morning Session (9:00 - 12:00)
**Goal:** Delete all wrong code

#### Files to Delete
- [ ] `packages/viloapp/src/viloapp/ui/widgets/split_pane_model.py`
- [ ] `packages/viloapp/src/viloapp/ui/widgets/split_pane_controller.py`
- [ ] `packages/viloapp/src/viloapp/ui/widgets/split_pane_drag_handler.py`
- [ ] `packages/viloapp/src/viloapp/ui/widgets/split_pane_view_helpers.py`
- [ ] `packages/viloapp/src/viloapp/ui/widgets/split_pane_theme_manager.py`
- [ ] `packages/viloapp/src/viloapp/ui/widgets/widget_registry.py`
- [ ] `packages/viloapp/src/viloapp/ui/widgets/widget_state.py`
- [ ] `packages/viloapp/src/viloapp/services/workspace_widget_registry.py`
- [ ] `packages/viloapp/src/viloapp/controllers/state_controller.py`

#### Code to Gut
- [ ] Remove all model logic from `SplitPaneWidget`
- [ ] Remove direct widget creation from `Workspace`
- [ ] Remove lazy loading hacks from `terminal_app_widget.py`
- [ ] Remove all `@property` workarounds for circular imports

#### Commit Checkpoint
```bash
git add -A
git commit -m "🔥 PURGE: Deleted all dual model and legacy state management"
```

### Afternoon Session (13:00 - 17:00)
**Goal:** Disable broken code to make codebase compilable

#### Tasks
- [ ] Comment out all broken imports
- [ ] Add TODO markers for reimplementation
- [ ] Ensure Python can at least import modules
- [ ] Document what functionality was lost

#### Validation
- [ ] `python -c "import viloapp"` succeeds (even if app won't run)
- [ ] No import errors at module level
- [ ] Clear list of what needs rebuilding

#### Commit Checkpoint
```bash
git commit -m "🔧 STABILIZE: Disabled broken code after purge"
```

### Day 1 Success Criteria
- ✅ All legacy model code deleted
- ✅ All redundant registries removed
- ✅ Codebase imports without errors
- ✅ Clear inventory of what was removed

### Day 1 Blockers/Issues
*Document any unexpected issues here*
-

---

## Day 2: BUILD THE MODEL 🏗️

### Morning Session (9:00 - 12:00)
**Goal:** Create complete WorkspaceModel

#### Create New Files
- [ ] `packages/viloapp/src/viloapp/newarch/__init__.py`
- [ ] `packages/viloapp/src/viloapp/newarch/model.py`

#### Implement Core Classes
- [ ] `WorkspaceModel` - Main model class
- [ ] `WorkspaceState` - Complete state container
- [ ] `Tab` - Tab with embedded tree
- [ ] `PaneTree` - Tree structure
- [ ] `PaneNode` - Node abstraction
- [ ] `Pane` - Leaf node data

#### Core Operations
- [ ] `create_tab(name) -> tab_id`
- [ ] `close_tab(tab_id) -> bool`
- [ ] `split_pane(pane_id, orientation) -> new_pane_id`
- [ ] `close_pane(pane_id) -> bool`
- [ ] `focus_pane(pane_id) -> bool`

#### Commit Checkpoint
```bash
git add packages/viloapp/src/viloapp/newarch/
git commit -m "✨ NEW: Complete WorkspaceModel implementation"
```

### Afternoon Session (13:00 - 17:00)
**Goal:** Test model in isolation

#### Test Implementation
- [ ] Create `test_new_model.py`
- [ ] Test tab creation/deletion
- [ ] Test pane splitting
- [ ] Test tree operations
- [ ] Test state serialization

#### Model Validation Script
```python
# validate_model.py
from viloapp.newarch.model import WorkspaceModel

model = WorkspaceModel()
tab = model.create_tab("Test")
print(f"Created tab: {tab}")

pane = model.get_active_pane()
new_pane = model.split_pane(pane, "horizontal")
print(f"Split pane: {new_pane}")

state = model.serialize()
print(f"State: {state}")
```

- [ ] Run validation script successfully
- [ ] Model operations work correctly
- [ ] State can be serialized/deserialized

#### Commit Checkpoint
```bash
git commit -m "✅ TEST: Model validation complete"
```

### Day 2 Success Criteria
- ✅ Complete model implementation
- ✅ All operations working
- ✅ Tests passing
- ✅ Can serialize/deserialize state

### Day 2 Blockers/Issues
*Document any unexpected issues here*
-

---

## Day 3: PURE COMMANDS 📝

### Morning Session (9:00 - 12:00)
**Goal:** Implement command system

#### Create Command Infrastructure
- [ ] `packages/viloapp/src/viloapp/newarch/commands.py`
- [ ] Base `Command` class
- [ ] `CommandContext` for execution context
- [ ] `CommandResult` for results

#### Implement Core Commands
- [ ] `CreateTabCommand`
- [ ] `CloseTabCommand`
- [ ] `SplitPaneCommand`
- [ ] `ClosePaneCommand`
- [ ] `FocusPaneCommand`
- [ ] `ChangeWidgetTypeCommand`

#### Command Registry
- [ ] `CommandRegistry` class
- [ ] Command registration
- [ ] Command lookup
- [ ] Command execution

#### Commit Checkpoint
```bash
git commit -m "⚡ COMMANDS: Complete command system implementation"
```

### Afternoon Session (13:00 - 17:00)
**Goal:** Test command execution

#### Command Tests
- [ ] Test each command individually
- [ ] Test command sequences
- [ ] Test undo/redo if implemented
- [ ] Test error handling

#### Command Validation Script
```python
# validate_commands.py
from viloapp.newarch.model import WorkspaceModel
from viloapp.newarch.commands import CommandRegistry, SplitPaneCommand

model = WorkspaceModel()
registry = CommandRegistry()

# Execute command
cmd = SplitPaneCommand(orientation="horizontal")
result = registry.execute(cmd, model)
print(f"Command result: {result}")
```

- [ ] Commands execute successfully
- [ ] Model updates correctly
- [ ] Results are returned properly

#### Commit Checkpoint
```bash
git commit -m "✅ TEST: Command system validation complete"
```

### Day 3 Success Criteria
- ✅ All commands implemented
- ✅ Commands modify model correctly
- ✅ No direct UI manipulation
- ✅ Tests passing

### Day 3 Blockers/Issues
*Document any unexpected issues here*
-

---

## Day 4: PURE VIEWS 🎨

### Morning Session (9:00 - 12:00)
**Goal:** Create view layer

#### Create View Classes
- [ ] `packages/viloapp/src/viloapp/newarch/views.py`
- [ ] `WorkspaceView` - Main container
- [ ] `TabView` - Tab rendering
- [ ] `TreeView` - Tree structure rendering
- [ ] `PaneView` - Individual pane

#### Implement Rendering
- [ ] `render()` method for each view
- [ ] Observer pattern connection
- [ ] Event handling (clicks, etc.)
- [ ] NO state storage in views

#### Widget Factory
- [ ] `packages/viloapp/src/viloapp/newarch/factory.py`
- [ ] Single `WidgetFactory.create()` method
- [ ] Support all widget types

#### Commit Checkpoint
```bash
git commit -m "🎨 VIEWS: Complete view layer implementation"
```

### Afternoon Session (13:00 - 17:00)
**Goal:** Connect views to model

#### View-Model Binding
- [ ] Connect observers
- [ ] Test model changes trigger render
- [ ] Test user actions trigger commands
- [ ] Verify no state in views

#### View Validation Script
```python
# validate_views.py
from PySide6.QtWidgets import QApplication
from viloapp.newarch.model import WorkspaceModel
from viloapp.newarch.views import WorkspaceView

app = QApplication([])
model = WorkspaceModel()
view = WorkspaceView(model)

# Model change should update view
model.create_tab("Test")
view.show()
app.exec()
```

- [ ] Views render correctly
- [ ] Updates when model changes
- [ ] No crashes or errors

#### Commit Checkpoint
```bash
git commit -m "🔗 CONNECT: Views bound to model"
```

### Day 4 Success Criteria
- ✅ Pure view implementation
- ✅ Views update on model changes
- ✅ No state in views
- ✅ User interactions work

### Day 4 Blockers/Issues
*Document any unexpected issues here*
-

---

## Day 5: INTEGRATION 🚀

### Morning Session (9:00 - 12:00)
**Goal:** Wire everything together

#### Create New Main
- [ ] `packages/viloapp/src/viloapp/main_new.py`
- [ ] Initialize model
- [ ] Create view
- [ ] Setup command handlers
- [ ] Connect everything

#### Keyboard Shortcuts
- [ ] Map shortcuts to commands
- [ ] Test all shortcuts work
- [ ] No direct UI manipulation

#### State Persistence
- [ ] Save model state
- [ ] Load model state
- [ ] State migration from old format

#### Commit Checkpoint
```bash
git commit -m "🚀 INTEGRATE: Complete application wiring"
```

### Afternoon Session (13:00 - 17:00)
**Goal:** Final validation and cleanup

#### Full Application Test
- [ ] Application starts
- [ ] Can create tabs
- [ ] Can split panes
- [ ] Can close panes
- [ ] State persists
- [ ] No crashes

#### Performance Check
- [ ] Measure command execution time
- [ ] Measure render time
- [ ] Check memory usage
- [ ] Verify <10ms operations

#### Final Cleanup
- [ ] Remove all TODO markers
- [ ] Delete old main.py
- [ ] Update imports everywhere
- [ ] Clean up any remaining legacy code

#### Commit Checkpoint
```bash
git commit -m "✨ COMPLETE: Big bang refactor done"
```

### Day 5 Success Criteria
- ✅ Application fully functional
- ✅ Clean architecture throughout
- ✅ Performance targets met
- ✅ No legacy code remains

### Day 5 Blockers/Issues
*Document any unexpected issues here*
-

---

## Overall Progress

### Architecture Goals
- [ ] Single source of truth (WorkspaceModel)
- [ ] Pure command system
- [ ] Pure view layer
- [ ] No circular dependencies
- [ ] No lazy loading hacks
- [ ] No dual models
- [ ] Clean separation of concerns

### Code Quality Metrics
- Lines deleted:
- Lines added:
- Files deleted:
- Files created:
- Cyclomatic complexity:
- Test coverage:

### Performance Metrics
- Command execution: ___ ms
- View render: ___ ms
- Memory usage: ___ MB
- Startup time: ___ s

---

## Issues Log

### Day 1 Issues
-

### Day 2 Issues
-

### Day 3 Issues
-

### Day 4 Issues
-

### Day 5 Issues
-

---

## Decisions Made

### Architectural Decisions
-

### Trade-offs Accepted
-

### Future Work Identified
-

---

## Final Notes

### What Went Well
-

### What Was Harder Than Expected
-

### Lessons Learned
-

### Would Do Differently
-

---

## Sign-off

- [ ] All goals achieved
- [ ] Architecture clean
- [ ] Tests passing
- [ ] Performance acceptable
- [ ] Documentation complete

**Completed:** ___________
**Signed:** ___________