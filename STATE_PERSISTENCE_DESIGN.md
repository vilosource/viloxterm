# State Persistence Architecture Design

## Overview

This document outlines the comprehensive design for implementing robust state persistence for the VSCode-style desktop application's tab panes, split layouts, and widget configurations.

## Current State Analysis

### Working Infrastructure (Keep & Enhance)
- **`SplitPaneWidget`** - Our proven recursive split implementation with tree-based state
- **`PaneContent`** - Widget containers with focus handling and headers
- **`PaneFocusEventFilter`** - Proper focus event management
- **`WidgetRegistry`** - Extensible widget type management system
- **`Workspace.save_state()/restore_state()`** - Tab-level state persistence framework
- **`MainWindow`** - QSettings integration for JSON persistence

### What Needs Enhancement
1. **Complete State Implementation**: `SplitPaneWidget.set_state()` is a stub - needs full tree reconstruction
2. **Widget Self-Serialization**: Each widget should handle its own state serialization
3. **MVC Separation**: Need proper separation between state data (Model), UI components (View), and coordination logic (Controller)
4. **Cleanup**: Remove unused old split pane implementations and code remnants

## Architectural Patterns

### 1. Memento Pattern (Primary)
**Purpose**: Complete widget state snapshots for reliable persistence and future undo/redo capability

**Implementation**:
- Immutable state objects for safe persistence
- Version-aware serialization with migration support
- Complete widget state snapshots

**Benefits**:
- Reliable state restoration
- Foundation for undo/redo
- Version compatibility

### 2. Strategy Pattern (Widget Serialization)
**Purpose**: Pluggable serialization strategies per widget type

**Implementation**:
```python
class WidgetStateSerializer(ABC):
    def serialize(self, widget: QWidget) -> Dict[str, Any]
    def deserialize(self, state: Dict[str, Any]) -> QWidget
    def get_widget_type(self) -> WidgetType

class TextEditorSerializer(WidgetStateSerializer):
    # Handles QPlainTextEdit/QTextEdit content, cursor position, selection
    
class TerminalSerializer(WidgetStateSerializer):  
    # Handles terminal history, working directory, environment
```

**Integration**:
- Extend existing `widget_registry.py` with serialization capabilities
- Registry-based approach for extensibility

### 3. Command Pattern (Future Extensions)
**Purpose**: Foundation for undo/redo operations

**Implementation**:
- State change tracking and rollback capabilities
- Command objects for each state modification
- History management

### 4. Observer Pattern (State Change Notifications)
**Purpose**: Centralized state change management

**Implementation**:
- Leverage existing Qt signals for state change events
- Centralized state change listeners for consistency
- Event-driven state updates

## Technical Architecture

### Hierarchical State Management
```
ApplicationState
├── WorkspaceState
│   ├── TabState (multiple)
│   │   ├── PaneState (multiple)
│   │   │   ├── WidgetState
│   │   │   └── Widget-specific data
│   │   └── Split layout configuration
│   └── Tab management (active tab, tab order)
└── Window state (geometry, theme, etc.)
```

### Clean MVC Architecture

**Model Layer (State Data)**:
- **TreeStateData**: Serializable state objects that mirror our working SplitPaneWidget structure
- **PaneStateData**: Individual pane configuration (widget type, content, metadata)
- **WidgetStateData**: Widget-specific serializable data (content, UI state, preferences)
- Pure data objects with no Qt dependencies - easily serializable

**View Layer (UI Components)**:
- **SplitPaneWidget**: Our proven recursive split implementation (keep as-is, enhance state methods)
- **PaneContent**: Widget containers with headers and focus management
- **Content Widgets**: Actual functional widgets (editors, terminals, etc.)
- Pure UI components - no direct persistence logic

**Controller Layer (State Management)**:
- **StateController**: Orchestrates save/restore operations between Model and View
- **WidgetStateManager**: Coordinates widget-specific serialization strategies
- **TreeStateBuilder**: Converts between View tree structure and Model state objects
- Clean separation - controllers handle coordination without UI dependencies

### Widget State Serialization Framework

**Core Components**:
1. **WidgetStateSerializer Interface** - Abstract base for all widget serializers
2. **SerializerRegistry** - Central registry for widget type -> serializer mapping
3. **StateValidator** - Validates state integrity and version compatibility
4. **StateMigrator** - Handles state format migrations between versions

**Widget-Specific Serializers**:
- **TextEditorSerializer**: Content, cursor position, selection, syntax highlighting
- **TerminalSerializer**: Command history, working directory, environment variables
- **OutputSerializer**: Content, scroll position, filtering state
- **ExplorerSerializer**: Tree expansion state, selected items, view mode
- **TableSerializer**: Column widths, sorting, filtering, selection
- **ImageViewerSerializer**: Zoom level, pan position, rotation state

### Persistence Layer

**Storage Strategy**:
- **Primary**: JSON format in QSettings for cross-platform compatibility
- **Backup**: Automatic backup creation before major state changes
- **Compression**: Optional compression for large workspace states

**Data Structure**:
```json
{
  "version": "1.0",
  "timestamp": "2025-09-08T17:45:00Z",
  "application_state": {
    "window_geometry": "...",
    "theme": "dark",
    "workspace": {
      "current_tab": 0,
      "tabs": [
        {
          "name": "Main",
          "split_state": {
            "root": {
              "type": "split",
              "orientation": "horizontal",
              "children": [...],
              "sizes": [0.5, 0.5]
            },
            "active_pane_id": "pane-123"
          }
        }
      ]
    }
  }
}
```

## Implementation Plan

### Phase 1: Commit & Clean Foundation (Priority 1)
**Goal**: Commit current improvements and clean up architecture

**Tasks**:
1. **Commit Current Changes**
   - Focus handling improvements for split panes
   - VSCode theme implementation and icon contrast fixes
   - Activity bar and sidebar functionality

2. **Clean Up Architecture**
   - Remove unused old split pane implementations
   - Clean up any remnant code that's not being used
   - Identify and document what we're keeping vs removing

### Phase 2: Complete Current Implementation (Priority 1)
**Goal**: Finish the state persistence in our working SplitPaneWidget

**Tasks**:
1. **Complete SplitPaneWidget State Methods**
   - Implement full `set_state()` method with tree reconstruction
   - Enhance `get_state()` to capture complete pane configurations
   - Add validation and error handling for malformed states

2. **Widget Self-Serialization**
   - Make each widget type responsible for its own state serialization
   - Extend `WidgetRegistry` with serialization capabilities
   - Add widget-specific state capture (content, UI state, metadata)

### Phase 3: Apply MVC Architecture (Priority 2)
**Goal**: Implement proper separation of concerns with MVC pattern

**Tasks**:
1. **Create Model Classes**
   - Design clean state data objects (TreeStateData, PaneStateData, WidgetStateData)
   - Implement serialization/deserialization for state objects
   - Add validation and versioning support

2. **Create Controller Classes**
   - Implement `StateController` for orchestrating save/restore operations
   - Create `WidgetStateManager` for coordinating widget serialization
   - Add `TreeStateBuilder` for converting between UI and state objects

### Phase 4: Workspace & Advanced Features (Priority 3)
**Goal**: Complete integration and add production-ready features

**Tasks**:
1. **Enhanced Workspace Integration**
   - Complete TODO in `workspace_simple.py` using new state system
   - Implement atomic save/restore operations with rollback
   - Add comprehensive error handling and user feedback

2. **Advanced Features**
   - Add version management and migration support
   - Implement backup/restore system
   - Add performance optimizations (lazy loading, background saving)

3. **User-Facing Features**
   - Workspace templates and sharing capabilities
   - Import/export functionality
   - State snapshots for rollback

## Quality Assurance

### Testing Strategy
**Unit Tests**:
- Each widget serializer
- State model conversions
- Validation and migration logic

**Integration Tests**:
- Complete save/restore cycles
- Complex nested layout scenarios
- Error recovery and rollback

**Performance Tests**:
- Large workspace states
- Background saving operations
- Memory usage under load

### Error Handling
**Graceful Degradation**:
- Corrupt state detection and recovery
- Fallback to default layouts
- Preserve user data when possible

**User Experience**:
- Clear error messages for state issues
- Automatic backup before risky operations
- Progress indicators for long operations

## Migration Strategy

### Version Compatibility
**Forward Compatibility**:
- Extensible JSON schema
- Unknown field preservation
- Graceful handling of new features

**Backward Compatibility**:
- State format migration utilities
- Support for multiple version formats
- Automatic upgrades with backup

### Deployment Approach
**Phased Rollout**:
1. Foundation framework (no user-visible changes)
2. Basic state persistence (improved reliability)
3. Advanced features (new capabilities)
4. Performance optimizations

## Success Metrics

### Functional Goals
- [ ] 100% reliable state persistence across app restarts
- [ ] Complete split layout preservation
- [ ] Widget-specific configuration persistence
- [ ] Error-free state migration between versions

### Performance Goals
- [ ] State save/restore under 100ms for typical workspaces
- [ ] Background saving without UI blocking
- [ ] Memory usage increase < 10% for state management

### Maintainability Goals
- [ ] 90%+ test coverage for state persistence code
- [ ] Pluggable architecture for new widget types
- [ ] Clear documentation and examples

## Future Extensions

### Planned Enhancements
1. **Undo/Redo System**: Leverage Memento pattern foundation
2. **Workspace Sharing**: Export/import workspace configurations
3. **Plugin Architecture**: Third-party widget state serializers
4. **Cloud Sync**: Sync workspace states across devices
5. **Workspace Templates**: Pre-configured layout templates

### Technical Debt Prevention
1. **Clean Interfaces**: Well-defined abstractions for extensibility
2. **Comprehensive Testing**: Catch regressions early
3. **Documentation**: Maintain design decisions and patterns
4. **Performance Monitoring**: Track state management overhead

## Conclusion

This design takes our proven, working SplitPaneWidget implementation and enhances it with robust state persistence using proper MVC architectural patterns. By building on what works rather than replacing it, we minimize risk while maximizing the benefits of our existing investment.

The clean separation between Model (state data), View (UI components), and Controller (coordination logic) ensures maintainability and extensibility. Each widget becomes self-contained and responsible for its own serialization, promoting good separation of concerns.

The phased approach allows us to incrementally add capabilities:
1. **Phase 1**: Clean up and commit current improvements
2. **Phase 2**: Complete state persistence in our working system  
3. **Phase 3**: Apply proper MVC patterns for maintainability
4. **Phase 4**: Add advanced features and optimizations

Success will be measured by:
- **Reliability**: Complete workspace state preservation across restarts
- **Performance**: Responsive save/restore operations
- **Maintainability**: Clean architecture with proper separation of concerns
- **Extensibility**: Easy addition of new widget types and features

This approach leverages our working foundation while creating a robust, maintainable system that follows GUI best practices and prepares us for future enhancements.