# ViloxTerm Next Generation (NG) - Plugin Architecture Vision

> **Status**: Future Project Concept  
> **Created**: December 2024  
> **Type**: Architecture Design Document  

## Executive Summary

This document outlines the vision for transforming ViloxTerm from its current monolithic desktop application into a next-generation, extensible plugin framework. Drawing inspiration from successful plugin architectures like VS Code, Jupyter, and IntelliJ IDEA, ViloxTerm-NG would become a minimal core framework that can be extended through a rich plugin ecosystem.

### Vision Statement
*Transform ViloxTerm into the VS Code of desktop applications - a lightweight, extensible framework where functionality is delivered through plugins rather than monolithic features.*

### Key Goals
- **Modularity**: Convert built-in widgets (Terminal, Editor) into plugins
- **Extensibility**: Enable community-developed plugins 
- **Performance**: Lazy loading and resource management
- **Security**: Process isolation and permission system
- **Developer Experience**: Rich SDK and development tools
- **Ecosystem**: Plugin marketplace and distribution

---

## Current Architecture Analysis

### What We Have Now ✅
- **AppWidget Base Class**: Solid foundation for content widgets
- **Widget Registry**: Central registration system for widget types
- **Command Pattern**: Robust command architecture with registry
- **Service Layer**: Business logic separated from UI components
- **Theme System**: Consistent theming across components
- **State Persistence**: QSettings-based state management

### Current Limitations ❌
- **Monolithic Structure**: Terminal and Editor hardcoded into source
- **Static Widget Types**: Cannot add new widget types without code changes
- **No Plugin System**: All functionality must be built into core
- **Resource Coupling**: All widgets share the same process/resources
- **Limited Extensibility**: Third parties cannot extend functionality
- **Distribution Constraints**: Cannot install/uninstall features independently

---

## Research Findings: Learning from Industry Leaders

### VS Code Architecture Insights

**Process Isolation**
- Extensions run in separate Node.js process (Extension Host)
- Main UI cannot be broken by misbehaving extensions
- Late loading - extensions only activate when needed
- No direct DOM access prevents UI corruption

**Contribution Points**
- Predefined extension points: commands, views, themes, languages
- Declarative contributions in package.json manifest
- Type-safe extension APIs

**Activation Events**
- Granular control: onLanguage, onCommand, onFileSystem
- Performance optimization through lazy loading

### Jupyter Architecture Insights

**Service Provider Pattern**
- Dependency injection system for plugin communication
- Plugins can provide and consume services
- Clean separation of concerns

**Mime Renderers**
- Specialized extension type for content rendering
- Prebuilt extensions - no rebuild required
- Server-side extensions can extend both client and server

### IntelliJ Architecture Insights

**Massive Plugin Ecosystem**
- 8000+ plugins demonstrates scalability
- Custom UI components ensure consistency
- Domain context providers for framework-specific understanding
- GPU acceleration for performance

**Key Architectural Patterns**
- Service-oriented architecture
- Contribution-based extension system  
- Resource management and monitoring
- Robust error handling and recovery

---

## Proposed Plugin Architecture Design

### Core Framework Structure

```
viloapp-core/                      # Minimal core framework
├── viloapp/
│   ├── core/
│   │   ├── plugin/                # Plugin system
│   │   │   ├── host.py           # Plugin host process
│   │   │   ├── sandbox.py        # Security sandbox
│   │   │   ├── loader.py         # Plugin discovery & loading
│   │   │   ├── registry.py       # Plugin registry
│   │   │   ├── marketplace.py    # Plugin marketplace client
│   │   │   ├── events.py         # Inter-plugin event system
│   │   │   └── resources.py      # Resource management
│   │   ├── services/
│   │   │   ├── registry.py       # Service registry
│   │   │   └── injection.py      # Dependency injection
│   │   ├── contributions/
│   │   │   ├── commands.py       # Command contributions
│   │   │   ├── views.py          # View contributions
│   │   │   ├── themes.py         # Theme contributions
│   │   │   └── languages.py      # Language support
│   │   ├── api/
│   │   │   ├── secure.py         # Secure plugin API
│   │   │   ├── permissions.py    # Permission system
│   │   │   └── ipc.py            # Inter-process communication
│   │   └── commands/             # Core command system (existing)
│   ├── ui/                       # Core UI shell only
│   │   ├── main_window.py        # Application shell
│   │   ├── activity_bar.py       # Plugin activation points
│   │   ├── sidebar.py            # Plugin container
│   │   └── workspace.py          # Plugin content area
│   └── dev/                      # Development tools
│       ├── debug.py              # Plugin debugging
│       ├── profiler.py           # Performance profiling
│       ├── hot_reload.py         # Hot reloading
│       └── scaffold.py           # Plugin scaffolding
├── builtin_plugins/              # Essential plugins
│   └── welcome/                  # Welcome screen only
└── sdk/                          # Plugin SDK
    └── viloapp_sdk/
        ├── widgets/              # Widget development API
        ├── commands/             # Command development API
        ├── services/             # Service development API
        └── testing/              # Testing utilities
```

### Plugin Structure

Each plugin would be a complete Python package:

```
viloapp-terminal/                  # Example plugin
├── viloapp_terminal/
│   ├── __init__.py
│   ├── plugin.py                 # Plugin entry point
│   ├── widgets/
│   │   └── terminal_widget.py
│   ├── services/
│   │   └── terminal_service.py
│   ├── commands/
│   │   └── terminal_commands.py
│   └── assets/
│       ├── xterm.js
│       └── styles.css
├── tests/
├── plugin.yaml                   # Plugin manifest
├── setup.py                      # Python package setup
├── pyproject.toml               # Modern packaging
└── README.md
```

### Plugin Manifest Format

```yaml
# plugin.yaml
name: terminal
id: com.viloapp.terminal
version: 1.0.0
author: ViloApp Team
description: Terminal emulator for ViloApp
main: viloapp_terminal.plugin:TerminalPlugin

requires:
  viloapp-core: ">=1.0.0"
  python: ">=3.8"

dependencies:
  - xterm-js: ">=4.0.0"
  - websocket-client: ">=1.0.0"

provides:
  widgets:
    - id: terminal
      class: TerminalWidget
      factory: create_terminal_widget
  services:
    - id: terminal
      class: TerminalService
  commands:
    - id: terminal.new
      title: New Terminal
      category: Terminal

contributions:
  commands:
    - id: "terminal.new"
      title: "New Terminal" 
      category: "Terminal"
      shortcut: "ctrl+shift+`"
  views:
    - id: "terminal.tabs"
      name: "Terminal Tabs"
      location: "sidebar"
  activityBar:
    - id: "terminal"
      title: "Terminal"
      icon: "terminal"

activationEvents:
  - "onStartup"
  - "onCommand:terminal.new"
  - "onView:terminal.tabs"

permissions:
  - "filesystem:read"
  - "shell:execute"
  - "network:outbound"

marketplace:
  category: "Development Tools"
  tags: ["terminal", "shell", "command-line"]
  license: "MIT"
  homepage: "https://github.com/viloapp/terminal-plugin"
  screenshots: ["preview.png", "settings.png"]
```

### Security & Sandboxing

```python
# Plugin security model
class PluginSandbox:
    """Isolates plugins and controls their access to system resources."""
    
    def __init__(self, plugin_id: str, permissions: List[str]):
        self.plugin_id = plugin_id
        self.permissions = permissions
        self.resource_limits = ResourceLimits()
        
    def check_permission(self, action: str) -> bool:
        """Check if plugin has permission for action."""
        return action in self.permissions
        
    def limit_resources(self, memory_mb: int, cpu_percent: int):
        """Set resource limits for plugin process."""
        pass
        
    def isolate_filesystem(self, allowed_paths: List[Path]):
        """Restrict filesystem access to specific paths."""
        pass

class PluginPermissions:
    """Available permissions for plugins."""
    FILESYSTEM_READ = "filesystem:read"
    FILESYSTEM_WRITE = "filesystem:write" 
    NETWORK_OUTBOUND = "network:outbound"
    NETWORK_INBOUND = "network:inbound"
    SHELL_EXECUTE = "shell:execute"
    UI_MODIFY = "ui:modify"
    SYSTEM_INFO = "system:info"
```

### Service Provider Architecture

```python
# Jupyter-inspired service system
class ServiceRegistry:
    """Central registry for all services with dependency injection."""
    
    def __init__(self):
        self._providers = {}
        self._services = {}
        self._dependencies = {}
        
    def register_provider(self, service_id: str, provider_class: Type):
        """Register a service provider."""
        self._providers[service_id] = provider_class
        
    def require_service(self, service_id: str, consumer: str):
        """Declare service dependency."""
        if consumer not in self._dependencies:
            self._dependencies[consumer] = []
        self._dependencies[consumer].append(service_id)
        
    def get_service(self, service_id: str) -> Optional[Any]:
        """Get instantiated service."""
        if service_id not in self._services:
            provider = self._providers.get(service_id)
            if provider:
                self._services[service_id] = provider()
        return self._services.get(service_id)
        
    def resolve_dependencies(self) -> List[str]:
        """Resolve all dependencies and return load order."""
        pass

# Example plugin using services
class TerminalPlugin(Plugin):
    provides = ["terminal.service"]
    requires = ["editor.service", "workspace.service", "file.service"]
    
    def activate(self, context: PluginContext):
        # Get required services
        editor_service = context.services.get("editor.service")
        workspace_service = context.services.get("workspace.service")
        
        # Provide terminal service
        terminal_service = TerminalService(editor_service, workspace_service)
        context.services.register("terminal.service", terminal_service)
```

### Contribution Points System

```python
# VS Code-inspired contribution system
class ContributionRegistry:
    """Registry for plugin contributions."""
    
    def __init__(self):
        self._contributions = {
            'commands': {},
            'views': {},
            'activityBar': {},
            'contextMenus': {},
            'themes': {},
            'languages': {},
        }
    
    def register_contribution(self, type: str, contrib: Dict[str, Any]):
        """Register a plugin contribution."""
        self._contributions[type][contrib['id']] = contrib
        
    def get_contributions(self, type: str) -> Dict[str, Any]:
        """Get all contributions of a specific type."""
        return self._contributions.get(type, {})

# Plugin declares contributions
class MarkdownPlugin(Plugin):
    def register_contributions(self, context: PluginContext):
        # Register commands
        context.contributions.register_contribution('commands', {
            'id': 'markdown.preview',
            'title': 'Markdown: Show Preview',
            'category': 'Markdown',
            'handler': self.show_preview
        })
        
        # Register view
        context.contributions.register_contribution('views', {
            'id': 'markdown.outline',
            'title': 'Outline',
            'location': 'sidebar',
            'widget_class': MarkdownOutlineWidget
        })
```

### Plugin Event System

```python
# Inter-plugin communication via events
class PluginEventBus:
    """Event system for plugin communication."""
    
    def __init__(self):
        self._subscribers = defaultdict(list)
        
    def subscribe(self, event: str, handler: Callable, plugin_id: str):
        """Subscribe to events from other plugins."""
        self._subscribers[event].append((handler, plugin_id))
        
    def publish(self, event: str, data: Any, publisher: str):
        """Publish event to all subscribers."""
        for handler, subscriber_id in self._subscribers[event]:
            try:
                handler(data, publisher)
            except Exception as e:
                logger.error(f"Event handler error in {subscriber_id}: {e}")
                
    def unsubscribe(self, plugin_id: str):
        """Remove all subscriptions for a plugin."""
        for event, subscribers in self._subscribers.items():
            self._subscribers[event] = [
                (h, p) for h, p in subscribers if p != plugin_id
            ]

# Plugin usage
class GitPlugin(Plugin):
    def activate(self, context: PluginContext):
        # Subscribe to file events
        context.events.subscribe('file.saved', self.on_file_saved)
        context.events.subscribe('file.opened', self.check_git_status)
        
    def on_file_saved(self, data: Dict, publisher: str):
        file_path = data['path']
        # Update git status for file
        
class EditorPlugin(Plugin):
    def save_file(self, file_path: str):
        # Save file
        self.context.events.publish('file.saved', {'path': file_path})
```

---

## Migration Strategy

### Phase 1: Foundation (Months 1-3)
**Goal**: Create plugin infrastructure without breaking existing functionality

**Tasks**:
- [ ] Design and implement plugin loader system
- [ ] Create plugin base classes and context API
- [ ] Build contribution points registry
- [ ] Implement basic service provider system
- [ ] Add plugin manifest parsing
- [ ] Create development tools and debugging support

**Deliverables**:
- Working plugin system that can load simple plugins
- Existing widgets still work as before (no regression)
- Basic SDK for plugin development

### Phase 2: Internal Plugin Conversion (Months 4-6) 
**Goal**: Convert existing widgets to plugins while maintaining monorepo structure

**Tasks**:
- [ ] Extract Terminal widget to internal plugin
- [ ] Extract Editor widget to internal plugin  
- [ ] Extract Explorer functionality to plugin
- [ ] Create builtin plugin loader for development
- [ ] Implement hot reloading for development
- [ ] Add comprehensive testing for plugin system

**Deliverables**:
- Terminal and Editor work as plugins in monorepo
- Plugin hot reloading works for development
- No user-visible changes to functionality

### Phase 3: External Plugin Support (Months 7-9)
**Goal**: Enable installation of external plugins

**Tasks**:
- [ ] Implement plugin marketplace client
- [ ] Add pip-based plugin installation
- [ ] Create plugin packaging and distribution tools
- [ ] Build plugin security sandbox
- [ ] Add resource monitoring and limits
- [ ] Create plugin management UI

**Deliverables**:
- Users can install plugins via pip
- Basic plugin marketplace integration
- Security sandbox protects main application

### Phase 4: SDK & Ecosystem (Months 10-12)
**Goal**: Enable community plugin development

**Tasks**:
- [ ] Publish comprehensive plugin SDK
- [ ] Create plugin development documentation
- [ ] Build plugin scaffolding tools
- [ ] Implement plugin validation system
- [ ] Launch plugin marketplace
- [ ] Create example plugins and tutorials

**Deliverables**:
- Published viloapp-sdk package
- Plugin marketplace with community plugins
- Documentation and examples for plugin developers

---

## SDK Design & Developer Experience

### Installation & Getting Started

```bash
# Install the SDK
pip install viloapp-sdk

# Create new plugin project
viloapp-sdk create-plugin my-markdown-editor
cd my-markdown-editor

# Generated structure
tree .
my-markdown-editor/
├── plugin.yaml                   # Plugin manifest
├── src/
│   ├── __init__.py
│   ├── plugin.py                 # Plugin entry point
│   ├── widgets/
│   │   └── markdown_widget.py
│   ├── commands/
│   └── services/
├── resources/
│   ├── icons/
│   └── styles/
├── tests/
├── setup.py
└── README.md
```

### Plugin Development API

```python
# SDK provides rich development experience
from viloapp_sdk import AppWidget, Plugin, widget
from viloapp_sdk.decorators import auto_save, theme_aware
from viloapp_sdk.api import CommandAPI, ServiceAPI, UIAPi

@widget(
    id="markdown-editor",
    title="Markdown Editor", 
    icon="file-text",
    file_extensions=[".md", ".markdown"]
)
@theme_aware  # Automatically handles theme changes
@auto_save(interval=30)  # Auto-save every 30 seconds
class MarkdownEditorWidget(AppWidget):
    """Rich markdown editor with live preview."""
    
    def __init__(self, widget_id: str, context):
        super().__init__(widget_id, context)
        self.context = context  # Plugin API access
        self.setup_ui()
        
    def setup_ui(self):
        """Use SDK components for consistent UI."""
        # Create toolbar with SDK utilities
        self.toolbar = self.context.ui.create_toolbar()
        self.toolbar.add_action("bold", "Bold", self.make_bold)
        
        # Create split view with editor and preview
        self.editor = self.context.ui.create_code_editor(
            language="markdown",
            line_numbers=True,
            word_wrap=True
        )
        
        self.preview = self.context.ui.create_web_view()
        
        # SDK handles layout and theming automatically
        
    def load_file(self, file_path: str):
        """SDK handles file operations."""
        content = self.context.storage.read_file(file_path)
        self.editor.set_text(content)
        
    def save_file(self, file_path: str = None):
        """SDK provides file dialogs."""
        if not file_path:
            file_path = self.context.ui.get_save_file_path(
                filter="Markdown Files (*.md *.markdown)"
            )
        
        if file_path:
            self.context.storage.write_file(file_path, self.editor.get_text())

class MarkdownPlugin(Plugin):
    """Main plugin class."""
    
    provides = ["markdown.parser", "markdown.renderer"] 
    requires = ["editor.service", "file.service"]
    
    def activate(self, context):
        # Register widget
        context.widgets.register("markdown-editor", MarkdownEditorWidget)
        
        # Register commands
        context.commands.register("markdown.preview", self.show_preview)
        
        # Subscribe to events
        context.events.subscribe("file.opened", self.on_file_opened)
```

### Development Tools

```bash
# SDK provides comprehensive development tools

# Validate plugin
viloapp-sdk validate

# Run tests with framework
viloapp-sdk test

# Start development server with hot reload
viloapp-sdk dev

# Debug plugin in isolation
viloapp-sdk debug --plugin=markdown-editor

# Profile plugin performance  
viloapp-sdk profile --plugin=markdown-editor

# Package for distribution
viloapp-sdk package

# Publish to marketplace
viloapp-sdk publish --marketplace=viloapp
```

### Plugin Testing Framework

```python
# SDK provides testing utilities
from viloapp_sdk.testing import PluginTestCase, mock_context
from src.widgets.markdown_widget import MarkdownEditorWidget

class TestMarkdownEditor(PluginTestCase):
    def setUp(self):
        self.context = mock_context()
        self.widget = MarkdownEditorWidget("test-1", self.context) 
        
    def test_file_operations(self):
        """Test file loading and saving."""
        # Mock file system
        self.context.storage.mock_file("test.md", "# Test Content")
        
        # Test loading
        self.widget.load_file("test.md")
        self.assertEqual(self.widget.editor.get_text(), "# Test Content")
        
        # Test saving
        self.widget.editor.set_text("# Modified Content")
        self.widget.save_file("test.md")
        
        saved_content = self.context.storage.read_file("test.md")
        self.assertEqual(saved_content, "# Modified Content")
        
    def test_preview_updates(self):
        """Test that preview updates on content change."""
        with self.assert_signal_emitted(self.widget.preview_updated):
            self.widget.editor.set_text("# New Content")
```

---

## Implementation Challenges & Solutions

### Challenge 1: Process Isolation
**Problem**: How to safely isolate plugins without breaking performance?

**Solution**: 
- Use Python multiprocessing for true isolation
- Implement efficient IPC (Inter-Process Communication) layer
- Share read-only data via memory mapping
- Cache frequently accessed APIs

```python
# Plugin host process architecture
class PluginHost:
    """Manages plugin in isolated process."""
    
    def __init__(self, plugin_id: str):
        self.plugin_id = plugin_id
        self.process = None
        self.ipc_channel = None
        
    def start(self):
        """Start plugin in separate process."""
        self.process = Process(target=self._run_plugin)
        self.ipc_channel = IPCChannel(self.plugin_id)
        self.process.start()
        
    def _run_plugin(self):
        """Plugin entry point in isolated process."""
        # Load plugin with restricted API access
        # Set up resource monitoring
        # Handle IPC communications
```

### Challenge 2: Performance Impact
**Problem**: Plugin system might slow down application startup.

**Solution**:
- Lazy loading - plugins activate only when needed
- Prebuilt plugin bundles for faster loading
- Aggressive caching of plugin metadata
- Parallel plugin initialization where possible

### Challenge 3: API Stability
**Problem**: Maintaining backward compatibility as core evolves.

**Solution**:
- Semantic versioning for plugin API
- Deprecation warnings and migration guides
- API compatibility shims for older plugins
- Plugin API version negotiation

### Challenge 4: Resource Management  
**Problem**: Preventing plugins from consuming too many resources.

**Solution**:
```python
class ResourceManager:
    """Monitor and limit plugin resource usage."""
    
    def __init__(self):
        self.limits = {}
        self.monitors = {}
        
    def set_limits(self, plugin_id: str, memory_mb: int, cpu_percent: int):
        """Set resource limits for plugin."""
        self.limits[plugin_id] = {
            'memory': memory_mb * 1024 * 1024,  # Convert to bytes
            'cpu': cpu_percent / 100.0
        }
        
    def monitor_plugin(self, plugin_id: str):
        """Start monitoring plugin resource usage."""
        monitor = ResourceMonitor(plugin_id, self.limits.get(plugin_id))
        self.monitors[plugin_id] = monitor
        monitor.start()
        
    def kill_plugin_if_exceeded(self, plugin_id: str):
        """Terminate plugin if it exceeds limits.""" 
        monitor = self.monitors.get(plugin_id)
        if monitor and monitor.has_exceeded_limits():
            self.terminate_plugin(plugin_id)
            self.notify_user(f"Plugin {plugin_id} terminated for exceeding limits")
```

### Challenge 5: Plugin Dependencies
**Problem**: Managing complex dependency chains between plugins.

**Solution**:
- Dependency resolution algorithm similar to package managers
- Plugin dependency graph validation
- Graceful handling of missing dependencies
- Version conflict resolution

```python
class DependencyResolver:
    """Resolves plugin dependencies and load order."""
    
    def resolve(self, plugins: List[PluginInfo]) -> List[PluginInfo]:
        """Return plugins in dependency order.""" 
        graph = self._build_dependency_graph(plugins)
        return self._topological_sort(graph)
        
    def _build_dependency_graph(self, plugins: List[PluginInfo]) -> Dict:
        """Build directed graph of plugin dependencies."""
        pass
        
    def _topological_sort(self, graph: Dict) -> List[PluginInfo]:
        """Sort plugins by dependency order."""
        pass
```

---

## Success Metrics & Goals

### Technical Metrics
- [ ] **Plugin Load Time**: < 500ms for typical plugin
- [ ] **Memory Overhead**: < 10% additional memory usage for plugin system  
- [ ] **Resource Isolation**: 99.9% uptime even with failing plugins
- [ ] **API Stability**: Maintain backward compatibility across minor versions
- [ ] **Hot Reload Time**: < 1 second for plugin updates during development

### Ecosystem Metrics
- [ ] **Community Plugins**: 50+ community-developed plugins within 1 year
- [ ] **Plugin Downloads**: 10,000+ plugin installations per month
- [ ] **Developer Adoption**: 100+ developers contributing plugins
- [ ] **Plugin Marketplace**: Featured plugin showcase with ratings/reviews
- [ ] **Documentation Quality**: < 30 minutes from idea to working plugin

### User Experience Metrics
- [ ] **Installation Success Rate**: 95%+ successful plugin installations
- [ ] **User Satisfaction**: 4.5+ star average rating for plugin system
- [ ] **Support Requests**: < 5% of issues related to plugin problems
- [ ] **Feature Coverage**: 80%+ of current monolithic features available as plugins

---

## Comparison: Current vs Next-Generation

| Aspect | Current ViloApp | ViloApp-NG |
|--------|-----------------|------------|
| **Architecture** | Monolithic | Plugin-based |
| **Extensibility** | Code changes required | Plugin installation |
| **Performance** | All features loaded | Lazy loading |
| **Distribution** | Single package | Core + plugins |
| **Community** | Core team only | Community contributors |
| **Security** | Shared process | Process isolation |
| **Development** | Full rebuild | Hot reloading |
| **Dependencies** | All bundled | Per-plugin dependencies |
| **Size** | Large installation | Minimal core |
| **Updates** | All-or-nothing | Individual plugin updates |

---

## Conclusion & Next Steps

The transformation to ViloApp-NG represents a fundamental shift in how we think about desktop application architecture. By adopting proven patterns from VS Code, Jupyter, and IntelliJ, we can create a more flexible, performant, and community-friendly platform.

### Immediate Actions
1. **Validate Assumptions**: Build prototype plugin system to test key concepts
2. **Architecture Review**: Get stakeholder input on proposed architecture
3. **Resource Planning**: Estimate development resources for 12-month timeline  
4. **Risk Assessment**: Identify potential technical and business risks
5. **Community Engagement**: Gauge developer interest in plugin ecosystem

### Long-term Vision
ViloApp-NG positions us to become the premier platform for desktop application development in Python, offering the flexibility of VS Code with the power of native desktop applications. This transformation will enable:

- **Faster Innovation**: New features delivered as plugins rather than core updates
- **Community Growth**: Third-party developers extending our platform
- **Market Expansion**: Specialized plugins for different industries/use cases
- **Sustainable Development**: Distributed maintenance across plugin ecosystem

This document serves as our north star for the next evolution of ViloApp. The proposed architecture is ambitious but achievable, drawing from proven patterns while addressing the unique challenges of PySide6/Qt desktop applications.

---

*This document is a living specification and will be updated as we refine the architecture and implementation details.*