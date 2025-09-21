# Building Custom Frameless Windows in PySide6/Qt6 (Cross-Platform Guide)

This guide covers creating custom frameless windows that work reliably across Windows, macOS, and Linux (including Wayland). Based on real-world implementation experience with PySide6/Qt6.

## Table of Contents
- [Why Frameless Windows?](#why-frameless-windows)
- [Platform Considerations](#platform-considerations)
- [Complete Implementation](#complete-implementation)
- [Edge Cases and Solutions](#edge-cases-and-solutions)
- [Testing Considerations](#testing-considerations)

---

## Why Frameless Windows?

Custom frameless windows allow you to:
- **Maximize screen real estate** by integrating controls into your UI
- **Create consistent branding** across all platforms
- **Implement modern UI patterns** like combined tab/title bars (Chrome-style)
- **Control every pixel** of your application's appearance

---

## Platform Considerations

### The Wayland Challenge

On traditional X11, Windows, and macOS, you can manually position windows using `move()`. However, **Wayland prohibits this** for security and compositor control reasons.

**The Solution:** Qt6 provides platform-agnostic APIs:
- `QWindow.startSystemMove()` - Initiates system-controlled window dragging
- `QWindow.startSystemResize(edges)` - Initiates system-controlled resizing

These work on ALL platforms, making them the preferred approach.

---

## Complete Implementation

### 1. Basic Frameless Window Setup

```python
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMainWindow

class FramelessWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Essential window flags for frameless mode
        self.setWindowFlags(
            Qt.FramelessWindowHint |           # Remove window decorations
            Qt.WindowSystemMenuHint |          # Keep system menu functionality
            Qt.WindowMinMaxButtonsHint         # Allow min/max operations
        )

        # Enable mouse tracking for resize cursor feedback
        self.setMouseTracking(True)

        # Set minimum size to prevent window from becoming too small
        self.setMinimumSize(400, 300)
```

### 2. Custom Title Bar Implementation

```python
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QToolButton
from PySide6.QtCore import Signal

class CustomTitleBar(QWidget):
    # Signals for window operations
    minimize_requested = Signal()
    maximize_requested = Signal()
    close_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(36)  # Standard height for title bars
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 8, 0)

        # Application title
        self.title_label = QLabel("My Application")
        layout.addWidget(self.title_label)

        # Spacer
        layout.addStretch()

        # Window control buttons
        self.minimize_btn = QToolButton()
        self.minimize_btn.setText("─")
        self.minimize_btn.clicked.connect(self.minimize_requested.emit)

        self.maximize_btn = QToolButton()
        self.maximize_btn.setText("□")
        self.maximize_btn.clicked.connect(self.maximize_requested.emit)

        self.close_btn = QToolButton()
        self.close_btn.setText("×")
        self.close_btn.clicked.connect(self.close_requested.emit)

        layout.addWidget(self.minimize_btn)
        layout.addWidget(self.maximize_btn)
        layout.addWidget(self.close_btn)

    def mousePressEvent(self, event):
        """Initiate window dragging on title bar click."""
        if event.button() == Qt.LeftButton:
            # Get the window's native handle
            window_handle = self.window().windowHandle()
            if window_handle:
                # Use Qt's system move (works on Wayland!)
                window_handle.startSystemMove()

    def mouseDoubleClickEvent(self, event):
        """Toggle maximize on double-click."""
        if event.button() == Qt.LeftButton:
            self.maximize_requested.emit()
```

### 3. Edge Detection and Resizing

```python
class FramelessWindow(QMainWindow):
    RESIZE_BORDER = 6  # Pixels for resize detection

    def get_resize_direction(self, pos):
        """Determine resize direction based on mouse position."""
        rect = self.rect()
        x, y = pos.x(), pos.y()

        # Check corners first (8 pixels for corner detection)
        corner_size = 8

        # Use Qt.Edge enum (Qt6 style)
        if x <= corner_size and y <= corner_size:
            return Qt.Edge.TopEdge | Qt.Edge.LeftEdge
        elif x >= rect.width() - corner_size and y <= corner_size:
            return Qt.Edge.TopEdge | Qt.Edge.RightEdge
        elif x <= corner_size and y >= rect.height() - corner_size:
            return Qt.Edge.BottomEdge | Qt.Edge.LeftEdge
        elif x >= rect.width() - corner_size and y >= rect.height() - corner_size:
            return Qt.Edge.BottomEdge | Qt.Edge.RightEdge

        # Check edges
        elif x <= self.RESIZE_BORDER:
            return Qt.Edge.LeftEdge
        elif x >= rect.width() - self.RESIZE_BORDER:
            return Qt.Edge.RightEdge
        elif y <= self.RESIZE_BORDER:
            return Qt.Edge.TopEdge
        elif y >= rect.height() - self.RESIZE_BORDER:
            return Qt.Edge.BottomEdge

        return None

    def update_cursor(self, pos):
        """Update cursor based on resize direction."""
        direction = self.get_resize_direction(pos)

        if direction == Qt.Edge.LeftEdge or direction == Qt.Edge.RightEdge:
            self.setCursor(Qt.SizeHorCursor)
        elif direction == Qt.Edge.TopEdge or direction == Qt.Edge.BottomEdge:
            self.setCursor(Qt.SizeVerCursor)
        elif direction == (Qt.Edge.TopEdge | Qt.Edge.LeftEdge) or \
             direction == (Qt.Edge.BottomEdge | Qt.Edge.RightEdge):
            self.setCursor(Qt.SizeFDiagCursor)
        elif direction == (Qt.Edge.TopEdge | Qt.Edge.RightEdge) or \
             direction == (Qt.Edge.BottomEdge | Qt.Edge.LeftEdge):
            self.setCursor(Qt.SizeBDiagCursor)
        else:
            self.setCursor(Qt.ArrowCursor)

    def mousePressEvent(self, event):
        """Handle mouse press for resize operations."""
        if event.button() == Qt.LeftButton and not self.isMaximized():
            direction = self.get_resize_direction(event.pos())
            if direction:
                window_handle = self.windowHandle()
                if window_handle:
                    # Use Qt's system resize (Wayland-compatible!)
                    window_handle.startSystemResize(direction)
                    return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Update cursor on mouse move."""
        if not self.isMaximized():
            self.update_cursor(event.pos())
        super().mouseMoveEvent(event)
```

### 4. Complete Integration

```python
from PySide6.QtWidgets import QVBoxLayout, QWidget

class FramelessWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_frameless()
        self.setup_ui()

    def setup_frameless(self):
        """Configure frameless window settings."""
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowSystemMenuHint |
            Qt.WindowMinMaxButtonsHint
        )
        self.setMouseTracking(True)
        self.setMinimumSize(400, 300)

    def setup_ui(self):
        """Create and integrate custom title bar."""
        # Create custom title bar
        self.title_bar = CustomTitleBar(self)

        # Connect signals
        self.title_bar.minimize_requested.connect(self.showMinimized)
        self.title_bar.maximize_requested.connect(self.toggle_maximize)
        self.title_bar.close_requested.connect(self.close)

        # Get current central widget
        original_central = self.centralWidget()

        # Create container for new layout
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Add title bar at top
        layout.addWidget(self.title_bar)

        # Add original content below
        if original_central:
            layout.addWidget(original_central)

        # Set as new central widget
        self.setCentralWidget(container)

    def toggle_maximize(self):
        """Toggle between maximized and normal state."""
        if self.isMaximized():
            self.showNormal()
            self.title_bar.maximize_btn.setText("□")
        else:
            self.showMaximized()
            self.title_bar.maximize_btn.setText("❐")
```

---

## Edge Cases and Solutions

### 1. Menu Bar Integration

When removing the native menu bar, you need alternative access to menu items:

```python
def hide_native_menu_bar(self):
    """Hide native menu bar and provide alternative access."""
    if self.menuBar():
        # Option 1: Create hamburger menu
        self.create_hamburger_menu()

        # Option 2: Hide completely
        self.menuBar().hide()
        self.menuBar().setMaximumHeight(0)

def create_hamburger_menu(self):
    """Create consolidated menu for hamburger button."""
    menu = QMenu(self)

    # Copy all menus from menu bar
    for action in self.menuBar().actions():
        if action.menu():
            # Add submenu
            menu.addMenu(action.menu())
        else:
            # Add action directly
            menu.addAction(action)

    # Attach to hamburger button
    self.title_bar.menu_button.setMenu(menu)
```

### 2. State Preservation

Maximize state needs special handling:

```python
def changeEvent(self, event):
    """Handle window state changes."""
    if event.type() == QEvent.WindowStateChange:
        if self.isMaximized():
            # Remove resize borders when maximized
            self.RESIZE_BORDER = 0
            self.title_bar.maximize_btn.setText("❐")
        else:
            # Restore resize borders
            self.RESIZE_BORDER = 6
            self.title_bar.maximize_btn.setText("□")
    super().changeEvent(event)
```

### 3. Settings Persistence

Store user preference for frameless mode:

```python
from PySide6.QtCore import QSettings

def save_frameless_preference(enabled: bool):
    settings = QSettings("MyCompany", "MyApp")
    settings.setValue("UI/FramelessMode", enabled)
    settings.sync()

def load_frameless_preference() -> bool:
    settings = QSettings("MyCompany", "MyApp")
    return settings.value("UI/FramelessMode", False, type=bool)
```

---

## Testing Considerations

### 1. Automated Testing

When testing frameless windows, bypass confirmation dialogs:

```python
import os

# Set environment variable before importing app modules
os.environ['APP_TEST_MODE'] = '1'

# In your app configuration
def should_show_confirmations():
    return os.environ.get('APP_TEST_MODE') != '1'
```

### 2. Platform-Specific Testing

Test on multiple platforms and configurations:

```python
import platform

def test_window_operations():
    """Test window operations across platforms."""
    window = FramelessWindow()

    # Test dragging (mock for CI/CD)
    if platform.system() == "Linux":
        # Wayland requires special handling
        assert window.windowHandle() is not None

    # Test resize operations
    for edge in [Qt.Edge.LeftEdge, Qt.Edge.RightEdge]:
        # Verify edge detection works
        pass
```

### 3. Common Test Cases

Essential tests for frameless windows:

```python
def test_frameless_window_creation(qtbot):
    """Test frameless window is created with correct flags."""
    window = FramelessWindow()
    qtbot.addWidget(window)

    flags = window.windowFlags()
    assert flags & Qt.FramelessWindowHint
    assert hasattr(window, 'title_bar')

def test_window_controls(qtbot):
    """Test minimize, maximize, close buttons."""
    window = FramelessWindow()
    qtbot.addWidget(window)

    # Test each control
    window.title_bar.minimize_requested.emit()
    assert window.isMinimized()

    window.showNormal()
    window.title_bar.maximize_requested.emit()
    assert window.isMaximized()
```

---

## Common Pitfalls and Solutions

| Problem | Solution |
|---------|----------|
| **Window not draggable on Wayland** | Use `startSystemMove()` instead of manual `move()` |
| **Resize doesn't work** | Use `startSystemResize()` with proper edge detection |
| **Menu bar still visible** | Call both `hide()` and `setMaximumHeight(0)` |
| **Double-click maximize not working** | Handle `mouseDoubleClickEvent` in title bar |
| **Settings not persisting** | Ensure consistent QSettings organization/app names |
| **Tests blocked by dialogs** | Implement test mode flag to bypass confirmations |
| **Window too small** | Set `minimumSize()` in constructor |
| **Cursor not changing on edges** | Enable `setMouseTracking(True)` |

---

## Best Practices

1. **Always use Qt's system APIs** (`startSystemMove/Resize`) for compatibility
2. **Set reasonable minimum window size** (typically 400x300)
3. **Provide visual feedback** with cursor changes on resize borders
4. **Test on all target platforms**, especially Wayland
5. **Handle window state changes** properly (maximize/restore)
6. **Make resize borders at least 6px** for usability
7. **Use Qt.Edge enum** (not the deprecated individual edge constants)
8. **Store user preferences** for window mode

---

## Conclusion

Creating frameless windows in PySide6/Qt6 requires careful attention to platform differences, especially Wayland's restrictions. By using Qt's `startSystemMove()` and `startSystemResize()` APIs, you can create beautiful, custom-styled windows that work reliably across all platforms.

Remember: The compositor is your friend on modern systems. Work with it, not against it, and your users will have a smooth, native-feeling experience regardless of their platform.