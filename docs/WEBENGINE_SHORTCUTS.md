# Qt WebEngine Keyboard Shortcuts Solution

## Problem Statement
Qt WebEngine widgets (used for terminal and potentially other web-based widgets) don't propagate keyboard events up to parent widgets by default. This prevents global keyboard shortcuts from working when these widgets have focus.

## Solution Overview
We implement a multi-layered approach to ensure keyboard shortcuts work with Qt WebEngine:

1. **Event Filter on MainWindow** instead of QApplication (avoids segfaults)
2. **Recursive filter installation** on all workspace widgets
3. **Shifted character mapping** for correct shortcut recognition
4. **Dynamic filter updates** when new widgets are added

## Implementation Details

### 1. MainWindow Event Filter
```python
# In MainWindow.__init__:
self.installEventFilter(self)  # NOT QApplication.instance()
```
- Installing on QApplication causes immediate segfault with Qt WebEngine
- MainWindow filter is safe and still captures events from child widgets

### 2. Recursive Filter Installation
```python
def _install_filters_recursively(self, widget):
    # Install on every widget, including QWebEngineView
    widget.installEventFilter(self)
    
    # For WebEngineView, also install on focus proxy
    if isinstance(widget, QWebEngineView):
        focus_proxy = widget.focusProxy()
        if focus_proxy:
            focus_proxy.installEventFilter(self)
    
    # Recurse to children, skip internal WebEngine widgets
    for child in widget.findChildren(QWidget):
        if "RenderWidgetHostViewQtDelegateWidget" not in child.__class__.__name__:
            self._install_filters_recursively(child)
```

### 3. Shifted Character Handling
When Shift is pressed, Qt reports the shifted character (e.g., `|` instead of `\`).
The keyboard service maps these back to base characters:
```python
shifted_to_base = {
    Qt.Key_Bar: "\\",        # | -> \ for Ctrl+Shift+\
    Qt.Key_Plus: "=",        # + -> =
    Qt.Key_Underscore: "-",  # _ -> -
    # ... etc
}
```

### 4. Dynamic Updates
When new panes/widgets are added:
```python
# Connect to pane_added signal
self.workspace.split_widget.pane_added.connect(self._on_pane_added)

def _on_pane_added(self, pane_id):
    # Re-install filters to include new widgets
    self._install_workspace_filters()
```

## Adding New WebEngine Widgets

When adding new Qt WebEngine-based widgets:

1. **Inherit from AppWidget** for consistent behavior
2. **No special handling needed** - the recursive filter installation will handle it
3. **Test keyboard shortcuts** to ensure they work with your widget focused

Example:
```python
class MyWebWidget(AppWidget):
    def __init__(self, widget_id: str, parent=None):
        super().__init__(widget_id, WidgetType.CUSTOM, parent)
        self.web_view = QWebEngineView()
        # Setup your web view...
        # No need for special keyboard handling!
```

## Known Limitations

1. **Copy/Paste in Terminal**: Ctrl+C/V may need special handling as terminals traditionally use these differently
2. **Focus Management**: WebEngine widgets may grab focus aggressively - use `setFocusPolicy()` if needed
3. **Performance**: Installing many event filters has minimal overhead but monitor if you have many widgets

## Testing Shortcuts

To test that shortcuts work with a new WebEngine widget:

1. Focus the widget
2. Try these common shortcuts:
   - Ctrl+B (toggle sidebar)
   - Ctrl+\ (split horizontal)
   - Ctrl+Shift+\ (split vertical)
   - Ctrl+N (new tab)
   - Ctrl+T (toggle theme)

## Debugging Tips

Enable debug logging to see event flow:
```python
# In eventFilter method:
logger.debug(f"eventFilter received KeyPress from {obj.__class__.__name__}")
```

Check if filters are installed:
```python
# List all event filters on a widget
widget.installEventFilter(debug_filter)  # Your debug filter
```

## Summary

The solution ensures all keyboard shortcuts work regardless of which widget has focus, including Qt WebEngine widgets. The key insights are:

1. Never use QApplication event filter with WebEngine (causes segfault)
2. Install filters recursively on all widgets
3. Handle shifted characters properly
4. Skip WebEngine internal widgets to avoid issues

This approach is future-proof for any new WebEngine-based widgets added to the application.