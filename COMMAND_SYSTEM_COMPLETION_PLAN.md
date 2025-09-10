# Command System Completion Plan

**Phase 5: Command UI & User Experience**  
*Status: Architecture Review Complete - Ready for Implementation*  
*Timeline: 15-20 days*  
*Last Updated: Analysis of existing systems completed*

## 🎯 Executive Summary

Complete ViloApp's command system by implementing production-ready UI components and user experience features. We have a solid foundation with 51 commands, service layer architecture, keyboard shortcuts, and comprehensive testing (66 tests passing). This phase adds the missing UI/UX layer to make commands easily discoverable and usable.

## 🔍 **CRITICAL ARCHITECTURE REVIEW FINDINGS**

After comprehensive codebase analysis, we discovered several **existing systems** that our implementation must integrate with rather than duplicate:

### ✅ **Discovered Existing Infrastructure**

**1. Comprehensive Context System (Fully Implemented)**
- `core/context/manager.py` - Singleton context manager with observer pattern
- `core/context/keys.py` - 40+ predefined context keys (`COMMAND_PALETTE_FOCUS`, `VIM_MODE`, etc.)
- `core/context/evaluator.py` - Complete when-clause expression parser with lexer/AST
- `ContextProvider` abstract class and provider pattern already established
- Advanced features: Expression evaluation, complex boolean logic, comparisons

**2. UI Widget Infrastructure**  
- `ui/widgets/widget_registry.py` - Established widget registration patterns
- Consistent PySide6 theming integration throughout codebase
- Standardized signal/slot patterns and icon management

**3. Command Registry Search**
- `command_registry.search_commands()` already implements fuzzy search with scoring
- Title, category, description, and keyword matching
- Relevance-based ranking system

### ❌ **Critical Missing Systems**
- **Settings System**: No centralized settings management (critical dependency)
- **State Persistence**: QSettings used sporadically, no unified approach
- **Command History**: No usage tracking or analytics

### 🚨 **Architecture Impact**
Our original plan would create **competing systems**. Must revise to **extend existing architecture**.

## 📊 Current State Analysis

### ✅ What We Have (Completed Phases 1-4)
- **51 Commands** across 6 categories (File, View, Workspace, Edit, Navigation, Debug)
- **Service Layer** with 5 services (Workspace, UI, Terminal, State, Editor)
- **Keyboard System** with shortcut parsing, conflict resolution, and keymaps
- **Command Infrastructure**: Registry, executor, decorators, context evaluation
- **66 Tests** passing (16 command + 20 service + 25 keyboard + 5 integration)

### ❌ What We're Missing
- **Command Discovery**: No way to find/browse available commands
- **User Interface**: Commands only accessible via hardcoded menu items and shortcuts
- **Command Palette**: Essential VSCode-style Ctrl+Shift+P functionality
- **Settings UI**: No way to customize shortcuts or preferences
- **User Feedback**: Limited feedback on command execution results
- **Command History**: No tracking of frequently used commands

## 🏗️ Architecture Design

### MVC + Service Layer Pattern

```
┌─────────────────────────────────────────────────────────────────┐
│                           VIEWS (UI Layer)                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │ Command Palette │  │ Settings Dialog │  │ Context Menus   │ │
│  │    Widget       │  │     Widget      │  │   & Toolbars    │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────┬───────────────────────────────────┘
                              │ Events & User Input
┌─────────────────────────────▼───────────────────────────────────┐
│                     CONTROLLERS (Coordination)                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │ Palette         │  │ Settings        │  │ Context Menu    │ │
│  │ Controller      │  │ Controller      │  │ Controller      │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────┬───────────────────────────────────┘
                              │ Orchestrates
┌─────────────────────────────▼───────────────────────────────────┐
│                      MODELS (State & Logic)                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │ Command UI      │  │ Settings        │  │ Usage Analytics │ │
│  │ State           │  │ Manager         │  │ & History       │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────┬───────────────────────────────────┘
                              │ Uses
┌─────────────────────────────▼───────────────────────────────────┐
│                  SERVICES (Business Logic)                      │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │ Command         │  │ Keyboard        │  │ Workspace       │ │
│  │ Registry/Executor│  │ Service         │  │ Services        │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Key Design Principles
1. **Separation of Concerns**: Each layer has a single responsibility
2. **Testability**: All layers can be unit tested in isolation
3. **Extensibility**: Easy to add new commands, UI components, and features
4. **Consistency**: All user actions flow through the command system
5. **Accessibility**: Keyboard-first design with screen reader support

## 📋 **REVISED Implementation Plan**

### **PRIORITY 1: Settings Foundation** 🏗️
*Duration: 2-3 days*
**Status: CRITICAL - Must implement before all UI components**

#### Files to Create:
```
core/settings/
├── __init__.py
├── schema.py               # JSON schema definitions for all settings
├── store.py               # QSettings wrapper with validation
├── service.py             # Settings service layer
├── defaults.py            # Default configuration values
└── migration.py           # Settings version migration

services/settings_service.py   # Service layer integration
```

#### Key Components:
```python
class SettingsStore:
    """QSettings wrapper with validation and type safety"""
    def get(self, key: str, default: Any = None) -> Any
    def set(self, key: str, value: Any) -> bool
    def validate_schema(self, data: Dict) -> bool
    
class SettingsService(Service):
    """Service layer for application settings"""
    def get_keyboard_shortcuts(self) -> Dict[str, str]
    def update_keyboard_shortcut(self, command_id: str, shortcut: str) -> bool
    def get_theme_settings(self) -> Dict[str, Any]
    def get_palette_settings(self) -> Dict[str, Any]
```

#### **Why This Must Be First:**
- Command palette persistence depends on settings
- Keyboard shortcut customization requires settings foundation
- Theme and appearance preferences need storage
- All UI state persistence flows through settings

---

### **PRIORITY 2: Context Integration** 🔌
*Duration: 1 day*
**Status: EXTENDS EXISTING SYSTEM**

#### Files to Create:
```
core/context/providers/
├── __init__.py
├── command_palette.py      # Command palette context provider
├── settings_dialog.py      # Settings dialog context provider
└── ui_state.py            # General UI state context provider
```

#### Integration Approach:
```python
class CommandPaletteContextProvider(ContextProvider):
    """Extends existing context system for command palette"""
    def get_context(self) -> Dict[str, Any]:
        return {
            ContextKey.COMMAND_PALETTE_VISIBLE: self.palette.isVisible(),
            ContextKey.COMMAND_PALETTE_FOCUS: self.palette.hasFocus(),
            # Use existing context keys, don't create new ones
        }
        
# Register with existing context manager
context_manager.register_provider(CommandPaletteContextProvider())
```

#### **Integration Points:**
- Use existing `ContextManager` singleton
- Extend existing `ContextKey` constants  
- Leverage existing `WhenClauseEvaluator` for command filtering
- Follow established `ContextProvider` pattern

---

### **PRIORITY 3: Command Palette (Revised)** 🎨
*Duration: 3-4 days*
**Status: INTEGRATES WITH EXISTING SEARCH & CONTEXT**

#### Files to Create:
```
ui/command_palette/
├── __init__.py
├── palette_widget.py        # Main palette UI (QDialog)
├── search_input.py         # Search input widget  
├── command_list.py         # Command list widget
├── palette_controller.py   # Controller logic
└── command_renderer.py     # Custom command list item
```

#### **Integration-First Implementation:**
```python
class CommandPaletteController:
    """Integrates with existing systems rather than duplicating"""
    def __init__(self):
        # Use existing command registry search
        self.registry = command_registry  # Don't create new search
        
        # Use existing context system
        self.context_manager = context_manager  # Don't create parallel state
        
        # Use existing settings system
        self.settings = settings_service  # Don't create separate persistence
    
    def search_commands(self, query: str) -> List[Command]:
        # Leverage existing search with scoring
        results = self.registry.search_commands(query)
        
        # Filter using existing when-clause evaluation
        current_context = self.context_manager.get_all()
        filtered = []
        for command in results:
            if command.can_execute(current_context):  # Uses existing evaluation
                filtered.append(command)
        
        return filtered
```

#### **Key Integration Points:**
- **Search**: Use `command_registry.search_commands()` (already has fuzzy matching)
- **Context**: Use `context_manager.get_all()` for current context
- **Filtering**: Use `command.can_execute()` with existing when-clause evaluation
- **Persistence**: Store history/preferences via new settings system
- **Theming**: Follow existing widget theming patterns

---

#### Key Features:

**Search & Filtering:**
- **Fuzzy Search**: Type "newt" → finds "New Terminal Tab"
- **Category Filtering**: Filter by command categories
- **Context Awareness**: Only show applicable commands
- **Search History**: Remember previous searches

**Keyboard Navigation:**
- **Arrow Keys**: Navigate up/down through results
- **Tab/Shift+Tab**: Navigate between search and results
- **Enter**: Execute selected command
- **Escape**: Close palette
- **Ctrl+Up/Down**: Jump to category boundaries

**Visual Design:**
- **VSCode-style appearance**: Dark theme with subtle borders
- **Command Icons**: Visual indicators for command types
- **Keyboard Shortcuts**: Show shortcuts next to commands
- **Category Grouping**: Group commands by category
- **Recently Used**: Special section for recent commands

#### Implementation Details:

```python
class CommandPaletteWidget(QDialog):
    """Main command palette dialog"""
    
    # Signals
    command_selected = Signal(str)  # Emitted when command chosen
    palette_hidden = Signal()       # Emitted when palette closes
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.setup_shortcuts()
        self.setup_styling()
    
    def show_palette(self):
        """Show palette and focus search input"""
        
    def filter_commands(self, query: str):
        """Filter commands based on search query"""
        
    def select_command(self, index: int):
        """Select command at given index"""

class CommandPaletteController:
    """Coordinates between palette UI and command services"""
    
    def __init__(self, palette_widget, command_registry, state_manager):
        self.palette = palette_widget
        self.registry = command_registry
        self.state = state_manager
    
    def show_palette(self):
        """Show command palette"""
        
    def handle_search(self, query: str):
        """Handle search query with fuzzy matching"""
        
    def execute_selected_command(self):
        """Execute the currently selected command"""
        
    def update_recent_commands(self, command_id: str):
        """Update recent command list"""
```

#### Tests:
- Fuzzy search algorithm accuracy
- Keyboard navigation behavior
- Command filtering and ranking
- UI state management
- Integration with command execution

---

### 3. Command History & Analytics
*Duration: 1-2 days*

#### Files to Create:
```
core/commands/analytics/
├── __init__.py
├── usage_tracker.py        # Track command usage patterns
├── recommendation.py       # Intelligent command suggestions
└── history_manager.py      # Manage command history
```

#### Features:
- **Usage Analytics**: Frequency, recency, time-of-day patterns
- **Smart Ranking**: Surface commands based on usage patterns
- **Contextual Suggestions**: Different commands for different contexts
- **Learning System**: Improve suggestions over time

#### Implementation:
```python
class CommandUsageTracker:
    """Tracks detailed command usage analytics"""
    
    def track_execution(self, command_id: str, context: Dict[str, Any]):
        """Track command execution with context"""
        
    def get_usage_stats(self, command_id: str) -> UsageStats:
        """Get detailed usage statistics for a command"""
        
    def get_recommendations(self, context: Dict[str, Any]) -> List[Command]:
        """Get recommended commands for current context"""

@dataclass
class UsageStats:
    total_executions: int
    last_executed: datetime
    average_executions_per_day: float
    contexts_used_in: List[str]
    time_patterns: Dict[int, int]  # hour -> frequency
```

---

### 4. Quick Action Toolbar
*Duration: 2-3 days*

#### Files to Create:
```
ui/toolbar/
├── __init__.py
├── quick_actions.py        # Main toolbar widget
├── action_button.py        # Individual command buttons
├── toolbar_controller.py   # Controller for toolbar logic
└── customization_dialog.py # Toolbar customization UI
```

#### Features:
- **Customizable Layout**: Users can add/remove/reorder buttons
- **Context-Aware Buttons**: Enable/disable based on current context
- **Icon Support**: Use command icons or fallback to text
- **Overflow Handling**: Gracefully handle too many buttons
- **Drag & Drop**: Intuitive customization

---

### 5. Context Menu System
*Duration: 2-3 days*

#### Files to Create:
```
ui/context_menu/
├── __init__.py
├── menu_builder.py         # Build context menus dynamically
├── menu_provider.py        # Abstract menu provider interface
├── providers/
│   ├── __init__.py
│   ├── workspace_provider.py    # Workspace context menus
│   ├── editor_provider.py       # Editor context menus
│   └── sidebar_provider.py      # Sidebar context menus
└── context_detector.py     # Detect current UI context
```

#### Features:
- **Context-Aware**: Different menus for different UI elements
- **Extensible**: Plugin system for new menu providers
- **Command Integration**: All menu items execute commands
- **Keyboard Navigation**: Full keyboard accessibility

---

### 6. Settings & Preferences UI
*Duration: 3-4 days*

#### Files to Create:
```
ui/settings/
├── __init__.py
├── settings_dialog.py      # Main settings dialog
├── pages/
│   ├── __init__.py
│   ├── general_page.py         # General preferences
│   ├── shortcuts_page.py       # Keyboard shortcut editor
│   ├── appearance_page.py      # Theme and appearance
│   └── commands_page.py        # Command-specific settings
├── widgets/
│   ├── __init__.py
│   ├── shortcut_editor.py      # Edit individual shortcuts
│   ├── conflict_resolver.py    # Handle shortcut conflicts
│   └── theme_selector.py       # Theme selection widget
└── settings_controller.py  # Settings logic controller

core/settings/
├── __init__.py
├── settings_manager.py     # Core settings management
├── schema.py              # Settings schema and validation
└── persistence.py         # Settings persistence layer
```

#### Features:
- **Tabbed Interface**: Organized by category
- **Shortcut Customization**: Visual shortcut editor with conflict detection
- **Theme Selection**: Light/Dark/High Contrast themes
- **Command Preferences**: Hide/show specific commands
- **Import/Export**: Settings portability
- **Real-time Preview**: Changes visible immediately

---

### 7. Command Feedback & Validation
*Duration: 1-2 days*

#### Files to Create:
```
ui/feedback/
├── __init__.py
├── notification_system.py  # Toast notification system
├── progress_manager.py     # Progress indicators
├── error_dialog.py        # Enhanced error reporting
└── undo_notification.py   # Undo-style notifications

core/commands/feedback/
├── __init__.py
├── result_processor.py    # Process command results
├── error_analyzer.py      # Analyze and categorize errors
└── suggestion_engine.py   # Suggest fixes for errors
```

#### Features:
- **Success Notifications**: Subtle confirmation of command execution
- **Error Messages**: Clear error reporting with suggested fixes
- **Progress Indicators**: For long-running commands
- **Undo Notifications**: "File saved. Undo?" style messages
- **Command Suggestions**: "Did you mean...?" for typos

---

### 8. Advanced Features
*Duration: 2-3 days*

#### Files to Create:
```
core/commands/advanced/
├── __init__.py
├── templates.py           # Command templates with parameters
├── macros.py             # Command macro recording/playback
├── workspace_commands.py  # Project-specific commands
└── aliases.py            # User-defined command aliases

ui/advanced/
├── __init__.py
├── template_dialog.py    # Template parameter input
├── macro_recorder.py     # Macro recording UI
└── alias_manager.py      # Command alias management
```

#### Features:
- **Command Templates**: "Open file in {language}" with parameter prompts
- **Command Macros**: Record and replay command sequences
- **Workspace Commands**: Commands specific to current project type
- **Command Aliases**: User-defined shortcuts for complex commands

---

## 🧪 Testing Strategy

### Test Coverage Goals
- **Target**: 95+ total tests (current: 66)
- **Coverage**: >90% line coverage
- **Performance**: All UI interactions <100ms response time

### Test Categories

#### Unit Tests (60+ tests)
```
tests/command_ui/
├── test_models.py          # State management tests
├── test_palette_logic.py   # Palette controller tests  
├── test_search.py          # Fuzzy search algorithm tests
├── test_settings.py        # Settings management tests
├── test_history.py         # Command history tests
└── test_feedback.py        # Notification system tests
```

#### Integration Tests (20+ tests)
```
tests/integration/
├── test_palette_workflow.py    # Full palette interaction
├── test_settings_persistence.py # Settings save/load
├── test_command_execution.py    # End-to-end command flow
└── test_keyboard_integration.py # Keyboard shortcut integration
```

#### UI Tests (15+ tests)
```
tests/ui/
├── test_palette_widget.py      # Palette UI behavior
├── test_settings_dialog.py     # Settings dialog behavior
├── test_context_menus.py       # Context menu behavior
└── test_accessibility.py       # Accessibility compliance
```

### Test Patterns Used
- **AAA Pattern**: Arrange, Act, Assert
- **Mock Services**: Mock external dependencies
- **Qt Test Framework**: For UI component testing
- **Parametric Tests**: Test multiple scenarios
- **Property-based Testing**: For fuzzy search algorithm

---

## 🎨 Design Patterns Reference

### 1. Model-View-Controller (MVC)
- **Models**: Pure data and business logic
- **Views**: UI components with minimal logic
- **Controllers**: Coordinate between models and views

### 2. Observer Pattern
- **State Changes**: UI components observe model changes
- **Event Handling**: Loose coupling between components

### 3. Command Pattern
- **User Actions**: All interactions become command objects
- **Undo/Redo**: Natural fit for command pattern
- **Macro Recording**: Commands can be combined

### 4. Strategy Pattern  
- **Search Algorithms**: Different search strategies
- **Ranking Systems**: Multiple ranking approaches
- **Menu Providers**: Different context menu strategies

### 5. Factory Pattern
- **UI Creation**: Dynamic UI component creation
- **Menu Building**: Dynamic menu construction
- **Command Creation**: Template-based command creation

### 6. Singleton Pattern (Existing)
- **Global Services**: Registry, executor, etc.
- **Settings Manager**: Global configuration access

### 7. Adapter Pattern
- **Service Integration**: Adapt existing services to new UI
- **Legacy Support**: Support old menu/toolbar systems

---

## 🔗 Integration Points

### Existing Systems Integration
1. **Command Registry**: Leverage existing 51 commands
2. **Keyboard Service**: Use existing shortcut system
3. **Service Layer**: Integrate with existing 5 services
4. **Main Window**: Add palette to existing window
5. **Theme System**: Use existing dark/light themes

### New System Dependencies
```
Command Palette → Command Registry → Commands
Settings UI → Settings Manager → Persistence
Context Menus → Context Detector → Menu Providers  
Feedback System → Command Executor → Result Processor
```

---

## 📈 **Updated Success Metrics**

### **Integration Metrics** (New Priority)
- ✅ **Context Integration**: 100% compatibility with existing context system (40+ keys)
- ✅ **Search Integration**: Use existing `command_registry.search_commands()` without duplication
- ✅ **Settings Foundation**: Complete settings system supporting all UI persistence
- ✅ **Architecture Consistency**: Zero competing systems, all extensions follow existing patterns

### **Functionality Metrics**
- ✅ **Command Accessibility**: All 51 commands accessible via palette
- ✅ **Search Performance**: <100ms response leveraging existing search (was sub-second)
- ✅ **Context Filtering**: Real-time command filtering using existing when-clause evaluation  
- ✅ **Customization**: Users can customize shortcuts via integrated settings system

### **Quality Metrics**  
- ✅ **Test Coverage**: >95% line coverage (increased from 90% due to integration complexity)
- ✅ **Performance**: UI interactions <100ms, context evaluation <10ms
- ✅ **Memory Usage**: <30MB additional (reduced from 50MB due to reuse of existing systems)
- ✅ **Integration Testing**: 100% compatibility with existing 66 tests

### **User Experience Metrics**
- ✅ **Keyboard Accessibility**: 100% functionality via existing keyboard service
- ✅ **Error Handling**: Integrated with existing error handling patterns
- ✅ **Consistency**: Uses existing themes, widgets, and interaction patterns
- ✅ **Context Awareness**: Commands filtered based on 40+ existing context keys

---

## 🚀 **REVISED Implementation Timeline**

### **Phase 1: Foundation (Days 1-4)**
- ✅ **Day 1-2**: Settings System Infrastructure
  - Core settings store with QSettings integration
  - JSON schema validation and migration system
  - Settings service integration
- ✅ **Day 3**: Context System Integration
  - Command palette context providers
  - Integration with existing context manager
  - Extend existing context keys as needed
- ✅ **Day 4**: Command History Foundation
  - Usage tracking via settings system
  - Analytics and recommendation engine base

### **Phase 2: Command Palette MVP (Days 5-8)**  
- ✅ **Day 5-6**: Command Palette Core UI
  - Basic QDialog with existing theme integration
  - Search input with existing command registry
  - Command list with existing context filtering
- ✅ **Day 7-8**: Command Palette Polish
  - Keyboard navigation and shortcuts
  - Context-aware command filtering
  - History and usage tracking integration

### **Phase 3: UI Components (Days 9-13)**
- ✅ **Day 9-11**: Settings & Preferences UI
  - Tabbed settings dialog
  - Keyboard shortcut customization editor
  - Theme and appearance preferences
- ✅ **Day 12-13**: Context Menu System
  - Dynamic menu builder using existing context
  - Menu providers for different UI elements

### **Phase 4: Polish & Advanced (Days 14-17)**
- ✅ **Day 14**: Command Feedback & Validation Systems
- ✅ **Day 15**: Quick Action Toolbar (Optional)
- ✅ **Day 16-17**: Advanced Features & Final Integration

### **Critical Milestones**
- **Day 2**: Settings foundation complete (enables all other persistence)
- **Day 4**: Context integration complete (enables proper command filtering) 
- **Day 8**: MVP Command Palette working with existing systems
- **Day 13**: Complete UI component set implemented
- **Day 17**: Production-ready integrated system

### **Risk Mitigation**
- **Settings dependency**: Must complete before any UI persistence
- **Context integration**: Requires understanding of existing evaluation system
- **Testing**: All integration points must be thoroughly tested

---

## 📝 Documentation Plan

### Developer Documentation
- **Architecture Guide**: Detailed MVC pattern explanation
- **API Reference**: All public classes and methods
- **Extension Guide**: How to add new commands/features
- **Testing Guide**: How to write tests for command UI

### User Documentation
- **Command Palette Guide**: How to use the command palette
- **Keyboard Shortcuts**: Complete shortcut reference
- **Customization Guide**: How to customize the interface
- **Troubleshooting**: Common issues and solutions

### Code Documentation
- **Inline Comments**: Explain complex algorithms
- **Docstrings**: Complete API documentation
- **Type Hints**: Full type annotation coverage
- **Examples**: Usage examples for all public APIs

---

## 🔧 Technical Considerations

### Performance Optimization
- **Lazy Loading**: Load UI components on demand
- **Caching**: Cache search results and command metadata
- **Debouncing**: Debounce search input to reduce CPU usage
- **Virtual Lists**: Handle large command lists efficiently

### Accessibility
- **Screen Reader Support**: ARIA labels and roles
- **High Contrast**: Support for high contrast themes  
- **Keyboard Navigation**: Full keyboard accessibility
- **Focus Management**: Proper focus handling throughout

### Internationalization (Future)
- **String Externalization**: All UI strings in resource files
- **RTL Support**: Right-to-left language support
- **Cultural Adaptation**: Date/time formatting

### Error Handling
- **Graceful Degradation**: UI works even if services fail
- **User-Friendly Messages**: Clear, actionable error messages
- **Logging**: Comprehensive logging for debugging
- **Recovery**: Automatic recovery from transient failures

---

## 🔄 Future Extensions

### Potential Phase 6 Features
- **AI-Powered Suggestions**: Machine learning for command recommendations
- **Voice Commands**: Voice-to-command translation
- **Extension Marketplace**: Third-party command extensions
- **Cloud Sync**: Sync settings and preferences across devices
- **Collaboration**: Share command macros and templates
- **Analytics Dashboard**: Usage analytics and insights

### Plugin System Architecture
```
Plugin API → Extension Manager → Command Registry
     ↓              ↓                    ↓
Plugin Commands → UI Extensions → Theme Extensions
```

---

This comprehensive plan provides a roadmap for completing ViloApp's command system with production-ready UI components that match the quality and usability of modern IDE command systems like VSCode.