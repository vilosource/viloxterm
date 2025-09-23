#!/usr/bin/env python3
"""
Capability-based command utilities for ViloxTerm.

This module provides utilities for commands to interact with widgets
based on their capabilities rather than their types.

ARCHITECTURE COMPLIANCE:
- Commands target capabilities, not widget types
- No hardcoded widget knowledge
- Dynamic capability discovery
"""

import logging
from typing import Any, List, Optional

from viloapp.core.capabilities import WidgetCapability
from viloapp.core.capability_manager import capability_manager
from viloapp.core.commands.base import CommandContext, CommandResult, CommandStatus

logger = logging.getLogger(__name__)


def find_widget_for_capability(
    capability: WidgetCapability,
    prefer_active: bool = True,
    context: Optional[CommandContext] = None
) -> Optional[str]:
    """
    Find a widget that supports a specific capability.

    Args:
        capability: The required capability
        prefer_active: If True, prefer the currently active widget if it has the capability
        context: Command context for accessing active widget

    Returns:
        Widget instance ID or None if no suitable widget found
    """
    # Check active widget first if requested
    if prefer_active and context:
        active_widget_id = _get_active_widget_id(context)
        if active_widget_id and capability_manager.widget_has_capability(
            active_widget_id, capability
        ):
            return active_widget_id

    # Find any widget with the capability
    widgets = capability_manager.find_widgets_with_capability(capability)
    return widgets[0] if widgets else None


def find_widget_for_capabilities(
    capabilities: List[WidgetCapability],
    require_all: bool = True,
    prefer_active: bool = True,
    context: Optional[CommandContext] = None
) -> Optional[str]:
    """
    Find a widget that supports multiple capabilities.

    Args:
        capabilities: List of required capabilities
        require_all: If True, widget must have all capabilities. If False, any one is enough
        prefer_active: If True, prefer the currently active widget
        context: Command context for accessing active widget

    Returns:
        Widget instance ID or None if no suitable widget found
    """
    if not capabilities:
        return None

    # Check active widget first
    if prefer_active and context:
        active_widget_id = _get_active_widget_id(context)
        if active_widget_id:
            widget_caps = capability_manager.get_widget_capabilities(active_widget_id)
            if require_all:
                if all(cap in widget_caps for cap in capabilities):
                    return active_widget_id
            else:
                if any(cap in widget_caps for cap in capabilities):
                    return active_widget_id

    # Find any widget with the capabilities
    if require_all:
        # Widget must have all capabilities
        for capability in capabilities:
            widgets = capability_manager.find_widgets_with_capability(capability)
            for widget_id in widgets:
                widget_caps = capability_manager.get_widget_capabilities(widget_id)
                if all(cap in widget_caps for cap in capabilities):
                    return widget_id
    else:
        # Widget needs just one capability
        for capability in capabilities:
            widgets = capability_manager.find_widgets_with_capability(capability)
            if widgets:
                return widgets[0]

    return None


def execute_on_capable_widget(
    capability: WidgetCapability,
    context: CommandContext,
    **kwargs: Any
) -> CommandResult:
    """
    Execute a capability on any widget that supports it.

    Args:
        capability: The capability to execute
        context: Command context
        **kwargs: Arguments to pass to the capability

    Returns:
        CommandResult with execution status
    """
    # Find a widget with the capability
    widget_id = find_widget_for_capability(capability, context=context)

    if not widget_id:
        return CommandResult(
            status=CommandStatus.FAILURE,
            message=f"No widget found with capability: {capability.value}"
        )

    try:
        # Execute the capability
        result = capability_manager.execute_capability(widget_id, capability, **kwargs)

        return CommandResult(
            status=CommandStatus.SUCCESS,
            data={"widget_id": widget_id, "result": result}
        )
    except Exception as e:
        logger.error(f"Failed to execute capability {capability.value}: {e}")
        return CommandResult(
            status=CommandStatus.FAILURE,
            message=str(e)
        )


def get_default_widget_for_capability(capability: WidgetCapability) -> Optional[str]:
    """
    Get the default widget ID for widgets that support a capability.

    This is used when creating new widgets based on capability requirements.

    Args:
        capability: The required capability

    Returns:
        Widget ID (not instance ID) or None
    """
    from viloapp.core.app_widget_manager import app_widget_manager

    # Get all widget metadata
    all_widgets = app_widget_manager.get_all_widgets()

    # Find widgets that declare this capability in their metadata
    for widget in all_widgets:
        if capability.value in widget.provides_capabilities:
            return widget.widget_id

    return None


def get_widget_for_file_operation() -> Optional[str]:
    """
    Get the best widget ID for file operations.

    Returns:
        Widget ID suitable for file editing/viewing
    """
    # Look for widgets with file editing capability
    widget_id = get_default_widget_for_capability(WidgetCapability.FILE_EDITING)
    if widget_id:
        return widget_id

    # Fall back to text editing
    widget_id = get_default_widget_for_capability(WidgetCapability.TEXT_EDITING)
    if widget_id:
        return widget_id

    # Fall back to viewing
    return get_default_widget_for_capability(WidgetCapability.FILE_VIEWING)


def get_widget_for_shell_operation() -> Optional[str]:
    """
    Get the best widget ID for shell operations.

    Returns:
        Widget ID suitable for shell/terminal operations
    """
    # Look for widgets with shell execution capability
    widget_id = get_default_widget_for_capability(WidgetCapability.SHELL_EXECUTION)
    if widget_id:
        return widget_id

    # Fall back to command running
    return get_default_widget_for_capability(WidgetCapability.COMMAND_RUNNING)


def _get_active_widget_id(context: CommandContext) -> Optional[str]:
    """
    Get the active widget instance ID from context.

    Args:
        context: Command context

    Returns:
        Active widget instance ID or None
    """
    if not context or not context.model:
        return None

    try:
        # Get active tab
        active_tab = context.model.state.get_active_tab()
        if not active_tab:
            return None

        # Get active pane in the tab
        if active_tab.active_pane_id:
            # Get the widget instance in this pane
            # This would need to be tracked by the model
            # For now, return None as we need model updates
            pass

    except Exception as e:
        logger.debug(f"Could not determine active widget: {e}")

    return None


class CapabilityCommand:
    """
    Base class for capability-based commands.

    Commands that extend this class can easily target capabilities
    instead of specific widget types.
    """

    def __init__(self, required_capability: WidgetCapability):
        """
        Initialize capability command.

        Args:
            required_capability: The capability this command requires
        """
        self.required_capability = required_capability

    def find_target_widget(self, context: CommandContext) -> Optional[str]:
        """
        Find a widget that can handle this command.

        Args:
            context: Command context

        Returns:
            Widget instance ID or None
        """
        return find_widget_for_capability(
            self.required_capability,
            prefer_active=True,
            context=context
        )

    def execute_on_widget(
        self,
        widget_id: str,
        context: CommandContext,
        **kwargs: Any
    ) -> CommandResult:
        """
        Execute the capability on a specific widget.

        Args:
            widget_id: Target widget instance ID
            context: Command context
            **kwargs: Capability-specific arguments

        Returns:
            Command result
        """
        try:
            result = capability_manager.execute_capability(
                widget_id,
                self.required_capability,
                **kwargs
            )

            return CommandResult(
                status=CommandStatus.SUCCESS,
                data={"widget_id": widget_id, "result": result}
            )
        except Exception as e:
            logger.error(f"Capability execution failed: {e}")
            return CommandResult(
                status=CommandStatus.FAILURE,
                message=str(e)
            )
