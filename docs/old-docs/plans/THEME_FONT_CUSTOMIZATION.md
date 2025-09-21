# Theme Font Customization - Implementation Plan

## Executive Summary

This plan extends the theme system to support font size customization within themes, allowing users to define different font sizes for various UI components (editor, terminal, UI elements) as part of their theme configuration. This addresses the current limitation where font sizes are hardcoded throughout the application and not customizable per theme.

## Problem Statement

### Current Issues

1. **Hardcoded Font Sizes**: Font sizes are scattered across the codebase as hardcoded values:
   - StylesheetGenerator: 12px, 13px, 14px in different components
   - Editor widgets: 11pt hardcoded
   - Terminal config: Separate 14px default
   - Theme preview: 9pt, 10pt hardcoded

2. **Disconnected Font Settings**:
   - Global `settings.font_size` exists but isn't used by stylesheets
   - Terminal has its own font configuration system
   - No way to customize fonts per theme

3. **Poor User Experience**:
   - Users cannot adjust font sizes to their preference
   - Different themes may need different optimal font sizes
   - No granular control over different UI areas

### Root Causes

1. **Theme Structure Limitation**: Themes only contain `colors` dictionary, no typography
2. **No Central Font Management**: Each component manages fonts independently
3. **Static Stylesheet Generation**: Font sizes are literals in stylesheet templates

## Solution Architecture

### Core Concept: Typography as Theme Property

Extend themes to include a `typography` section alongside `colors`, making font customization a first-class theme feature.

### Data Structure

```python
theme = {
    "id": "vscode-dark",
    "name": "VSCode Dark+",
    "colors": { ... },
    "typography": {
        # Font sizes (in pixels)
        "fontSize.base": 13,
        "fontSize.ui": 13,
        "fontSize.menu": 13,
        "fontSize.editor": 13,
        "fontSize.terminal": 12,
        "fontSize.sidebar": 13,
        "fontSize.statusBar": 12,
        "fontSize.tabs": 13,
        "fontSize.activityBar": 12,
        "fontSize.commandPalette": 14,

        # Font families
        "fontFamily.editor": "Consolas, 'Cascadia Code', Monaco, monospace",
        "fontFamily.terminal": "Consolas, 'Cascadia Code', Monaco, monospace",
        "fontFamily.ui": "system-ui, -apple-system, 'Segoe UI', sans-serif",

        # Line heights
        "lineHeight.editor": 1.5,
        "lineHeight.terminal": 1.2
    }
}
```

## Implementation Phases

### Phase 1: Core Data Model (Foundation)

#### 1.1 Extend Theme Class
**File**: `core/themes/theme.py`

```python
@dataclass
class Theme:
    # Existing fields...
    typography: Dict[str, Union[int, float, str]] = field(
        default_factory=lambda: ThemeTypography.get_defaults()
    )

    def get_font_size(self, key: str, fallback: int = 13) -> int:
        """Get font size with fallback."""
        return self.typography.get(key, fallback)

    def get_font_family(self, key: str, fallback: str = "sans-serif") -> str:
        """Get font family with fallback."""
        return self.typography.get(key, fallback)
```

#### 1.2 Create Typography Constants
**File**: `core/themes/typography.py` (New)

```python
class ThemeTypography:
    # Font size keys
    FONT_SIZE_BASE = "fontSize.base"
    FONT_SIZE_UI = "fontSize.ui"
    FONT_SIZE_MENU = "fontSize.menu"
    FONT_SIZE_EDITOR = "fontSize.editor"
    FONT_SIZE_TERMINAL = "fontSize.terminal"
    FONT_SIZE_SIDEBAR = "fontSize.sidebar"
    FONT_SIZE_STATUS_BAR = "fontSize.statusBar"
    FONT_SIZE_TABS = "fontSize.tabs"
    FONT_SIZE_ACTIVITY_BAR = "fontSize.activityBar"
    FONT_SIZE_COMMAND_PALETTE = "fontSize.commandPalette"

    # Font family keys
    FONT_FAMILY_EDITOR = "fontFamily.editor"
    FONT_FAMILY_TERMINAL = "fontFamily.terminal"
    FONT_FAMILY_UI = "fontFamily.ui"

    # Line height keys
    LINE_HEIGHT_EDITOR = "lineHeight.editor"
    LINE_HEIGHT_TERMINAL = "lineHeight.terminal"

    @staticmethod
    def get_defaults() -> Dict[str, Any]:
        """Get default typography settings."""
        return {
            # Font sizes
            ThemeTypography.FONT_SIZE_BASE: 13,
            ThemeTypography.FONT_SIZE_UI: 13,
            ThemeTypography.FONT_SIZE_MENU: 13,
            ThemeTypography.FONT_SIZE_EDITOR: 13,
            ThemeTypography.FONT_SIZE_TERMINAL: 12,
            ThemeTypography.FONT_SIZE_SIDEBAR: 13,
            ThemeTypography.FONT_SIZE_STATUS_BAR: 12,
            ThemeTypography.FONT_SIZE_TABS: 13,
            ThemeTypography.FONT_SIZE_ACTIVITY_BAR: 12,
            ThemeTypography.FONT_SIZE_COMMAND_PALETTE: 14,

            # Font families
            ThemeTypography.FONT_FAMILY_EDITOR: "Consolas, 'Cascadia Code', Monaco, 'Courier New', monospace",
            ThemeTypography.FONT_FAMILY_TERMINAL: "Consolas, 'Cascadia Code', Monaco, 'Courier New', monospace",
            ThemeTypography.FONT_FAMILY_UI: "system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif",

            # Line heights
            ThemeTypography.LINE_HEIGHT_EDITOR: 1.5,
            ThemeTypography.LINE_HEIGHT_TERMINAL: 1.2,
        }
```

#### 1.3 Update Theme Schema
**File**: `core/themes/schema.py`

Add typography validation (optional field):
```python
@staticmethod
def validate_typography(typography: Dict[str, Any]) -> List[str]:
    """Validate typography settings."""
    errors = []

    # Validate font sizes (should be integers 8-72)
    for key, value in typography.items():
        if key.startswith("fontSize."):
            if not isinstance(value, int) or value < 8 or value > 72:
                errors.append(f"Invalid font size for {key}: {value}")
        elif key.startswith("fontFamily."):
            if not isinstance(value, str):
                errors.append(f"Invalid font family for {key}: {value}")
        elif key.startswith("lineHeight."):
            if not isinstance(value, (int, float)) or value < 0.5 or value > 3.0:
                errors.append(f"Invalid line height for {key}: {value}")

    return errors
```

### Phase 2: Service Layer Integration

#### 2.1 Enhance Theme Service
**File**: `services/theme_service.py`

```python
def get_font_size(self, key: str, fallback: int = 13) -> int:
    """Get font size from current theme."""
    if self._current_theme:
        return self._current_theme.get_font_size(key, fallback)
    return fallback

def get_font_family(self, key: str, fallback: str = "sans-serif") -> str:
    """Get font family from current theme."""
    if self._current_theme:
        return self._current_theme.get_font_family(key, fallback)
    return fallback

def update_typography(self, key: str, value: Union[int, str, float]) -> bool:
    """Update typography setting in current theme."""
    if self._current_theme:
        if not hasattr(self._current_theme, 'typography'):
            self._current_theme.typography = {}
        self._current_theme.typography[key] = value
        self._emit_theme_changed()
        return True
    return False
```

### Phase 3: Stylesheet Generation

#### 3.1 Update StylesheetGenerator
**File**: `ui/themes/stylesheet_generator.py`

Add typography methods:
```python
def _get_font_size(self, key: str, fallback: int = 13) -> str:
    """Get font size from theme."""
    size = self._theme_service.get_font_size(key, fallback)
    return f"{size}px"

def _get_font_family(self, key: str, fallback: str = "sans-serif") -> str:
    """Get font family from theme."""
    return self._theme_service.get_font_family(key, fallback)
```

Update all style methods to use dynamic values:
```python
def _editor_style(self) -> str:
    """Generate editor stylesheet."""
    return f"""
        QPlainTextEdit, QTextEdit {{
            background-color: {self._get_color("editor.background")};
            color: {self._get_color("editor.foreground")};
            border: none;
            font-family: {self._get_font_family("fontFamily.editor")};
            font-size: {self._get_font_size("fontSize.editor")};
            selection-background-color: {self._get_color("editor.selectionBackground")};
            selection-color: {self._get_color("editor.foreground")};
        }}
    """

def _status_bar_style(self) -> str:
    """Generate status bar stylesheet."""
    return f"""
        QStatusBar {{
            background-color: {self._get_color("statusBar.background")};
            color: {self._get_color("statusBar.foreground")};
            border: none;
            padding: 2px 10px;
            font-size: {self._get_font_size("fontSize.statusBar")};
        }}
    """
# Update all other style methods similarly...
```

### Phase 4: Widget Integration

#### 4.1 Update Editor Widget
**File**: `ui/widgets/editor_app_widget.py`

```python
def setup_editor_style(self):
    """Configure editor appearance."""
    # Get font settings from theme
    from services.service_locator import ServiceLocator
    from services.theme_service import ThemeService

    locator = ServiceLocator.get_instance()
    theme_service = locator.get(ThemeService)

    if theme_service:
        font_family = theme_service.get_font_family("fontFamily.editor",
                                                    "Consolas, Monaco, monospace")
        font_size = theme_service.get_font_size("fontSize.editor", 11)
    else:
        font_family = "Consolas, Monaco, monospace"
        font_size = 11

    # Apply font
    font = QFont(font_family.split(',')[0].strip())  # Use first font
    font.setPointSize(font_size)
    self.editor.setFont(font)

    # Apply theme colors via stylesheet
    self.apply_theme()
```

#### 4.2 Coordinate Terminal Config
**File**: `ui/terminal/terminal_config.py`

```python
def to_xterm_config(self, is_dark_theme: bool = True) -> Dict[str, Any]:
    """Convert to xterm.js configuration object."""
    # Try to get from theme first
    from services.service_locator import ServiceLocator
    from services.theme_service import ThemeService

    locator = ServiceLocator.get_instance()
    theme_service = locator.get(ThemeService)

    if theme_service:
        font_size = theme_service.get_font_size("fontSize.terminal", self.font_size)
        font_family = theme_service.get_font_family("fontFamily.terminal", self.font_family)
        line_height = theme_service.get_font_size("lineHeight.terminal", self.line_height)
    else:
        font_size = self.font_size
        font_family = self.font_family
        line_height = self.line_height

    color_scheme = self.get_color_scheme(is_dark_theme)

    return {
        'cursorBlink': self.cursor_blink,
        'cursorStyle': self.cursor_style,
        'fontFamily': font_family,
        'fontSize': font_size,
        'lineHeight': line_height,
        'scrollback': self.scrollback,
        'theme': color_scheme.to_dict(),
        # ...
    }
```

### Phase 5: Theme Editor UI

#### 5.1 Add Typography Controls
**File**: `ui/widgets/theme_editor_widget.py`

Create typography section in property editor:
```python
def _create_typography_section(self) -> QWidget:
    """Create typography editing section."""
    section = QGroupBox("Typography")
    layout = QFormLayout()

    # Font size controls
    font_sizes = [
        ("Base Size", "fontSize.base"),
        ("Editor", "fontSize.editor"),
        ("Terminal", "fontSize.terminal"),
        ("UI Elements", "fontSize.ui"),
        ("Status Bar", "fontSize.statusBar"),
        ("Tabs", "fontSize.tabs"),
        ("Sidebar", "fontSize.sidebar"),
        ("Menu", "fontSize.menu"),
        ("Command Palette", "fontSize.commandPalette"),
    ]

    for label, key in font_sizes:
        spinbox = QSpinBox()
        spinbox.setRange(8, 72)
        spinbox.setSuffix(" px")
        spinbox.setValue(self._current_theme.get_font_size(key, 13))
        spinbox.valueChanged.connect(
            lambda v, k=key: self._update_typography(k, v)
        )
        layout.addRow(label + ":", spinbox)
        self._typography_controls[key] = spinbox

    # Font family controls
    font_families = [
        ("Editor Font", "fontFamily.editor"),
        ("Terminal Font", "fontFamily.terminal"),
        ("UI Font", "fontFamily.ui"),
    ]

    for label, key in font_families:
        combo = QFontComboBox()
        combo.setCurrentFont(QFont(self._current_theme.get_font_family(key)))
        combo.currentFontChanged.connect(
            lambda f, k=key: self._update_typography(k, f.family())
        )
        layout.addRow(label + ":", combo)
        self._typography_controls[key] = combo

    section.setLayout(layout)
    return section
```

#### 5.2 Update Property Categories
**File**: `core/themes/property_categories.py`

```python
@staticmethod
def get_categories() -> Dict[str, Dict[str, List[Tuple[str, str]]]]:
    return {
        # ... existing color categories ...

        "Typography": {
            "Font Sizes": [
                ("fontSize.base", "Base font size for UI"),
                ("fontSize.editor", "Editor font size"),
                ("fontSize.terminal", "Terminal font size"),
                ("fontSize.ui", "General UI elements"),
                ("fontSize.statusBar", "Status bar text"),
                ("fontSize.tabs", "Tab labels"),
                ("fontSize.sidebar", "Sidebar items"),
                ("fontSize.menu", "Menu items"),
                ("fontSize.commandPalette", "Command palette"),
            ],
            "Font Families": [
                ("fontFamily.editor", "Editor font family"),
                ("fontFamily.terminal", "Terminal font family"),
                ("fontFamily.ui", "UI font family"),
            ],
            "Line Heights": [
                ("lineHeight.editor", "Editor line spacing"),
                ("lineHeight.terminal", "Terminal line spacing"),
            ]
        }
    }
```

### Phase 6: Theme Files Update

#### 6.1 Update Built-in Themes
**File**: `resources/themes/builtin/vscode-dark.json`

```json
{
  "id": "vscode-dark",
  "name": "VSCode Dark+",
  "description": "Official Visual Studio Code Dark+ theme",
  "version": "1.0.0",
  "author": "ViloxTerm",
  "colors": { ... },
  "typography": {
    "fontSize.base": 13,
    "fontSize.editor": 13,
    "fontSize.terminal": 12,
    "fontSize.ui": 13,
    "fontSize.statusBar": 12,
    "fontSize.tabs": 13,
    "fontSize.sidebar": 13,
    "fontSize.menu": 13,
    "fontSize.activityBar": 12,
    "fontSize.commandPalette": 14,
    "fontFamily.editor": "Consolas, 'Cascadia Code', Monaco, 'Courier New', monospace",
    "fontFamily.terminal": "Consolas, 'Cascadia Code', Monaco, 'Courier New', monospace",
    "fontFamily.ui": "system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif",
    "lineHeight.editor": 1.5,
    "lineHeight.terminal": 1.2
  }
}
```

## Migration Strategy

### Backward Compatibility

1. **Optional Typography**: Themes without typography section use defaults
2. **Settings Migration**: On first load with new version:
   ```python
   if not theme.typography and settings.has("theme.font_size"):
       theme.typography["fontSize.base"] = settings.get("theme.font_size")
   ```
3. **Import Compatibility**: VSCode themes import without typography (unchanged)

### Rollout Plan

1. **Version 1**: Basic font size support (Phase 1-3)
2. **Version 2**: Full typography with Theme Editor UI (Phase 4-5)
3. **Version 3**: Advanced features (font weight, letter spacing, etc.)

## Testing Requirements

### Unit Tests
- Theme typography validation
- Font size retrieval with fallbacks
- Typography inheritance in extended themes
- Migration from old settings

### Integration Tests
- Stylesheet generation with dynamic fonts
- Widget font application
- Terminal config coordination
- Theme Editor typography controls

### Manual Testing
- Font size changes apply to all components
- Live preview in Theme Editor
- Theme persistence with typography
- Import/export with typography
- Cross-platform font families

## Performance Considerations

### Optimizations
1. **Cache Stylesheets**: Only regenerate on typography change
2. **Batch Updates**: Group typography changes in Theme Editor
3. **Lazy Loading**: Load font families only when needed
4. **Efficient Signals**: Single theme_changed signal for all typography

### Benchmarks
- Stylesheet generation: < 10ms
- Font application: < 5ms per widget
- Theme switching with typography: < 100ms total

## Future Enhancements

### Phase 7: Advanced Typography
- Font weight support (normal, bold, light)
- Letter spacing control
- Text transform options (uppercase for headers)
- Font variant support (ligatures, etc.)

### Phase 8: Accessibility
- Font size presets (Small, Normal, Large, X-Large)
- High contrast font options
- Dyslexia-friendly font options
- Zoom level support (Ctrl+/Ctrl-)

### Phase 9: User Experience
- Font preview in Theme Editor
- Font size slider in status bar
- Quick font size adjustment shortcuts
- Per-workspace font overrides

## Risk Analysis

### Technical Risks
1. **Performance Impact**: Mitigated by caching
2. **Cross-platform Fonts**: Use font stacks with fallbacks
3. **Qt Font Rendering**: Test on all platforms

### User Experience Risks
1. **Complexity**: Hide advanced options by default
2. **Breaking Changes**: Full backward compatibility
3. **Migration Issues**: Automated migration with fallbacks

## Success Metrics

### Quantitative
- Zero performance regression
- < 100ms theme switch time
- 100% backward compatibility

### Qualitative
- User satisfaction with font customization
- Accessibility improvements
- Theme sharing with typography

## Timeline

### Week 1-2: Foundation
- Phase 1: Core Data Model
- Phase 2: Service Layer

### Week 3-4: Integration
- Phase 3: Stylesheet Generation
- Phase 4: Widget Integration

### Week 5-6: UI and Polish
- Phase 5: Theme Editor UI
- Phase 6: Theme Files Update
- Testing and bug fixes

### Week 7-8: Release
- Documentation
- Migration testing
- Release preparation

## Dependencies

### Internal
- Theme system (existing)
- Settings service (existing)
- Widget system (existing)

### External
- Qt font rendering
- System font availability
- xterm.js font support

## Approval

This plan requires approval from:
- [ ] Technical Lead - Architecture review
- [ ] UX Lead - User experience impact
- [ ] QA Lead - Testing requirements
- [ ] Product Owner - Feature scope

## References

- [VSCode Theme Documentation](https://code.visualstudio.com/api/references/theme-color)
- [Qt Font Documentation](https://doc.qt.io/qt-6/qfont.html)
- [xterm.js Font Configuration](https://xtermjs.org/docs/api/terminal/interfaces/iterminaloptions/)
- Current Theme Architecture: `docs/architecture/THEME_MANAGEMENT_SYSTEM.md`
- Theme Editor Implementation: `docs/plans/theme-editor-implementation.md`