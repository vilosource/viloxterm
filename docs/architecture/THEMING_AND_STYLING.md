# Theming and Styling Architecture

## Overview
This document explains how theming and styling works in ViloApp, including the color system, stylesheet management, and solutions to Qt styling challenges.

## File Structure

### Core Theme Files
- **`ui/vscode_theme.py`** - Central theme definition file
  - All color constants (VSCode Dark+ theme)
  - Stylesheet generator functions
  - Color palette definitions

### Widget-Specific Styling
- **`ui/widgets/pane_header.py`** - Pane header with custom painting
- **`ui/widgets/split_pane_widget.py`** - Split pane container styling
- **`ui/terminal/terminal_assets.py`** - Terminal-specific theming
- **`ui/activity_bar.py`** - Activity bar styling
- **`ui/sidebar.py`** - Sidebar panel styling

## Color System

### VSCode Dark+ Theme Colors
We use the official VSCode Dark+ color palette defined in `ui/vscode_theme.py`:

```python
# Core Editor Colors
EDITOR_BACKGROUND = "#1e1e1e"      # Main editor background
EDITOR_FOREGROUND = "#d4d4d4"      # Main text color
EDITOR_SELECTION = "#264f78"       # Selection highlight

# Activity Bar (left icon bar)
ACTIVITY_BAR_BACKGROUND = "#333333"
ACTIVITY_BAR_FOREGROUND = "#ffffff"

# Sidebar
SIDEBAR_BACKGROUND = "#252526"
SIDEBAR_FOREGROUND = "#cccccc"

# Tabs
TAB_ACTIVE_BACKGROUND = "#1e1e1e"
TAB_INACTIVE_BACKGROUND = "#2d2d30"

# Pane Headers (custom)
PANE_HEADER_BACKGROUND = "#2d2d30"        # Subtle dark gray
PANE_HEADER_ACTIVE_BACKGROUND = "#3c3c3c" # Lighter gray for active
```

### Adding New Colors
1. Define the color constant in `ui/vscode_theme.py`
2. Follow the naming convention: `COMPONENT_STATE_PROPERTY`
3. Use hex color values for consistency
4. Add a comment explaining the usage

## Stylesheet Application Methods

### Method 1: Qt Stylesheets (Preferred for Simple Cases)
```python
widget.setStyleSheet(f"""
    QWidget {{
        background-color: {BACKGROUND_COLOR};
        color: {FOREGROUND_COLOR};
    }}
""")
```

**Pros:**
- Easy to write and understand
- Supports pseudo-states (:hover, :pressed)
- Good for standard Qt widgets

**Cons:**
- Can be overridden by child widgets
- Cascading issues with complex hierarchies
- Limited control over painting order

### Method 2: QPalette (For System Integration)
```python
palette = widget.palette()
palette.setColor(QPalette.Window, QColor(BACKGROUND_COLOR))
palette.setColor(QPalette.WindowText, QColor(FOREGROUND_COLOR))
widget.setPalette(palette)
```

**Pros:**
- Integrates with system theme
- Consistent with Qt standards
- Good for basic color changes

**Cons:**
- Limited to predefined palette roles
- Can conflict with stylesheets
- Not all widgets respect palette colors

### Method 3: Custom Paint Event (For Full Control)
```python
def paintEvent(self, event):
    painter = QPainter(self)
    painter.fillRect(self.rect(), QBrush(self.background_color))
    super().paintEvent(event)
```

**Pros:**
- Complete control over rendering
- Cannot be overridden by stylesheets
- Reliable for dynamic colors

**Cons:**
- More code required
- Must handle all painting manually
- Performance considerations for complex widgets

## Common Styling Challenges and Solutions

### Challenge 1: Stylesheet Cascade Issues
**Problem:** Child widgets inherit or override parent stylesheets unexpectedly.

**Solution:** Use specific selectors and object names:
```python
widget.setObjectName("myWidget")
widget.setStyleSheet("#myWidget { background-color: #1e1e1e; }")
```

### Challenge 2: Dynamic Color Updates Not Applying
**Problem:** Changing stylesheet or palette doesn't update widget appearance.

**Solution:** Use custom paint events (see `ui/widgets/pane_header.py`):
```python
class PaneHeaderBar(QWidget):
    def __init__(self):
        self.background_color = QColor(PANE_HEADER_BACKGROUND)
        self.setAttribute(Qt.WA_StyledBackground, False)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QBrush(self.background_color))
        super().paintEvent(event)
    
    def set_active(self, active: bool):
        if active:
            self.background_color = QColor(PANE_HEADER_ACTIVE_BACKGROUND)
        else:
            self.background_color = QColor(PANE_HEADER_BACKGROUND)
        self.update()  # Force repaint
```

### Challenge 3: QSplitter Handle Styling
**Problem:** QSplitter handles are difficult to style consistently.

**Solution:** Use handle width and hover effects:
```python
splitter.setStyleSheet(f"""
    QSplitter::handle {{
        background-color: {SPLITTER_BACKGROUND};
    }}
    QSplitter::handle:horizontal {{
        width: 1px;
    }}
    QSplitter::handle:hover {{
        background-color: {SPLITTER_HOVER};
    }}
""")
```

### Challenge 4: WebEngine Widget Styling
**Problem:** QWebEngineView doesn't respect Qt stylesheets.

**Solution:** Inject CSS via JavaScript (see `ui/terminal/terminal_assets.py`):
```javascript
const style = document.createElement('style');
style.textContent = `
    body {
        background-color: ${backgroundColor};
        color: ${foregroundColor};
    }
`;
document.head.appendChild(style);
```

## Widget-Specific Styling Guidelines

### Pane Headers
- **File:** `ui/widgets/pane_header.py`
- **Method:** Custom paint event
- **Reason:** Dynamic active/inactive state changes
- **Key Features:**
  - Ultra-compact design (18px height)
  - Minimal padding (2px horizontal)
  - Subtle color differences for active state

### Terminal Widgets
- **File:** `ui/terminal/terminal_assets.py`
- **Method:** HTML/CSS + xterm.js theming
- **Key Features:**
  - VSCode terminal color palette
  - ANSI color support
  - Custom scrollbar styling

### Tab Widgets
- **File:** `ui/vscode_theme.py::get_tab_widget_stylesheet()`
- **Method:** Qt stylesheets
- **Key Features:**
  - Active tab border-top highlight
  - Hover effects on inactive tabs
  - Close button styling

## Best Practices

### 1. Centralize Colors
Always define colors in `ui/vscode_theme.py` rather than hardcoding values.

### 2. Document Styling Decisions
When using custom paint events or workarounds, add comments explaining why:
```python
# Using custom paint event because stylesheets don't update
# reliably when active state changes during widget recreation
def paintEvent(self, event):
    ...
```

### 3. Test Dynamic Updates
Always test that colors update correctly when:
- Theme changes (light/dark mode)
- Widget state changes (active/inactive, hover)
- Widgets are recreated (after splits)

### 4. Minimize Repaints
For custom paint events, only call `update()` when necessary:
```python
def set_active(self, active: bool):
    if self.is_active != active:  # Only update if changed
        self.is_active = active
        self.update()
```

### 5. Handle High DPI
Consider high DPI displays when setting fixed sizes:
```python
from PySide6.QtCore import Qt
self.setAttribute(Qt.WA_DontShowOnScreen)  # For testing
# Use logical pixels, Qt handles DPI scaling
```

## Adding New Themed Components

1. **Define colors** in `ui/vscode_theme.py`
2. **Create stylesheet function** if using stylesheets:
   ```python
   def get_my_component_stylesheet():
       return f"""..."""
   ```
3. **Apply styling** in widget constructor
4. **Test** with theme toggle (Ctrl+T)
5. **Document** any special handling required

## Debugging Styling Issues

### Check Stylesheet Cascade
```python
print(widget.styleSheet())  # Widget's own stylesheet
print(widget.parentWidget().styleSheet())  # Parent's stylesheet
```

### Verify Paint Events
```python
def paintEvent(self, event):
    print(f"Paint event: {self.rect()}")
    super().paintEvent(event)
```

### Inspect Palette
```python
palette = widget.palette()
for role in [QPalette.Window, QPalette.WindowText, QPalette.Base]:
    color = palette.color(role)
    print(f"{role}: {color.name()}")
```

### Force Repaint
```python
widget.style().unpolish(widget)
widget.style().polish(widget)
widget.update()
```

## Known Issues and Workarounds

### Issue 1: Stylesheet Inheritance in Split Panes
**Problem:** When panes are split, new widgets may not inherit expected styles.
**Solution:** Reapply stylesheets in `_render_tree_recursive()` method.

### Issue 2: QPalette Ignored by Some Widgets
**Problem:** QTextEdit and QPlainTextEdit don't always respect palette colors.
**Solution:** Use stylesheets for these widgets specifically.

### Issue 3: Focus Rectangle on Custom Widgets
**Problem:** Dotted focus rectangle appears on custom painted widgets.
**Solution:** Override `focusInEvent` and don't call super, or use:
```python
self.setFocusPolicy(Qt.NoFocus)  # If widget doesn't need keyboard focus
```

### Issue 4: Custom Widget Stylesheet Selectors
**Problem:** Using ID selectors (#widgetName) or class selectors in stylesheets may not apply to the widget itself.
**Solution:** For custom widgets, combine multiple approaches:
```python
# Method 1: Use class name selector without ID
widget.setStyleSheet("CustomTitleBar { background-color: #8B0000; }")

# Method 2: Combine with QPalette for reliability
widget.setAutoFillBackground(True)
palette = widget.palette()
palette.setColor(QPalette.Window, QColor("#8B0000"))
widget.setPalette(palette)

# Method 3: Use inline styles for critical styling
widget.setStyleSheet("background-color: #8B0000;")
```

### Issue 5: Frameless Window Custom Title Bars
**Problem:** Custom title bars in frameless windows may not respond to stylesheet changes.
**Solution:** Apply styling through multiple methods and ensure proper initialization order:
```python
class CustomTitleBar(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        # Apply styles AFTER UI setup to ensure widgets exist
        self.apply_styles()

    def apply_styles(self):
        # Use both palette and stylesheet for reliability
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(bg_color))
        self.setPalette(palette)
```

## Theme Toggle Implementation

The theme toggle (Ctrl+T) is implemented in:
- **Command:** `view.toggleTheme` in `core/commands/builtin/view_commands.py`
- **Service:** `UIService` in `services/ui_service.py`
- **Storage:** `SettingsService` persists the theme preference

To add theme support to new components:
1. Listen to the `theme_changed` signal
2. Update colors from `vscode_theme.py`
3. Call `update()` or reapply stylesheets

## Development Mode Visual Indicators

### Overview
ViloxTerm provides visual indicators to distinguish development builds from production releases.

### Implementation
**Files:** `core/app_config.py`, `ui/widgets/custom_title_bar.py`

**Detection Logic:**
```python
# Auto-detect production builds
def _is_production_build(self) -> bool:
    if os.environ.get('APPIMAGE'):  # Running from AppImage
        return True
    if os.environ.get('VILOAPP_PRODUCTION', '').lower() in ('1', 'true', 'yes'):
        return True
    if getattr(sys, 'frozen', False):  # PyInstaller/Nuitka build
        return True
    if '.dist' in sys.executable:  # Nuitka dist folder
        return True
    return False
```

**Visual Changes in Dev Mode:**
1. Title bar shows "[DEV]" suffix: "ViloxTerm [DEV]"
2. Title bar background color: #8B0000 (dark red) instead of #2d2d30 (dark gray)

**Styling Approach:**
```python
# Combine palette and stylesheet for reliability
def apply_styles(self):
    from core.app_config import app_config

    # Choose color based on mode
    title_bar_bg = "#8B0000" if app_config.dev_mode else "#2d2d30"

    # Method 1: Set background using palette
    self.setAutoFillBackground(True)
    palette = self.palette()
    palette.setColor(QPalette.Window, QColor(title_bar_bg))
    self.setPalette(palette)

    # Method 2: Apply stylesheets for child widgets
    self.setStyleSheet(f"""
        QToolButton {{
            background-color: transparent;
            color: #cccccc;
        }}
        /* ... other styles ... */
    """)
```

### Build System Integration
The build system automatically sets production mode:
- Docker builds: `export VILOAPP_PRODUCTION=1` in entrypoint.sh
- AppImage wrapper: Sets environment variable before launching

## Future Improvements

1. **Light Theme Support**
   - Create `vscode_theme_light.py` with light color palette
   - Add theme switching logic to stylesheet generators

2. **Custom Theme Support**
   - Allow loading theme from JSON/YAML file
   - Create theme editor UI

3. **Performance Optimization**
   - Cache compiled stylesheets
   - Batch repaint operations

4. **Accessibility**
   - High contrast theme option
   - Configurable font sizes
   - Better focus indicators

5. **Enhanced Dev Mode Indicators**
   - Optional debug overlay showing performance metrics
   - Configurable dev mode colors via settings
   - Git branch name in title bar

## References

- [Qt Stylesheet Reference](https://doc.qt.io/qt-6/stylesheet-reference.html)
- [VSCode Theme Color Reference](https://code.visualstudio.com/api/references/theme-color)
- [QPalette Documentation](https://doc.qt.io/qt-6/qpalette.html)
- [Custom Widget Painting](https://doc.qt.io/qt-6/paintsystem.html)