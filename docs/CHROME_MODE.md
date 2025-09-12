# Chrome-Style Tab Bar Feature

## Overview
ViloApp now supports a Chrome-style UI mode where tabs are integrated into the title bar, similar to Google Chrome and other modern browsers. This saves vertical screen space and provides a cleaner, more modern interface.

## Features

### Chrome Mode Includes:
- **Integrated Tab Bar**: Tabs appear in the title bar area, saving ~30-40px of vertical space
- **Custom Window Controls**: Minimize, maximize/restore, and close buttons styled like Chrome
- **Frameless Window**: Clean edges without traditional window decorations
- **Window Dragging**: Click and drag on empty title bar space to move the window
- **Resize Handles**: Invisible 8px borders for resizing from any edge or corner
- **Double-Click to Maximize**: Double-click empty title bar space to maximize/restore
- **State Persistence**: Window position, size, and maximized state are saved

### Visual Comparison:
- **Traditional Mode**: Separate title bar, menu bar, and tab bar (3 rows)
- **Chrome Mode**: Combined title and tab bar with integrated controls (1 row)

## How to Enable Chrome Mode

### Method 1: Through the UI
1. Launch the application normally
2. Go to **View** menu → **Enable Chrome-Style Tabs**
3. Restart the application when prompted
4. The app will restart with Chrome-style tabs

### Method 2: Command Palette
1. Press `Ctrl+Shift+P` to open command palette
2. Type "chrome" and select "Enable Chrome Mode"
3. Restart when prompted

### Method 3: Programmatically
```python
from PySide6.QtCore import QSettings
settings = QSettings("ViloApp", "ViloApp")
settings.setValue("UI/ChromeMode", True)
```

## How to Disable Chrome Mode

### Through the UI:
1. In Chrome mode, tabs hide the menu bar by default
2. Press `Ctrl+Shift+M` to show the menu bar temporarily
3. Go to **View** menu → Uncheck **Enable Chrome-Style Tabs**
4. Restart the application

### Via Command:
Use the command palette (`Ctrl+Shift+P`) and search for "Disable Chrome Mode"

## Technical Implementation

### Architecture
The Chrome mode implementation consists of several key components:

1. **WindowControls** (`ui/widgets/window_controls.py`)
   - Custom minimize, maximize, and close buttons
   - Platform-aware button ordering
   - Hover and click effects matching Chrome's style

2. **ChromeTitleBar** (`ui/widgets/chrome_title_bar.py`)
   - Integrated tab bar and window controls
   - Drag region handling for window movement
   - New tab button (+) like Chrome
   - Tab management (add, remove, rename)

3. **ChromeMainWindow** (`ui/chrome_main_window.py`)
   - Frameless window implementation
   - Custom resize handling from edges/corners
   - Window state management (maximize/restore)
   - Integration with existing MainWindow functionality

### Key Features:
- **Frameless Window**: Uses `Qt.FramelessWindowHint` for borderless design
- **Custom Resize**: 8px invisible borders detect mouse for resizing
- **Drag Regions**: Smart detection of draggable vs interactive areas
- **State Saving**: Full window geometry and state persistence

## Customization

### Styling
The Chrome mode appearance can be customized through the theme system:
- Window control colors and hover effects
- Tab appearance and animations
- Title bar background color
- Border and shadow styles

### Configuration
Future enhancements may include:
- Configurable title bar height
- Option to show/hide menu button
- Custom tab width limits
- Animation speed controls

## Platform Considerations

### Windows
- Window controls appear on the right
- Supports Windows Aero Snap
- Native window shadow effects

### Linux
- Window controls on the right (follows most Linux DEs)
- Compatible with various window managers
- May require compositor for shadows

### macOS (Future)
- Traffic light buttons on the left
- Native macOS window behavior
- Platform-specific adjustments

## Known Limitations

1. **Menu Bar Access**: In Chrome mode, the menu bar is hidden by default. Use `Ctrl+Shift+M` to toggle it.
2. **Restart Required**: Switching between modes requires application restart.
3. **Theme Compatibility**: Some third-party themes may need adjustments for Chrome mode.

## Troubleshooting

### Window Controls Not Responding
- Ensure Chrome mode is fully enabled (check settings)
- Restart the application after enabling
- Check for conflicting window manager settings on Linux

### Tabs Not Visible
- Verify Chrome mode is enabled in settings
- Check if traditional tab bar is hidden
- Ensure window is not in fullscreen mode

### Cannot Resize Window
- Move cursor to window edges (8px border)
- Look for resize cursor indicators
- Check if window is maximized (unmaximize first)

## Future Enhancements

Planned improvements for Chrome mode:
- [ ] Menu button (hamburger menu) in title bar
- [ ] Tab preview on hover
- [ ] Tab grouping and coloring
- [ ] Vertical tab option
- [ ] Custom new tab page
- [ ] Tab search functionality
- [ ] Session management (save/restore tab sets)

## Related Commands

- `ui.toggleChromeMode` - Toggle Chrome mode on/off
- `ui.enableChromeMode` - Enable Chrome mode
- `ui.disableChromeMode` - Disable Chrome mode
- `view.toggleMenuBar` - Show/hide menu bar (Ctrl+Shift+M)

## Development

To work on Chrome mode features:

1. Key files to modify:
   - `ui/widgets/chrome_title_bar.py` - Tab bar behavior
   - `ui/widgets/window_controls.py` - Window button styling
   - `ui/chrome_main_window.py` - Window management

2. Testing Chrome mode:
   ```bash
   python test_chrome_mode.py  # Component test
   python main.py              # Full application test
   ```

3. Debugging:
   - Check `QSettings` for saved preferences
   - Monitor resize/drag events in ChromeMainWindow
   - Verify signal connections in ChromeTitleBar