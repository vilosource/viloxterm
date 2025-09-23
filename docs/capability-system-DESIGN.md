# Capability-Based Architecture Design

**Date**: 2025-01-23
**Phase**: 1.3 - Capability System Architecture
**Status**: COMPLETE

## Executive Summary

Design of a **capability-based architecture** that transforms ViloxTerm from widget-aware to widget-agnostic. The platform will interact with widgets through **declared capabilities** rather than specific widget types, enabling true plugin extensibility and clean separation of concerns.

## 🎯 Core Principles

### 1. Capability-Driven Interactions
**Principle**: Commands target capabilities, not specific widgets.
```python
# Current (WRONG): Command knows about specific widgets
if widget_type == "terminal":
    widget.clear_terminal()

# New (CORRECT): Command targets capability
execute_capability("clear_display", active_widget)
```

### 2. Self-Describing Widgets
**Principle**: Widgets declare their own capabilities.
```python
class TerminalWidget:
    def get_capabilities(self) -> Set[WidgetCapability]:
        return {
            WidgetCapability.SHELL_EXECUTION,
            WidgetCapability.TEXT_INPUT,
            WidgetCapability.CLIPBOARD_OPERATIONS,
            WidgetCapability.CLEAR_DISPLAY
        }
```

### 3. Dynamic Capability Discovery
**Principle**: Platform discovers capabilities at runtime.
```python
# Platform never hardcodes widget knowledge
capable_widgets = capability_manager.find_widgets_with_capability(
    WidgetCapability.TEXT_EDITING
)
```

## 🔧 Architecture Components

### 1. Capability Enumeration

```python
from enum import Enum
from typing import Set, Optional, Dict, Any

class WidgetCapability(Enum):
    """Core widget capabilities that platform can interact with."""

    # === Text Operations ===
    TEXT_EDITING = "text_editing"
    TEXT_VIEWING = "text_viewing"
    TEXT_INPUT = "text_input"
    TEXT_SELECTION = "text_selection"
    TEXT_SEARCH = "text_search"

    # === Display Operations ===
    CLEAR_DISPLAY = "clear_display"
    SCROLL_CONTENT = "scroll_content"
    ZOOM_CONTENT = "zoom_content"
    SYNTAX_HIGHLIGHTING = "syntax_highlighting"

    # === File Operations ===
    FILE_VIEWING = "file_viewing"
    FILE_EDITING = "file_editing"
    FILE_SAVING = "file_saving"
    FILE_OPENING = "file_opening"

    # === Clipboard Operations ===
    CLIPBOARD_COPY = "clipboard_copy"
    CLIPBOARD_PASTE = "clipboard_paste"
    CLIPBOARD_CUT = "clipboard_cut"

    # === Shell Operations ===
    SHELL_EXECUTION = "shell_execution"
    COMMAND_RUNNING = "command_running"
    PROCESS_MANAGEMENT = "process_management"

    # === Navigation Operations ===
    FIND_AND_REPLACE = "find_and_replace"
    GOTO_LINE = "goto_line"
    NAVIGATE_HISTORY = "navigate_history"

    # === UI Operations ===
    SPLIT_VIEW = "split_view"
    FOCUS_MANAGEMENT = "focus_management"
    CONTEXT_MENU = "context_menu"

    # === Development Operations ===
    CODE_COMPLETION = "code_completion"
    DEBUGGING = "debugging"
    VERSION_CONTROL = "version_control"
```

### 2. Capability Registration System

```python
from dataclasses import dataclass
from typing import Callable, Any

@dataclass
class CapabilityHandler:
    """Handler for a specific capability."""
    capability: WidgetCapability
    method_name: str
    handler: Callable[[Any, ...], Any]
    parameters: Dict[str, type] = None
    description: str = ""

class ICapabilityProvider(ABC):
    """Interface for widgets that provide capabilities."""

    @abstractmethod
    def get_capabilities(self) -> Set[WidgetCapability]:
        """Return set of capabilities this widget provides."""
        pass

    @abstractmethod
    def get_capability_handler(self, capability: WidgetCapability) -> Optional[CapabilityHandler]:
        """Get handler for specific capability."""
        pass

    @abstractmethod
    def supports_capability(self, capability: WidgetCapability) -> bool:
        """Check if widget supports a capability."""
        pass

class CapabilityManager:
    """Central manager for widget capabilities."""

    def __init__(self):
        self._widget_capabilities: Dict[str, Set[WidgetCapability]] = {}
        self._capability_handlers: Dict[str, Dict[WidgetCapability, CapabilityHandler]] = {}

    def register_widget(self, widget_id: str, widget: ICapabilityProvider):
        """Register widget's capabilities."""
        capabilities = widget.get_capabilities()
        self._widget_capabilities[widget_id] = capabilities

        # Cache handlers for efficiency
        handlers = {}
        for capability in capabilities:
            handler = widget.get_capability_handler(capability)
            if handler:
                handlers[capability] = handler
        self._capability_handlers[widget_id] = handlers

    def find_widgets_with_capability(self, capability: WidgetCapability) -> List[str]:
        """Find all widgets that support a capability."""
        return [
            widget_id for widget_id, capabilities in self._widget_capabilities.items()
            if capability in capabilities
        ]

    def execute_capability(self, widget_id: str, capability: WidgetCapability, **kwargs) -> Any:
        """Execute capability on specific widget."""
        if widget_id not in self._capability_handlers:
            raise ValueError(f"Widget {widget_id} not registered")

        handler = self._capability_handlers[widget_id].get(capability)
        if not handler:
            raise ValueError(f"Widget {widget_id} does not support capability {capability}")

        return handler.handler(**kwargs)
```

### 3. Command Delegation System

```python
@dataclass
class CapabilityCommand:
    """Command that targets capabilities instead of specific widgets."""

    id: str
    title: str
    capability_required: WidgetCapability
    method_name: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    fallback_behavior: Optional[Callable] = None
    target_preference: str = "active"  # "active", "all", "first"

class CapabilityCommandExecutor:
    """Executes commands through capability system."""

    def __init__(self, capability_manager: CapabilityManager):
        self.capability_manager = capability_manager

    def execute_command(self, command: CapabilityCommand, context: CommandContext) -> CommandResult:
        """Execute capability-based command."""

        # 1. Determine target widget(s)
        target_widgets = self._resolve_target_widgets(command, context)

        if not target_widgets:
            if command.fallback_behavior:
                return command.fallback_behavior(context)
            return CommandResult(
                status=CommandStatus.NOT_APPLICABLE,
                message=f"No widgets support capability {command.capability_required}"
            )

        # 2. Execute on target widget(s)
        results = []
        for widget_id in target_widgets:
            try:
                result = self.capability_manager.execute_capability(
                    widget_id,
                    command.capability_required,
                    **command.parameters
                )
                results.append(result)
            except Exception as e:
                return CommandResult(
                    status=CommandStatus.FAILURE,
                    message=f"Failed to execute {command.capability_required}: {e}"
                )

        return CommandResult(
            status=CommandStatus.SUCCESS,
            data=results[0] if len(results) == 1 else results
        )

    def _resolve_target_widgets(self, command: CapabilityCommand, context: CommandContext) -> List[str]:
        """Resolve which widgets should receive the command."""
        capable_widgets = self.capability_manager.find_widgets_with_capability(
            command.capability_required
        )

        if command.target_preference == "active":
            # Try to use active widget first
            active_widget_id = self._get_active_widget_id(context)
            if active_widget_id and active_widget_id in capable_widgets:
                return [active_widget_id]
            # Fallback to first capable widget
            return capable_widgets[:1]

        elif command.target_preference == "all":
            return capable_widgets

        elif command.target_preference == "first":
            return capable_widgets[:1]

        return []
```

### 4. Service Discovery System

```python
class IPlatformService(ABC):
    """Interface for platform services."""

    @abstractmethod
    def get_service_id(self) -> str:
        """Get unique service identifier."""
        pass

    @abstractmethod
    def get_service_interface(self) -> type:
        """Get service interface class."""
        pass

class ServiceRegistry:
    """Registry for platform services."""

    def __init__(self):
        self._services: Dict[str, IPlatformService] = {}
        self._service_interfaces: Dict[type, str] = {}

    def register_service(self, service: IPlatformService):
        """Register a platform service."""
        service_id = service.get_service_id()
        interface = service.get_service_interface()

        self._services[service_id] = service
        self._service_interfaces[interface] = service_id

    def get_service(self, service_id: str) -> Optional[IPlatformService]:
        """Get service by ID."""
        return self._services.get(service_id)

    def get_service_by_interface(self, interface: type) -> Optional[IPlatformService]:
        """Get service by interface type."""
        service_id = self._service_interfaces.get(interface)
        return self._services.get(service_id) if service_id else None

class IServiceConsumer(ABC):
    """Interface for widgets that consume services."""

    @abstractmethod
    def set_service_registry(self, registry: ServiceRegistry):
        """Provide service registry to widget."""
        pass

    @abstractmethod
    def get_required_services(self) -> List[type]:
        """Get list of required service interfaces."""
        pass
```

## 🔄 Integration Patterns

### 1. Widget Implementation Pattern

```python
class TerminalWidget(AppWidget, ICapabilityProvider, IServiceConsumer):
    """Example terminal widget with capability support."""

    def __init__(self):
        super().__init__()
        self.service_registry: Optional[ServiceRegistry] = None
        self.clipboard_service = None
        self.terminal_server = None

    # === Capability Provider Implementation ===

    def get_capabilities(self) -> Set[WidgetCapability]:
        return {
            WidgetCapability.SHELL_EXECUTION,
            WidgetCapability.TEXT_INPUT,
            WidgetCapability.CLIPBOARD_COPY,
            WidgetCapability.CLIPBOARD_PASTE,
            WidgetCapability.CLEAR_DISPLAY,
            WidgetCapability.TEXT_SELECTION,
        }

    def get_capability_handler(self, capability: WidgetCapability) -> Optional[CapabilityHandler]:
        handlers = {
            WidgetCapability.CLEAR_DISPLAY: CapabilityHandler(
                capability=capability,
                method_name="clear_display",
                handler=self.clear_display,
                description="Clear terminal display"
            ),
            WidgetCapability.CLIPBOARD_COPY: CapabilityHandler(
                capability=capability,
                method_name="copy_selection",
                handler=self.copy_selection,
                description="Copy selected text to clipboard"
            ),
            # ... other handlers
        }
        return handlers.get(capability)

    def supports_capability(self, capability: WidgetCapability) -> bool:
        return capability in self.get_capabilities()

    # === Service Consumer Implementation ===

    def set_service_registry(self, registry: ServiceRegistry):
        self.service_registry = registry
        # Discover required services
        self.clipboard_service = registry.get_service_by_interface(IClipboardService)
        self.terminal_server = registry.get_service_by_interface(ITerminalServerService)

    def get_required_services(self) -> List[type]:
        return [IClipboardService, ITerminalServerService]

    # === Capability Implementations ===

    def clear_display(self):
        """Clear terminal display."""
        # Implementation using terminal server service
        if self.terminal_server:
            self.terminal_server.clear_terminal(self.terminal_id)

    def copy_selection(self):
        """Copy selected text to clipboard."""
        selected_text = self.get_selected_text()
        if selected_text and self.clipboard_service:
            self.clipboard_service.set_text(selected_text)
```

### 2. Command Registration Pattern

```python
def register_capability_commands():
    """Register all capability-based commands."""

    commands = [
        CapabilityCommand(
            id="editor.clear",
            title="Clear Display",
            capability_required=WidgetCapability.CLEAR_DISPLAY,
            method_name="clear_display",
            target_preference="active"
        ),

        CapabilityCommand(
            id="clipboard.copy",
            title="Copy",
            capability_required=WidgetCapability.CLIPBOARD_COPY,
            method_name="copy_selection",
            target_preference="active"
        ),

        CapabilityCommand(
            id="editor.save",
            title="Save File",
            capability_required=WidgetCapability.FILE_SAVING,
            method_name="save_file",
            target_preference="active",
            fallback_behavior=lambda ctx: CommandResult(
                status=CommandStatus.NOT_APPLICABLE,
                message="No file editor available"
            )
        ),
    ]

    for command in commands:
        command_registry.register_capability_command(command)
```

## 🎯 Migration Strategy

### Phase 1: Core Infrastructure
1. **Implement capability enumeration** - Define all capability types
2. **Create capability manager** - Central capability registration/discovery
3. **Build command delegation** - Capability-based command execution
4. **Design service registry** - Platform service discovery

### Phase 2: Widget Integration
1. **Update widget base classes** - Add capability interfaces
2. **Implement capability providers** - Widgets declare capabilities
3. **Service consumer pattern** - Widgets consume platform services
4. **Capability registration** - Widgets register with capability manager

### Phase 3: Command Migration
1. **Replace widget-specific commands** - Convert to capability commands
2. **Update command handlers** - Use capability delegation
3. **Remove widget type checking** - Use capability checking instead
4. **Test command compatibility** - Ensure all commands work

## 🚀 Benefits

### For Platform (Core)
- **Zero widget knowledge** - Core never imports widget implementations
- **Dynamic extensibility** - New widget types work without core changes
- **Service-oriented** - Clear boundaries between platform and widgets
- **Future-proof** - Ready for multi-process architecture

### For Widgets (Plugins)
- **Self-describing** - Widgets declare their own capabilities
- **Service discovery** - Easy access to platform services
- **Loose coupling** - No direct dependencies on core internals
- **Standardized APIs** - Consistent interaction patterns

### For Users
- **Consistent commands** - Same commands work across widget types
- **Better discoverability** - Commands automatically available for capable widgets
- **Flexible workflows** - Commands target functionality, not specific tools
- **Plugin extensibility** - New widgets automatically integrate

## 📋 Implementation Checklist

### Core Components
- [ ] `WidgetCapability` enumeration with all capability types
- [ ] `ICapabilityProvider` interface for widgets
- [ ] `CapabilityManager` for registration and discovery
- [ ] `CapabilityCommand` class for capability-based commands
- [ ] `CapabilityCommandExecutor` for command delegation
- [ ] `ServiceRegistry` for platform service discovery
- [ ] `IServiceConsumer` interface for service-using widgets

### Integration Points
- [ ] Update `AppWidget` base class with capability interfaces
- [ ] Modify command system to support capability commands
- [ ] Create platform services for common functionality
- [ ] Update widget registry to use capability manager
- [ ] Convert existing commands to capability-based

### Testing & Validation
- [ ] Unit tests for capability system
- [ ] Integration tests for command delegation
- [ ] Service discovery tests
- [ ] Widget capability registration tests
- [ ] End-to-end workflow tests

---

**Status**: COMPLETE ✅
**Next**: Task 1.4 - Create Backward Compatibility Strategy
**Key Innovation**: Capability-based architecture enables true widget platform without hardcoded widget knowledge.