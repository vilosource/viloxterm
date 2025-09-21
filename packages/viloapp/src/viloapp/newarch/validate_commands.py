#!/usr/bin/env python3
"""
Validation script for the command system.

This script tests all commands to ensure they work correctly
with the model through the pure command interface.
"""


from commands import (
    ChangeWidgetTypeCommand,
    ClosePaneCommand,
    CloseTabCommand,
    CommandContext,
    CommandRegistry,
    CommandStatus,
    CompositeCommand,
    CreateTabCommand,
    FocusPaneCommand,
    SplitPaneCommand,
)
from model import WidgetType, WorkspaceModel


def print_header(title: str):
    """Print a section header."""
    print(f"\n{'=' * 60}")
    print(f" {title}")
    print(f"{'=' * 60}")


def print_success(msg: str):
    """Print success message."""
    print(f"✅ {msg}")


def print_error(msg: str):
    """Print error message."""
    print(f"❌ {msg}")


def print_info(msg: str):
    """Print info message."""
    print(f"ℹ️  {msg}")


def validate_commands():
    """Run comprehensive command validation."""
    print_header("COMMAND SYSTEM VALIDATION")

    # Create model and context
    model = WorkspaceModel()
    context = CommandContext(model=model)
    print_success("Model and context created")

    # Test 1: Direct command execution
    print_header("Test 1: Direct Command Execution")

    # Create tab command
    cmd = CreateTabCommand("Test Tab", WidgetType.TERMINAL)
    result = cmd.execute(context)
    assert result.success, f"Failed to create tab: {result.message}"
    tab_id = result.data["tab_id"]
    print_success(f"Created tab via command: {tab_id}")

    # Update context with active tab
    context.active_tab_id = tab_id

    # Get initial pane
    tab = model.state.get_active_tab()
    assert tab is not None
    initial_pane = tab.get_active_pane()
    assert initial_pane is not None
    context.active_pane_id = initial_pane.id

    # Split pane command
    cmd = SplitPaneCommand("horizontal", initial_pane.id)
    result = cmd.execute(context)
    assert result.success, f"Failed to split pane: {result.message}"
    new_pane_id = result.data["new_pane_id"]
    print_success(f"Split pane via command: {new_pane_id}")

    # Test 2: Command Registry
    print_header("Test 2: Command Registry")

    registry = CommandRegistry()
    print_success(f"Registry created with {len(registry.commands)} commands")

    # List commands
    commands = registry.list_commands()
    print_info(f"Available commands: {', '.join(commands[:5])}...")

    # Execute via registry
    result = registry.execute("tab.create", context, name="Registry Tab")
    assert result.success
    print_success("Created tab via registry")

    # Test split via alias
    # First update context with active tab and pane
    tab = model.state.get_active_tab()
    if tab:
        context.active_tab_id = tab.id
        pane = tab.get_active_pane()
        if pane:
            context.active_pane_id = pane.id

    result = registry.execute("workbench.action.splitPaneHorizontal", context)
    assert result.success, f"Split via alias failed: {result.message}"
    print_success("Split pane via alias")

    # Test 3: Command Parameters
    print_header("Test 3: Command Parameters")

    # Create terminal tab
    result = registry.execute(
        "tab.create", context, name="Terminal", widget_type=WidgetType.TERMINAL
    )
    assert result.success
    terminal_tab_id = result.data["tab_id"]
    print_success("Created terminal tab with parameters")

    # Switch to terminal tab
    result = registry.execute("tab.switch", context, tab_id=terminal_tab_id)
    assert result.success
    assert model.state.active_tab_id == terminal_tab_id
    print_success("Switched to terminal tab")

    # Rename tab
    result = registry.execute(
        "tab.rename", context, new_name="Renamed Terminal", tab_id=terminal_tab_id
    )
    assert result.success, f"Rename failed: {result.message}"
    tab = model._find_tab(terminal_tab_id)
    assert tab and tab.name == "Renamed Terminal", f"Tab name is: {tab.name if tab else 'None'}"
    print_success("Renamed tab via command")

    # Test 4: Pane Operations
    print_header("Test 4: Pane Operations")

    # Get current pane
    pane = model.get_active_pane()
    assert pane is not None
    pane_id = pane.id

    # Split vertical
    cmd = SplitPaneCommand("vertical", pane_id, WidgetType.OUTPUT)
    result = cmd.execute(context)
    assert result.success
    output_pane_id = result.data["new_pane_id"]
    print_success("Split vertically with OUTPUT widget")

    # Verify widget type was set
    output_pane = model.get_pane(output_pane_id)
    assert output_pane and output_pane.widget_type == WidgetType.OUTPUT
    print_success("Widget type set correctly")

    # Change widget type
    cmd = ChangeWidgetTypeCommand(WidgetType.EDITOR, output_pane_id)
    result = cmd.execute(context)
    assert result.success
    output_pane = model.get_pane(output_pane_id)
    assert output_pane and output_pane.widget_type == WidgetType.EDITOR
    print_success("Changed widget type to EDITOR")

    # Focus pane
    cmd = FocusPaneCommand(pane_id)
    result = cmd.execute(context)
    assert result.success
    assert model.get_active_pane() and model.get_active_pane().id == pane_id
    print_success("Focused original pane")

    # Close pane
    cmd = ClosePaneCommand(output_pane_id)
    result = cmd.execute(context)
    assert result.success
    assert model.get_pane(output_pane_id) is None
    print_success("Closed pane via command")

    # Test 5: Error Handling
    print_header("Test 5: Error Handling")

    # Try to close last tab
    # First close all but one tab
    while len(model.state.tabs) > 1:
        model.close_tab(model.state.tabs[0].id)

    cmd = CloseTabCommand(model.state.tabs[0].id)
    result = cmd.execute(context)
    assert result.status == CommandStatus.NOT_APPLICABLE
    print_success("Prevented closing last tab")

    # Try to close last pane
    tab = model.state.tabs[0]
    if tab:
        # Ensure only one pane
        while len(tab.tree.root.get_all_panes()) > 1:
            panes = tab.tree.root.get_all_panes()
            model.close_pane(panes[0].id)

        last_pane = tab.tree.root.get_all_panes()[0]
        cmd = ClosePaneCommand(last_pane.id)
        result = cmd.execute(context)
        assert result.status == CommandStatus.NOT_APPLICABLE
        print_success("Prevented closing last pane")

    # Invalid command
    result = registry.execute("invalid.command", context)
    assert not result.success
    print_success("Handled invalid command gracefully")

    # Test 6: Composite Commands
    print_header("Test 6: Composite Commands")

    # Create a simple macro
    macro = CompositeCommand(
        [
            CreateTabCommand("Macro Tab", WidgetType.EDITOR),
        ],
        name="CreateSimpleTab",
    )

    # Execute macro
    result = macro.execute(context)
    assert result.success
    print_success("Executed simple composite command")

    # Verify results
    tab = model.state.get_active_tab()
    assert tab and tab.name == "Macro Tab"
    print_success("Macro created tab successfully")

    # Now test a more complex one with context update
    # Update context first with the new tab
    context.active_tab_id = tab.id
    pane = tab.get_active_pane()
    if pane:
        context.active_pane_id = pane.id

    # Split that pane
    split_cmd = SplitPaneCommand("horizontal")
    result = split_cmd.execute(context)
    assert result.success
    print_success("Complex operations work with proper context")

    # Test 7: Context Usage
    print_header("Test 7: Context Usage")

    # Create new context with specific active items
    # Make sure we have a tab with a pane
    tab = model.state.get_active_tab()
    if not tab:
        # Create a tab if needed
        tab_id = model.create_tab("Context Test")
        tab = model._find_tab(tab_id)

    pane = tab.get_active_pane() if tab else None
    assert pane is not None, "No pane available for context test"

    context2 = CommandContext(
        model=model,
        active_tab_id=tab.id,
        active_pane_id=pane.id,
        parameters={"custom": "value"},
    )

    # Commands should use context
    cmd = SplitPaneCommand()  # No pane_id specified
    result = cmd.execute(context2)
    assert result.success, f"Context split failed: {result.message}"
    print_success("Command used context for active pane")

    # Test 8: Command Aliases
    print_header("Test 8: Command Aliases")

    aliases = registry.list_aliases()
    print_info(f"Found {len(aliases)} aliases")

    for alias, command in list(aliases.items())[:3]:
        print_info(f"  {alias} -> {command}")

    # Test workbench aliases
    result = registry.execute("workbench.action.closePane", context2)
    # May fail if only one pane, but command should execute
    assert result.status in [CommandStatus.SUCCESS, CommandStatus.NOT_APPLICABLE]
    print_success("Workbench alias executed")

    # Summary
    print_header("VALIDATION SUMMARY")
    print_success("All command tests passed! ✨")
    print_info("\nThe command system is fully functional:")
    print_info("- Direct command execution works")
    print_info("- Registry manages commands properly")
    print_info("- Parameters are handled correctly")
    print_info("- Error handling is robust")
    print_info("- Composite commands work")
    print_info("- Context is used appropriately")
    print_info("- Aliases function correctly")

    return True


if __name__ == "__main__":
    try:
        success = validate_commands()
        if success:
            exit(0)
        else:
            exit(1)
    except Exception as e:
        print_error(f"Validation failed with error: {e}")
        import traceback

        traceback.print_exc()
        exit(1)
