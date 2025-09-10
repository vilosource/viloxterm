# ViloApp - VSCode-Style Desktop Application Specification

## Overview

ViloApp is a PySide6-based desktop GUI application that implements a VSCode-style interface with a fixed Activity Bar, collapsible Sidebar, tabbed Workspace with recursive split panes, and Status Bar. The application features sophisticated terminal integration, theme management, and a robust widget system.

## Core Architecture

### Application Structure
The application follows a modern MVC-style architecture with clear separation of concerns:

```
viloapp/
├── main.py                    # Entry point with environment configuration
├── core/                      # Core utilities and environment detection
│   └── environment_detector.py # Platform-specific optimizations
├── ui/                        # UI components
│   ├── main_window.py        # QMainWindow orchestration
│   ├── activity_bar.py       # VSCode-style activity bar
│   ├── sidebar.py            # Collapsible sidebar with animation
│   ├── workspace_simple.py   # Tab-based workspace manager
│   ├── status_bar.py         # Application status bar
│   ├── icon_manager.py       # Theme-aware icon management
│   ├── vscode_theme.py       # VSCode-style theming system
│   ├── widgets/              # Reusable widget components
│   │   ├── app_widget.py     # Base widget class with lifecycle
│   │   ├── split_pane_*.py   # Model-View split pane system
│   │   ├── widget_registry.py # Widget type management
│   │   ├── widget_pool.py    # Widget recycling for performance
│   │   ├── editor_app_widget.py # Text editor widget
│   │   └── pane_header.py    # Pane header bars with controls
│   └── terminal/             # Terminal subsystem
│       ├── terminal_server.py # Flask/SocketIO backend
│       ├── terminal_widget.py # QWebEngine terminal frontend
│       ├── terminal_app_widget.py # Terminal AppWidget
│       ├── terminal_bridge.py # Qt-Web communication bridge
│       └── terminal_*.py     # Terminal components
├── models/                   # Data models (minimal usage)
├── controllers/              # Controllers (state management)
│   └── state_controller.py  # Application state coordination
└── resources/               # Icons, themes, and assets
    ├── icons/              # SVG icons for light/dark themes
    └── resources.qrc       # Qt resource compilation
```

## Layout Components

### Activity Bar (Implemented ✅)

* **Location**: Far left side of the window
* **Implementation**: Vertical `QToolBar` with 48px fixed width
* **Features**:
  - Icon-only buttons (Explorer, Search, Git, Settings)
  - Non-movable and non-floatable
  - VSCode-style theming with hover effects
  - Each button toggles corresponding Sidebar view
  - Smart state management with collapse detection

### Sidebar (Implemented ✅)

* **Location**: To the right of the Activity Bar
* **Implementation**: Custom `QWidget` with `QStackedWidget` for views
* **Features**:
  - Smooth collapse/expand animation (200ms QPropertyAnimation)
  - Multiple tool panels: Explorer, Search, Git, Settings
  - Width persistence (250px default)
  - Toggle via Activity Bar or keyboard shortcut (Ctrl+B)
  - VSCode-style styling with proper borders

### Workspace (Enhanced Implementation ✅)

The workspace has evolved beyond the original specification into a **tab-based architecture**:

#### Tab-Based Workspace Design
* **Implementation**: `QTabWidget` containing multiple workspace tabs
* **Each Tab**: Contains its own independent `SplitPaneWidget` 
* **Benefits**:
  - Multiple isolated workspaces
  - Independent split layouts per tab
  - Tab context menus (duplicate, close others, etc.)
  - Proper tab lifecycle management

#### Split Pane System (Model-View Architecture)
* **Model**: `SplitPaneModel` - Pure data structure managing binary tree
* **View**: `SplitPaneWidget` - Qt rendering layer
* **Features**:
  - Recursive horizontal and vertical splits
  - Binary tree structure with proper parent-child relationships
  - Ratio tracking and persistence
  - Clean separation of concerns
  - AppWidget lifecycle management

#### AppWidget System
* **Base Class**: `AppWidget` - Abstract base for all content widgets
* **Features**:
  - Standardized lifecycle (cleanup, focus, state management)
  - Action request system (split, close, type change)
  - Back-reference to containing leaf node
  - Signal-based communication with parent
* **Widget Types**:
  - `TEXT_EDITOR` - Text editing capabilities
  - `TERMINAL` - Full terminal emulation
  - `OUTPUT` - Read-only output display
  - `PLACEHOLDER` - Fallback widget type

#### Widget Management
* **Widget Pool**: Performance optimization through widget reuse
* **Widget Registry**: Type-based widget configuration and factory
* **Focus Management**: Event-driven focus tracking across panes
* **State Persistence**: Full layout and content state serialization

### Terminal Integration (New Feature ✅)

#### Architecture
* **Backend**: Flask server with SocketIO for real-time communication
* **Frontend**: QWebEngine-based terminal rendering
* **Bridge**: Qt-Web communication layer for seamless integration

#### Features
* **Full Terminal Emulation**: 
  - Real shell process spawning
  - PTY support for proper terminal behavior
  - Session management and cleanup
* **Web-Based Rendering**:
  - xterm.js for authentic terminal experience
  - Theme synchronization with application
  - Proper keyboard and mouse handling
* **Integration**:
  - Terminal widgets as first-class AppWidgets
  - Tabs specifically for terminal instances
  - Proper cleanup on application exit

### Status Bar (Implemented ✅)

* **Location**: Bottom of the window
* **Implementation**: Custom `AppStatusBar` extending `QStatusBar`
* **Features**:
  - Full-width spanning
  - Message display with timeout
  - Status indicators and progress display

## Advanced Features

### Theme System (Implemented ✅)

#### Comprehensive Theming
* **Icon Management**: `IconManager` with theme-aware SVG loading
* **Light/Dark Themes**: Automatic system detection and manual toggle
* **VSCode Styling**: Authentic color schemes and component styling
* **Theme Persistence**: User preference saved across sessions

#### Implementation Details
* **Dynamic Icon Loading**: SVG icons automatically switch with theme
* **Stylesheet System**: Modular CSS-like styling per component
* **Theme Detection**: System theme integration where available

### Environment Detection (New Feature ✅)

#### Smart Environment Configuration
* **Platform Detection**: WSL, Docker, SSH, native Linux, macOS, Windows
* **Optimization Strategies**: Platform-specific Qt configurations
* **Performance Tuning**: GPU detection and appropriate rendering backends

#### Supported Environments
* **WSL**: Software rendering, sandbox disabling, display detection
* **Docker**: Headless-friendly configurations
* **SSH**: Network-optimized settings
* **Native**: Full hardware acceleration when available

### State Persistence (Implemented ✅)

#### Comprehensive State Management
* **Window State**: Geometry, splitter sizes, menu bar visibility
* **Workspace State**: Tab layouts, split configurations, active panes
* **Theme Preferences**: Light/dark mode, icon preferences
* **Widget States**: Individual widget content and configuration

#### Implementation
* **QSettings Integration**: Cross-platform settings storage
* **JSON Serialization**: Complex state structures properly preserved
* **Graceful Degradation**: Fallback to defaults on restoration failure

## Keyboard Shortcuts (Current Implementation)

### File Operations
* `Ctrl+N` - New Editor Tab
* `Ctrl+`\` - New Terminal Tab

### View Operations  
* `Ctrl+T` - Toggle Theme
* `Ctrl+B` - Toggle Sidebar
* `Ctrl+Shift+M` - Toggle Menu Bar (global shortcut)

### Split Operations
* `Ctrl+\` - Split Pane Right (horizontal)
* `Ctrl+Shift+\` - Split Pane Down (vertical)
* `Ctrl+W` - Close Active Pane

### Debug Operations
* `Ctrl+Shift+R` - Reset Application State

## Interaction Patterns

### Activity Bar Integration
* **View Selection**: Click to switch sidebar view
* **Sidebar Toggle**: Click same view to collapse/expand sidebar
* **Visual Feedback**: Active view highlighting and hover effects
* **State Synchronization**: Activity bar reflects sidebar visibility

### Split Pane Operations
* **Context Menus**: Right-click for split/close operations
* **Header Controls**: Pane headers with split/close buttons (configurable)
* **Drag Operations**: Splitter handles for resizing
* **Type Changes**: Widget type switching via context menus

### Tab Management
* **Tab Creation**: File menu or keyboard shortcuts
* **Tab Operations**: Context menu for duplicate, close others, close right
* **Tab Switching**: Standard tab widget behavior
* **Independent Layouts**: Each tab maintains its own split configuration

## Technical Implementation Details

### Widget Lifecycle Management
```python
# AppWidget base class provides:
class AppWidget(QWidget):
    def cleanup(self)           # Resource cleanup
    def focus_widget(self)      # Focus management  
    def get_state(self) -> dict # State serialization
    def set_state(self, state)  # State restoration
    def request_action(action, params)  # Action system
```

### Split Pane Model-View Pattern
```python
# Clean separation between data and presentation
SplitPaneModel   # Binary tree data structure
SplitPaneWidget  # Qt view rendering
LeafNode         # Contains AppWidget content
SplitNode        # Contains split configuration
```

### Signal-Based Communication
* **Loose Coupling**: Components communicate via Qt signals/slots
* **Event-Driven**: Focus changes, layout updates, theme changes
* **Clean Interfaces**: Well-defined signal contracts between components

### Performance Optimizations
* **Widget Pooling**: Reuse QSplitter instances for better performance
* **Event-Driven Focus**: No polling, efficient focus tracking
* **Lazy Loading**: Widgets created on demand
* **Resource Cleanup**: Proper cleanup prevents memory leaks

## State Diagrams

### Expanded State
```
+-------------------------------------------------------------+
| [Icons] | [ Sidebar (Explorer) ]    |     Workspace         |
|         |                           |  ┌─────────────────┐ |
|  A B C  |  ┌─────────────────────┐  |  │ Tab1 | Tab2 |   │ |
|  D E F  |  │  File Explorer      │  |  │ ─────────────── │ |
|         |  │  - src/             │  |  │ [Split Pane]   │ |
|         |  │  - docs/            │  |  │ Editor|Terminal │ |
|         |  │  - tests/           │  |  └─────────────────┘ |
+---------+---------------------------+-----------------------+
| Status Bar (theme: dark, 4 panes active, terminal ready)   |
+-------------------------------------------------------------+
```

### Collapsed State  
```
+-------------------------------------------------------------+
| [Icons] |                   Workspace                       |
|         |          ┌─────────────────┐                      |
|  A B C  |          │ Tab1 | Tab2 |   │                      |
|  D E F  |          │ ─────────────── │                      |
|         |          │ [Split Layout]  │                      |
|         |          │ Multi-pane view │                      |
+---------+---------------------------------------------------+
| Status Bar (sidebar collapsed, 6 panes active)             |
+-------------------------------------------------------------+
```

## Dependencies

### Core Framework
```
PySide6>=6.7.0              # Main GUI framework with WebEngine
```

### Terminal Backend
```
flask>=2.0.0                # Terminal server backend
flask-socketio>=5.0.0       # Real-time terminal communication
```

### Development Tools
```
pytest>=8.0.0               # Testing framework
pytest-qt>=4.4.0            # Qt widget testing
black>=24.0.0               # Code formatting
ruff>=0.3.0                 # Fast Python linter
mypy>=1.8.0                 # Type checking
```

## Development Workflow

### Available Commands
```bash
make setup          # Initial project setup
make run           # Run the application  
make test          # Run all tests
make check         # Code quality checks (format, lint, typecheck)
make resources     # Compile Qt resources
make clean         # Clean generated files
```

### Testing Strategy
* **Unit Tests**: Individual component testing with pytest-qt
* **Integration Tests**: Component interaction testing
* **E2E Tests**: Full workflow testing with PyAutoGUI
* **Headless Testing**: xvfb support for CI/CD

## Architecture Status

### ✅ Fully Implemented
- [x] Core layout structure (Activity Bar, Sidebar, Workspace, Status Bar)
- [x] Split pane system with Model-View architecture
- [x] Tab-based workspace with independent layouts
- [x] AppWidget system with lifecycle management
- [x] Terminal integration with Flask/SocketIO backend
- [x] Theme system with light/dark mode support
- [x] State persistence with QSettings
- [x] Environment detection and optimization
- [x] Widget pooling for performance
- [x] Focus management system

### 🚧 Planned Improvements (Architecture Review Identified)
- [ ] **Command System**: Centralized action management for keyboard shortcuts
- [ ] **Command Palette**: Discoverable actions with fuzzy search
- [ ] **Context System**: Context-aware commands with "when" clauses  
- [ ] **Service Layer**: Business logic extraction from UI components
- [ ] **Dependency Injection**: Loose coupling via service locator pattern
- [ ] **Plugin Architecture**: Extension points for third-party features

### 🔄 Continuous Improvements
- [ ] Performance optimization through profiling
- [ ] Accessibility improvements (keyboard navigation)
- [ ] Comprehensive keyboard shortcuts
- [ ] Advanced terminal features (tabs, sessions)
- [ ] File system integration
- [ ] Search and replace functionality

## Future Roadmap

### Phase 1: Command System Foundation
Implementation of centralized command pattern as identified in architecture review to enable advanced keyboard support and command palette functionality.

### Phase 2: Enhanced User Experience  
Advanced features like command palette, comprehensive keyboard shortcuts, and context-sensitive operations.

### Phase 3: Extensibility
Plugin architecture and API for third-party extensions.

This specification reflects the current state of ViloApp as of January 2025, incorporating all implemented features and planned architectural improvements.