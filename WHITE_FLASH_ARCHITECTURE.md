# Deep Architectural Solutions to Eliminate White Flash

## Problem Analysis

The current implementation in `refresh_view()` destroys and recreates the entire widget tree on every split operation. This causes:
- Brief moments where no widgets exist (white flash)
- Unnecessary memory allocation/deallocation
- Loss of widget state
- Poor performance with complex layouts

## Proposed Solutions (Ordered by Impact/Complexity Ratio)

### 1. Incremental DOM-like Updates (Highest Priority) ⭐
**Concept**: Instead of destroying everything, diff the old and new tree structures and only update what changed.

**Implementation**:
- Compare old tree structure with new tree structure
- Identify added, removed, and moved nodes
- Surgically update only affected widgets
- Keep existing widgets and splitters when possible

**Benefits**:
- Minimal widget destruction/creation
- Maintains visual continuity
- Better performance
- Preserves widget state where possible

### 2. Widget Pooling and Reuse
**Concept**: Maintain pools of reusable widgets to avoid creation/destruction overhead.

**Implementation**:
- Pool of PaneContent widgets
- Pool of QSplitter widgets
- Recycle widgets instead of destroying
- Reset and reconfigure pooled widgets

**Benefits**:
- Reduced memory allocation
- Faster split operations
- Less garbage collection pressure

### 3. Overlay Transition System
**Concept**: Use an overlay widget to mask transitions.

**Implementation**:
- Capture current view as QPixmap
- Show overlay with captured image
- Perform layout changes behind overlay
- Fade out overlay when ready

**Benefits**:
- Completely eliminates visual artifacts
- Smooth professional transitions
- Works with any underlying changes

### 4. Two-Buffer Widget Approach
**Concept**: Maintain two complete widget trees and swap them.

**Implementation**:
- Visible tree (currently shown)
- Staging tree (build new layout here)
- Atomic swap when staging is ready
- Hide staging tree during construction

**Benefits**:
- Zero flicker guaranteed
- Clean separation of concerns
- Rollback capability

### 5. QGraphicsView Migration (Most Complex)
**Concept**: Replace QWidget-based approach with QGraphicsView scene graph.

**Implementation**:
- Use QGraphicsScene for layout
- QGraphicsProxyWidget for embedding widgets
- Leverage scene graph optimizations
- Custom animations and transitions

**Benefits**:
- Ultimate control over rendering
- Hardware acceleration
- Advanced visual effects
- Professional-grade performance

## Implementation Plan

### Phase 1: Incremental Updates (Immediate)
1. Add tree comparison logic
2. Implement selective widget updates
3. Preserve existing splitters when possible
4. Test with complex layouts

### Phase 2: Widget Pooling (Short-term)
1. Create widget pool manager
2. Implement recycling logic
3. Add pool size management
4. Profile memory improvements

### Phase 3: Overlay System (Medium-term)
1. Create overlay widget class
2. Implement screenshot capture
3. Add fade animations
4. Integrate with split operations

### Phase 4: Evaluate Need for Further Changes
Based on results from Phases 1-3, determine if QGraphicsView migration is necessary.

## Expected Outcomes

- **Immediate** (Phase 1): 80% reduction in white flash occurrences
- **Short-term** (Phase 2): Further 15% improvement, better memory usage
- **Medium-term** (Phase 3): Complete elimination of visible artifacts
- **Long-term** (Phase 4): Professional-grade smooth transitions

## Technical Considerations

1. **Qt Version Compatibility**: All solutions work with Qt 5.15+/Qt 6.x
2. **Performance Impact**: Incremental updates actually improve performance
3. **Code Complexity**: Solutions ordered by increasing complexity
4. **Backward Compatibility**: Can be implemented without breaking existing API