"""Plugin-related commands."""

from viloapp.core.commands.base import CommandContext, CommandResult
from viloapp.core.commands.decorators import command


@command(
    id="plugins.list",
    title="List Installed Plugins",
    category="Plugins",
    description="Show all installed plugins and their status",
)
def list_plugins_command(context: CommandContext) -> CommandResult:
    """List all plugins."""
    plugin_manager = context.get_service("plugin_manager")
    if not plugin_manager:
        return CommandResult(success=False, error="Plugin manager not available")

    plugins = plugin_manager.list_plugins()
    return CommandResult(success=True, value=plugins)


@command(
    id="plugins.enable",
    title="Enable Plugin",
    category="Plugins",
    description="Enable a disabled plugin",
)
def enable_plugin_command(context: CommandContext, plugin_id: str) -> CommandResult:
    """Enable a plugin."""
    plugin_manager = context.get_service("plugin_manager")
    if not plugin_manager:
        return CommandResult(success=False, error="Plugin manager not available")

    if plugin_manager.enable_plugin(plugin_id):
        return CommandResult(success=True, value=f"Plugin {plugin_id} enabled")
    else:
        return CommandResult(success=False, error=f"Failed to enable plugin {plugin_id}")


@command(
    id="plugins.disable",
    title="Disable Plugin",
    category="Plugins",
    description="Disable an enabled plugin",
)
def disable_plugin_command(context: CommandContext, plugin_id: str) -> CommandResult:
    """Disable a plugin."""
    plugin_manager = context.get_service("plugin_manager")
    if not plugin_manager:
        return CommandResult(success=False, error="Plugin manager not available")

    if plugin_manager.disable_plugin(plugin_id):
        return CommandResult(success=True, value=f"Plugin {plugin_id} disabled")
    else:
        return CommandResult(success=False, error=f"Failed to disable plugin {plugin_id}")


@command(
    id="plugins.reload", title="Reload Plugin", category="Plugins", description="Reload a plugin"
)
def reload_plugin_command(context: CommandContext, plugin_id: str) -> CommandResult:
    """Reload a plugin."""
    plugin_manager = context.get_service("plugin_manager")
    if not plugin_manager:
        return CommandResult(success=False, error="Plugin manager not available")

    if plugin_manager.reload_plugin(plugin_id):
        return CommandResult(success=True, value=f"Plugin {plugin_id} reloaded")
    else:
        return CommandResult(success=False, error=f"Failed to reload plugin {plugin_id}")


@command(
    id="plugins.info",
    title="Plugin Information",
    category="Plugins",
    description="Show detailed information about a plugin",
)
def plugin_info_command(context: CommandContext, plugin_id: str) -> CommandResult:
    """Get plugin information."""
    plugin_manager = context.get_service("plugin_manager")
    if not plugin_manager:
        return CommandResult(success=False, error="Plugin manager not available")

    info = plugin_manager.get_plugin_metadata(plugin_id)
    if info:
        return CommandResult(success=True, value=info)
    else:
        return CommandResult(success=False, error=f"Plugin {plugin_id} not found")


@command(
    id="plugins.discover",
    title="Discover Plugins",
    category="Plugins",
    description="Discover new plugins",
)
def discover_plugins_command(context: CommandContext) -> CommandResult:
    """Discover new plugins."""
    plugin_manager = context.get_service("plugin_manager")
    if not plugin_manager:
        return CommandResult(success=False, error="Plugin manager not available")

    plugin_ids = plugin_manager.discover_plugins()
    return CommandResult(
        success=True, value=f"Discovered {len(plugin_ids)} plugins: {', '.join(plugin_ids)}"
    )
