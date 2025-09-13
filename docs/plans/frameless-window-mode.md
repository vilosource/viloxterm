# Plan: Implement Frameless Window Mode with Custom Title Bar

## Overview
Create a frameless window mode that maximizes screen real estate by:
1. Removing native window decorations (title bar)
2. Creating a custom title bar with integrated menu and window controls
3. Implementing proper window dragging and resizing
4. Following Wayland-compatible best practices

## New Files to Create

### 1. `ui/widgets/custom_title_bar.py`
- Custom title bar widget with:
  - Application title
  - Integrated menu bar
  - Window control buttons (min/max/close)
  - Proper drag handling using `startSystemMove()`
  - Height: ~36px to be compact

### 2. `ui/frameless_window.py`
- New frameless window class that:
  - Sets `Qt.FramelessWindowHint`
  - Integrates custom title bar
  - Handles edge resizing with `startSystemResize()`
  - Manages maximize/restore state
  - Optionally sets `WA_TranslucentBackground` for rounded corners

### 3. `core/commands/builtin/window_commands.py`
- New commands:
  - `window.toggleFrameless` - Switch between normal and frameless mode
  - `window.minimize` - Minimize window
  - `window.maximize` - Maximize window
  - `window.restore` - Restore window
  - `window.close` - Close window

## Files to Modify

### 1. `main.py`
- Add check for frameless mode preference
- Create `FramelessWindow` instead of `MainWindow` when enabled
- Similar to how Chrome mode was handled, but simpler

### 2. `ui/main_window.py`
- Refactor to extract common initialization logic
- Create base class or mixin for shared functionality
- Ensure both frameless and normal windows share same features

### 3. `services/ui_service.py`
- Add methods:
  - `is_frameless_mode_enabled()`
  - `toggle_frameless_mode()`
  - `get_window_state()`

### 4. `core/settings/defaults.py`
- Add setting: `"UI/FramelessMode": False`

## Implementation Details

### Custom Title Bar Design
```
[≡ Menu] [ViloxTerm]                    [_] [□] [×]
 ^                                        ^   ^   ^
 Menu icon                              Min Max Close
```

### Resize Hit Test Areas
- 6px border on all edges for resize handles
- Corners allow diagonal resizing
- Use `startSystemResize()` with appropriate `Qt.Edges`

### Key Code Structure
```python
class CustomTitleBar(QWidget):
    def __init__(self):
        # Layout: Menu button | Title | Spacer | Window controls
        # Height: 36px

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.window().windowHandle().startSystemMove()

class FramelessWindow(QMainWindow):
    def __init__(self):
        super().__init__(flags=Qt.FramelessWindowHint)
        # Create custom title bar
        # Set up central widget with existing layout

    def mousePressEvent(self, event):
        # Detect edge/corner for resize
        # Call startSystemResize() with appropriate edges
```

## Testing Strategy
1. Create `tests/gui/test_frameless_window.py`
2. Test window controls (min/max/close)
3. Test drag functionality
4. Test resize from edges
5. Test mode switching

## Benefits
- **More screen space**: ~30px saved from native title bar
- **Integrated UI**: Menu bar integrated into title bar
- **Modern look**: Clean, minimal design
- **Wayland compatible**: Uses proper system move/resize APIs

## Migration Path
1. Implement as optional mode (like Chrome mode was)
2. Toggle via settings or command
3. Preserve all existing functionality
4. Settings persist between sessions

## Implementation Checklist
- [ ] Create CustomTitleBar widget
- [ ] Create FramelessWindow class
- [ ] Add window commands
- [ ] Update main.py for mode selection
- [ ] Add UI service methods
- [ ] Update settings defaults
- [ ] Create tests
- [ ] Test on Wayland
- [ ] Test on X11
- [ ] Documentation