# Theme Management System - Implementation Plan

## Overview

Complete redesign of the theme system to support multiple themes, custom themes, and dynamic theme switching without application restart. This is a clean implementation that removes the old hardcoded system entirely.

## Goals

1. **Multiple Built-in Themes**: VSCode Dark+, VSCode Light, Monokai, Solarized
2. **Custom User Themes**: Create, edit, import, export themes
3. **Dynamic Switching**: Change themes without restart
4. **Clean Architecture**: Proper separation of concerns
5. **Comprehensive Testing**: Full pytest-qt test coverage

## Architecture

### Core Components

```
/core/themes/
├── __init__.py
├── theme.py           # Theme data model
├── schema.py          # Theme validation schema
└── constants.py       # Theme color key constants

/services/
└── theme_service.py   # Theme business logic

/ui/themes/
├── __init__.py
├── theme_provider.py  # UI bridge for themes
└── stylesheet_generator.py  # Dynamic stylesheet generation

/resources/themes/builtin/
├── vscode-dark.json
├── vscode-light.json
├── monokai.json
└── solarized-dark.json
```

### Service Architecture

```
ThemeService (Business Logic)
    ↓
ThemeProvider (UI Bridge)
    ↓
StylesheetGenerator (CSS Generation)
    ↓
Widgets (Apply Stylesheets)
```

## Implementation Phases

### Phase 1: Core Infrastructure

#### 1.1 Theme Model (`core/themes/theme.py`)
```python
@dataclass
class Theme:
    id: str
    name: str
    description: str
    version: str
    author: str
    extends: Optional[str] = None
    colors: Dict[str, str] = field(default_factory=dict)
```

#### 1.2 Theme Service (`services/theme_service.py`)
- Load themes from resources and user directory
- Theme inheritance support
- Apply theme with signal emission
- Theme validation
- Import/export functionality

#### 1.3 Theme Provider (`ui/themes/theme_provider.py`)
- Bridge between ThemeService and UI
- Stylesheet caching
- Widget update orchestration

#### 1.4 Stylesheet Generator (`ui/themes/stylesheet_generator.py`)
- Component-specific stylesheet generation
- Dynamic color injection
- Efficient caching

### Phase 2: Remove Old System & Update Widgets

#### 2.1 Remove Static System
- Delete `ui/vscode_theme.py`
- Remove all `from ui.vscode_theme import *`
- Clean up hardcoded stylesheets

#### 2.2 Update All Widgets
Each widget needs:
```python
def apply_theme(self):
    """Apply current theme"""
    provider = self.get_theme_provider()
    self.setStyleSheet(provider.get_stylesheet("component_name"))
```

Widgets to update:
- MainWindow
- ActivityBar
- Sidebar
- Workspace
- StatusBar
- All AppWidgets
- Dialogs

#### 2.3 Service Registration
Update `services/__init__.py`:
- Register ThemeService before UIService
- Register ThemeProvider
- Connect theme signals

### Phase 3: Theme Resources

#### 3.1 Theme JSON Format
```json
{
  "id": "vscode-dark",
  "name": "VSCode Dark+",
  "description": "Official VSCode Dark+ theme",
  "version": "1.0.0",
  "author": "ViloxTerm",
  "colors": {
    "editor.background": "#1e1e1e",
    "editor.foreground": "#d4d4d4",
    "activityBar.background": "#333333",
    "sideBar.background": "#252526",
    "statusBar.background": "#16825d",
    "terminal.ansiBlack": "#000000"
  }
}
```

#### 3.2 Resource Integration
- Add themes to `resources/resources.qrc`
- Update Makefile for theme validation
- Handle dev vs production paths

### Phase 4: Commands

#### 4.1 Theme Commands
- `theme.selectTheme` - Open theme selector
- `theme.createCustomTheme` - Create new theme
- `theme.editTheme` - Edit existing theme
- `theme.importTheme` - Import from file
- `theme.exportTheme` - Export to file
- `theme.resetTheme` - Reset to default

### Phase 5: Testing

#### 5.1 Unit Tests (`tests/unit/test_theme_service.py`)
- Theme loading
- Theme validation
- Theme inheritance
- Color resolution

#### 5.2 GUI Tests (`tests/gui/test_theme_gui.py`)
- Theme switching without restart
- Widget updates
- Theme persistence
- Non-blocking tests with mocks

#### 5.3 Integration Tests (`tests/integration/test_theme_integration.py`)
- Service cooperation
- Signal propagation
- Settings persistence

### Phase 6: Theme Editor

#### 6.1 Theme Editor AppWidget
- Color picker for each property
- Live preview
- Save as new theme
- Export functionality

## File Changes Summary

### Files to Delete
- `ui/vscode_theme.py`

### Files to Create
- `core/themes/__init__.py`
- `core/themes/theme.py`
- `core/themes/schema.py`
- `core/themes/constants.py`
- `services/theme_service.py`
- `ui/themes/__init__.py`
- `ui/themes/theme_provider.py`
- `ui/themes/stylesheet_generator.py`
- `resources/themes/builtin/vscode-dark.json`
- `resources/themes/builtin/vscode-light.json`
- `resources/themes/builtin/monokai.json`
- `resources/themes/builtin/solarized-dark.json`
- `core/commands/builtin/theme_commands.py`
- `tests/unit/test_theme_service.py`
- `tests/gui/test_theme_gui.py`
- `tests/integration/test_theme_integration.py`
- `docs/architecture/THEME_MANAGEMENT_SYSTEM.md`
- `docs/dev-guides/theme-development-guide.md`

### Files to Modify
- `services/__init__.py` - Add ThemeService registration
- `ui/main_window.py` - Remove vscode_theme import, add theme support
- `ui/activity_bar.py` - Remove vscode_theme import, add apply_theme()
- `ui/sidebar.py` - Remove vscode_theme import, add apply_theme()
- `ui/workspace.py` - Remove vscode_theme import, add apply_theme()
- `ui/status_bar.py` - Remove vscode_theme import, add apply_theme()
- `ui/widgets/*.py` - Update all widgets for theme support
- `resources/resources.qrc` - Add theme resources
- `Makefile` - Add theme compilation target
- `main.py` - Initialize theme service early

## Testing Strategy

### Non-blocking GUI Tests
All GUI tests use mocks to avoid blocking dialogs:
```python
with patch('ui.dialogs.theme_selector.show_theme_selector') as mock:
    mock.return_value = "theme-id"
    # Test theme application
```

### Temporary Settings
Use `tmp_path` fixture for isolated settings:
```python
def test_theme_persistence(tmp_path):
    settings_dir = tmp_path / "settings"
    # Test with isolated settings
```

### Signal Testing
Use `qtbot.waitSignal` for async operations:
```python
with qtbot.waitSignal(theme_service.theme_changed):
    theme_service.apply_theme("new-theme")
```

## Implementation Timeline

### Week 1: Core Infrastructure
- [ ] Create theme model and service
- [ ] Implement theme provider
- [ ] Create stylesheet generator
- [ ] Convert current theme to JSON

### Week 2: Widget Updates
- [ ] Remove old vscode_theme system
- [ ] Update all widgets
- [ ] Test theme switching
- [ ] Create light theme

### Week 3: Commands & Testing
- [ ] Implement theme commands
- [ ] Write comprehensive tests
- [ ] Create additional themes
- [ ] Theme persistence

### Week 4: Polish
- [ ] Theme editor widget
- [ ] Import/export functionality
- [ ] Documentation
- [ ] Performance optimization

## Success Criteria

1. **No Hardcoded Colors**: All colors from theme system
2. **Dynamic Switching**: Themes change without restart
3. **Full Test Coverage**: All components tested
4. **Clean Architecture**: Proper separation of concerns
5. **User Themes**: Support for custom themes
6. **Performance**: Fast theme switching with caching

## Migration Notes

This is a complete rewrite with no backward compatibility:
1. All widgets must be updated
2. All tests must be rewritten
3. All hardcoded colors removed
4. New command structure

## Documentation

### Architecture Documentation
- System design and flow
- Service interactions
- Theme file format

### Developer Guide
- Creating new themes
- Adding theme support to widgets
- Testing themes

### User Guide
- Changing themes
- Creating custom themes
- Importing/exporting themes