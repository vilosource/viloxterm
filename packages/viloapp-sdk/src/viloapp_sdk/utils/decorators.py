"""Decorators for plugin development."""

import functools
import inspect
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union
from dataclasses import dataclass, field
from enum import Enum

from ..exceptions import PluginError


class ActivationEventType(Enum):
    """Plugin activation event types."""
    ON_STARTUP = "onStartup"
    ON_COMMAND = "onCommand"
    ON_FILE_SYSTEM = "onFileSystem"
    ON_WORKSPACE_OPEN = "onWorkspaceOpen"
    ON_WORKSPACE_CONTAINS = "onWorkspaceContains"
    ON_LANGUAGE = "onLanguage"
    ON_SCHEME = "onScheme"
    ON_UI = "onUI"
    ON_DEBUG = "onDebug"
    ON_TASK = "onTask"


class ContributionPointType(Enum):
    """Plugin contribution point types."""
    COMMANDS = "commands"
    MENUS = "menus"
    KEYBINDINGS = "keybindings"
    LANGUAGES = "languages"
    GRAMMARS = "grammars"
    THEMES = "themes"
    SNIPPETS = "snippets"
    DEBUGGERS = "debuggers"
    BREAKPOINTS = "breakpoints"
    VIEWS = "views"
    VIEWSCONTAINERS = "viewsContainers"
    PROBLEMMATCHERS = "problemMatchers"
    PROBLEMPATTERNS = "problemPatterns"
    TASK_DEFINITIONS = "taskDefinitions"
    CONFIGURATION = "configuration"


@dataclass
class PluginMetadata:
    """Plugin metadata collected from decorators."""
    plugin_id: Optional[str] = None
    name: Optional[str] = None
    version: Optional[str] = None
    description: Optional[str] = None
    author: Optional[Dict[str, str]] = None
    license: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    activation_events: List[str] = field(default_factory=list)
    main: Optional[str] = None
    engines: Dict[str, str] = field(default_factory=dict)
    categories: List[str] = field(default_factory=list)
    icon: Optional[str] = None
    galleryBanner: Optional[Dict[str, str]] = None
    preview: bool = False
    extensionPack: List[str] = field(default_factory=list)
    extensionDependencies: List[str] = field(default_factory=list)


@dataclass
class CommandMetadata:
    """Command metadata collected from decorators."""
    command_id: str
    title: str
    category: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    enablement: Optional[str] = None
    handler: Optional[Callable] = None
    shortcut: Optional[str] = None
    when: Optional[str] = None


@dataclass
class WidgetMetadata:
    """Widget metadata collected from decorators."""
    widget_id: str
    title: str
    icon: Optional[str] = None
    when: Optional[str] = None
    group: Optional[str] = None
    position: str = "main"
    closable: bool = True
    singleton: bool = False
    factory_class: Optional[Type] = None


@dataclass
class ServiceMetadata:
    """Service metadata collected from decorators."""
    service_id: str
    name: str
    description: Optional[str] = None
    version: str = "1.0.0"
    interface_type: Optional[Type] = None
    singleton: bool = True
    lazy: bool = False


@dataclass
class ContributionMetadata:
    """Contribution metadata collected from decorators."""
    contribution_point: str
    contribution_type: ContributionPointType
    configuration: Dict[str, Any] = field(default_factory=dict)
    target_class: Optional[Type] = None


F = TypeVar('F', bound=Callable[..., Any])
T = TypeVar('T', bound=Type)


def plugin(
    plugin_id: Optional[str] = None,
    name: Optional[str] = None,
    version: str = "1.0.0",
    description: Optional[str] = None,
    author: Optional[Union[str, Dict[str, str]]] = None,
    license: str = "MIT",
    keywords: Optional[List[str]] = None,
    engines: Optional[Dict[str, str]] = None,
    categories: Optional[List[str]] = None,
    icon: Optional[str] = None,
    galleryBanner: Optional[Dict[str, str]] = None,
    preview: bool = False,
    extensionPack: Optional[List[str]] = None,
    extensionDependencies: Optional[List[str]] = None,
    main: Optional[str] = None
) -> Callable[[T], T]:
    """
    Class decorator for plugin registration.

    Args:
        plugin_id: Unique plugin identifier (defaults to class name)
        name: Human-readable plugin name
        version: Plugin version in semver format
        description: Plugin description
        author: Author information (string or dict with name, email, url)
        license: Plugin license identifier
        keywords: Keywords for plugin discovery
        engines: Engine version requirements
        categories: Plugin categories
        icon: Plugin icon identifier
        galleryBanner: Gallery banner configuration
        preview: Whether plugin is in preview
        extensionPack: List of extension pack IDs
        extensionDependencies: List of extension dependencies
        main: Main entry point module

    Returns:
        Decorated class with plugin metadata

    Example:
        @plugin(
            plugin_id="my-awesome-plugin",
            name="My Awesome Plugin",
            version="1.0.0",
            description="An awesome plugin for ViloxTerm",
            author={"name": "John Doe", "email": "john@example.com"},
            keywords=["terminal", "productivity"],
            categories=["Other"]
        )
        class MyPlugin(IPlugin):
            pass
    """
    def decorator(cls: T) -> T:
        # Validate required parameters
        if not name:
            raise PluginError("Plugin name is required")

        # Default plugin_id to class name if not provided
        if plugin_id:
            final_plugin_id = plugin_id
        else:
            # Convert class name to plugin ID format
            class_name = cls.__name__
            # Remove 'Plugin' suffix if present
            if class_name.endswith('Plugin'):
                class_name = class_name[:-6]
            final_plugin_id = class_name.lower()

        # Validate plugin_id format
        if not final_plugin_id.replace('-', '').replace('.', '').isalnum():
            raise PluginError(f"Invalid plugin ID format: {final_plugin_id}")

        # Normalize author to dict format
        normalized_author = author
        if isinstance(author, str):
            normalized_author = {"name": author}
        elif author is None:
            normalized_author = {}

        # Create metadata object
        metadata = PluginMetadata(
            plugin_id=final_plugin_id,
            name=name,
            version=version,
            description=description,
            author=normalized_author,
            license=license,
            keywords=keywords or [],
            main=main,
            engines=engines or {"viloapp": ">=2.0.0"},
            categories=categories or ["Other"],
            icon=icon,
            galleryBanner=galleryBanner,
            preview=preview,
            extensionPack=extensionPack or [],
            extensionDependencies=extensionDependencies or []
        )

        # Attach metadata to class
        cls.__plugin_metadata__ = metadata

        return cls

    return decorator


def command(
    command_id: str,
    title: str,
    category: Optional[str] = None,
    description: Optional[str] = None,
    icon: Optional[str] = None,
    enablement: Optional[str] = None,
    shortcut: Optional[str] = None,
    when: Optional[str] = None
) -> Callable[[F], F]:
    """
    Method decorator for command registration.

    Args:
        command_id: Unique command identifier
        title: Human-readable command title
        category: Command category for grouping
        description: Command description
        icon: Command icon identifier
        enablement: When command should be enabled (expression)
        shortcut: Keyboard shortcut (e.g., "ctrl+shift+p")
        when: Context when command is available

    Returns:
        Decorated method with command metadata

    Example:
        @command(
            command_id="myPlugin.openTerminal",
            title="Open Terminal",
            category="Terminal",
            description="Opens a new terminal instance",
            shortcut="ctrl+shift+`"
        )
        def open_terminal(self, context):
            # Command implementation
            pass
    """
    def decorator(func: F) -> F:
        # Validate command_id
        if not command_id:
            raise PluginError("Command ID is required")

        if not command_id.replace('.', '').replace('-', '').replace('_', '').isalnum():
            raise PluginError(f"Invalid command ID format: {command_id}")

        # Create metadata
        metadata = CommandMetadata(
            command_id=command_id,
            title=title,
            category=category,
            description=description,
            icon=icon,
            enablement=enablement,
            handler=func,
            shortcut=shortcut,
            when=when
        )

        # Attach metadata to function
        func.__command_metadata__ = metadata

        # Get or create command registry on class
        if hasattr(func, '__self__'):
            # Method is bound, attach to instance
            instance = func.__self__
            if not hasattr(instance, '__commands__'):
                instance.__commands__ = {}
            instance.__commands__[command_id] = metadata
        else:
            # Method is unbound, will be handled during plugin activation
            func.__command_id__ = command_id

        return func

    return decorator


def widget(
    widget_id: str,
    title: str,
    icon: Optional[str] = None,
    when: Optional[str] = None,
    group: Optional[str] = None,
    position: str = "main",
    closable: bool = True,
    singleton: bool = False
) -> Callable[[T], T]:
    """
    Class decorator for widget registration.

    Args:
        widget_id: Unique widget identifier
        title: Widget display title
        icon: Widget icon identifier
        when: Context when widget is available
        group: Widget group for organization
        position: Widget position (main, sidebar, panel, auxiliary, floating)
        closable: Whether widget can be closed
        singleton: Whether only one instance is allowed

    Returns:
        Decorated class with widget metadata

    Example:
        @widget(
            widget_id="terminal",
            title="Terminal",
            icon="terminal",
            position="main",
            closable=True
        )
        class TerminalWidget(IWidget):
            pass
    """
    def decorator(cls: T) -> T:
        # Validate required parameters
        if not widget_id:
            raise PluginError("Widget ID is required")

        if not title:
            raise PluginError("Widget title is required")

        # Validate position
        valid_positions = ["main", "sidebar", "panel", "auxiliary", "floating"]
        if position not in valid_positions:
            raise PluginError(f"Invalid widget position: {position}. Must be one of {valid_positions}")

        # Create metadata
        metadata = WidgetMetadata(
            widget_id=widget_id,
            title=title,
            icon=icon,
            when=when,
            group=group,
            position=position,
            closable=closable,
            singleton=singleton,
            factory_class=cls
        )

        # Attach metadata to class
        cls.__widget_metadata__ = metadata

        return cls

    return decorator


def service(
    service_id: str,
    name: str,
    description: Optional[str] = None,
    version: str = "1.0.0",
    interface_type: Optional[Type] = None,
    singleton: bool = True,
    lazy: bool = False
) -> Callable[[T], T]:
    """
    Class decorator for service registration.

    Args:
        service_id: Unique service identifier
        name: Service display name
        description: Service description
        version: Service version
        interface_type: Service interface type
        singleton: Whether service is singleton
        lazy: Whether service should be lazily initialized

    Returns:
        Decorated class with service metadata

    Example:
        @service(
            service_id="my-service",
            name="My Service",
            description="A custom service",
            singleton=True
        )
        class MyService(IService):
            pass
    """
    def decorator(cls: T) -> T:
        # Validate required parameters
        if not service_id:
            raise PluginError("Service ID is required")

        if not name:
            raise PluginError("Service name is required")

        # Create metadata
        metadata = ServiceMetadata(
            service_id=service_id,
            name=name,
            description=description,
            version=version,
            interface_type=interface_type,
            singleton=singleton,
            lazy=lazy
        )

        # Attach metadata to class
        cls.__service_metadata__ = metadata

        return cls

    return decorator


def activation_event(
    event_type: Union[ActivationEventType, str],
    parameter: Optional[str] = None
) -> Callable[[T], T]:
    """
    Class decorator for activation event registration.

    Args:
        event_type: Type of activation event
        parameter: Additional parameter for the event

    Returns:
        Decorated class with activation event metadata

    Example:
        @activation_event(ActivationEventType.ON_COMMAND, "myPlugin.openTerminal")
        @activation_event(ActivationEventType.ON_LANGUAGE, "python")
        class MyPlugin(IPlugin):
            pass
    """
    def decorator(cls: T) -> T:
        # Convert enum to string if needed
        if isinstance(event_type, ActivationEventType):
            event_str = event_type.value
        else:
            event_str = str(event_type)

        # Add parameter if provided
        if parameter:
            event_str = f"{event_str}:{parameter}"

        # Get or create activation events list
        if not hasattr(cls, '__activation_events__'):
            cls.__activation_events__ = []

        # Add event if not already present
        if event_str not in cls.__activation_events__:
            cls.__activation_events__.append(event_str)

        return cls

    return decorator


def contribution(
    contribution_point: Union[ContributionPointType, str],
    **config: Any
) -> Callable[[T], T]:
    """
    Class decorator for contribution point registration.

    Args:
        contribution_point: Type of contribution point
        **config: Configuration for the contribution

    Returns:
        Decorated class with contribution metadata

    Example:
        @contribution(
            ContributionPointType.COMMANDS,
            commands=[
                {
                    "command": "myPlugin.hello",
                    "title": "Hello World"
                }
            ]
        )
        class MyPlugin(IPlugin):
            pass
    """
    def decorator(cls: T) -> T:
        # Convert enum to string if needed
        if isinstance(contribution_point, ContributionPointType):
            point_str = contribution_point.value
            point_type = contribution_point
        else:
            point_str = str(contribution_point)
            # Try to find matching enum
            point_type = None
            for cp in ContributionPointType:
                if cp.value == point_str:
                    point_type = cp
                    break
            if point_type is None:
                raise PluginError(f"Unknown contribution point: {point_str}")

        # Create metadata
        metadata = ContributionMetadata(
            contribution_point=point_str,
            contribution_type=point_type,
            configuration=config,
            target_class=cls
        )

        # Get or create contributions list
        if not hasattr(cls, '__contributions__'):
            cls.__contributions__ = []

        cls.__contributions__.append(metadata)

        return cls

    return decorator


# Utility functions for metadata extraction

def get_plugin_metadata(cls: Type) -> Optional[PluginMetadata]:
    """Get plugin metadata from a class."""
    return getattr(cls, '__plugin_metadata__', None)


def get_command_metadata(func: Callable) -> Optional[CommandMetadata]:
    """Get command metadata from a function."""
    return getattr(func, '__command_metadata__', None)


def get_widget_metadata(cls: Type) -> Optional[WidgetMetadata]:
    """Get widget metadata from a class."""
    return getattr(cls, '__widget_metadata__', None)


def get_service_metadata(cls: Type) -> Optional[ServiceMetadata]:
    """Get service metadata from a class."""
    return getattr(cls, '__service_metadata__', None)


def get_activation_events(cls: Type) -> List[str]:
    """Get activation events from a class."""
    return getattr(cls, '__activation_events__', [])


def get_contributions(cls: Type) -> List[ContributionMetadata]:
    """Get contributions from a class."""
    return getattr(cls, '__contributions__', [])


def get_commands_from_class(cls: Type) -> Dict[str, CommandMetadata]:
    """Get all command metadata from a class."""
    commands = {}

    # Check class methods
    for attr_name in dir(cls):
        attr = getattr(cls, attr_name)
        if callable(attr):
            metadata = get_command_metadata(attr)
            if metadata:
                commands[metadata.command_id] = metadata

    # Check class-level commands registry
    if hasattr(cls, '__commands__'):
        commands.update(cls.__commands__)

    return commands


def create_manifest_from_decorators(plugin_class: Type) -> Dict[str, Any]:
    """
    Create a plugin manifest dictionary from decorator metadata.

    Args:
        plugin_class: Plugin class with decorator metadata

    Returns:
        Plugin manifest dictionary
    """
    manifest = {}

    # Get plugin metadata
    plugin_metadata = get_plugin_metadata(plugin_class)
    if plugin_metadata:
        manifest.update({
            "name": plugin_metadata.plugin_id,
            "displayName": plugin_metadata.name,
            "version": plugin_metadata.version,
            "description": plugin_metadata.description,
            "author": plugin_metadata.author,
            "license": plugin_metadata.license,
            "keywords": plugin_metadata.keywords,
            "engines": plugin_metadata.engines,
            "categories": plugin_metadata.categories,
            "main": plugin_metadata.main,
        })

        if plugin_metadata.icon:
            manifest["icon"] = plugin_metadata.icon

        if plugin_metadata.galleryBanner:
            manifest["galleryBanner"] = plugin_metadata.galleryBanner

        if plugin_metadata.preview:
            manifest["preview"] = plugin_metadata.preview

        if plugin_metadata.extensionPack:
            manifest["extensionPack"] = plugin_metadata.extensionPack

        if plugin_metadata.extensionDependencies:
            manifest["extensionDependencies"] = plugin_metadata.extensionDependencies

    # Get activation events
    activation_events = get_activation_events(plugin_class)
    if activation_events:
        manifest["activationEvents"] = activation_events

    # Get contributions
    contributions = get_contributions(plugin_class)
    contributes = {}
    for contrib in contributions:
        contributes[contrib.contribution_point] = contrib.configuration

    # Get commands
    commands = get_commands_from_class(plugin_class)
    if commands:
        command_list = []
        for cmd_metadata in commands.values():
            cmd_dict = {
                "command": cmd_metadata.command_id,
                "title": cmd_metadata.title,
            }
            if cmd_metadata.category:
                cmd_dict["category"] = cmd_metadata.category
            if cmd_metadata.icon:
                cmd_dict["icon"] = cmd_metadata.icon
            if cmd_metadata.enablement:
                cmd_dict["enablement"] = cmd_metadata.enablement
            command_list.append(cmd_dict)

        contributes["commands"] = command_list

    if contributes:
        manifest["contributes"] = contributes

    return manifest