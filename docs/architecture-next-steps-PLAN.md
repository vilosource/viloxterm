# Next Steps Implementation Plan

## Current State Assessment

### What's Working ✅
- Model-first state restoration implemented
- Commands execute through proper architecture
- Observer pattern connects model to UI
- Split commands work after state restoration
- Bridge components properly documented
- 300x performance improvement achieved

### What's Not Working ❌
- Dual models still exist (WorkspaceModelImpl + SplitPaneModel)
- Tree structure split between models
- Widget ownership unclear
- Multiple event systems causing confusion
- Plugin system not integrated with new model

### Technical Debt 🔧
- SplitPaneWidget still creates its own model
- AppWidgets created in multiple places
- Three widget registries exist
- Incomplete test coverage

## Prioritized Action Plan

### Priority 1: Stabilize Current Implementation (1-2 days)

**Goal**: Make the current dual-model system reliable

#### 1.1 Fix Immediate Bugs
- [ ] Ensure split commands work consistently
- [ ] Fix any state desync issues
- [ ] Handle edge cases in state restoration

#### 1.2 Add Critical Tests
```python
# Test priorities:
- test_state_restoration_populates_model()
- test_split_command_after_restoration()
- test_model_observer_notifications()
- test_ui_reacts_to_model_changes()
```

#### 1.3 Document Current Behavior
- [ ] Add inline comments explaining dual model
- [ ] Update user documentation if needed
- [ ] Create migration warnings in code

### Priority 2: Complete Model Integration (3-5 days)

**Goal**: Make WorkspaceModelImpl the true single source of truth

#### 2.1 Migrate Tree Structure to Model
```python
# In WorkspaceModelImpl, add:
class PaneTreeNode:
    """Represents tree structure in model"""
    type: Literal["split", "leaf"]
    orientation: Optional[str]  # For splits
    pane_id: Optional[str]      # For leaves
    children: List[PaneTreeNode]  # For splits
```

#### 2.2 Make SplitPaneWidget Pure View
- [ ] Remove SplitPaneModel creation
- [ ] Read tree from WorkspaceModelImpl
- [ ] Convert to pure display component
- [ ] Handle only UI interactions

#### 2.3 Centralize Widget Creation
```python
# Single factory in model layer:
class WidgetFactory:
    def create_widget(pane_id: str, widget_type: WidgetType):
        # Create AppWidget
        # Register in AppWidgetManager
        # Return widget instance
```

### Priority 3: Clean Architecture (1-2 weeks)

**Goal**: Eliminate technical debt and confusion

#### 3.1 Unify Widget Registries
- Merge all registries into AppWidgetManager
- Clear ownership: Model owns IDs, Manager owns instances
- Remove duplicate registrations

#### 3.2 Simplify Event Systems
```
Decision Matrix:
- Model → UI: Use Observer Pattern
- UI → UI: Use Qt Signals
- Service → Service: Use method calls
- Cross-cutting: Use Event Bus (sparingly)
```

#### 3.3 Complete Plugin Integration
- Update SDK to work with WorkspaceModelImpl
- Create plugin adapter for model access
- Test existing plugins still work

### Priority 4: Testing & Documentation (Ongoing)

#### 4.1 Integration Test Suite
```python
class TestCompleteUserJourney:
    def test_app_lifecycle():
        # Start app
        # Create tabs/panes
        # Save state
        # Restart app
        # Verify state restored
        # Execute commands
        # Verify they work
```

#### 4.2 Performance Benchmarks
- Measure observer overhead
- Profile model operations
- Check memory usage

#### 4.3 Architecture Documentation
- Create architecture decision records (ADRs)
- Update developer guides
- Create plugin migration guide

## Implementation Strategy

### Phase 1: Stabilize (Week 1)
**Focus**: Make current system reliable
1. Fix critical bugs
2. Add essential tests
3. Document gotchas

### Phase 2: Unify Models (Week 2)
**Focus**: Single source of truth
1. Migrate tree to WorkspaceModelImpl
2. Make SplitPaneWidget reactive
3. Centralize widget creation

### Phase 3: Clean Up (Week 3)
**Focus**: Remove confusion
1. Unify registries
2. Simplify events
3. Update plugins

### Phase 4: Polish (Week 4)
**Focus**: Production ready
1. Complete test coverage
2. Performance optimization
3. Documentation

## Success Criteria

### Short Term (1 week)
- [ ] No split command failures
- [ ] State restoration 100% reliable
- [ ] No model desync issues

### Medium Term (2 weeks)
- [ ] Single model implementation
- [ ] SplitPaneWidget is pure view
- [ ] Widget creation centralized

### Long Term (1 month)
- [ ] Single widget registry
- [ ] Clear event system
- [ ] Plugin system integrated
- [ ] 80% test coverage
- [ ] Complete documentation

## Risk Mitigation

### Risk 1: Breaking Existing Functionality
**Mitigation**:
- Keep dual model working during migration
- Add feature flags for new behavior
- Comprehensive testing before switching

### Risk 2: Performance Regression
**Mitigation**:
- Benchmark before changes
- Profile after each phase
- Keep observer notifications efficient

### Risk 3: Plugin Breakage
**Mitigation**:
- Create compatibility layer
- Test plugins continuously
- Provide migration guide

## Recommended Immediate Next Step

**Start with Phase 1: Stabilize**

1. **Today**: Add integration tests for current behavior
2. **Tomorrow**: Fix any bugs found by tests
3. **Day 3**: Document current dual-model behavior

This ensures we have a stable base before attempting the larger migration.

## Alternative: Quick Win Approach

If you prefer quick wins over systematic approach:

1. **Fix Most Annoying Bug** - Whatever users complain about most
2. **Add Most Valuable Feature** - Something users really want
3. **Then Circle Back** - Do architecture cleanup later

## Decision Point

Choose your path:

### Option A: Systematic Architecture Fix 🏗️
- Pros: Clean, maintainable, long-term solution
- Cons: Takes time, might introduce temporary bugs
- Timeline: 4 weeks to completion

### Option B: Quick Wins First 🚀
- Pros: Immediate user value, maintains momentum
- Cons: Technical debt grows, harder to fix later
- Timeline: Ongoing improvements

### Option C: Hybrid Approach 🎯
- Week 1: Stabilize current system
- Week 2: Add one killer feature
- Week 3-4: Architecture cleanup
- Pros: Balance of stability and progress
- Cons: Longer total timeline

## My Recommendation

**Go with Option C: Hybrid Approach**

1. First, stabilize what we have (tests + bug fixes)
2. Then add one user-visible improvement (show progress)
3. Finally, complete the architecture migration

This balances technical excellence with user value and maintains development momentum.

## Next Concrete Actions

If you agree with the hybrid approach:

1. ```bash
   # Create test file for state restoration
   touch packages/viloapp/tests/integration/test_state_restoration.py
   ```

2. Write integration tests for current behavior

3. Fix any bugs the tests reveal

4. Choose one user feature to implement

5. Then proceed with model unification

What do you think? Should we proceed with the hybrid approach?