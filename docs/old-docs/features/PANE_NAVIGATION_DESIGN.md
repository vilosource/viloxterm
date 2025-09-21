# Pane Navigation & Identification Design

## Overview

This document outlines the design for pane identification and navigation features in ViloApp, enabling users to quickly identify and jump between split panes using keyboard shortcuts. This feature is planned for future implementation after the core keyboard infrastructure is in place.

## Problem Statement

When users have multiple split panes open, they need:
1. A way to visually identify which pane is which
2. Quick keyboard navigation between panes
3. Direct jumping to specific panes
4. Clear indication of the active pane

## Research: How Other Software Handles This

### 1. Tmux - Overlay Numbers
**Activation**: `Ctrl+B, q`

**Behavior**:
- Large numbers appear overlaid on each pane
- Numbers are displayed for 1-3 seconds
- Pressing a number jumps to that pane
- Clean, temporary visual

```
┌─────────────┬─────────────┐
│             │             │
│      0      │      1      │
│             │             │
├─────────────┼─────────────┤
│             │             │
│      2      │      3      │
│             │             │
└─────────────┴─────────────┘
```

**Pros**: Clear, unobtrusive, intuitive
**Cons**: Temporarily obscures content

### 2. Vim/Neovim - Window Numbers
**Built-in Commands**:
- `Ctrl+W, W` - Cycle through windows
- `Ctrl+W, [number]` - Jump to window N
- `Ctrl+W, [hjkl]` - Move directionally

**Plugins** (e.g., vim-choosewin):
- Shows letter overlays
- Single key to jump

**Pros**: Multiple navigation methods
**Cons**: Numbers not always visible

### 3. Emacs - Ace Window
**Behavior**:
- Shows letters in window corners
- Single keypress to jump
- Customizable positions and characters

```
┌─[a]─────────┬─[b]─────────┐
│             │             │
│   Buffer 1  │   Buffer 2  │
│             │             │
├─[c]─────────┼─[d]─────────┤
│             │             │
│   Buffer 3  │   Buffer 4  │
└─────────────┴─────────────┘
```

**Pros**: Minimal visual intrusion
**Cons**: Small identifiers might be hard to see

### 4. VSCode - Focus Groups
**Navigation**:
- `Ctrl+K, Ctrl+Arrow` - Focus by direction
- `Ctrl+1-9` - Focus editor group N
- No visual identifiers by default

**Pros**: Clean interface
**Cons**: No visual reference for panes

### 5. IntelliJ IDEA - Switcher
**Behavior**:
- `Ctrl+Tab` shows switcher dialog
- Numbered list of open files/panes
- Preview on hover

**Pros**: Rich information
**Cons**: Modal dialog blocks view

### 6. i3/Sway Window Managers
**Features**:
- `$mod+Arrow` - Directional focus
- Named marks for windows
- Visual focus indicators via borders

**Pros**: Flexible marking system
**Cons**: Requires manual marking

## Proposed Design for ViloApp

### Primary Method: Overlay Identifiers (Tmux-style)

#### Activation
- **Primary**: `Ctrl+W, Q` (Vim-like)
- **Alternative**: `Ctrl+K, P` (VSCode-like, P for "Pane")

#### Visual Design

```
┌───────────────────────────────────────┐
│              Editor Pane               │
│                                        │
│          ╔═══════════════╗            │
│          ║               ║            │
│          ║       1       ║            │
│          ║               ║            │
│          ╚═══════════════╝            │
│                                        │
└───────────────────────────────────────┘
```

#### Overlay Specifications

```python
class PaneOverlaySpec:
    # Visual properties
    background_color = "rgba(0, 0, 0, 0.7)"
    text_color = "#FFFFFF"
    border_color = "#007ACC"
    border_width = 2
    border_radius = 8
    
    # Size and position
    width = 100  # pixels
    height = 100  # pixels
    position = "center"  # center, top-left, top-right, etc.
    
    # Typography
    font_size = 48  # pixels
    font_weight = "bold"
    font_family = "system-ui"
    
    # Behavior
    timeout_ms = 3000  # auto-hide after 3 seconds
    fade_in_ms = 150
    fade_out_ms = 150
    
    # Identifier style
    identifier_type = "numbers"  # numbers, letters, or smart
    start_from = 1  # 1-indexed for numbers
```

#### Implementation Sketch

```python
class PaneIdentifierOverlay(QWidget):
    """Overlay system for pane identification"""
    
    def __init__(self):
        super().__init__()
        self.overlays = []
        self.active = False
        self.timeout_timer = QTimer()
        
    def show_identifiers(self):
        """Display identifiers on all panes"""
        if self.active:
            return
            
        self.active = True
        panes = self.workspace.get_all_panes()
        
        for index, pane in enumerate(panes):
            overlay = self.create_overlay(pane, index)
            overlay.show()
            self.overlays.append(overlay)
        
        # Set timeout for auto-hide
        self.timeout_timer.timeout.connect(self.hide_identifiers)
        self.timeout_timer.start(3000)
        
        # Connect keyboard handler
        self.grabKeyboard()
    
    def create_overlay(self, pane, index):
        """Create a single overlay widget"""
        overlay = QWidget(pane)
        overlay.setStyleSheet(self.get_overlay_style())
        
        # Create label with identifier
        label = QLabel(self.get_identifier(index), overlay)
        label.setAlignment(Qt.AlignCenter)
        
        # Position in center of pane
        self.position_overlay(overlay, pane)
        
        # Add fade-in animation
        self.animate_fade_in(overlay)
        
        return overlay
    
    def keyPressEvent(self, event):
        """Handle key press for pane selection"""
        key = event.text()
        
        if key.isdigit():
            pane_index = int(key) - 1
            if 0 <= pane_index < len(self.overlays):
                self.focus_pane(pane_index)
                self.hide_identifiers()
        elif event.key() == Qt.Key_Escape:
            self.hide_identifiers()
    
    def hide_identifiers(self):
        """Hide all overlay identifiers"""
        for overlay in self.overlays:
            self.animate_fade_out(overlay)
        self.overlays.clear()
        self.active = False
        self.releaseKeyboard()
```

### Secondary Method: Directional Navigation

#### Vim-style Navigation
- `Ctrl+W, H` - Focus left pane
- `Ctrl+W, J` - Focus down pane
- `Ctrl+W, K` - Focus up pane
- `Ctrl+W, L` - Focus right pane

#### VSCode-style Navigation
- `Ctrl+K, Ctrl+Left` - Focus left pane
- `Ctrl+K, Ctrl+Down` - Focus down pane
- `Ctrl+K, Ctrl+Up` - Focus up pane
- `Ctrl+K, Ctrl+Right` - Focus right pane

#### Arrow Key Navigation
- `Alt+Left` - Focus left pane
- `Alt+Down` - Focus down pane
- `Alt+Up` - Focus up pane
- `Alt+Right` - Focus right pane

### Tertiary Method: Direct Access

#### Number Keys
- `Ctrl+1` through `Ctrl+9` - Jump to pane N
- Uses MRU (Most Recently Used) or spatial ordering

#### Named Panes (Future)
- User can assign names to panes
- `Ctrl+K, N` - Name current pane
- `Ctrl+K, G` - Go to named pane

### Additional Navigation Features

#### Cycle Navigation
- `Ctrl+W, W` - Cycle forward through panes
- `Ctrl+W, Shift+W` - Cycle backward through panes

#### History Navigation
- `Ctrl+W, O` - Go to previous pane (like Alt+Tab)
- Maintains history stack of focused panes

#### Pane Swapping
- `Ctrl+W, X` - Swap with next pane
- `Ctrl+W, Shift+H/J/K/L` - Swap in direction

## Visual Indicators

### Active Pane Indication
1. **Border Highlight** - Colored border on active pane
2. **Header Accent** - Highlighted pane header
3. **Opacity** - Slightly dim inactive panes (optional)

### Focus Trail (Optional)
- Brief animation showing focus movement
- Helps track where focus went

## Accessibility Features

### Screen Reader Support
```python
def announce_pane_focus(pane):
    """Announce pane information to screen readers"""
    announcement = f"Focused on pane {pane.index + 1} of {total_panes}"
    if pane.has_title():
        announcement += f", {pane.title}"
    announcement += f", {pane.content_type}"
    
    # Send to screen reader
    QAccessible.updateAccessibility(
        QAccessibleEvent(pane, QAccessible.Focus)
    )
```

### High Contrast Mode
- Ensure identifiers are visible in all themes
- Use patterns/shapes in addition to colors
- Sufficient contrast ratios (WCAG AAA)

### Keyboard-Only Operation
- All features accessible without mouse
- Clear focus indicators
- Escape key always cancels

## Configuration Options

```json
{
  "panes.identifiers": {
    "enabled": true,
    "style": "numbers",          // numbers | letters | smart
    "position": "center",         // center | topLeft | topRight | bottomLeft | bottomRight
    "size": "large",             // small | medium | large
    "timeout": 3000,             // milliseconds, 0 for no timeout
    "opacity": 0.9,              // 0.0 - 1.0
    "animation": true,           // enable fade animations
    "startFrom": 1               // 0 or 1 for zero/one-indexed
  },
  
  "panes.navigation": {
    "wrapAround": true,          // wrap at edges when navigating
    "mruOrder": false,           // use MRU vs spatial ordering
    "followFocus": true,         // auto-scroll to show focused pane
    "animateFocus": true         // animate focus transitions
  },
  
  "panes.appearance": {
    "dimInactive": false,        // dim inactive panes
    "inactiveOpacity": 0.8,      // opacity for inactive panes
    "borderWidth": 2,            // active pane border width
    "borderColor": "#007ACC"     // active pane border color
  }
}
```

## Smart Identifiers (Future Enhancement)

Instead of just numbers, use content-aware identifiers:

```python
def get_smart_identifier(pane):
    """Generate meaningful identifier based on content"""
    if pane.is_terminal():
        return f"T{pane.terminal_index}"  # T1, T2, etc.
    elif pane.is_editor():
        if pane.has_file():
            # Use file extension or name initial
            ext = pane.file_extension()
            return ext[:2].upper()  # PY, JS, MD, etc.
        return f"E{pane.editor_index}"
    elif pane.is_output():
        return "OUT"
    elif pane.is_problems():
        return "PRB"
    else:
        return str(pane.index + 1)
```

## Performance Considerations

### Optimization Strategies

1. **Lazy Creation**
   - Only create overlays when shown
   - Reuse overlay widgets when possible

2. **Efficient Updates**
   - Cache pane positions
   - Update only on layout changes

3. **Lightweight Overlays**
   - Use simple widgets
   - Minimal styling
   - No complex layouts

### Memory Management

```python
class OverlayPool:
    """Pool overlay widgets for reuse"""
    def __init__(self, max_size=20):
        self.pool = []
        self.max_size = max_size
    
    def acquire(self):
        if self.pool:
            return self.pool.pop()
        return PaneOverlay()
    
    def release(self, overlay):
        if len(self.pool) < self.max_size:
            overlay.reset()
            self.pool.append(overlay)
        else:
            overlay.deleteLater()
```

## Implementation Phases

### Phase 1: Basic Overlay System
- Number overlays (1-9)
- Center positioning
- 3-second timeout
- Keyboard activation

### Phase 2: Directional Navigation
- Vim-style commands
- VSCode-style commands
- Arrow key navigation
- Wrap-around option

### Phase 3: Enhanced Features
- Letter identifiers
- Position options
- Animation effects
- Configuration UI

### Phase 4: Advanced Features
- Smart identifiers
- Named panes
- History navigation
- Pane swapping

## Testing Strategy

### Unit Tests
- Overlay creation and positioning
- Identifier generation
- Keyboard handling
- Navigation logic

### Integration Tests
- Multi-pane scenarios
- Rapid activation/deactivation
- Theme compatibility
- Performance with many panes

### User Testing
- Discoverability
- Learning curve
- Efficiency gains
- Accessibility

## Alternative Approaches Considered

### 1. Persistent Badges
- Always visible numbers in pane headers
- **Rejected**: Visual clutter

### 2. Mini-map
- Small overview showing all panes
- **Rejected**: Too complex, uses screen space

### 3. Command Palette Navigation
- List panes in command palette
- **Kept as secondary**: Good for many panes

### 4. Mouse Gestures
- Middle-click to show identifiers
- **Rejected**: Not keyboard-focused

## Success Metrics

1. **Discoverability**: Users find feature within first session
2. **Speed**: <100ms to show overlays
3. **Accuracy**: >95% successful pane selections
4. **Adoption**: >50% of users use it regularly
5. **Accessibility**: Works with all screen readers

## Future Enhancements

### Version 2.0
- **Pane Groups**: Color-code related panes
- **Pane Layouts**: Save/restore arrangements
- **Smart Suggestions**: AI predicts next pane

### Version 3.0
- **Voice Control**: "Focus terminal pane"
- **Touch Gestures**: Swipe between panes
- **Remote Control**: Navigate from mobile app

## Conclusion

The overlay identifier system, inspired by tmux, provides an elegant solution for pane navigation that is:
- **Intuitive**: Large, clear numbers
- **Unobtrusive**: Only visible when needed
- **Efficient**: Single keypress to jump
- **Accessible**: Works for all users
- **Flexible**: Multiple navigation methods

Combined with directional navigation and direct access shortcuts, this creates a comprehensive pane navigation system that scales from 2 to 20+ panes while remaining fast and intuitive.

The implementation fits naturally into the planned command system architecture, with pane navigation commands registered in the command registry and shortcuts managed by the keyboard service.