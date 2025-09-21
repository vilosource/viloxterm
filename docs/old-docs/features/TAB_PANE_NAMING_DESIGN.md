# Tab & Pane Naming Design

## Overview

This document outlines the design for user-customizable tab and pane names in ViloApp, allowing users to replace generic identifiers (IDs, numbers) with meaningful names that improve navigation and organization.

## Problem Statement

Currently:
- Tabs show generic names like "Editor", "Terminal", "Welcome"
- Panes display technical IDs like "pane_a1b2c3"
- No way for users to customize these names
- Difficult to distinguish between multiple similar tabs/panes

Users need:
- Ability to rename tabs and panes with meaningful names
- Visual distinction between named and unnamed items
- Persistence of custom names across sessions
- Quick renaming methods (keyboard and mouse)

## Research: How Other Applications Handle This

### 1. VSCode - Tab Naming

**Behavior**:
- Tabs show filename by default
- Untitled files show "Untitled-1", "Untitled-2"
- Cannot directly rename tabs (tied to file)
- Shows path for disambiguation

**Unsaved Changes Indicator**:
- White dot for unsaved
- Italics for preview mode

### 2. Terminal Applications (iTerm2, Windows Terminal)

**Tab Naming**:
- Double-click to rename
- Right-click → Rename
- Shows process/directory by default
- Custom names persist

**Title Patterns**:
- Can use variables: `${task}`, `${cwd}`, `${profile}`
- Automatic titles based on running process

### 3. Tmux - Pane/Window Naming

**Commands**:
- `Ctrl+B ,` - Rename window
- `Ctrl+B $` - Rename session
- Names shown in status bar

**Automatic Naming**:
- Based on running process
- Updates dynamically

### 4. Browser Tabs

**Behavior**:
- Show page title
- Truncate long titles
- Show favicon for recognition
- Cannot manually rename

### 5. IDE Panels (IntelliJ, Eclipse)

**Features**:
- Panels have descriptive titles
- Some allow renaming (e.g., tool windows)
- Show content type icons
- Breadcrumbs for context

## Proposed Design for ViloApp

### Tab Naming

#### Default Names

```python
class TabNameGenerator:
    """Generate smart default names for tabs"""
    
    def generate_default_name(self, tab_type: str, content: Any) -> str:
        if tab_type == "editor":
            if content.has_file():
                return content.get_filename()  # "main.py"
            else:
                return f"Untitled-{self.untitled_counter}"
                
        elif tab_type == "terminal":
            if content.has_process():
                return content.get_process_name()  # "npm start"
            else:
                return f"Terminal {content.index}"
                
        elif tab_type == "output":
            return f"Output - {content.source}"  # "Output - Python"
            
        else:
            return tab_type.capitalize()
```

#### Renaming Methods

##### 1. Double-Click Rename (Primary)

```python
def on_tab_double_clicked(self, index: int):
    """Enable inline editing on double-click"""
    tab_rect = self.tab_widget.tabBar().tabRect(index)
    
    # Create inline editor
    editor = QLineEdit(self.tab_widget.tabBar())
    editor.setText(self.tab_widget.tabText(index))
    editor.setGeometry(tab_rect)
    editor.selectAll()
    
    # Connect signals
    editor.editingFinished.connect(
        lambda: self.finish_rename(index, editor.text())
    )
    editor.show()
    editor.setFocus()
```

##### 2. Context Menu Rename

```python
def show_tab_context_menu(self, pos):
    menu = QMenu()
    
    rename_action = QAction("Rename Tab", self)
    rename_action.setShortcut("F2")
    rename_action.triggered.connect(
        lambda: self.start_rename(index)
    )
    menu.addAction(rename_action)
    
    # Other actions...
    reset_name_action = QAction("Reset to Default Name", self)
    menu.addAction(reset_name_action)
```

##### 3. Keyboard Shortcut

- `F2` - Rename current tab (standard)
- `Ctrl+K, R, T` - Rename Tab command

#### Visual Design

```
Standard Tab:
┌──────────────┬──────────────┬──────────────┐
│ • main.py    │  Terminal 1  │  Output      │
└──────────────┴──────────────┴──────────────┘

Custom Named Tab:
┌──────────────┬──────────────┬──────────────┐
│ • main.py    │ 📝 API Server│  Output      │
└──────────────┴──────────────┴──────────────┘
        ↑              ↑
   File indicator  Custom name icon
```

### Pane Naming

#### Default Names

```python
class PaneNameGenerator:
    """Generate smart default names for panes"""
    
    def generate_default_name(self, pane: Pane) -> str:
        widget = pane.get_widget()
        
        if isinstance(widget, EditorWidget):
            if widget.has_file():
                return widget.get_filename()
            return f"Editor {pane.index}"
            
        elif isinstance(widget, TerminalWidget):
            if widget.has_title():
                return widget.get_title()
            return f"Terminal {pane.index}"
            
        else:
            return f"Pane {pane.index}"
```

#### Display Locations

##### 1. Pane Header (Primary)

```python
class PaneHeaderBar(QWidget):
    def __init__(self):
        # Replace ID label with name label
        self.name_label = QLabel()
        self.name_label.setStyleSheet("""
            QLabel {
                font-weight: bold;
                color: #cccccc;
            }
        """)
        
        # Add edit button (pencil icon)
        self.edit_button = QToolButton()
        self.edit_button.setIcon(QIcon("edit.svg"))
        self.edit_button.clicked.connect(self.start_rename)
```

##### 2. Status Bar

```
[Editor: main.py] [Terminal: npm start] [3 panes]
```

##### 3. Command Palette

```
> Focus Pane
  📝 main.py (Editor)
  🖥️ API Server (Terminal)
  📊 Output
```

#### Renaming Methods

##### 1. Inline Editing

```python
def start_rename_pane(self, pane_id: str):
    """Start inline rename for pane"""
    header = self.get_pane_header(pane_id)
    
    # Hide label, show editor
    header.name_label.hide()
    
    editor = QLineEdit(header)
    editor.setText(header.name_label.text())
    editor.selectAll()
    editor.editingFinished.connect(
        lambda: self.finish_rename_pane(pane_id, editor.text())
    )
    
    # Position where label was
    editor.setGeometry(header.name_label.geometry())
    editor.show()
    editor.setFocus()
```

##### 2. Command Palette

```
Command: Rename Current Pane
Shortcut: Ctrl+K, R, P
```

### Smart Naming Features

#### 1. Auto-Update Option

```python
class SmartNaming:
    """Intelligent name management"""
    
    def __init__(self):
        self.auto_update = True
        self.custom_names = {}  # Track user customizations
    
    def update_name(self, item_id: str, context: Dict):
        """Update name based on context"""
        if item_id in self.custom_names:
            # User renamed - don't auto-update
            return self.custom_names[item_id]
            
        if self.auto_update:
            # Generate contextual name
            if context['type'] == 'terminal':
                if context['process']:
                    return f"{context['process']} - {context['cwd']}"
            elif context['type'] == 'editor':
                if context['file']:
                    if context['modified']:
                        return f"• {context['file']}"
                    return context['file']
```

#### 2. Name Templates

```python
NAMING_TEMPLATES = {
    'terminal': {
        'default': '${type} ${index}',
        'process': '${process}',
        'directory': '${cwd}',
        'custom': '${name} - ${process}'
    },
    'editor': {
        'default': '${filename}',
        'path': '${relative_path}',
        'modified': '${modified_indicator} ${filename}'
    }
}
```

#### 3. Icon Support

```python
def get_icon_for_name(self, name: str, type: str) -> QIcon:
    """Return appropriate icon based on name/type"""
    
    # File type icons
    if name.endswith('.py'):
        return QIcon('python.svg')
    elif name.endswith('.js'):
        return QIcon('javascript.svg')
    
    # Process icons
    if 'npm' in name:
        return QIcon('npm.svg')
    elif 'git' in name:
        return QIcon('git.svg')
    
    # Default type icons
    return QIcon(f'{type}.svg')
```

### Persistence

#### Storage Format

```json
{
  "tabs": {
    "tab_uuid_1": {
      "custom_name": "API Server",
      "auto_update": false,
      "created": "2024-01-10T10:00:00Z"
    }
  },
  "panes": {
    "pane_uuid_1": {
      "custom_name": "Main Editor",
      "auto_update": true,
      "template": "${filename} - ${modified_indicator}"
    }
  }
}
```

#### Session Restoration

```python
def restore_names(self):
    """Restore custom names from settings"""
    settings = QSettings()
    
    # Restore tab names
    for tab_id, tab_data in self.tabs.items():
        if custom_name := settings.value(f'tabs/{tab_id}/name'):
            tab_data.set_custom_name(custom_name)
    
    # Restore pane names
    for pane_id, pane_data in self.panes.items():
        if custom_name := settings.value(f'panes/{pane_id}/name'):
            pane_data.set_custom_name(custom_name)
```

### UI/UX Guidelines

#### Visual Indicators

1. **Custom Named Items**
   - Italic or different color
   - Icon prefix (📝)
   - Tooltip showing original name

2. **Truncation**
   - Max width with ellipsis
   - Full name in tooltip
   - Middle truncation for files

3. **Validation**
   - No empty names
   - Max length (50 chars)
   - No special characters that break UI

#### Interaction Patterns

1. **Quick Rename**
   - F2 key standard
   - Double-click for mouse users
   - Escape to cancel

2. **Name Suggestions**
   - Recent names
   - Smart completions
   - Template variables

3. **Batch Operations**
   - Rename pattern: "Terminal *" → "Server *"
   - Reset all to defaults
   - Copy names between sessions

### Accessibility

#### Screen Reader Support

```python
def announce_rename(self, old_name: str, new_name: str):
    """Announce name change to screen readers"""
    QAccessible.updateAccessibility(
        QAccessibleEvent(
            self.widget,
            QAccessible.NameChanged,
            f"Renamed from {old_name} to {new_name}"
        )
    )
```

#### Keyboard Navigation

- Tab through renameable items
- F2 to start rename
- Enter to confirm
- Escape to cancel
- Tab to next item while renaming

### Configuration Options

```json
{
  "naming": {
    "tabs": {
      "auto_update": true,
      "show_icons": true,
      "max_length": 30,
      "template": "${type} - ${name}"
    },
    "panes": {
      "show_in_header": true,
      "show_in_overlay": true,
      "auto_number": true,
      "template": "${index}. ${name}"
    },
    "persistence": {
      "save_custom_names": true,
      "restore_on_startup": true
    }
  }
}
```

## Implementation Plan

### Phase 1: Basic Tab Renaming
1. Double-click to rename tabs
2. F2 keyboard shortcut
3. Persist custom names
4. Visual indicators

### Phase 2: Pane Naming
1. Add name to pane header
2. Replace ID with name
3. Rename functionality
4. Show in overlays

### Phase 3: Smart Features
1. Auto-update based on content
2. Name templates
3. Icon support
4. Batch operations

### Phase 4: Polish
1. Animations for rename
2. Name suggestions
3. Search by name
4. Name history

## Alternative Approaches Considered

### 1. Modal Dialog for Renaming
**Rejected**: Breaks flow, not as intuitive as inline

### 2. Always Show IDs
**Rejected**: Technical IDs not user-friendly

### 3. Auto-Generated Names Only
**Rejected**: Users need customization for organization

### 4. Sidebar for Name Management
**Rejected**: Too heavy, not discoverable

## Success Metrics

1. **Adoption**: >70% of users rename at least one tab/pane
2. **Retention**: Custom names used in >50% of sessions
3. **Efficiency**: <2 seconds to rename
4. **Discoverability**: Found within first session

## Future Enhancements

### Version 2.0
- **Emoji Support**: Use emojis in names
- **Color Coding**: Assign colors to names
- **Name Groups**: Group related tabs/panes

### Version 3.0
- **AI Naming**: Suggest names based on content
- **Voice Input**: "Rename this tab to Server"
- **Sync Names**: Share names across devices

## Example User Flows

### Flow 1: Renaming a Terminal Tab

1. User opens terminal tab (shows "Terminal 1")
2. Starts npm dev server
3. Double-clicks tab
4. Types "Dev Server"
5. Presses Enter
6. Tab now shows "📝 Dev Server"

### Flow 2: Using Templates

1. User opens settings
2. Sets terminal template to "${process} - ${cwd}"
3. Opens terminal in /project/api
4. Runs "npm start"
5. Tab automatically shows "npm start - /project/api"

### Flow 3: Batch Rename

1. User has 3 terminals: "Terminal 1", "Terminal 2", "Terminal 3"
2. Opens command palette
3. Runs "Rename All Terminals"
4. Enters pattern "Server ${index}"
5. Terminals renamed to "Server 1", "Server 2", "Server 3"

## Conclusion

The tab and pane naming system transforms generic identifiers into meaningful, user-controlled labels that significantly improve navigation and organization. By combining smart defaults, easy renaming methods, and persistent storage, users can organize their workspace in a way that matches their mental model.

The inline editing approach (double-click or F2) provides the most intuitive experience, while command palette integration ensures keyboard users have full access. Smart features like auto-updating and templates reduce manual work while preserving user customization.

This feature integrates seamlessly with the planned pane navigation system, where named panes will be easier to identify and jump to using keyboard shortcuts or overlay identifiers.