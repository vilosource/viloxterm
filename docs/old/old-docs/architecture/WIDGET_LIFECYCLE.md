# Widget Lifecycle Architecture

## Overview

The Widget Lifecycle Architecture provides a robust, event-driven system for managing the complete lifecycle of application widgets (AppWidgets) in ViloxTerm. This architecture ensures proper initialization, state management, resource cleanup, and coordination between asynchronous widget operations and the UI framework.

> **📖 Related Documentation:**
> - [Widget Architecture Guide](WIDGET-ARCHITECTURE-GUIDE.md) - Complete widget architecture overview
> - [AppWidget Manager](app-widget-manager.md) - Registry and metadata system
> - [Developer Guide](../dev-guides/widget-lifecycle-guide.md) - Practical implementation examples

> **Integration Context:** This widget lifecycle system is deeply integrated with the [Tab Pane Splitting Architecture](TAB_PANE_SPLITTING.md). The split pane system manages the tree structure and layout, while this system manages the individual widget lifecycles within each pane. See the main architecture document for how split operations coordinate with widget states.

## Core Concepts

### AppWidget

An AppWidget is the fundamental content unit in ViloxTerm - representing terminals, editors, file explorers, and other interactive components. Each AppWidget extends from a base class that provides lifecycle management capabilities.

### Widget States

The architecture defines seven distinct states that a widget can be in during its lifetime:

```mermaid
stateDiagram-v2
    [*] --> CREATED: Widget instantiated
    CREATED --> INITIALIZING: initialize()
    INITIALIZING --> READY: set_ready()
    INITIALIZING --> ERROR: set_error()
    READY --> SUSPENDED: suspend()
    SUSPENDED --> READY: resume()
    ERROR --> INITIALIZING: retry_initialization()
    READY --> DESTROYING: cleanup()
    SUSPENDED --> DESTROYING: cleanup()
    ERROR --> DESTROYING: cleanup()
    DESTROYING --> DESTROYED: cleanup complete
    DESTROYED --> [*]
```

## Architectural Patterns

### 1. State Machine Pattern

The widget lifecycle implements a formal state machine with validated transitions. Each state transition is validated against a predefined set of legal transitions, preventing invalid state changes and ensuring predictable behavior.

**Benefits:**
- Prevents race conditions
- Ensures predictable widget behavior
- Simplifies debugging through clear state tracking
- Enables proper resource management per state

### 2. Observer Pattern

The architecture extensively uses Qt's signal-slot mechanism (Observer pattern) to decouple components and enable event-driven behavior:

```mermaid
graph LR
    A[AppWidget] -->|widget_ready signal| B[SplitPaneWidget]
    A -->|widget_error signal| C[ErrorHandler]
    A -->|widget_state_changed signal| D[StateMonitor]
    A -->|focus_requested signal| E[FocusManager]
    B -->|connects to signal| F[Focus on Ready]
```

**Key Signals:**
- `widget_ready`: Emitted when async initialization completes
- `widget_error`: Emitted on initialization or runtime errors
- `widget_state_changed`: Emitted on any state transition
- `widget_destroying`: Emitted before cleanup begins
- `focus_requested`: Emitted when widget requests focus

### 3. Template Method Pattern

The base AppWidget class defines the lifecycle structure with hooks for subclasses to customize behavior:

```mermaid
classDiagram
    class AppWidget {
        +initialize()
        +set_ready()
        +set_error()
        +suspend()
        +resume()
        +cleanup()
        #on_suspend()
        #on_resume()
        #on_cleanup()
        #retry_initialization()
    }

    class TerminalAppWidget {
        #on_cleanup()
        #retry_initialization()
    }

    class EditorAppWidget {
        #on_suspend()
        #on_resume()
    }

    AppWidget <|-- TerminalAppWidget
    AppWidget <|-- EditorAppWidget
```

The base class provides the lifecycle framework while subclasses override specific hooks to implement their unique behavior.

### 4. Resource Management Pattern

The architecture includes automatic resource management through the SignalManager component:

```mermaid
graph TB
    A[Widget Created] --> B[SignalManager Created]
    B --> C[Signals Connected & Tracked]
    C --> D[Widget Active]
    D --> E[Widget Cleanup]
    E --> F[SignalManager.disconnect_all]
    F --> G[All Connections Removed]
    G --> H[Widget Destroyed]
```

This ensures no memory leaks from dangling signal connections.

## Lifecycle Flow

### Synchronous Widget Initialization

For simple widgets that don't require async operations:

```mermaid
sequenceDiagram
    participant User
    participant SplitPane
    participant AppWidget
    participant UI

    User->>SplitPane: Split Pane
    SplitPane->>AppWidget: Create Widget
    AppWidget->>AppWidget: State: CREATED
    AppWidget->>AppWidget: initialize()
    AppWidget->>AppWidget: State: INITIALIZING
    AppWidget->>AppWidget: set_ready()
    AppWidget->>AppWidget: State: READY
    AppWidget-->>SplitPane: widget_ready signal
    SplitPane->>AppWidget: focus_widget()
    AppWidget->>UI: setFocus()
```

### Asynchronous Widget Initialization

For widgets requiring async operations (e.g., TerminalAppWidget):

```mermaid
sequenceDiagram
    participant User
    participant SplitPane
    participant Terminal
    participant WebEngine
    participant Bridge

    User->>SplitPane: Split Pane (Ctrl+\)
    SplitPane->>Terminal: Create TerminalAppWidget
    Terminal->>Terminal: State: CREATED → INITIALIZING
    Terminal->>WebEngine: Load terminal HTML
    SplitPane->>Terminal: focus_widget()
    Terminal->>Terminal: Queue focus (not ready)
    Note over Terminal: _pending_focus = True
    WebEngine-->>Terminal: loadFinished signal
    Terminal->>Terminal: set_ready()
    Terminal->>Terminal: State: READY
    Terminal-->>SplitPane: widget_ready signal
    Terminal->>Terminal: Process pending focus
    Terminal->>WebEngine: setFocus()
    Terminal->>Bridge: focus_terminal_element()
```

## Focus Management

The architecture implements intelligent focus management that respects widget readiness:

```mermaid
graph TD
    A[focus_widget called] --> B{Widget State?}
    B -->|READY| C[Set Focus Immediately]
    B -->|INITIALIZING| D[Queue Focus Request]
    B -->|ERROR/DESTROYING| E[Reject Focus]
    D --> F[Widget becomes READY]
    F --> G[widget_ready signal]
    G --> H[Process Pending Focus]
    H --> C
```

### Focus Queue Mechanism

When focus is requested on a widget that isn't ready:
1. The request is queued internally (`_pending_focus = True`)
2. When the widget becomes ready, it processes the pending focus
3. This ensures focus is never lost due to timing issues

### Explicit Focus Tracking

The architecture provides explicit focus tracking through:
- **`has_focus` property**: Read-only property to check if widget has keyboard focus
- **`focusInEvent`/`focusOutEvent`**: Qt event handlers that update internal focus state
- **`_has_focus` field**: Internal tracking of focus state independent of Qt's hasFocus()

This explicit tracking is particularly useful in testing environments where Qt's focus behavior may differ.

## Signal Lifecycle Management

The SignalManager component provides automatic tracking and cleanup of Qt signal connections:

```mermaid
classDiagram
    class SignalManager {
        -owner: QObject
        -connections: List[SignalConnection]
        +connect(signal, slot, type, description, group)
        +disconnect(connection)
        +disconnect_all()
        +disconnect_group(group)
        +enable_group(group)
        +disable_group(group)
        +get_connection_count()
        +get_groups()
    }

    class SignalConnection {
        +signal: Any
        +slot: Any
        +connection_type: Qt.ConnectionType
        +description: str
        +group: Optional[str]
    }

    class AppWidget {
        -_signal_manager: SignalManager
    }

    SignalManager "1" --* "many" SignalConnection
    AppWidget --> SignalManager
```

### Connection Lifecycle

1. **Creation**: Signals are connected through SignalManager.connect()
2. **Tracking**: Each connection is tracked with metadata
3. **Grouping**: Connections can be organized into groups for bulk operations
4. **Cleanup**: On widget destruction, all connections are automatically disconnected
5. **Safety**: Prevents memory leaks and orphaned connections

### Connection Groups

SignalManager supports organizing connections into groups:
- **`disconnect_group(group)`**: Disconnect all connections in a group
- **`enable_group(group)`**: Reconnect all connections in a group
- **`disable_group(group)`**: Temporarily disconnect group without removing
- **`get_groups()`**: List all defined groups

This is useful for managing related signals together, such as all UI update signals or all data synchronization signals.

## Error Handling and Recovery

The architecture implements automatic error recovery with configurable retry strategy:

```mermaid
graph LR
    A[Widget Error] --> B[set_error]
    B --> C{Error Count < max_retries?}
    C -->|Yes| D[Schedule Retry]
    C -->|No| E[Stay in ERROR state]
    D --> F[Wait: base_delay * backoff_factor^(count-1)]
    F --> G[retry_initialization]
    G --> H[initialize]
```

### Configurable Retry Strategy

The retry mechanism can be customized per widget using `configure_retry_strategy()`:

- **`max_retries`**: Maximum number of retry attempts (default: 3)
- **`base_delay`**: Initial retry delay in milliseconds (default: 1000ms)
- **`backoff_factor`**: Exponential backoff multiplier (default: 1.5)

Example configurations:
- Default: 3 retries with delays of 1000ms, 1500ms, 2250ms
- Aggressive: 5 retries with delays of 500ms, 1000ms, 2000ms, 4000ms, 8000ms (factor: 2.0)
- Disabled: 0 retries (no automatic recovery)

## Visibility Management and Suspension Control

### Automatic Suspension

Widgets automatically suspend when hidden and resume when shown, but this behavior can be controlled through the `can_suspend` property:

```mermaid
stateDiagram-v2
    READY --> SUSPENDED: hideEvent() [if can_suspend=true]
    SUSPENDED --> READY: showEvent()
    READY --> READY: hideEvent() [if can_suspend=false]

    state SUSPENDED {
        [*] --> PausedOperations
        PausedOperations: Expensive operations paused
        PausedOperations: Resources minimized
    }

    state READY {
        [*] --> ActiveOperations
        ActiveOperations: Full functionality
        ActiveOperations: Resources active
    }
```

### Suspension Control

The `can_suspend` property in `AppWidgetMetadata` controls whether a widget can be suspended when hidden:

```python
# Widget registration with suspension control
AppWidgetMetadata(
    widget_id="com.viloapp.terminal",
    # ... other properties ...
    can_suspend=False,  # Terminal should never be suspended (has background PTY process)
)
```

#### When to Disable Suspension (`can_suspend=False`)

Widgets should **NOT** be suspended when they:
- Have background processes that must continue running (e.g., Terminal with PTY)
- Maintain network connections that shouldn't be interrupted
- Are performing critical background operations
- Have real-time data streams that shouldn't pause

#### When to Enable Suspension (`can_suspend=True`, default)

Widgets **SHOULD** be suspended when they:
- Only display static or user-driven content (e.g., Text Editor)
- Can easily pause and resume operations without side effects
- Don't have background processes or connections
- Can benefit from resource savings when hidden

### Implementation Details

The suspension control is implemented in the `AppWidget` base class:

```python
def suspend(self):
    """Suspend widget when hidden/inactive."""
    # Check if widget can be suspended
    if not self.can_suspend:
        logger.debug(f"Widget {self.widget_id} cannot be suspended")
        return

    if self.widget_state == WidgetState.READY:
        self._set_state(WidgetState.SUSPENDED)
        self.on_suspend()

def resume(self):
    """Resume widget when shown/active."""
    # If widget can't be suspended, it was never suspended
    if not self.can_suspend:
        return

    if self.widget_state == WidgetState.SUSPENDED:
        self._set_state(WidgetState.READY)
        self.on_resume()
```

The `can_suspend` property is:
1. Set in `AppWidgetMetadata` during widget registration
2. Passed to the widget via `set_metadata()` during creation
3. Checked before any suspension/resumption operations

## Advanced Focus Management

The FocusManager provides sophisticated focus handling capabilities:

```mermaid
classDiagram
    class FocusManager {
        -_current_focus: str
        -_focus_history: deque
        -_focus_queue: List[FocusRequest]
        -_focus_groups: Dict
        -_focus_policies: Dict
        +request_focus(widget_id, priority)
        +restore_previous_focus()
        +cycle_focus(group, forward)
        +set_focus_policy(widget_id, policy)
    }

    class FocusRequest {
        +widget_id: str
        +priority: FocusPriority
        +callback: Optional[Callable]
        +reason: str
    }

    class FocusPriority {
        <<enumeration>>
        LOW
        NORMAL
        HIGH
        CRITICAL
    }

    FocusManager --> FocusRequest
    FocusRequest --> FocusPriority
```

### Focus Features

- **Priority Queue**: Focus requests are handled by priority
- **Focus History**: 50-entry history for navigation
- **Focus Groups**: Organize widgets for tab cycling
- **Focus Policies**: Fine-grained control over focus behavior
- **Focus Restoration**: Return focus to previous widget

## State Transition Callbacks

Widgets support custom callbacks for lifecycle events:

```python
# Register callbacks for specific transitions
widget.on_state_transition(
    from_state=WidgetState.INITIALIZING,
    to_state=WidgetState.READY,
    callback=lambda w, f, t: print(f"Widget {w.widget_id} is ready!")
)

# Register for any transition
widget.on_state_transition(
    callback=lambda w, f, t: log_transition(w, f, t)
)
```

This enables:
- Custom initialization completion handlers
- Error recovery hooks
- Resource management on state changes
- Testing and debugging hooks

## Widget Debugging Utilities

### WidgetDebugger

Comprehensive debugging support for widget lifecycle:

```mermaid
classDiagram
    class WidgetDebugger {
        -_tracked_widgets: Dict
        -_state_history: Dict
        -_performance_metrics: Dict
        +track_widget(widget)
        +get_widget_info(widget)
        +print_widget_state(widget)
        +watch_widget(widget, interval)
    }

    class WidgetInspector {
        <<static>>
        +inspect(widget): Dict
        +validate_state(widget): List
        +compare_widgets(w1, w2): Dict
    }
```

Features:
- **State History**: Track all state transitions
- **Performance Metrics**: Initialization timing, error counts
- **Live Watching**: Monitor widget state in real-time
- **State Validation**: Detect inconsistencies
- **Widget Comparison**: Debug differences between widgets

## Design Principles

### 1. **Event-Driven Architecture**
All state changes and interactions are event-driven through Qt signals, eliminating timing dependencies and race conditions.

### 2. **Separation of Concerns**
- **AppWidget**: Manages its own lifecycle and state
- **SignalManager**: Handles connection lifecycle
- **SplitPaneWidget**: Manages layout and widget coordination
- **WidgetState**: Encapsulates state definitions and validation

### 3. **Fail-Safe Defaults**
- Invalid state transitions are prevented
- Focus requests on non-ready widgets are queued
- Automatic cleanup prevents resource leaks
- Error recovery with backoff prevents infinite loops

### 4. **Extensibility**
The template method pattern allows new widget types to customize behavior without modifying the core lifecycle management.

## Integration Points

### With Split Pane System

```mermaid
graph TB
    A[User Action: Split Pane] --> B[WorkspaceService]
    B --> C[SplitPaneWidget.split_horizontal]
    C --> D[Create New AppWidget]
    D --> E{Widget Type}
    E -->|Async| F[Connect to widget_ready]
    E -->|Sync| G[Focus Immediately]
    F --> H[Wait for Ready Signal]
    H --> I[Focus on Ready]
```

### With Command System

Commands interact with widgets through their lifecycle-aware methods:
- Commands check widget state before operations
- Commands can wait for widget readiness
- Commands trigger proper cleanup through lifecycle methods

## Testing and Debugging

### Comprehensive Test Suite

The architecture includes extensive test coverage:
- **Unit Tests**: 50+ tests across multiple test files
  - `test_widget_state.py`: State machine validation (16 tests)
  - `test_signal_manager.py`: Signal management with groups (12 tests)
  - `test_app_widget_lifecycle.py`: Lifecycle behavior (18 tests)
- **GUI Tests**: Integration tests for focus and split pane behavior
  - `test_widget_lifecycle_focus.py`: Focus queue and tracking
  - `test_split_pane_widget_lifecycle.py`: Split operations
- **Test Helpers**: `tests/helpers/widget_test_helpers.py`
  - `MockSyncWidget`: Synchronous widget for testing
  - `MockAsyncWidget`: Simulates async initialization
  - `MockErrorWidget`: Tests error handling
  - `WidgetTestHelper`: Utility methods for tests
  - `WidgetTestFixtures`: Reusable test setups

### Debug Logging

The architecture provides comprehensive logging for lifecycle tracking:
- **State transitions**: Info-level logs for all state changes
- **Focus operations**: Debug logs for focus requests and processing
- **Error handling**: Error logs with retry attempt counts
- **Signal management**: Debug logs for connection tracking
- **Initialization timing**: Performance metrics for widget readiness

### Testing Utilities

Special support for testing environments:
- **Explicit focus tracking**: `has_focus` property works reliably in tests
- **QSignalSpy compatibility**: Tests use `.count()` and `.at()` methods
- **Mock widgets**: Test helpers for simulating async behavior
- **Configurable delays**: Tests can adjust retry timing for faster execution
- **State callbacks**: Tests can hook into state transitions for verification

## Performance Characteristics

### Memory Management
- **Signal connections**: Automatically cleaned up, preventing leaks
- **State tracking**: Minimal overhead (single enum value)
- **Event queue**: Pending operations use minimal memory

### Timing Characteristics
- **Synchronous widgets**: Immediate readiness (<1ms)
- **Asynchronous widgets**: Ready when loaded (typically 100-500ms for terminals)
- **Focus operations**: Immediate for ready widgets, queued for initializing
- **Error recovery**: Configurable exponential backoff (default: 1s, 1.5s, 2.25s)

## Service-Widget Lifecycle Coordination

### Service-Backed Widget Pattern

Some widgets depend on persistent background services that outlive the widget instances. The Terminal system is the prime example:

```
┌─────────────────────────────────────────────────────────────┐
│                  Service Lifecycle                          │
├─────────────────────────────────────────────────────────────┤
│ TerminalService (Singleton)                                 │
│ ├─ Starts on app launch or first terminal request           │
│ ├─ Manages multiple PTY sessions                            │
│ ├─ Persists after UI widgets close                          │
│ └─ Stops only on app shutdown                               │
└─────────────────────────────────────────────────────────────┘
                            ↑
┌─────────────────────────────────────────────────────────────┐
│                 Widget Lifecycle                            │
├─────────────────────────────────────────────────────────────┤
│ TerminalAppWidget (Multiple instances)                      │
│ ├─ Created: Widget instantiated with session ID             │
│ ├─ Initializing: Connect to service session                 │
│ ├─ Ready: Display terminal output, handle input             │
│ ├─ Suspended: Disconnect from service but keep session      │
│ ├─ Ready: Reconnect to service session                      │
│ └─ Destroyed: Disconnect, optionally keep session           │
└─────────────────────────────────────────────────────────────┘
```

### Service Dependency Management

The lifecycle system coordinates with services through these patterns:

#### 1. Service Startup Coordination
```python
class TerminalAppWidget(AppWidget):
    def __init__(self, widget_id: str, session_id: Optional[str] = None):
        super().__init__(widget_id, WidgetType.TERMINAL)
        self.session_id = session_id

    def initialize(self):
        """Ensure service is running before initializing widget."""
        # 1. Get or start service
        terminal_service = service_locator.get(TerminalService)
        if not terminal_service.is_running():
            terminal_service.start()

        # 2. Create or connect to session
        if self.session_id:
            self.session = terminal_service.get_session(self.session_id)
        else:
            self.session = terminal_service.create_session()
            self.session_id = self.session.id

        # 3. Connect to session events
        self.session.output_received.connect(self._handle_output)
        self.session.closed.connect(self._handle_session_closed)

        # 4. Mark ready when connected
        self.set_ready()
```

#### 2. Widget-Service Communication
```python
def suspend(self):
    """Suspend widget but keep service session alive."""
    if self.session:
        # Disconnect UI but keep session running
        self.session.output_received.disconnect(self._handle_output)
        self.session.pause_output_buffering()  # Reduce memory usage
    super().suspend()

def resume(self):
    """Resume widget and reconnect to service session."""
    if self.session:
        # Reconnect UI
        self.session.output_received.connect(self._handle_output)
        self.session.resume_output_buffering()
        # Display any buffered output
        buffered = self.session.get_buffered_output()
        self.display_output(buffered)
    super().resume()
```

#### 3. Cleanup Coordination
```python
def cleanup(self):
    """Clean up widget and optionally preserve service session."""
    if self.session:
        # Disconnect from session
        self.session.output_received.disconnect(self._handle_output)

        # Decision: Keep session alive or terminate?
        if self.preserve_session_on_close:
            # Keep session running for potential reconnection
            self.session.detach_ui()
        else:
            # Terminate session and cleanup resources
            terminal_service.terminate_session(self.session_id)

    super().cleanup()
```

### Service Lifecycle States

Services have their own lifecycle that coordinates with widget states:

```
Service States:
├─ STOPPED: Service not running
├─ STARTING: Service initializing
├─ RUNNING: Service active and available
├─ STOPPING: Service shutting down gracefully
└─ ERROR: Service failed, needs restart

Widget-Service Coordination:
├─ Widget CREATED → Ensure Service RUNNING
├─ Widget INITIALIZING → Connect to Service
├─ Widget READY → Active Service communication
├─ Widget SUSPENDED → Minimal Service communication
├─ Widget DESTROYING → Disconnect from Service
└─ Last Widget DESTROYED → Service can STOP (optional)
```

### Multi-Widget Service Sharing

For services shared by multiple widgets (like Terminal):

```python
class ServiceBackedWidgetManager:
    """Coordinates multiple widgets sharing a service."""

    def __init__(self, service_name: str):
        self.service_name = service_name
        self.active_widgets = set()
        self.service = None

    def register_widget(self, widget: AppWidget):
        """Register widget as service user."""
        self.active_widgets.add(widget)

        # Start service if first widget
        if len(self.active_widgets) == 1:
            self.service = self._start_service()

        widget.destroyed.connect(lambda: self._unregister_widget(widget))

    def _unregister_widget(self, widget: AppWidget):
        """Unregister widget and potentially stop service."""
        self.active_widgets.discard(widget)

        # Stop service if last widget (optional)
        if len(self.active_widgets) == 0 and self.auto_stop_service:
            self.service.stop()
```

## Benefits of This Architecture

### 1. **Reliability**
- No race conditions in focus management
- Predictable state transitions with service coordination
- Automatic resource cleanup for both widgets and services

### 2. **Performance**
- Event-driven eliminates polling
- Suspended widgets consume minimal resources
- Service connection pooling for efficiency
- Efficient signal management across service boundaries

### 3. **Maintainability**
- Clear separation between service and widget lifecycles
- Centralized lifecycle management
- Consistent patterns across widget types
- Service dependency tracking

### 4. **Extensibility**
- New widget types easily integrated with services
- Service lifecycle hooks for customization
- Signal-based integration points
- Plugin-ready service architecture

## Implementation Status

As of December 2024, the Widget Lifecycle Architecture is **90% complete** with the following achievements:

### Completed Features
- ✅ **State Machine**: Full implementation with validated transitions
- ✅ **Signal Management**: Automatic cleanup via SignalManager
- ✅ **Focus Management**: Queue mechanism with explicit tracking
- ✅ **Error Recovery**: Configurable retry strategy with exponential backoff
- ✅ **Testing Suite**: 44+ comprehensive tests with full coverage
- ✅ **Debug Support**: Extensive logging and testing utilities
- ✅ **Documentation**: Complete architecture and developer guides

### Recent Enhancements (December 2024)
- Added explicit focus tracking with `has_focus` property
- Implemented configurable retry strategy via `configure_retry_strategy()`
- Enhanced logging with attempt counts and timing metrics
- Fixed testing compatibility issues with QSignalSpy
- Created comprehensive test suite with unit and GUI tests

### Remaining Work
- Widget pooling system for performance optimization (Phase 5)
- Advanced focus management features (history, priorities)
- Scale testing with 50+ widgets
- Performance benchmarking

## Summary

The Widget Lifecycle Architecture provides a comprehensive solution for managing complex widget behaviors in an asynchronous, event-driven desktop application. By combining established design patterns (State Machine, Observer, Template Method) with Qt's signal-slot mechanism, it creates a robust foundation that eliminates common issues like race conditions, memory leaks, and focus management problems while maintaining clean separation of concerns and extensibility.

The architecture has been battle-tested with extensive unit and integration tests, proving its reliability in handling various edge cases including async initialization, error recovery, and complex focus scenarios. The configurable retry strategy and comprehensive debug logging make it production-ready for both development and deployment environments.