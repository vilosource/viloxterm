# Systematic Architecture Fix Roadmap

## Overview
Complete transformation to single-model architecture following Option A: Systematic Architecture Fix.

## Week 1: Foundation & Analysis

### Day 1-2: Deep Analysis & Planning
- [ ] Map all current SplitPaneModel usages
- [ ] Document all WorkspaceModelImpl gaps
- [ ] Identify every UI→Model connection point
- [ ] Create detailed migration checklist

### Day 3-4: Test Infrastructure
```python
# Create comprehensive test suite BEFORE changes
tests/architecture/
  ├── test_model_state_consistency.py
  ├── test_command_execution.py
  ├── test_state_persistence.py
  ├── test_observer_notifications.py
  └── test_ui_model_sync.py
```

### Day 5: Freeze & Document Current State
- [ ] Document current behavior precisely
- [ ] Create snapshot tests of current state
- [ ] Mark all legacy code clearly
- [ ] Create rollback plan

## Week 2: Model Layer Completion

### Day 1-2: Extend WorkspaceModelImpl
```python
# Add missing tree structure to WorkspaceModelImpl
class PaneTree:
    """Complete tree structure in model"""
    root: PaneNode

class PaneNode:
    node_id: str
    node_type: Literal["split", "leaf"]
    # For splits
    orientation: Optional[Literal["horizontal", "vertical"]]
    ratio: float = 0.5
    first_child: Optional[PaneNode]
    second_child: Optional[PaneNode]
    # For leaves
    pane_state: Optional[PaneState]
```

### Day 3-4: Model Operations
```python
# Implement all tree operations in model
class WorkspaceModelImpl:
    def split_pane_with_tree(self, pane_id: str, orientation: str) -> str:
        """Split maintaining tree structure"""

    def close_pane_with_tree(self, pane_id: str) -> bool:
        """Close and rebalance tree"""

    def get_pane_tree(self, tab_id: str) -> PaneTree:
        """Get complete tree for tab"""

    def traverse_panes(self, tab_id: str) -> Iterator[PaneState]:
        """Traverse all panes in tree order"""
```

### Day 5: Migration Adapters
```python
# Create adapters for gradual migration
class ModelAdapter:
    """Adapts between old SplitPaneModel and new WorkspaceModelImpl"""

    @staticmethod
    def split_model_to_pane_tree(split_model) -> PaneTree:
        """Convert old model to new structure"""

    @staticmethod
    def pane_tree_to_split_model(pane_tree) -> SplitPaneModel:
        """Convert new structure to old (temporary)"""
```

## Week 3: UI Layer Transformation

### Day 1-2: Create Pure View Components
```python
# New pure view components
class SplitPaneView(QWidget):
    """Pure view - no model, only display"""

    def __init__(self, model: WorkspaceModelImpl, tab_id: str):
        self.model = model  # Read-only reference
        self.tab_id = tab_id

    def render_from_model(self):
        """Render tree from model state"""
        tree = self.model.get_pane_tree(self.tab_id)
        self._render_tree(tree.root)
```

### Day 3-4: Observer Implementation
```python
# Efficient observer pattern
class ModelObserverMixin:
    def observe_model(self, model: WorkspaceModelImpl):
        model.add_observer(self._on_model_change)

    def _on_model_change(self, event: ModelEvent):
        if self._should_react_to(event):
            self._react_to_change(event)

    def _should_react_to(self, event: ModelEvent) -> bool:
        """Filter relevant events for this view"""
```

### Day 5: Connect Everything
- [ ] Wire all views to model
- [ ] Remove all direct UI manipulation
- [ ] Verify observer notifications work
- [ ] Test UI updates correctly

## Week 4: Migration & Cleanup

### Day 1-2: Gradual Rollout
```python
# Feature flag controlled migration
class FeatureFlags:
    USE_NEW_MODEL_TREE = False  # Start false
    USE_PURE_VIEWS = False      # Start false

def get_split_widget():
    if FeatureFlags.USE_PURE_VIEWS:
        return SplitPaneView(model, tab_id)
    else:
        return SplitPaneWidget()  # Legacy
```

### Day 3: Remove Legacy Code
- [ ] Delete SplitPaneModel completely
- [ ] Remove old split_pane_model.py
- [ ] Clean up legacy imports
- [ ] Update all references

### Day 4: Performance Optimization
```python
# Optimize observer notifications
class BatchedNotifier:
    def batch_changes(self):
        """Collect changes, notify once"""

class DiffBasedUpdater:
    def update_only_changed(self, old_tree, new_tree):
        """Update only what changed in UI"""
```

### Day 5: Final Validation
- [ ] Run full test suite
- [ ] Performance benchmarks
- [ ] Memory profiling
- [ ] User acceptance testing

## Detailed Task Breakdown

### Critical Path Tasks

#### 1. Model Tree Structure (BLOCKING)
**Why Critical**: Everything depends on this
```python
# Must be implemented first
- PaneNode class definition
- Tree traversal algorithms
- Tree manipulation operations
- Tree serialization/deserialization
```

#### 2. Model-View Binding (BLOCKING)
**Why Critical**: UI can't work without this
```python
# Efficient binding system
- Change detection
- Minimal UI updates
- Batch notifications
```

#### 3. State Migration (BLOCKING)
**Why Critical**: Can't lose user data
```python
# Safe state migration
- Read old format
- Convert to new format
- Validate conversion
- Save in new format
```

### Parallel Workstreams

#### Stream A: Model Development
- Owner: Backend developer
- Timeline: Weeks 1-2
- Dependencies: None

#### Stream B: UI Preparation
- Owner: Frontend developer
- Timeline: Weeks 1-2
- Dependencies: None initially

#### Stream C: Testing
- Owner: QA/Test engineer
- Timeline: Continuous
- Dependencies: Each completed feature

### Integration Points

#### Week 2, Day 5: Model-Adapter Integration
- Model team provides adapters
- UI team tests with adapters
- Identify any gaps

#### Week 3, Day 3: View-Model Integration
- Views connect to model
- Test observer pattern
- Verify updates work

#### Week 4, Day 1: Full System Integration
- Everything connected
- Feature flags control rollout
- Gradual migration

## Risk Mitigation

### Risk: Breaking Current Functionality
**Mitigation Strategy**:
1. Comprehensive tests before starting
2. Feature flags for gradual rollout
3. Adapter pattern for compatibility
4. Rollback plan at each step

### Risk: Performance Degradation
**Mitigation Strategy**:
1. Benchmark before changes
2. Profile after each major change
3. Optimization sprint in Week 4
4. Batch observer notifications

### Risk: State Loss/Corruption
**Mitigation Strategy**:
1. Backup state before migration
2. Validate all conversions
3. Keep old format reader
4. Atomic state updates only

## Success Criteria

### Week 1 Success
- [ ] All current behavior documented
- [ ] Complete test coverage of current state
- [ ] Migration plan reviewed and approved

### Week 2 Success
- [ ] WorkspaceModelImpl has tree structure
- [ ] All tree operations implemented
- [ ] Adapters working bi-directionally

### Week 3 Success
- [ ] Pure views rendering from model
- [ ] Observer pattern working
- [ ] No direct UI manipulation

### Week 4 Success
- [ ] SplitPaneModel deleted
- [ ] All tests passing
- [ ] Performance targets met
- [ ] Zero regressions

## Validation Checkpoints

### Checkpoint 1 (End of Week 1)
**Go/No-Go Decision**:
- Tests provide adequate coverage?
- Risks identified and mitigated?
- Team aligned on approach?

### Checkpoint 2 (End of Week 2)
**Go/No-Go Decision**:
- Model layer complete?
- Adapters working?
- No breaking changes?

### Checkpoint 3 (End of Week 3)
**Go/No-Go Decision**:
- Views working with model?
- Observer pattern efficient?
- UI responsive?

### Checkpoint 4 (End of Week 4)
**Final Validation**:
- All legacy code removed?
- Performance acceptable?
- User experience improved?

## Tools & Techniques

### Development Tools
```bash
# Model visualization
python -m viloapp.tools.visualize_model

# Performance profiling
python -m cProfile -o profile.stats main.py

# Memory profiling
mprof run python main.py
mprof plot

# Test coverage
pytest --cov=viloapp --cov-report=html
```

### Debugging Helpers
```python
# Add temporarily for debugging
class ModelDebugger:
    @staticmethod
    def dump_tree(node: PaneNode, indent=0):
        """Print tree structure"""

    @staticmethod
    def verify_consistency(model: WorkspaceModelImpl):
        """Check model consistency"""
```

### Monitoring
```python
# Add metrics collection
class ArchitectureMetrics:
    model_operations: int = 0
    ui_updates: int = 0
    observer_notifications: int = 0

    @classmethod
    def report(cls):
        """Print metrics report"""
```

## Communication Plan

### Daily Standups
- What was completed yesterday?
- What's planned for today?
- Any blockers?

### Weekly Architecture Review
- Progress against roadmap
- Risk assessment
- Adjustment decisions

### Stakeholder Updates
- End of each week
- Success metrics
- Next week preview

## Conclusion

This systematic approach ensures:
1. **No surprises** - Everything planned
2. **No regressions** - Tests catch issues
3. **No confusion** - Clear ownership
4. **No delays** - Parallel workstreams

By following this roadmap, we'll achieve a clean, maintainable architecture in 4 weeks with minimal risk.