# Widget Menu Intent System - Implementation Plan

## Executive Summary

This plan addresses the issue where widgets opened from the pane header menu create new tabs instead of replacing the current pane's content. The solution introduces an intent-based system that allows widgets to declare their placement preferences while maintaining backward compatibility and supporting future plugin systems.

## Problem Statement

### Current Issue
When users select a widget from the pane header menu (e.g., Theme Editor, Keyboard Shortcuts), the widget opens in a new tab instead of replacing the current pane's content. This is inconsistent and confusing as:
- Some widgets (basic types) replace the pane content
- Other widgets (with `open_command`) create new tabs
- Users expect pane header actions to affect the current pane

### Root Causes
1. **Intent Ambiguity**: The system doesn't distinguish between "open in new tab" vs "replace current pane"
2. **Dual Command Paths**: Different code paths for widgets with/without `open_command`
3. **Context Unawareness**: Commands don't know they're being invoked from pane header vs menu bar

## Solution Architecture

### Core Concept: Widget Placement Intent

Introduce explicit intent metadata that allows widgets to declare how they should be opened in different contexts.

```python
class WidgetPlacement(Enum):
    NEW_TAB = "new_tab"          # Always create new tab
    REPLACE_CURRENT = "replace"   # Always replace current
    SMART = "smart"               # Context-aware decision
```

### Key Components

1. **Enhanced AppWidgetMetadata**: Add placement intent fields
2. **Context-Aware Commands**: Pass context source to commands
3. **Unified Menu Logic**: Single code path for all widget types
4. **Backward Compatibility**: Existing widgets continue to work

## Implementation Phases

### Phase 1: Add Intent Metadata (Immediate Fix)

#### 1.1 Enhance AppWidgetMetadata
**File**: `core/app_widget_metadata.py`

Add new fields:
```python
# Placement behavior
default_placement: WidgetPlacement = WidgetPlacement.SMART
supports_replacement: bool = True
supports_new_tab: bool = True

# Context-specific commands
commands: Dict[str, str] = field(default_factory=dict)
# Expected keys: "open_new_tab", "replace_pane", "open_smart"
```

#### 1.2 Create Placement Logic
**File**: `core/widget_placement.py` (new)

```python
from enum import Enum

class WidgetPlacement(Enum):
    NEW_TAB = "new_tab"
    REPLACE_CURRENT = "replace"
    SMART = "smart"

class CommandSource(Enum):
    MENU_BAR = "menu_bar"
    PANE_HEADER = "pane_header"
    COMMAND_PALETTE = "command_palette"
    KEYBOARD_SHORTCUT = "keyboard"

def determine_placement(metadata, source):
    """Determine where to place widget based on context."""
    if source == CommandSource.PANE_HEADER:
        return WidgetPlacement.REPLACE_CURRENT
    elif source == CommandSource.MENU_BAR:
        return WidgetPlacement.NEW_TAB
    else:
        return metadata.default_placement
```

### Phase 2: Update Pane Header Menu

#### 2.1 Fix Menu Widget Selection
**File**: `ui/widgets/pane_header.py`

Replace lines 188-196 with unified logic:
```python
# Always use replacement behavior in pane header context
action.triggered.connect(
    lambda checked, wm=widget_meta: self._handle_widget_selection(wm)
)

def _handle_widget_selection(self, widget_meta):
    """Handle widget selection with proper placement intent."""
    # Check for replace command first
    if "replace_pane" in widget_meta.commands:
        execute_command(widget_meta.commands["replace_pane"],
                       pane=self.parent(),
                       widget_id=widget_meta.widget_id)
    elif widget_meta.supports_replacement:
        # Use generic replacement for widgets that support it
        execute_command("workbench.action.replaceWidgetInPane",
                       pane=self.parent(),
                       widget_id=widget_meta.widget_id)
    else:
        # Fallback to opening in new tab if replacement not supported
        if widget_meta.open_command:
            execute_command(widget_meta.open_command)
```

### Phase 3: Add Replace Commands

#### 3.1 Create Generic Replace Command
**File**: `core/commands/builtin/pane_commands.py`

Add new command:
```python
@command(
    id="workbench.action.replaceWidgetInPane",
    title="Replace Widget in Pane",
    category="Panes",
    description="Replace current pane content with specified widget"
)
def replace_widget_in_pane_command(context: CommandContext) -> CommandResult:
    """Replace the current pane's widget with a new one."""
    widget_id = context.args.get('widget_id')
    pane = context.args.get('pane')

    if not widget_id:
        return CommandResult(success=False, error="No widget_id specified")

    # Get the split pane widget
    workspace = context.get_service(WorkspaceService).get_workspace()
    split_widget = workspace.get_current_split_widget()

    # Get the pane's ID from the PaneContent wrapper
    if hasattr(pane, 'pane_id'):
        pane_id = pane.pane_id

        # Use AppWidgetManager to create the widget
        manager = AppWidgetManager.get_instance()
        metadata = manager.get_widget(widget_id)

        if metadata:
            # Change the pane type using the model
            split_widget.model.change_pane_to_widget(pane_id, widget_id, metadata)
            split_widget.refresh_view()
            return CommandResult(success=True)

    return CommandResult(success=False, error="Could not replace widget")
```

#### 3.2 Add Widget-Specific Replace Commands
**File**: `core/commands/builtin/theme_commands.py`

Add replace command for Theme Editor:
```python
@command(
    id="theme.replaceInPane",
    title="Replace Pane with Theme Editor",
    category="Preferences",
    description="Replace current pane content with theme editor"
)
def replace_with_theme_editor_command(context: CommandContext) -> CommandResult:
    """Replace current pane with theme editor."""
    return replace_widget_in_pane_command(
        context.with_args(widget_id="com.viloapp.theme_editor")
    )
```

### Phase 4: Update Widget Registrations

#### 4.1 Update Built-in Widget Registrations
**File**: `core/app_widget_registry.py`

Update Theme Editor registration:
```python
manager.register_widget(AppWidgetMetadata(
    widget_id="com.viloapp.theme_editor",
    # ... existing fields ...

    # New intent fields
    default_placement=WidgetPlacement.SMART,
    supports_replacement=True,
    supports_new_tab=True,

    # Context-specific commands
    commands={
        "open_new_tab": "theme.openEditor",
        "replace_pane": "theme.replaceInPane",
    },

    open_command="theme.openEditor",  # Keep for backward compatibility
))
```

### Phase 5: Update Split Pane Model

#### 5.1 Add Widget Creation Support
**File**: `ui/widgets/split_pane_model.py`

Add method to change pane to specific widget:
```python
def change_pane_to_widget(self, pane_id: str, widget_id: str, metadata: AppWidgetMetadata) -> bool:
    """Change pane to specific AppWidget from manager."""
    leaf = self.find_leaf(pane_id)
    if not leaf:
        return False

    # Clean up old widget
    leaf.cleanup()

    # Create new widget using AppWidgetManager
    manager = AppWidgetManager.get_instance()
    app_widget = manager.create_widget(widget_id, metadata)

    if app_widget:
        leaf.app_widget = app_widget
        leaf.widget_type = metadata.widget_type
        app_widget.leaf_node = leaf
        return True

    return False
```

## Testing Plan

### Unit Tests
1. Test placement determination logic
2. Test command context passing
3. Test widget metadata validation

### Integration Tests
1. Test Theme Editor replacement in pane
2. Test Terminal replacement in pane
3. Test backward compatibility with old widgets

### Manual Testing
1. Open pane header menu
2. Select Theme Editor → Should replace current pane
3. Select from main menu → Should open new tab
4. Verify all widget types work correctly

## Migration Strategy

### Backward Compatibility
- Existing widgets without new metadata continue to work
- `open_command` field remains functional
- Gradual migration of widgets to new system

### Future Enhancements
1. **Phase 2**: Add user preferences for default placement
2. **Phase 3**: Support "Open to the Right/Below" options
3. **Phase 4**: Plugin system integration
4. **Phase 5**: Deprecate legacy WidgetRegistry

## Success Criteria

1. ✅ All widgets in pane header menu replace current pane content
2. ✅ Menu bar commands still create new tabs where appropriate
3. ✅ No breaking changes to existing functionality
4. ✅ Clear and consistent user experience
5. ✅ System ready for plugin integration

## Risk Assessment

### Low Risk
- Changes are mostly additive (new fields, new commands)
- Backward compatibility maintained
- Can be rolled back easily

### Mitigations
- Extensive testing before merge
- Feature flag for new behavior if needed
- Gradual rollout possible

## Timeline

- **Day 1**: Implement Phase 1-3 (Core functionality)
- **Day 2**: Implement Phase 4-5 (Widget updates)
- **Day 3**: Testing and refinement
- **Day 4**: Documentation and review

## Conclusion

This plan provides a systematic approach to fixing the widget menu issue while improving the overall architecture. The solution is extensible, maintains backward compatibility, and sets the foundation for future plugin systems.