#!/usr/bin/env python3
"""
Decorators for easy command registration.

These decorators simplify the process of creating and registering commands
by allowing functions to be decorated with command metadata.
"""

from typing import Optional, Callable, List, Dict, Any
from functools import wraps
import logging

from core.commands.base import Command, CommandContext, CommandResult
from core.commands.registry import command_registry

logger = logging.getLogger(__name__)


def command(
    id: str,
    title: str,
    category: str,
    description: Optional[str] = None,
    icon: Optional[str] = None,
    shortcut: Optional[str] = None,
    when: Optional[str] = None,
    keywords: Optional[List[str]] = None,
    group: Optional[str] = None,
    order: int = 0,
    visible: bool = True,
    register: bool = True
) -> Callable:
    """
    Decorator for creating and registering commands.
    
    This decorator transforms a function into a command and optionally
    registers it with the global command registry.
    
    Args:
        id: Unique command identifier
        title: Display title
        category: Command category
        description: Detailed description
        icon: Icon identifier
        shortcut: Default keyboard shortcut
        when: Context expression for availability
        keywords: Search keywords
        group: Menu group
        order: Sort order
        visible: Whether to show in command palette
        register: Whether to auto-register with registry
        
    Returns:
        Decorator function
        
    Example:
        @command(
            id="file.newTab",
            title="New Tab",
            category="File",
            shortcut="ctrl+n",
            description="Create a new tab"
        )
        def new_tab_command(context: CommandContext) -> CommandResult:
            # Implementation
            return CommandResult(success=True)
    """
    def decorator(func: Callable) -> Command:
        # Ensure the function has the right signature
        @wraps(func)
        def handler(context: CommandContext) -> CommandResult:
            try:
                result = func(context)
                
                # Ensure we return a CommandResult
                if not isinstance(result, CommandResult):
                    if isinstance(result, bool):
                        return CommandResult(success=result)
                    else:
                        return CommandResult(success=True, value=result)
                
                return result
                
            except Exception as e:
                logger.error(f"Error in command {id}: {e}", exc_info=True)
                return CommandResult(success=False, error=str(e))
        
        # Create the command
        cmd = Command(
            id=id,
            title=title,
            category=category,
            handler=handler,
            description=description,
            icon=icon,
            shortcut=shortcut,
            when=when,
            keywords=keywords or [],
            group=group,
            order=order,
            visible=visible
        )
        
        # Store the original function for testing
        cmd._original_func = func

        # Transfer validation spec if present (for stacked decorators)
        if hasattr(func, '_validation_spec'):
            cmd._validation_spec = func._validation_spec
            # Re-wrap the handler with validation if needed
            original_handler = cmd.handler
            validation_spec = func._validation_spec

            @wraps(original_handler)
            def validated_handler(context):
                try:
                    validated_context = validation_spec.validate_context(context)
                    return original_handler(validated_context)
                except Exception as e:
                    from core.commands.validation import ValidationError
                    if isinstance(e, ValidationError):
                        logger.warning(f"Validation failed for command {id}: {e}")
                        return CommandResult(success=False, error=str(e))
                    else:
                        raise e

            cmd.handler = validated_handler
        
        # Auto-register if requested
        if register:
            command_registry.register(cmd)
            logger.debug(f"Auto-registered command: {id}")
            
            # Auto-register shortcut if provided
            if shortcut:
                try:
                    from services.service_locator import ServiceLocator
                    from core.keyboard import KeyboardService
                    
                    locator = ServiceLocator.get_instance()
                    keyboard_service = locator.get(KeyboardService)
                    
                    if keyboard_service and keyboard_service.is_initialized:
                        success = keyboard_service.register_shortcut_from_string(
                            shortcut_id=f"command.{id}",
                            sequence_str=shortcut,
                            command_id=id,
                            description=description or title,
                            source="command",
                            priority=75  # Default priority for command shortcuts
                        )
                        if success:
                            logger.debug(f"Auto-registered shortcut for {id}: {shortcut}")
                        else:
                            logger.warning(f"Failed to register shortcut for {id}: {shortcut}")
                    else:
                        # Store for later registration when keyboard service is available
                        if not hasattr(command_registry, '_pending_shortcuts'):
                            command_registry._pending_shortcuts = []
                        command_registry._pending_shortcuts.append((id, shortcut, description or title))
                        logger.debug(f"Queued shortcut for {id}: {shortcut}")
                        
                except Exception as e:
                    logger.warning(f"Could not register shortcut for {id}: {e}")
        
        # Return the command (not the function) so it can be used directly
        return cmd
    
    return decorator


def command_handler(
    command_id: str,
    undo: Optional[Callable] = None,
    redo: Optional[Callable] = None
) -> Callable:
    """
    Decorator for adding handlers to existing commands.
    
    This is useful for adding undo/redo handlers to commands defined elsewhere.
    
    Args:
        command_id: ID of command to modify
        undo: Undo handler function
        redo: Redo handler function
        
    Returns:
        Decorator function
        
    Example:
        @command_handler("file.newTab", undo=undo_new_tab)
        def enhance_new_tab(context: CommandContext) -> CommandResult:
            # Enhanced implementation
            return CommandResult(success=True)
    """
    def decorator(func: Callable) -> Callable:
        # Get the existing command
        cmd = command_registry.get_command(command_id)
        if not cmd:
            logger.warning(f"Command not found for handler: {command_id}")
            return func
        
        # Update the command
        if func:
            @wraps(func)
            def handler(context: CommandContext) -> CommandResult:
                try:
                    result = func(context)
                    if not isinstance(result, CommandResult):
                        return CommandResult(success=True, value=result)
                    return result
                except Exception as e:
                    logger.error(f"Error in command {command_id}: {e}", exc_info=True)
                    return CommandResult(success=False, error=str(e))
            
            cmd.handler = handler
        
        if undo:
            @wraps(undo)
            def undo_handler(context: CommandContext) -> CommandResult:
                try:
                    result = undo(context)
                    if not isinstance(result, CommandResult):
                        return CommandResult(success=True, value=result)
                    return result
                except Exception as e:
                    logger.error(f"Error in undo for {command_id}: {e}", exc_info=True)
                    return CommandResult(success=False, error=str(e))
            
            cmd.undo_handler = undo_handler
            cmd.supports_undo = True
        
        if redo:
            @wraps(redo)
            def redo_handler(context: CommandContext) -> CommandResult:
                try:
                    result = redo(context)
                    if not isinstance(result, CommandResult):
                        return CommandResult(success=True, value=result)
                    return result
                except Exception as e:
                    logger.error(f"Error in redo for {command_id}: {e}", exc_info=True)
                    return CommandResult(success=False, error=str(e))
            
            cmd.redo_handler = redo_handler
        
        return func
    
    return decorator


def batch_register(*commands: Command) -> None:
    """
    Register multiple commands at once.
    
    Args:
        *commands: Commands to register
        
    Example:
        batch_register(
            new_tab_cmd,
            close_tab_cmd,
            save_file_cmd
        )
    """
    for cmd in commands:
        if isinstance(cmd, Command):
            command_registry.register(cmd)
        else:
            logger.warning(f"Skipping non-command object: {cmd}")


def create_command_group(
    category: str,
    group: str,
    commands: List[Dict[str, Any]]
) -> List[Command]:
    """
    Create a group of related commands.
    
    Args:
        category: Category for all commands
        group: Group name for all commands
        commands: List of command definitions
        
    Returns:
        List of created commands
        
    Example:
        file_commands = create_command_group(
            category="File",
            group="file-operations",
            commands=[
                {
                    "id": "file.new",
                    "title": "New File",
                    "handler": new_file_handler,
                    "shortcut": "ctrl+n"
                },
                {
                    "id": "file.open",
                    "title": "Open File",
                    "handler": open_file_handler,
                    "shortcut": "ctrl+o"
                }
            ]
        )
    """
    created_commands = []
    
    for i, cmd_def in enumerate(commands):
        # Set defaults
        cmd_def.setdefault('category', category)
        cmd_def.setdefault('group', group)
        cmd_def.setdefault('order', i * 10)  # Space out orders
        
        # Extract handler
        handler = cmd_def.pop('handler', None)
        if not handler:
            logger.warning(f"No handler for command: {cmd_def.get('id')}")
            continue
        
        # Create command
        cmd = Command(handler=handler, **cmd_def)
        created_commands.append(cmd)
        
        # Register
        command_registry.register(cmd)
    
    return created_commands


def register_pending_shortcuts():
    """
    Register any pending shortcuts that were queued during command registration.
    
    This function should be called after the keyboard service is initialized
    to register shortcuts for commands that were created before the service was ready.
    """
    if not hasattr(command_registry, '_pending_shortcuts'):
        return
    
    try:
        from services.service_locator import ServiceLocator
        from core.keyboard import KeyboardService
        
        locator = ServiceLocator.get_instance()
        keyboard_service = locator.get(KeyboardService)
        
        if not keyboard_service or not keyboard_service.is_initialized:
            logger.warning("Keyboard service not available for pending shortcuts")
            return
        
        pending = command_registry._pending_shortcuts
        registered_count = 0
        
        for command_id, shortcut, description in pending:
            try:
                success = keyboard_service.register_shortcut_from_string(
                    shortcut_id=f"command.{command_id}",
                    sequence_str=shortcut,
                    command_id=command_id,
                    description=description,
                    source="command",
                    priority=75
                )
                if success:
                    registered_count += 1
                    logger.debug(f"Registered pending shortcut for {command_id}: {shortcut}")
                else:
                    logger.warning(f"Failed to register pending shortcut for {command_id}: {shortcut}")
                    
            except Exception as e:
                logger.error(f"Error registering shortcut for {command_id}: {e}")
        
        # Clear pending shortcuts
        command_registry._pending_shortcuts = []
        
        logger.info(f"Registered {registered_count}/{len(pending)} pending shortcuts")
        
    except Exception as e:
        logger.error(f"Error registering pending shortcuts: {e}")