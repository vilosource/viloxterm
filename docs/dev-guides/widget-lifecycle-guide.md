# Widget Lifecycle Developer Guide

## Overview

This guide provides practical information for developers working with the Widget Lifecycle system in ViloxTerm. For architectural concepts and design patterns, refer to the [Widget Lifecycle Architecture](../architecture/WIDGET_LIFECYCLE.md) document.

**Last Updated**: December 2024
**Implementation Status**: 90% Complete
**Test Coverage**: 44+ tests across 5 test files

## Table of Contents

1. [Quick Start](#quick-start)
2. [Working with Widget States](#working-with-widget-states)
3. [Creating New Widget Types](#creating-new-widget-types)
4. [Signal Management](#signal-management)
5. [Focus Handling](#focus-handling)
6. [Error Handling](#error-handling)
7. [Testing Widgets](#testing-widgets)
8. [Debugging Guide](#debugging-guide)
9. [Common Patterns](#common-patterns)
10. [Troubleshooting](#troubleshooting)

## Quick Start

### Essential Files

```
ui/widgets/
├── app_widget.py          # Base class - START HERE
├── widget_state.py         # State enum and validator
├── signal_manager.py       # Signal lifecycle management
└── split_pane_widget.py    # Integration with pane system

ui/terminal/
└── terminal_app_widget.py  # Example async widget implementation
```

### Basic Widget Implementation

```python
from ui.widgets.app_widget import AppWidget
from ui.widgets.widget_registry import WidgetType

class MyWidget(AppWidget):
    def __init__(self, widget_id: str, parent=None):
        super().__init__(widget_id, WidgetType.CUSTOM, parent)
        # For async widgets, call initialize()
        self.initialize()
        self.setup_ui()

    def setup_ui(self):
        # Create your UI here
        # For sync widgets, call set_ready() immediately
        self.set_ready()
```

## Working with Widget States

### State Transitions

The widget lifecycle uses a state machine with validated transitions. Always use the provided methods:

```python
# ✅ CORRECT - Use lifecycle methods
self.initialize()      # CREATED → INITIALIZING
self.set_ready()       # INITIALIZING → READY
self.set_error("msg")  # INITIALIZING/READY → ERROR
self.suspend()         # READY → SUSPENDED
self.resume()          # SUSPENDED → READY

# ❌ WRONG - Never set state directly
self.widget_state = WidgetState.READY  # DON'T DO THIS!
self._set_state(WidgetState.READY)     # DON'T DO THIS EITHER!
```

### Checking Widget State

```python
from ui.widgets.widget_state import WidgetState

# Check current state
if widget.widget_state == WidgetState.READY:
    # Widget is ready for operations
    widget.perform_action()

# Check if widget can accept focus
if widget.widget_state in [WidgetState.READY, WidgetState.SUSPENDED]:
    widget.focus_widget()
```

### State Change Notifications

Listen for state changes:

```python
widget.widget_state_changed.connect(self.on_state_changed)

def on_state_changed(self, state_str: str):
    logger.info(f"Widget entered state: {state_str}")
```

## Creating New Widget Types

### Widget Registration with Suspension Control

When registering your widget, consider whether it should be suspended:

```python
from core.app_widget_metadata import AppWidgetMetadata

# Widget with background process - should NOT suspend
AppWidgetMetadata(
    widget_id="com.myapp.monitor",
    widget_type=WidgetType.MONITOR,
    display_name="System Monitor",
    can_suspend=False,  # Keep monitoring even when hidden
    # ... other metadata
)

# UI-only widget - CAN suspend
AppWidgetMetadata(
    widget_id="com.myapp.editor",
    widget_type=WidgetType.EDITOR,
    display_name="Code Editor",
    can_suspend=True,  # Default - saves resources when hidden
    # ... other metadata
)
```

### Synchronous Widget Template

For widgets that initialize immediately (e.g., text editors):

```python
class SyncWidget(AppWidget):
    def __init__(self, widget_id: str, parent=None):
        super().__init__(widget_id, WidgetType.MY_TYPE, parent)
        self.setup_ui()
        # Ready immediately after UI setup
        self.set_ready()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.editor = QTextEdit()
        layout.addWidget(self.editor)

    def focus_widget(self):
        """Override to focus the actual content."""
        if super().focus_widget():  # Check state first
            self.editor.setFocus()
            return True
        return False
```

### Asynchronous Widget Template

For widgets that load resources asynchronously (e.g., terminals, web views):

```python
class AsyncWidget(AppWidget):
    def __init__(self, widget_id: str, parent=None):
        super().__init__(widget_id, WidgetType.MY_TYPE, parent)
        self.initialize()  # Start lifecycle
        self.load_content()

    def load_content(self):
        """Start async loading."""
        self.web_view = QWebEngineView()

        # Connect to load finished USING SignalManager
        self._signal_manager.connect(
            self.web_view.loadFinished,
            self.on_load_finished,
            description="Web content loaded"
        )

        self.web_view.load(QUrl("https://example.com"))

    def on_load_finished(self, success: bool):
        """Handle async load completion."""
        if success:
            self.set_ready()  # Now ready for interaction
        else:
            self.set_error("Failed to load content")

    def retry_initialization(self):
        """Override for custom retry logic."""
        self.web_view.reload()
```

### Lifecycle Hooks

Override these methods to customize behavior:

```python
class CustomWidget(AppWidget):
    def on_suspend(self):
        """Called when widget is hidden.

        NOTE: Only called if can_suspend=True in metadata.
        Widgets with can_suspend=False will never suspend.
        """
        # Pause expensive operations
        self.timer.stop()
        self.animation.pause()
        self.clear_cache()

    def on_resume(self):
        """Called when widget is shown again.

        NOTE: Only called if widget was previously suspended.
        Widgets with can_suspend=False never suspend/resume.
        """
        # Resume operations
        self.timer.start()
        self.animation.resume()
        self.rebuild_cache()

    def on_cleanup(self):
        """Called during widget destruction."""
        # Clean up resources
        if self.network_session:
            self.network_session.close()

    def retry_initialization(self):
        """Called on error retry."""
        # Custom retry logic
        self.reconnect_to_server()
```

## Signal Management

### Always Use SignalManager

The SignalManager automatically tracks and cleans up connections:

```python
# ✅ CORRECT - Use SignalManager
self._signal_manager.connect(
    some_object.some_signal,
    self.handle_signal,
    description="Handle some event"
)

# ❌ WRONG - Direct connection (memory leak risk)
some_object.some_signal.connect(self.handle_signal)
```

### Single-Shot Connections

For one-time connections (e.g., waiting for ready signal):

```python
widget.widget_ready.connect(
    self.on_widget_ready,
    Qt.SingleShotConnection  # Auto-disconnects after first emit
)
```

### Manual Disconnection

If you need to disconnect before cleanup:

```python
connection = self._signal_manager.connect(
    signal, slot, description="Temporary connection"
)

# Later...
self._signal_manager.disconnect(connection)
```

## Focus Handling

### Focus Tracking (New in Dec 2024)

The widget system now provides explicit focus tracking:

```python
# Check if widget has focus
if widget.has_focus:
    # Widget currently has keyboard focus
    perform_focus_specific_action()

# Focus tracking is automatic via focusInEvent/focusOutEvent
def focusInEvent(self, event):
    super().focusInEvent(event)  # Updates has_focus property
    # Your custom focus-in logic here
    self.highlight_border()

def focusOutEvent(self, event):
    super().focusOutEvent(event)  # Updates has_focus property
    # Your custom focus-out logic here
    self.unhighlight_border()
```

### Implementing Focus in Your Widget

```python
def focus_widget(self):
    """Set focus on your widget's content."""
    # ALWAYS call super() first - it handles state checking
    if super().focus_widget():
        # Widget is ready, set focus on your content
        if self.content_widget:
            self.content_widget.setFocus()
            # Additional focus logic
            self.highlight_active_element()
        return True
    return False
```

### Requesting Focus from Outside

```python
# From SplitPaneWidget or other containers
widget = self.model.find_leaf(pane_id).app_widget

# For immediate focus (if ready)
widget.focus_widget()

# For async widgets, wait for ready
if widget.widget_state != WidgetState.READY:
    widget.widget_ready.connect(
        lambda: widget.focus_widget(),
        Qt.SingleShotConnection
    )
```

### Focus During Split Operations

The SplitPaneWidget handles this automatically, but here's the pattern:

```python
def split_and_focus(self):
    new_widget = self.create_widget()

    if new_widget.widget_state == WidgetState.READY:
        # Sync widget - focus immediately
        new_widget.focus_widget()
    else:
        # Async widget - wait for ready
        new_widget.widget_ready.connect(
            lambda: self._on_widget_ready_for_focus(new_widget.widget_id),
            Qt.SingleShotConnection
        )
```

## Error Handling

### Configurable Retry Strategy (New in Dec 2024)

Configure retry behavior per widget:

```python
class MyWidget(AppWidget):
    def __init__(self, widget_id: str, parent=None):
        super().__init__(widget_id, WidgetType.CUSTOM, parent)

        # Configure retry strategy
        self.configure_retry_strategy(
            max_retries=5,        # Try 5 times (default: 3)
            base_delay=500,       # Start with 500ms (default: 1000)
            backoff_factor=2.0    # Double each time (default: 1.5)
        )
        # Results in delays: 500ms, 1000ms, 2000ms, 4000ms, 8000ms

        # Or disable retries entirely
        # self.configure_retry_strategy(max_retries=0)
```

### Setting Errors

```python
def load_resource(self):
    try:
        self.resource = load_from_network()
        self.set_ready()
    except NetworkError as e:
        # This will trigger automatic retry (using configured strategy)
        self.set_error(f"Network error: {e}")
    except FatalError as e:
        # For non-recoverable errors, disable retries
        self.configure_retry_strategy(max_retries=0)
        self.set_error(f"Fatal: {e}")
```

### Custom Retry Logic

```python
def retry_initialization(self):
    """Override for custom retry behavior."""
    # Clear any error state
    self.error_display.hide()

    # Try different approach
    if self._error_count == 1:
        self.try_primary_server()
    elif self._error_count == 2:
        self.try_backup_server()
    else:
        self.try_offline_mode()
```

### Error Recovery UI

```python
def set_error(self, msg: str):
    """Override to show error UI."""
    super().set_error(msg)  # Call parent first

    # Show error to user
    self.error_label.setText(msg)
    self.error_widget.show()
    self.content_widget.hide()
```

## Testing Widgets

### Unit Testing Widget States

```python
import pytest
from PySide6.QtTest import QSignalSpy
from ui.widgets.widget_state import WidgetState

def test_widget_lifecycle(qtbot):
    """Test widget state transitions."""
    widget = MyAsyncWidget("test-1")
    qtbot.addWidget(widget)

    # Initial state
    assert widget.widget_state == WidgetState.CREATED

    # Spy on state changes (use count() and at() for QSignalSpy)
    state_spy = QSignalSpy(widget.widget_state_changed)

    # After initialization
    widget.initialize()
    assert widget.widget_state == WidgetState.INITIALIZING
    assert state_spy.count() == 1
    assert state_spy.at(0)[0] == "initializing"

    # Wait for ready signal
    with qtbot.waitSignal(widget.widget_ready, timeout=1000):
        widget.simulate_load_complete()

    assert widget.widget_state == WidgetState.READY
    assert state_spy.count() == 2
    assert state_spy.at(1)[0] == "ready"
```

### Testing Focus Management

```python
def test_focus_queuing(qtbot):
    """Test focus queuing for async widgets."""
    widget = AsyncWidget("test-2")
    qtbot.addWidget(widget)

    # Request focus before ready
    result = widget.focus_widget()
    assert result == False  # Focus queued
    assert widget._pending_focus == True
    assert not widget.has_focus  # Use has_focus property

    # Trigger ready
    with qtbot.waitSignal(widget.widget_ready):
        widget.simulate_load_complete()

    # Focus should be set after ready
    qtbot.wait(10)  # Let event loop process

    # Use has_focus instead of Qt's hasFocus() for reliable testing
    assert widget.has_focus  # More reliable in tests than hasFocus()
```

### Testing Signal Cleanup

```python
def test_signal_cleanup(qtbot):
    """Test that signals are cleaned up."""
    widget = MyWidget("test-3")
    qtbot.addWidget(widget)

    # Connect some signals
    initial_count = widget._signal_manager.get_connection_count()

    # Cleanup
    widget.cleanup()

    # All connections should be gone
    assert widget._signal_manager.get_connection_count() == 0
```

## Debugging Guide

### Enhanced Logging (Improved in Dec 2024)

The widget system now provides comprehensive logging at different levels:

```python
# Set logging level to see lifecycle details
import logging
logging.basicConfig(level=logging.DEBUG)

# Info level: State transitions and important events
# Debug level: Focus operations, signal management
# Error level: Errors with retry attempt counts
```

### State Transition Tracking

The base AppWidget automatically logs all state transitions:

```
INFO: Widget abc123: State transition: created → initializing
INFO: Widget abc123 ready in 0.45s
ERROR: Widget abc123 error (attempt 1/3): Network timeout
INFO: Retrying widget abc123 initialization in 1000ms (attempt 2/3)
DEBUG: Widget abc123: initializing → ready
```

### Focus Debugging

```python
# The system now logs focus operations automatically
DEBUG: Widget abc123 gained focus
DEBUG: Widget abc123 lost focus
DEBUG: Focus set on widget abc123
DEBUG: Focus pending for widget abc123 (state: initializing)

# Check focus status programmatically
def debug_focus_state(self):
    logger.info(f"Widget {self.widget_id}:")
    logger.info(f"  has_focus: {self.has_focus}")
    logger.info(f"  _pending_focus: {self._pending_focus}")
    logger.info(f"  widget_state: {self.widget_state.value}")
```

### Retry Strategy Debugging

```python
# Monitor retry behavior
def debug_retry_config(self):
    logger.info(f"Retry configuration for {self.widget_id}:")
    logger.info(f"  max_retries: {self._max_retries}")
    logger.info(f"  base_delay: {self._retry_base_delay}ms")
    logger.info(f"  backoff_factor: {self._retry_backoff_factor}")
    logger.info(f"  current_error_count: {self._error_count}")
```

### Signal Connection Debugging

```python
# Check active connections
count = widget._signal_manager.get_connection_count()
logger.info(f"Widget has {count} active signal connections")

# Debug signal manager
if widget._signal_manager.has_connections():
    logger.warning("Widget still has connections at cleanup!")

# Track connection lifecycle
self._signal_manager.connect(
    signal, slot,
    description="Debug: tracking specific connection"
)
```

### Performance Debugging

```python
# The system tracks initialization timing
INFO: Widget abc123 ready in 0.23s

# Add custom performance tracking
def initialize(self):
    super().initialize()
    self._custom_timer = time.time()

def set_ready(self):
    if hasattr(self, '_custom_timer'):
        duration = time.time() - self._custom_timer
        logger.info(f"Custom init took {duration:.2f}s")
    super().set_ready()
```

## Advanced Features

### State Transition Callbacks

Register callbacks for lifecycle events:

```python
class MyWidget(AppWidget):
    def __init__(self, widget_id: str, parent=None):
        super().__init__(widget_id, WidgetType.CUSTOM, parent)

        # Register for specific transition
        self.on_state_transition(
            from_state=WidgetState.INITIALIZING,
            to_state=WidgetState.READY,
            callback=self._on_ready_callback
        )

        # Register for any error
        self.on_state_transition(
            to_state=WidgetState.ERROR,
            callback=self._on_any_error
        )

        # Register for all transitions
        self.on_state_transition(
            callback=self._log_all_transitions
        )

    def _on_ready_callback(self, widget, from_state, to_state):
        logger.info(f"Widget {widget.widget_id} is now ready!")
        self.emit_ready_notification()

    def _on_any_error(self, widget, from_state, to_state):
        logger.error(f"Widget entered error state from {from_state.value}")
        self.show_error_ui()

    def _log_all_transitions(self, widget, from_state, to_state):
        logger.debug(f"Transition: {from_state.value} -> {to_state.value}")
```

### Using FocusManager

The global FocusManager provides advanced focus control:

```python
from ui.widgets.focus_manager import get_focus_manager, FocusPriority

class MyComplexWidget(AppWidget):
    def __init__(self, widget_id: str, parent=None):
        super().__init__(widget_id, WidgetType.CUSTOM, parent)

        # Register with focus manager
        focus_manager = get_focus_manager()
        focus_manager.register_widget(
            self,
            group="editors",  # Focus group for cycling
            policy={
                "enabled": True,
                "max_focus_count": 10  # Limit focus history
            }
        )

    def request_urgent_focus(self):
        """Request focus with high priority."""
        focus_manager = get_focus_manager()
        focus_manager.request_focus(
            self.widget_id,
            priority=FocusPriority.HIGH,
            reason="User action requires immediate attention"
        )

    def restore_previous_focus(self):
        """Return focus to previous widget."""
        focus_manager = get_focus_manager()
        focus_manager.restore_previous_focus()
```

### Signal Groups

Organize related signals for bulk operations:

```python
class DataWidget(AppWidget):
    def __init__(self, widget_id: str, parent=None):
        super().__init__(widget_id, WidgetType.CUSTOM, parent)

        # Connect UI update signals in a group
        self._signal_manager.connect(
            self.data_changed, self.update_display,
            group="ui_updates",
            description="Update display on data change"
        )
        self._signal_manager.connect(
            self.selection_changed, self.update_selection_ui,
            group="ui_updates",
            description="Update selection UI"
        )

        # Connect data sync signals in another group
        self._signal_manager.connect(
            self.data_changed, self.sync_to_server,
            group="data_sync",
            description="Sync data to server"
        )

    def pause_ui_updates(self):
        """Temporarily disable UI updates."""
        self._signal_manager.disable_group("ui_updates")

    def resume_ui_updates(self):
        """Re-enable UI updates."""
        self._signal_manager.enable_group("ui_updates")

    def cleanup(self):
        """Clean up by groups."""
        # Disconnect data sync first
        self._signal_manager.disconnect_group("data_sync")
        # Then UI updates
        self._signal_manager.disconnect_group("ui_updates")
        super().cleanup()
```

### Widget Debugging

Use the debugging utilities for development:

```python
from ui.widgets.widget_debug import get_widget_debugger, WidgetInspector

# Enable global debugging
from ui.widgets.widget_debug import enable_widget_debugging
enable_widget_debugging()

class DebugWidget(AppWidget):
    def __init__(self, widget_id: str, parent=None):
        super().__init__(widget_id, WidgetType.CUSTOM, parent)

        # Track this widget for debugging
        debugger = get_widget_debugger()
        debugger.track_widget(self)

    def debug_state(self):
        """Print comprehensive debug info."""
        debugger = get_widget_debugger()
        debugger.print_widget_state(self)

    def validate(self):
        """Check for state inconsistencies."""
        issues = WidgetInspector.validate_state(self)
        if issues:
            logger.warning(f"State issues: {issues}")
        return len(issues) == 0

    def start_monitoring(self):
        """Watch widget state changes."""
        debugger = get_widget_debugger()
        # Print state every second
        debugger.watch_widget(self, interval_ms=1000)
```

### Test Helpers

Use the provided test helpers for widget testing:

```python
from tests.helpers import (
    MockSyncWidget, MockAsyncWidget, MockErrorWidget,
    WidgetTestHelper, WidgetTestFixtures
)

def test_async_widget_focus(qtbot):
    """Test async widget focus behavior."""
    # Use mock async widget
    widget = MockAsyncWidget("test-async", delay_ms=100)
    qtbot.addWidget(widget)

    # Use test helper to wait for ready
    helper = WidgetTestHelper()
    helper.wait_for_ready(qtbot, widget, timeout=200)

    assert widget.widget_state == WidgetState.READY

def test_error_recovery(qtbot):
    """Test error recovery with mock."""
    widget = MockErrorWidget("test-error", fail_count=2)
    qtbot.addWidget(widget)

    # Widget will fail twice then succeed
    widget.initialize()

    # Wait for recovery
    helper = WidgetTestHelper()
    helper.wait_for_ready(qtbot, widget, timeout=5000)

    assert widget._error_count == 2
    assert widget.widget_state == WidgetState.READY
```

## Suspension Control Patterns

### Pattern: Widget with Background Process

For widgets that must keep running even when hidden:

```python
class MonitorWidget(AppWidget):
    """Real-time monitoring widget that shouldn't suspend."""

    def __init__(self, widget_id: str, parent=None):
        super().__init__(widget_id, WidgetType.MONITOR, parent)
        self.initialize()

        # Start background monitoring
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self.collect_metrics)
        self.monitor_timer.start(1000)  # Collect every second

        self.set_ready()

    def collect_metrics(self):
        """Collect metrics even when widget is hidden."""
        # This continues running because can_suspend=False
        metrics = self.get_system_metrics()
        self.update_buffer(metrics)

        # Only update UI if visible
        if self.isVisible():
            self.update_display(metrics)

    # on_suspend() will NEVER be called due to can_suspend=False
```

### Pattern: Widget with Expensive UI Operations

For widgets that should pause expensive operations when hidden:

```python
class VisualizationWidget(AppWidget):
    """3D visualization that should pause when hidden."""

    def __init__(self, widget_id: str, parent=None):
        super().__init__(widget_id, WidgetType.VIEWER, parent)
        self.animation_timer = None
        self.setup_3d_scene()
        self.set_ready()

    def on_suspend(self):
        """Pause rendering when hidden (can_suspend=True)."""
        if self.animation_timer:
            self.animation_timer.stop()
        self.renderer.pause()
        self.free_gpu_resources()
        logger.debug("Visualization suspended - GPU resources freed")

    def on_resume(self):
        """Resume rendering when shown again."""
        self.allocate_gpu_resources()
        self.renderer.resume()
        if self.animation_timer:
            self.animation_timer.start()
        logger.debug("Visualization resumed - rendering active")
```

### Pattern: Terminal Widget (Never Suspends)

```python
class TerminalAppWidget(AppWidget):
    """Terminal with PTY process that must keep running."""

    # Registration includes can_suspend=False

    def hideEvent(self, event):
        """Terminal stays READY even when hidden."""
        super().hideEvent(event)
        # Widget remains in READY state
        # PTY process continues running
        # Output continues to be collected

    def showEvent(self, event):
        """Show accumulated output when visible again."""
        super().showEvent(event)
        # Flush any buffered output to display
        self.flush_output_buffer()
```

## Common Patterns

### Pattern: Wait for Multiple Widgets

```python
def wait_for_all_widgets(widgets: List[AppWidget], callback):
    """Execute callback when all widgets are ready."""
    pending = []

    for widget in widgets:
        if widget.widget_state != WidgetState.READY:
            pending.append(widget)

    if not pending:
        callback()
        return

    def check_all_ready():
        nonlocal pending
        pending = [w for w in pending
                  if w.widget_state != WidgetState.READY]
        if not pending:
            callback()

    for widget in pending:
        widget.widget_ready.connect(check_all_ready)
```

### Pattern: Widget with Fallback

```python
class ResilientWidget(AppWidget):
    def __init__(self, widget_id: str, parent=None):
        super().__init__(widget_id, WidgetType.CUSTOM, parent)
        self.fallback_mode = False
        self.initialize()
        self.try_primary_mode()

    def try_primary_mode(self):
        """Try to load primary functionality."""
        try:
            self.load_advanced_features()
            self.set_ready()
        except Exception as e:
            logger.warning(f"Primary mode failed: {e}")
            self.try_fallback_mode()

    def try_fallback_mode(self):
        """Fall back to basic functionality."""
        self.fallback_mode = True
        self.load_basic_features()
        self.set_ready()  # Ready with reduced functionality
```

### Pattern: Lazy Initialization

```python
class LazyWidget(AppWidget):
    def __init__(self, widget_id: str, parent=None):
        super().__init__(widget_id, WidgetType.CUSTOM, parent)
        # Don't initialize until first show
        self._initialized = False

    def showEvent(self, event):
        """Initialize on first show."""
        if not self._initialized:
            self._initialized = True
            self.initialize()
            self.load_content()
        super().showEvent(event)
```

## Troubleshooting

### Issue: Widget Never Becomes Ready

**Symptom**: Focus never sets, widget stays in INITIALIZING state

**Check**:
1. Is `set_ready()` called after async operation completes?
2. Is there an error preventing ready state?
3. Check logs for state transitions

### Issue: Background Process Stops When Widget Hidden

**Symptom**: Terminal output stops, monitoring pauses, connections drop

**Solution**:
1. Set `can_suspend=False` in widget metadata registration
2. Verify metadata is being set via `set_metadata()` during creation
3. Check that widget doesn't manually call `suspend()` in `hideEvent()`

```python
# In widget registration
AppWidgetMetadata(
    widget_id="com.viloapp.terminal",
    can_suspend=False,  # ← Critical for background processes
    # ...
)
```

### Issue: Widget Not Resuming After Being Shown

**Symptom**: Widget stays suspended after becoming visible

**Check**:
1. Is `can_suspend=True` (widgets with `False` never suspend/resume)?
2. Check if `showEvent()` is being called
3. Verify no exceptions in `on_resume()` hook
4. Check widget state with debugger

**Solution**:
```python
def on_load_finished(self, success):
    if success:
        self.set_ready()  # Don't forget this!
    else:
        self.set_error("Load failed")  # Or this!
```

### Issue: Memory Leaks from Signals

**Symptom**: Memory usage grows, widgets not garbage collected

**Check**:
1. Are you using `_signal_manager.connect()`?
2. Is `cleanup()` being called?
3. Are there circular references?

**Solution**:
```python
# Always use SignalManager
self._signal_manager.connect(signal, slot)

# Ensure cleanup is called
def closeEvent(self, event):
    self.cleanup()  # Clean up signals
    super().closeEvent(event)
```

### Issue: Focus Lost After Split

**Symptom**: New pane doesn't get focus after split

**Check**:
1. Is the widget async?
2. Is widget_ready signal connected?
3. Is focus_widget() overridden correctly?

**Solution**: See [Focus During Split Operations](#focus-during-split-operations)

### Issue: Widget Stuck in ERROR State

**Symptom**: Widget won't retry after error

**Check**:
1. Error count exceeded max_retries?
2. Is `retry_initialization()` implemented?
3. Is the error actually recoverable?
4. Check retry configuration

**Solution**:
```python
# Option 1: Adjust retry configuration
widget.configure_retry_strategy(max_retries=5, base_delay=2000)

# Option 2: Reset error count in retry
def retry_initialization(self):
    """Reset and retry."""
    self._error_count = 0  # Reset if needed
    self.clear_error_state()
    self.initialize()

# Option 3: Disable retries for fatal errors
if fatal_error:
    self.configure_retry_strategy(max_retries=0)
    self.set_error("Fatal error - no retry")
```

### Issue: Signals Not Disconnecting

**Symptom**: Callbacks still firing after widget destroyed

**Check**:
1. Using SignalManager?
2. Is parent `cleanup()` called?

**Solution**:
```python
def on_cleanup(self):
    """Ensure cleanup."""
    # Custom cleanup first
    self.stop_timers()
    # Parent cleanup handles signals
    super().on_cleanup()
```

## Testing Best Practices (Updated Dec 2024)

### QSignalSpy Usage

```python
# CORRECT - Use count() and at() methods
spy = QSignalSpy(widget.widget_ready)
widget.set_ready()
assert spy.count() == 1
assert spy.at(0)[0] == expected_value

# WRONG - Don't use len() or indexing
# assert len(spy) == 1  # TypeError!
# assert spy[0][0] == value  # TypeError!
```

### Mock Widgets for Testing

```python
class MockAsyncWidget(AppWidget):
    """Test widget with configurable async behavior."""

    def __init__(self, widget_id: str, delay_ms: int = 50):
        super().__init__(widget_id, WidgetType.TERMINAL)
        self.delay_ms = delay_ms
        self.initialize()
        QTimer.singleShot(delay_ms, self.set_ready)

# Use in tests
def test_async_behavior(qtbot):
    widget = MockAsyncWidget("test", delay_ms=100)
    qtbot.addWidget(widget)

    # Wait for ready with timeout
    with qtbot.waitSignal(widget.widget_ready, timeout=200):
        pass

    assert widget.widget_state == WidgetState.READY
```

### Testing Error Recovery

```python
def test_retry_strategy(qtbot):
    widget = MyWidget("test")
    widget.configure_retry_strategy(max_retries=2, base_delay=10)
    qtbot.addWidget(widget)

    with patch.object(QTimer, 'singleShot') as mock_timer:
        widget.set_error("Test error")

        # Verify retry scheduled
        mock_timer.assert_called_once()
        assert mock_timer.call_args[0][0] == 10  # base_delay
```

## Best Practices

### DO's

1. ✅ **Always call parent methods** when overriding lifecycle methods
2. ✅ **Use SignalManager** for all signal connections
3. ✅ **Call set_ready()** when async init completes
4. ✅ **Test state transitions** in unit tests
5. ✅ **Log state changes** for debugging
6. ✅ **Handle errors gracefully** with set_error()
7. ✅ **Clean up resources** in on_cleanup()
8. ✅ **Use has_focus property** for reliable focus checking
9. ✅ **Configure retry strategy** for network-dependent widgets

### DON'Ts

1. ❌ **Don't set widget_state directly** - use lifecycle methods
2. ❌ **Don't connect signals directly** - memory leak risk
3. ❌ **Don't assume widgets are ready** - check state first
4. ❌ **Don't forget set_ready()** in async widgets
5. ❌ **Don't ignore cleanup** - resources will leak
6. ❌ **Don't use timers for focus** - use widget_ready signal
7. ❌ **Don't bypass state validation** - it's there for safety
8. ❌ **Don't use len() on QSignalSpy** - use count() instead
9. ❌ **Don't rely on hasFocus() in tests** - use has_focus property

## Performance Tips

1. **Suspend expensive operations** when widget hidden (on_suspend)
2. **Use lazy initialization** for heavy widgets
3. **Cache resources** across retry attempts
4. **Batch signal connections** in SignalManager
5. **Profile state transitions** to find bottlenecks

## Quick Reference Card

### Key Properties and Methods

```python
# State Management
widget.widget_state              # Current state (WidgetState enum)
widget.initialize()              # Start initialization
widget.set_ready()               # Mark as ready
widget.set_error(msg)            # Set error state
widget.suspend()                 # Suspend when hidden
widget.resume()                  # Resume when shown
widget.cleanup()                 # Clean up resources

# Focus Management
widget.has_focus                 # Check if has focus (property)
widget.focus_widget()            # Set focus (respects state)
widget._pending_focus            # Internal: focus queued?

# Retry Configuration
widget.configure_retry_strategy(
    max_retries=5,               # Number of attempts
    base_delay=1000,             # Initial delay (ms)
    backoff_factor=2.0           # Exponential multiplier
)

# Signal Management
widget._signal_manager.connect(signal, slot, description="...", group="...")
widget._signal_manager.disconnect(connection)
widget._signal_manager.disconnect_all()
widget._signal_manager.disconnect_group("group_name")
widget._signal_manager.enable_group("group_name")
widget._signal_manager.disable_group("group_name")
widget._signal_manager.get_connection_count()

# State Callbacks
widget.on_state_transition(
    from_state=WidgetState.INITIALIZING,
    to_state=WidgetState.READY,
    callback=my_callback
)

# Focus Manager (global)
from ui.widgets.focus_manager import get_focus_manager
fm = get_focus_manager()
fm.request_focus(widget_id, priority=FocusPriority.HIGH)
fm.restore_previous_focus()
fm.cycle_focus(group="editors", forward=True)

# Debugging
from ui.widgets.widget_debug import get_widget_debugger, WidgetInspector
debugger = get_widget_debugger()
debugger.track_widget(widget)
debugger.print_widget_state(widget)
WidgetInspector.validate_state(widget)

# Lifecycle Hooks (override these)
widget.on_suspend()              # Called when suspended
widget.on_resume()               # Called when resumed
widget.on_cleanup()              # Called during cleanup
widget.retry_initialization()    # Called on retry
```

### State Transitions

```
CREATED → INITIALIZING → READY → SUSPENDED → READY
                      ↓        ↓           ↓
                    ERROR    DESTROYING → DESTROYED
                      ↑
                INITIALIZING (retry)
```

### Test Files Reference

- `tests/unit/test_widget_state.py` - State machine tests (16 tests)
- `tests/unit/test_signal_manager.py` - Signal management tests (12 tests)
- `tests/unit/test_app_widget_lifecycle.py` - Lifecycle tests (18 tests)
- `tests/gui/test_widget_lifecycle_focus.py` - Focus tests
- `tests/gui/test_split_pane_widget_lifecycle.py` - Integration tests
- `tests/helpers/widget_test_helpers.py` - Test utilities and mocks

## Further Reading

- [Widget Lifecycle Architecture](../architecture/WIDGET_LIFECYCLE.md) - Conceptual overview
- [Implementation Plan](../plans/widget-lifecycle-implementation.md) - Development roadmap
- [AppWidget Source](../../ui/widgets/app_widget.py) - Base class implementation
- [Terminal Implementation](../../ui/terminal/terminal_app_widget.py) - Complex async example