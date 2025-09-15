# Code Quality Fix Implementation Plan

Based on the audit findings, here's a prioritized action plan to address all issues systematically.

## 🔴 Phase 1: Critical Fixes (Week 1)
*These must be fixed immediately to maintain architectural integrity*

### 1.1 Fix Architecture Violations in Registry Commands

#### Problem
The `registry_commands.py` directly accesses `_widget_registry` private attribute, violating the Command → Service → UI flow.

#### Solution
Add proper registry methods to `WorkspaceService`:

```python
# In services/workspace_service.py

def register_widget(self, widget_id: str, tab_index: int) -> bool:
    """Register a widget with its tab index."""
    self._widget_registry[widget_id] = tab_index
    logger.debug(f"Registered widget {widget_id} at tab index {tab_index}")
    return True

def unregister_widget(self, widget_id: str) -> bool:
    """Unregister a widget."""
    if widget_id in self._widget_registry:
        del self._widget_registry[widget_id]
        logger.debug(f"Unregistered widget {widget_id}")
        return True
    return False

def update_registry_after_tab_close(self, closed_index: int, widget_id: Optional[str] = None) -> int:
    """Update registry indices after a tab is closed."""
    # Remove the closed widget if specified
    if widget_id and widget_id in self._widget_registry:
        del self._widget_registry[widget_id]

    # Update indices for remaining widgets
    updated_count = 0
    for wid, tab_idx in list(self._widget_registry.items()):
        if tab_idx > closed_index:
            self._widget_registry[wid] = tab_idx - 1
            updated_count += 1

    return updated_count

def get_widget_tab_index(self, widget_id: str) -> Optional[int]:
    """Get the tab index for a widget."""
    return self._widget_registry.get(widget_id)

def is_widget_registered(self, widget_id: str) -> bool:
    """Check if a widget is registered."""
    return widget_id in self._widget_registry
```

Then update `registry_commands.py` to use these methods:
```python
# Example fix for register_widget_command
result = workspace_service.register_widget(widget_id, tab_index)
if result:
    return CommandResult(success=True, value={"widget_id": widget_id, "tab_index": tab_index})
```

#### Files to Modify
- [ ] `services/workspace_service.py` - Add 5 new methods
- [ ] `core/commands/builtin/registry_commands.py` - Update all 5 commands
- [ ] `tests/unit/test_registry_commands.py` - Update tests to use new methods

### 1.2 Remove Duplicate Import

#### Problem
`theme_commands` is imported twice in `__init__.py` (lines 21 and 26).

#### Solution
Remove line 26 or consolidate imports.

#### Files to Modify
- [ ] `core/commands/builtin/__init__.py` - Remove duplicate import

## 🟡 Phase 2: Major Refactoring (Week 2-3)
*Address large classes and performance issues*

### 2.1 Refactor SplitPaneWidget (1044 lines)

#### Current Problems
- Too many responsibilities
- Complex nested logic
- Mixed view/controller concerns

#### Refactoring Plan

**Extract Three New Classes:**

1. **PaneLayoutCalculator** (~200 lines)
   - `calculate_split_sizes()`
   - `calculate_pane_positions()`
   - `update_layout_geometry()`
   - `validate_split_ratios()`

2. **PaneEventHandler** (~250 lines)
   - `handle_mouse_events()`
   - `handle_keyboard_navigation()`
   - `handle_context_menu()`
   - `handle_drag_drop()`
   - `handle_focus_changes()`

3. **PaneViewRenderer** (~150 lines)
   - `render_pane_borders()`
   - `render_pane_numbers()`
   - `render_active_indicators()`
   - `apply_theme_styles()`

**Simplified SplitPaneWidget** (~400 lines)
- Orchestrates the three helper classes
- Manages high-level widget lifecycle
- Handles model-view coordination

#### Files to Create/Modify
- [ ] Create `ui/widgets/pane_layout_calculator.py`
- [ ] Create `ui/widgets/pane_event_handler.py`
- [ ] Create `ui/widgets/pane_view_renderer.py`
- [ ] Refactor `ui/widgets/split_pane_widget.py`
- [ ] Update imports in files using SplitPaneWidget

### 2.2 Refactor WorkspaceService (801 lines)

#### Current Problems
- Handles tabs, panes, navigation, layout, and registry
- Long methods (from_dict ~100 lines)
- Mixed responsibilities

#### Refactoring Plan

**Extract Three Services:**

1. **TabManagementService** (~250 lines)
   - `add_editor_tab()`
   - `add_terminal_tab()`
   - `add_app_widget()`
   - `close_tab()`
   - `switch_to_tab()`
   - Tab state management

2. **PaneManagementService** (~300 lines)
   - `split_active_pane()`
   - `close_active_pane()`
   - `focus_pane()`
   - `navigate_panes()`
   - Pane numbering logic

3. **WidgetRegistryService** (~150 lines)
   - All widget registration methods
   - Widget tracking
   - Singleton management

**Simplified WorkspaceService** (~200 lines)
- Coordinates between the three services
- High-level workspace operations
- State persistence

#### Files to Create/Modify
- [ ] Create `services/tab_management_service.py`
- [ ] Create `services/pane_management_service.py`
- [ ] Create `services/widget_registry_service.py`
- [ ] Refactor `services/workspace_service.py`
- [ ] Update service registration in main.py

### 2.3 Fix Performance Issues

#### Lambda Memory Leaks
**Problem:** Lambda captures in QTimer.singleShot
**Solution:** Use functools.partial or direct method references

```python
# Bad
QTimer.singleShot(0, lambda: self._load_tab_content(index))

# Good
from functools import partial
QTimer.singleShot(0, partial(self._load_tab_content, index))
```

#### Files to Fix
- [ ] `ui/widgets/settings_app_widget.py:181`
- [ ] `ui/widgets/shortcut_config_app_widget.py:114`

#### Lazy Loading for Shortcuts
**Problem:** Loading all commands at once
**Solution:** Implement virtual scrolling or pagination

- [ ] Modify `shortcut_config_app_widget.py` to load commands on demand
- [ ] Add virtual scrolling to the tree widget

## 🟢 Phase 3: Minor Improvements (Week 3-4)

### 3.1 Add Missing Service Methods
Instead of checking `hasattr`, add proper initialization:

```python
# In WorkspaceService.__init__
self._widget_registry: Dict[str, int] = {}  # Already exists
```

### 3.2 Fix Magic Numbers
```python
# Bad
splitter.setSizes([400, 1200])

# Good
DEFAULT_PROPERTY_WIDTH = 400
DEFAULT_PREVIEW_WIDTH = 1200
splitter.setSizes([DEFAULT_PROPERTY_WIDTH, DEFAULT_PREVIEW_WIDTH])
```

### 3.3 Add Error Notifications
```python
# In split_pane_model.py
if not leaf.app_widget:
    error_msg = f"Failed to create widget for leaf {leaf.id}"
    logger.error(error_msg)
    # Emit signal for UI notification
    self.widget_creation_failed.emit(leaf.id, error_msg)
```

### 3.4 Theme Validation
Add schema validation for imported themes:
```python
def validate_theme_schema(theme_data: dict) -> bool:
    """Validate theme data against schema."""
    required_fields = ['id', 'name', 'colors']
    required_colors = ['background', 'foreground', 'primary']

    # Check required fields
    if not all(field in theme_data for field in required_fields):
        return False

    # Check required colors
    colors = theme_data.get('colors', {})
    if not all(color in colors for color in required_colors):
        return False

    # Validate color format (hex)
    import re
    hex_pattern = re.compile(r'^#[0-9A-Fa-f]{6}$')
    for color_value in colors.values():
        if not hex_pattern.match(str(color_value)):
            return False

    return True
```

## 📋 Testing Strategy

### Phase 1 Tests
- [ ] Test new WorkspaceService registry methods
- [ ] Verify commands use service methods correctly
- [ ] Test registry state persistence

### Phase 2 Tests
- [ ] Unit tests for extracted classes
- [ ] Integration tests for refactored services
- [ ] Performance benchmarks for lazy loading

### Phase 3 Tests
- [ ] Theme validation tests
- [ ] Error notification tests
- [ ] UI responsiveness tests

## 📊 Success Metrics

### Immediate Goals (Phase 1)
- ✅ Zero architecture violations
- ✅ No duplicate imports
- ✅ All commands use proper service methods

### Short-term Goals (Phase 2)
- ✅ No classes over 500 lines
- ✅ No methods over 50 lines
- ✅ Improved startup time by 30%

### Long-term Goals (Phase 3)
- ✅ Test coverage > 80%
- ✅ Zero critical issues in next audit
- ✅ Performance benchmarks pass

## 🚀 Implementation Order

### Week 1: Critical Fixes
1. **Monday-Tuesday**: Fix registry commands architecture
2. **Wednesday**: Remove duplicate imports
3. **Thursday-Friday**: Test and validate fixes

### Week 2: Major Refactoring Part 1
1. **Monday-Tuesday**: Extract PaneLayoutCalculator
2. **Wednesday-Thursday**: Extract PaneEventHandler
3. **Friday**: Extract PaneViewRenderer

### Week 3: Major Refactoring Part 2
1. **Monday-Tuesday**: Create TabManagementService
2. **Wednesday**: Create PaneManagementService
3. **Thursday**: Create WidgetRegistryService
4. **Friday**: Integration testing

### Week 4: Polish and Testing
1. **Monday-Tuesday**: Performance optimizations
2. **Wednesday**: Add error notifications
3. **Thursday**: Theme validation
4. **Friday**: Final testing and documentation

## 🛠️ Tools & Automation

### Pre-commit Hooks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: check-architecture
        name: Check Architecture Compliance
        entry: python scripts/check_architecture.py
        language: python
        types: [python]
```

### Architecture Validation Script
```python
# scripts/check_architecture.py
def check_direct_attribute_access():
    """Check for direct _private attribute access."""
    violations = []
    # Check for patterns like service._attribute
    # Report violations
    return violations
```

### Automated Metrics
```bash
# Makefile additions
metrics:
    @echo "Calculating code metrics..."
    @find . -name "*.py" -exec wc -l {} + | sort -rn | head -20
    @radon cc . -s -n B  # Cyclomatic complexity
    @radon mi . -s  # Maintainability index
```

## 📝 Documentation Updates

### Update CLAUDE.md
- [ ] Document new service methods
- [ ] Update architecture guidelines
- [ ] Add refactoring patterns

### Update Testing Guide
- [ ] Document test patterns for services
- [ ] Add performance testing guide
- [ ] Update mock patterns

## ✅ Definition of Done

Each phase is complete when:
1. All code changes implemented
2. All tests passing
3. Documentation updated
4. Code review completed
5. No new issues introduced
6. Performance benchmarks met

## 🎯 Risk Mitigation

### Potential Risks
1. **Breaking changes during refactoring**
   - Mitigation: Comprehensive test coverage before refactoring
   - Fallback: Feature flags for gradual rollout

2. **Performance regression**
   - Mitigation: Benchmark before/after each change
   - Fallback: Keep old implementation available

3. **Merge conflicts**
   - Mitigation: Small, frequent commits
   - Fallback: Work on separate branches

## 📈 Progress Tracking

Use this checklist to track implementation progress:

### Phase 1 Progress
- [ ] Registry methods added to WorkspaceService
- [ ] Registry commands updated
- [ ] Duplicate import removed
- [ ] Tests updated and passing
- [ ] Documentation updated

### Phase 2 Progress
- [ ] SplitPaneWidget refactored
- [ ] WorkspaceService refactored
- [ ] Performance issues fixed
- [ ] Integration tests passing
- [ ] Performance benchmarks met

### Phase 3 Progress
- [ ] Error notifications added
- [ ] Theme validation implemented
- [ ] Magic numbers replaced
- [ ] All tests passing
- [ ] Final audit clean

---
*Plan Created: 2025-09-15*
*Estimated Completion: 4 weeks*
*Priority: Critical*