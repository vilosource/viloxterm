# Chrome Mode Implementation & Debugging Guide

This document captures learnings, patterns, and best practices from implementing and debugging Chrome mode in the ViloApp application.

## Overview

Chrome mode provides a frameless window experience with tabs integrated into the title bar, similar to modern browsers. The implementation involves careful synchronization between the workspace data model and the Chrome UI components.

## Architecture

### Core Components

```
ChromeMainWindow
├── ChromeTitleBar (UI component)
│   ├── Tab widgets
│   ├── Window controls (min/max/close)
│   └── Menu button
├── Workspace (data model)
│   ├── QTabWidget (hidden in Chrome mode)
│   ├── Tab data structure
│   └── Signals (tab_added, tab_removed, etc.)
└── Synchronization layer
    ├── Signal connections
    └── Event handlers
```

### Key Files
- `ui/chrome_main_window.py` - Main Chrome window implementation
- `ui/widgets/chrome_title_bar_fixed.py` - Chrome title bar widget
- `ui/workspace_simple.py` - Workspace data model
- `services/workspace_service.py` - Business logic layer
- `core/commands/builtin/file_commands.py` - New tab commands

## Common Issues and Solutions

### 1. Tab Synchronization Problems

**Symptoms:**
- New tabs appear in workspace but not in Chrome title bar
- Tab counts don't match between workspace and Chrome UI
- Tabs persist after restart but don't show in Chrome UI during session

**Root Cause:**
Missing signal connections between workspace model and Chrome UI components.

**Solution Pattern:**
```python
def _setup_tab_synchronization(self):
    """Set up synchronization between workspace tabs and Chrome title bar."""
    if not hasattr(self.workspace, 'tab_added'):
        logger.warning("Workspace missing required signals")
        return
    
    # Connect workspace signals to Chrome title bar updates
    self.workspace.tab_added.connect(self.on_workspace_tab_added)
    self.workspace.tab_removed.connect(self.on_workspace_tab_removed)
    
def on_workspace_tab_added(self, name: str):
    """Handle when a new tab is added to the workspace."""
    index = self.chrome_title_bar.add_tab(name)
    self.chrome_title_bar.set_current_tab(index)
```

**Key Learnings:**
- Always set up bi-directional synchronization between data model and UI
- Use Qt signals/slots for loose coupling
- Connect signals in initialization, not just during initial transfer
- Handle both adding and removing tabs

### 2. Command Pattern Violations

**Symptoms:**
- Direct UI manipulation bypassing the command system
- Inconsistent behavior between different action triggers
- Chrome tabs not updating when commands are executed

**Solution Pattern:**
Ensure all user actions go through the command system:
```python
# ❌ Wrong - Direct UI manipulation
self.chrome_title_bar.add_tab("Terminal 1")

# ✅ Correct - Through command system
execute_command("file.newTerminalTab")
```

**Key Learnings:**
- Every user action MUST go through commands
- Commands should update services, not UI directly
- Services emit signals that UI components listen to
- Never bypass the MVC architecture

### 3. Signal Signature Mismatches

**Symptoms:**
- Signal connections fail silently
- Handler methods not being called
- Type errors in signal handlers

**Common Issue:**
```python
# Signal definition
tab_removed = Signal(str)  # Only emits name

# Wrong handler signature
def on_workspace_tab_removed(self, name: str, index: int):  # ❌ Too many params

# Correct handler signature  
def on_workspace_tab_removed(self, name: str):  # ✅ Matches signal
```

**Key Learnings:**
- Always verify signal signatures match handler signatures
- Use Qt Designer or documentation to check signal parameters
- Test signal connections with simple debug prints

### 4. Initialization Order Issues

**Symptoms:**
- Chrome mode not applying correctly
- Missing title bar or workspace
- Signals not connecting

**Solution Pattern:**
```python
def __init__(self):
    # 1. Store Chrome mode preference FIRST
    self.chrome_mode_enabled = self._load_chrome_mode_preference()
    
    # 2. Initialize parent (creates workspace)
    super().__init__()
    
    # 3. Apply Chrome modifications LAST
    if self.chrome_mode_enabled:
        self._apply_chrome_style()

def _apply_chrome_style(self):
    # 1. Create Chrome UI components
    # 2. Transfer existing tabs
    # 3. Set up synchronization
    # 4. Connect signals
```

**Key Learnings:**
- Order matters in Qt widget initialization
- Parent initialization must complete before Chrome modifications
- Set up synchronization after all components exist

## Debugging Strategies

### 1. Enable Comprehensive Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Add specific loggers for Chrome components
logger = logging.getLogger(__name__)
logger.info("Chrome tab added: %s", tab_name)
```

### 2. Verify Signal Connections

```python
def _setup_tab_synchronization(self):
    if not hasattr(self.workspace, 'tab_added'):
        logger.error("Missing tab_added signal!")
        return
    
    # Test signal emission
    self.workspace.tab_added.connect(
        lambda name: logger.info(f"Signal received: {name}")
    )
```

### 3. Check Component States

```python
def debug_chrome_state(self):
    """Debug helper to check Chrome component states."""
    workspace_tabs = self.workspace.tab_widget.count() if self.workspace else 0
    chrome_tabs = self.chrome_title_bar.tab_count() if hasattr(self.chrome_title_bar, 'tab_count') else 0
    
    logger.info(f"State: workspace={workspace_tabs}, chrome={chrome_tabs}")
    return workspace_tabs == chrome_tabs
```

### 4. Write Automated Tests

```python
def test_chrome_tab_sync():
    """Test Chrome tab synchronization."""
    # Enable Chrome mode
    settings = QSettings()
    settings.setValue("UI/ChromeMode", True)
    
    # Create window and execute command
    window = ChromeMainWindow()
    execute_command("file.newTerminalTab")
    
    # Verify synchronization
    assert window.workspace.tab_widget.count() == window.chrome_title_bar.tab_count()
```

## Best Practices

### 1. MVC Compliance
- **Commands** trigger business logic in **Services**
- **Services** update data models and emit notifications
- **UI Components** listen to service notifications and update display
- Never allow UI-to-UI direct communication

### 2. Signal Management
- Connect signals in component initialization
- Use descriptive signal names (`tab_added`, not `changed`)
- Handle both positive and negative cases (`added`/`removed`)
- Verify signal signatures match handler signatures

### 3. State Synchronization
- Always implement bi-directional sync
- Use the data model as the source of truth
- UI components should be reactive, not proactive
- Handle edge cases (empty states, single tabs, etc.)

### 4. Error Handling
- Add defensive checks for missing components
- Log warnings for missing signals or methods
- Gracefully degrade if Chrome components unavailable
- Use `hasattr()` checks before accessing dynamic properties

### 5. Testing Strategy
- Write integration tests for command → service → UI flow
- Test both Chrome and regular modes
- Verify state persistence across app restarts
- Mock Qt components for unit tests

## Common Gotchas

### 1. Qt Widget Lifecycle
- Parent widgets must exist before children
- Signal connections only work after widget initialization
- Calling `show()` too early can cause layout issues

### 2. Settings Persistence
- Chrome mode preference must be loaded before UI creation
- Use `QSettings.sync()` to ensure immediate persistence
- Clear settings in tests to avoid state contamination

### 3. Resource Management
- Chrome mode creates additional UI components
- Clean up signal connections on window close
- Handle terminal server shutdown gracefully

### 4. Cross-Platform Considerations
- Frameless windows behave differently on each platform
- Window controls may need platform-specific styling
- Test resize and move behaviors on all target platforms

## Troubleshooting Checklist

When Chrome mode issues occur:

- [ ] Is Chrome mode enabled in settings?
- [ ] Are all required signals defined in workspace?
- [ ] Are signal handlers connected in initialization?
- [ ] Do signal signatures match handler signatures?
- [ ] Is the command system being used correctly?
- [ ] Are services emitting notifications?
- [ ] Is initialization order correct?
- [ ] Are defensive checks in place for missing components?
- [ ] Is logging enabled to trace execution flow?
- [ ] Have you tested with both Chrome and regular modes?

## Future Improvements

### Potential Enhancements
- Add tab reordering support
- Implement tab context menus
- Add tab close buttons
- Support for tab icons
- Keyboard navigation between tabs
- Tab overflow handling for many tabs

### Architecture Improvements
- Create a dedicated `ChromeSyncService` for better separation
- Add tab state observers pattern
- Implement undo/redo for tab operations
- Add tab grouping/workspace features

## Related Documentation
- [PROJECT.md](../PROJECT.md) - Overall application specification
- [IMPLEMENTATION_GUIDE.md](../IMPLEMENTATION_GUIDE.md) - Development guidelines
- [TESTING_STRATEGY.md](../TESTING_STRATEGY.md) - Testing approaches
- [Chrome Title Bar Widget](../ui/widgets/chrome_title_bar_fixed.py) - Implementation details

---

**Last Updated:** September 2025  
**Contributors:** Development Team  
**Status:** Living document - update as new issues and solutions are discovered