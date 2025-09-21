# Theme Editor Implementation Plan

## Overview
The Theme Editor is an advanced AppWidget that provides a visual interface for creating, modifying, and managing themes in ViloxTerm. It follows the established AppWidget pattern and integrates seamlessly with the existing theme management system.

## Original Vision (from Phase 6 of THEME_MANAGEMENT_SYSTEM.md)
As specified in the original plan:
- **Color picker for each property** - Visual selection of 100+ theme colors
- **Live preview** - See changes immediately in the application
- **Save as new theme** - Create custom themes based on existing ones
- **Export functionality** - Share themes with others

## Architecture

### Component Structure
```
ui/widgets/
├── theme_editor_app_widget.py    # Main theme editor widget
├── color_picker_widget.py        # Custom color picker component
└── theme_preview_widget.py       # Live preview component

ui/dialogs/
└── theme_export_dialog.py        # Export/import dialog

core/commands/builtin/
└── theme_editor_commands.py      # Theme editor commands

tests/
├── gui/test_theme_editor.py      # GUI tests
└── unit/test_color_picker.py     # Unit tests
```

## Detailed Implementation

### 1. Theme Editor AppWidget (`theme_editor_app_widget.py`)

#### Purpose
Central widget that orchestrates the entire theme editing experience. Provides intuitive interface for modifying 100+ theme properties organized by category.

#### Features
- Three-panel layout (categories, properties, preview)
- Search/filter for color properties
- Undo/redo support for changes
- Base theme selection dropdown
- Theme metadata editing (name, author, description)
- Dirty state tracking with unsaved changes warning

#### Visual Layout
```
┌─────────────────────────────────────────────────────────────────┐
│ Theme: [My Custom Theme                    ] Based on: [VSCode Dark ▼] │
│ [Save] [Save As...] [Export] [Import] [Reset] [Undo] [Redo]    │
├──────────────┬──────────────────────┬──────────────────────────┤
│ Categories   │ Properties           │ Live Preview              │
│              │                      │                           │
│ ▼ Editor     │ Background           │ ┌───────────────────────┐ │
│   ▸ Syntax   │ [#1e1e1e] [▓]       │ │ Editor Area           │ │
│   ▸ Gutter   │ ○ Inherited          │ │                       │ │
│              │                      │ │ function hello() {    │ │
│ ▸ Activity   │ Foreground           │ │   return "world";     │ │
│ ▸ Sidebar    │ [#d4d4d4] [▓]       │ │ }                     │ │
│ ▸ Status Bar │ ● Modified           │ └───────────────────────┘ │
│ ▸ Terminal   │                      │                           │
│ ▸ Tabs       │ Line Highlight       │ ┌───────────────────────┐ │
│ ▸ Buttons    │ [#2a2a2a] [▓]       │ │ Terminal              │ │
│ ▸ Lists      │ ○ Inherited          │ │ $ npm run dev         │ │
│ ▸ Inputs     │                      │ │ Server started...     │ │
│ ▸ Menus      │ Selection Background │ └───────────────────────┘ │
│              │ [#264f78] [▓]       │                           │
│ [Search...] │ ● Modified           │ [Status Bar Preview    ] │
└──────────────┴──────────────────────┴──────────────────────────┘
```

#### Key Implementation Details

```python
class ThemeEditorAppWidget(AppWidget):
    """Theme editor widget for visual theme customization."""

    def __init__(self, widget_id: str, parent=None):
        super().__init__(widget_id, WidgetType.THEME_EDITOR, parent)

        # State management
        self.current_theme = None
        self.base_theme = None
        self.modified_colors = {}
        self.undo_stack = []
        self.redo_stack = []

        # UI components
        self.category_tree = None
        self.property_list = None
        self.preview_widget = None
        self.search_input = None

        self._init_ui()
        self._load_current_theme()

    def _init_ui(self):
        """Initialize the three-panel layout."""
        # Main horizontal splitter
        splitter = QSplitter(Qt.Horizontal)

        # Left: Category tree (25% width)
        self.category_tree = self._create_category_tree()

        # Middle: Property list (35% width)
        self.property_panel = self._create_property_panel()

        # Right: Live preview (40% width)
        self.preview_widget = ThemePreviewWidget()

        splitter.addWidget(self.category_tree)
        splitter.addWidget(self.property_panel)
        splitter.addWidget(self.preview_widget)
        splitter.setSizes([250, 350, 400])

    def _create_category_tree(self):
        """Create hierarchical category tree."""
        tree = QTreeWidget()
        tree.setHeaderLabel("Categories")

        # Build category structure from ThemeColors constants
        categories = self._organize_theme_properties()

        for category, subcategories in categories.items():
            cat_item = QTreeWidgetItem([category])
            for subcat in subcategories:
                sub_item = QTreeWidgetItem([subcat])
                cat_item.addChild(sub_item)
            tree.addTopLevelItem(cat_item)

        return tree

    def _create_property_panel(self):
        """Create scrollable property list."""
        # Property list with color pickers
        # Search bar at top
        # Filter by modified/inherited

    def apply_color_change(self, property_key: str, color: str):
        """Apply color change with live preview."""
        # Track in modified_colors
        self.modified_colors[property_key] = color

        # Add to undo stack
        self.undo_stack.append((property_key, self.current_theme.colors.get(property_key)))

        # Apply to preview
        self.preview_widget.update_color(property_key, color)

        # Optionally apply to main app (preview mode)
        if self.live_preview_enabled:
            self._apply_preview_to_app()
```

### 2. Color Picker Widget (`color_picker_widget.py`)

#### Purpose
Reusable color selection component that provides both inline and popup color picking functionality.

#### Features
- Compact inline display (color swatch + hex value)
- Click to open advanced picker
- Hex input with validation
- RGB/HSL/HSV modes
- Recently used colors
- Eyedropper tool for screen color picking
- Alpha channel support (optional)

#### Implementation

```python
class ColorPickerWidget(QWidget):
    """Inline color picker with popup dialog."""

    color_changed = Signal(str)  # Emits hex color string

    def __init__(self, initial_color: str = "#000000", allow_alpha: bool = False):
        super().__init__()
        self.current_color = QColor(initial_color)
        self.allow_alpha = allow_alpha

        # Inline layout: [swatch] [hex input]
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Color swatch button
        self.swatch_btn = QPushButton()
        self.swatch_btn.setFixedSize(24, 24)
        self.swatch_btn.clicked.connect(self.show_picker)
        self._update_swatch()

        # Hex input
        self.hex_input = QLineEdit(initial_color)
        self.hex_input.setMaximumWidth(80)
        self.hex_input.editingFinished.connect(self._on_hex_changed)

        layout.addWidget(self.swatch_btn)
        layout.addWidget(self.hex_input)
        layout.addStretch()

    def show_picker(self):
        """Show advanced color picker dialog."""
        dialog = AdvancedColorDialog(self.current_color, self)
        dialog.add_recent_colors(self._get_recent_colors())

        if dialog.exec():
            new_color = dialog.selectedColor()
            self.set_color(new_color)
            self.color_changed.emit(new_color.name())

    def _update_swatch(self):
        """Update swatch button appearance."""
        self.swatch_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.current_color.name()};
                border: 1px solid #555;
                border-radius: 2px;
            }}
            QPushButton:hover {{
                border: 2px solid #007ACC;
            }}
        """)
```

#### Advanced Color Dialog

```python
class AdvancedColorDialog(QColorDialog):
    """Extended color dialog with additional features."""

    def __init__(self, initial_color: QColor, parent=None):
        super().__init__(initial_color, parent)

        # Add custom widgets
        self._add_recent_colors_bar()
        self._add_theme_colors_palette()
        self._add_eyedropper_tool()

    def _add_recent_colors_bar(self):
        """Add recently used colors."""
        # Row of color swatches from history

    def _add_theme_colors_palette(self):
        """Add current theme colors as presets."""
        # Grid of colors from active theme

    def _add_eyedropper_tool(self):
        """Add screen color picker."""
        # Button to activate screen color picking
```

### 3. Theme Preview Widget (`theme_preview_widget.py`)

#### Purpose
Provides real-time preview of theme changes on miniature UI components.

#### Features
- Multiple preview contexts (Editor, Terminal, UI Components)
- Real-time style updates
- Syntax highlighting preview
- ANSI color preview for terminal
- Component state previews (hover, active, disabled)

#### Implementation

```python
class ThemePreviewWidget(QWidget):
    """Live preview panel showing theme changes."""

    def __init__(self):
        super().__init__()
        self.preview_components = {}
        self.current_colors = {}

        # Tabbed preview areas
        self.tab_widget = QTabWidget()

        # Editor preview
        self.editor_preview = self._create_editor_preview()
        self.tab_widget.addTab(self.editor_preview, "Editor")

        # Terminal preview
        self.terminal_preview = self._create_terminal_preview()
        self.tab_widget.addTab(self.terminal_preview, "Terminal")

        # UI Components preview
        self.ui_preview = self._create_ui_preview()
        self.tab_widget.addTab(self.ui_preview, "Components")

    def _create_editor_preview(self):
        """Create mini code editor with syntax highlighting."""
        editor = QPlainTextEdit()
        editor.setPlainText('''
function fibonacci(n) {
    // Calculate fibonacci number
    if (n <= 1) return n;
    return fibonacci(n - 1) + fibonacci(n - 2);
}

const result = fibonacci(10);
console.log(`Result: ${result}`);
        ''')

        # Apply syntax highlighting
        self._apply_syntax_highlighting(editor)
        return editor

    def _create_terminal_preview(self):
        """Create mini terminal with ANSI colors."""
        terminal = QTextEdit()
        terminal.setReadOnly(True)

        # Sample terminal output with ANSI colors
        self._render_terminal_content(terminal)
        return terminal

    def _create_ui_preview(self):
        """Create preview of UI components."""
        widget = QWidget()
        layout = QVBoxLayout()

        # Buttons
        button_group = QGroupBox("Buttons")
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(QPushButton("Primary"))
        btn_layout.addWidget(QPushButton("Secondary"))
        btn_layout.addWidget(QPushButton("Disabled"))
        button_group.setLayout(btn_layout)

        # Inputs
        input_group = QGroupBox("Inputs")
        input_layout = QVBoxLayout()
        input_layout.addWidget(QLineEdit("Text input"))
        input_layout.addWidget(QComboBox())
        input_group.setLayout(input_layout)

        # Lists
        list_group = QGroupBox("Lists")
        list_widget = QListWidget()
        list_widget.addItems(["Item 1", "Item 2 (selected)", "Item 3"])
        list_widget.setCurrentRow(1)

        layout.addWidget(button_group)
        layout.addWidget(input_group)
        layout.addWidget(list_group)

        widget.setLayout(layout)
        return widget

    def update_color(self, property_key: str, color: str):
        """Update preview with new color."""
        self.current_colors[property_key] = color

        # Generate and apply stylesheet
        stylesheet = self._generate_stylesheet()

        # Apply to all preview components
        for component in self.preview_components.values():
            component.setStyleSheet(stylesheet)
```

### 4. Theme Property Management

#### Data Model

```python
@dataclass
class ThemeProperty:
    """Represents a single theme property."""
    key: str                    # e.g., "editor.background"
    value: str                  # e.g., "#1e1e1e"
    category: str               # e.g., "Editor"
    subcategory: Optional[str]  # e.g., "Syntax"
    description: str            # User-friendly description
    default_value: str          # From base theme
    is_modified: bool           # Changed from base
    is_inherited: bool          # Using parent theme value

class ThemePropertyManager:
    """Manages theme properties with inheritance."""

    def __init__(self):
        self.properties: Dict[str, ThemeProperty] = {}
        self.categories: Dict[str, List[str]] = {}

    def load_theme(self, theme: Theme, base_theme: Optional[Theme] = None):
        """Load theme with optional base for inheritance."""
        # Build property list from theme
        # Mark inherited vs overridden

    def get_properties_by_category(self, category: str) -> List[ThemeProperty]:
        """Get all properties in a category."""

    def search_properties(self, query: str) -> List[ThemeProperty]:
        """Search properties by key or description."""

    def reset_property(self, key: str):
        """Reset property to inherited value."""
```

### 5. Import/Export Functionality

#### Theme Export Dialog

```python
class ThemeExportDialog(QDialog):
    """Dialog for exporting themes."""

    def __init__(self, theme: Theme, parent=None):
        super().__init__(parent)
        self.theme = theme

        # Export options
        self.format_combo = QComboBox()
        self.format_combo.addItems([
            "ViloxTerm Theme (.json)",
            "VSCode Theme (.json)",
            "TextMate Theme (.tmTheme)"
        ])

        # Include metadata checkbox
        self.include_metadata = QCheckBox("Include metadata")
        self.include_metadata.setChecked(True)

        # Minify output
        self.minify = QCheckBox("Minify JSON")

        # Preview area
        self.preview = QPlainTextEdit()
        self.preview.setReadOnly(True)
        self._update_preview()

    def export_theme(self) -> str:
        """Generate theme export string."""
        format_type = self.format_combo.currentText()

        if "ViloxTerm" in format_type:
            return self._export_viloxterm_format()
        elif "VSCode" in format_type:
            return self._export_vscode_format()
        elif "TextMate" in format_type:
            return self._export_textmate_format()
```

#### Theme Import

```python
class ThemeImporter:
    """Import themes from various formats."""

    @staticmethod
    def import_theme(file_path: str) -> Theme:
        """Import theme from file."""
        # Detect format
        # Parse and convert
        # Validate required properties
        # Return Theme object

    @staticmethod
    def import_vscode_theme(data: dict) -> Theme:
        """Convert VSCode theme to ViloxTerm format."""
        # Map VSCode color keys to ViloxTerm keys
        # Handle workbench.colorCustomizations
        # Extract metadata
```

### 6. Integration with Theme Service

#### Preview Mode

```python
class ThemeService:
    """Extended with preview support."""

    def apply_theme_preview(self, colors: Dict[str, str]):
        """Apply temporary theme for preview."""
        # Create temporary theme object
        # Apply without saving
        # Track preview state

    def end_preview(self):
        """Restore previous theme."""
        # Revert to saved theme
        # Clear preview state

    def save_custom_theme(self, theme: Theme) -> bool:
        """Save user-created theme."""
        # Validate theme
        # Save to user themes directory
        # Register in theme list
```

### 7. Commands and Keyboard Shortcuts

```python
# core/commands/builtin/theme_editor_commands.py

@command(
    id="theme.openEditor",
    title="Open Theme Editor",
    category="Preferences",
    description="Open the visual theme editor"
)
def open_theme_editor_command(context: CommandContext) -> CommandResult:
    """Open theme editor in new tab."""
    workspace_service = context.get_service(WorkspaceService)

    # Create theme editor widget
    editor = ThemeEditorAppWidget(f"theme-editor-{uuid.uuid4()}")

    # Add as new tab
    workspace_service.add_tab_with_widget(editor, "Theme Editor")

    return CommandResult(success=True)

@command(
    id="theme.editor.save",
    title="Save Theme",
    category="Theme Editor",
    shortcut="ctrl+s",
    when="editorFocus && activeEditor == 'theme-editor'"
)
def save_theme_command(context: CommandContext) -> CommandResult:
    """Save current theme edits."""
    # Get active theme editor
    # Validate changes
    # Save to file

@command(
    id="theme.editor.export",
    title="Export Theme",
    category="Theme Editor"
)
def export_theme_command(context: CommandContext) -> CommandResult:
    """Export theme to file."""
    # Show export dialog
    # Generate export
    # Save to file
```

### 8. Widget Registration

```python
# ui/widgets/widget_registry.py

WidgetType.THEME_EDITOR = "theme_editor"

WIDGET_CONFIGS[WidgetType.THEME_EDITOR] = WidgetConfig(
    widget_class=ThemeEditorAppWidget,
    factory=lambda pane_id: ThemeEditorAppWidget(pane_id),
    preserve_context_menu=False,
    show_header=True,
    allow_type_change=False,  # Theme editor is special-purpose
    can_be_closed=True,
    can_be_split=False,  # Don't split theme editor
    min_width=800,
    min_height=600,
    default_content="",
    stylesheet=""  # Theme editor manages its own styling
)
```

## Testing Strategy

### Unit Tests (`tests/unit/test_color_picker.py`)

```python
def test_hex_validation():
    """Test hex color validation."""
    picker = ColorPickerWidget()

    # Valid colors
    assert picker.validate_hex("#FF0000") == True
    assert picker.validate_hex("#f0f") == True

    # Invalid colors
    assert picker.validate_hex("red") == False
    assert picker.validate_hex("#GGGGGG") == False

def test_color_conversion():
    """Test color format conversions."""
    # RGB to Hex
    assert rgb_to_hex(255, 0, 0) == "#FF0000"

    # HSL to RGB
    r, g, b = hsl_to_rgb(0, 100, 50)
    assert (r, g, b) == (255, 0, 0)
```

### GUI Tests (`tests/gui/test_theme_editor.py`)

```python
def test_theme_editor_creation(qtbot):
    """Test theme editor widget creation."""
    editor = ThemeEditorAppWidget("test-editor")
    qtbot.addWidget(editor)

    # Check components created
    assert editor.category_tree is not None
    assert editor.property_panel is not None
    assert editor.preview_widget is not None

def test_color_change_preview(qtbot):
    """Test live preview updates."""
    editor = ThemeEditorAppWidget("test-editor")
    qtbot.addWidget(editor)

    # Change a color
    editor.apply_color_change("editor.background", "#FF0000")

    # Check preview updated
    assert editor.preview_widget.current_colors["editor.background"] == "#FF0000"

def test_undo_redo(qtbot):
    """Test undo/redo functionality."""
    editor = ThemeEditorAppWidget("test-editor")
    qtbot.addWidget(editor)

    # Make changes
    original = editor.current_theme.colors.get("editor.background")
    editor.apply_color_change("editor.background", "#FF0000")

    # Undo
    editor.undo()
    assert editor.current_theme.colors.get("editor.background") == original

    # Redo
    editor.redo()
    assert editor.current_theme.colors.get("editor.background") == "#FF0000"
```

### Integration Tests

```python
def test_theme_save_and_apply(tmp_path):
    """Test saving and applying custom theme."""
    # Create theme editor
    # Make changes
    # Save theme
    # Apply theme
    # Verify applied
```

## Performance Considerations

### Optimization Strategies

1. **Lazy Loading**
   - Load theme properties on demand
   - Defer preview component creation

2. **Debounced Updates**
   - Delay preview updates by 100ms
   - Batch multiple color changes

3. **Caching**
   - Cache generated stylesheets
   - Cache color conversions

4. **Virtual Scrolling**
   - For long property lists
   - Render only visible items

## User Experience

### Keyboard Navigation
- `Tab` - Navigate between panels
- `Arrow keys` - Navigate categories/properties
- `Enter` - Open color picker
- `Ctrl+S` - Save theme
- `Ctrl+Z/Y` - Undo/Redo
- `Ctrl+F` - Focus search

### Tooltips and Help
- Hover descriptions for each property
- "?" icon with detailed help
- Inline validation messages
- Status bar feedback

### Error Handling
- Validate colors before applying
- Warn about unsaved changes
- Handle import errors gracefully
- Provide meaningful error messages

## Implementation Timeline

### Week 1: Core Foundation
- [ ] Create ThemeEditorAppWidget base structure
- [ ] Implement category tree
- [ ] Build property list panel
- [ ] Set up basic layout

### Week 2: Color Picking
- [ ] Implement ColorPickerWidget
- [ ] Add inline color display
- [ ] Create color picker dialog
- [ ] Add validation and conversion

### Week 3: Live Preview
- [ ] Create ThemePreviewWidget
- [ ] Implement editor preview
- [ ] Add terminal preview
- [ ] Build component previews

### Week 4: Integration
- [ ] Connect to ThemeService
- [ ] Implement save/load
- [ ] Add undo/redo
- [ ] Create commands

### Week 5: Import/Export
- [ ] Build export dialog
- [ ] Implement format converters
- [ ] Add import validation
- [ ] Test with external themes

### Week 6: Polish
- [ ] Add search/filter
- [ ] Implement keyboard navigation
- [ ] Write documentation
- [ ] Performance optimization
- [ ] Comprehensive testing

## Success Metrics

1. **Usability**
   - Users can create custom theme in < 5 minutes
   - All properties accessible without scrolling issues
   - Changes visible immediately

2. **Performance**
   - Preview updates < 100ms
   - No lag when changing colors rapidly
   - Smooth scrolling with 100+ properties

3. **Reliability**
   - No crashes during extended use
   - Proper validation prevents invalid themes
   - Undo/redo always works correctly

4. **Completeness**
   - Access to all 100+ theme properties
   - Import/export with popular formats
   - Keyboard accessible

## Documentation Requirements

### User Documentation
- Getting started guide
- Video tutorial
- Tips for creating cohesive themes
- Troubleshooting guide

### Developer Documentation
- Architecture overview
- Extension points
- Theme format specification
- API reference

## Future Enhancements

### Phase 2 Features
- **Theme sharing marketplace**
- **A/B theme comparison**
- **Colorblind simulation**
- **Contrast checking (WCAG)**
- **Theme variants (light/dark pairs)**
- **Color palette generation**

### Phase 3 Features
- **AI-powered theme generation**
- **Theme from image extraction**
- **Seasonal theme rotation**
- **Per-workspace themes**
- **Theme inheritance chains**

## Conclusion

The Theme Editor represents a significant enhancement to ViloxTerm's customization capabilities. By following the established AppWidget pattern and integrating seamlessly with the existing theme system, it provides users with a powerful yet intuitive tool for personalizing their development environment.

The implementation prioritizes user experience through live preview, comprehensive undo/redo support, and intelligent organization of properties. The modular architecture ensures maintainability and enables future enhancements without disrupting the core functionality.