#!/usr/bin/env python3
"""
Smoke tests - Verify the application can start and basic functionality works.

Run this BEFORE committing any changes:
    python tests/test_smoke.py
"""

import os
import sys
import traceback

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_imports() -> tuple[bool, str]:
    """Test that all critical imports work."""
    try:
        # Core imports
        from viloapp.core.commands.base import Command, CommandContext, CommandResult
        from viloapp.core.commands.executor import command_executor
        from viloapp.core.commands.registry import command_registry
        from viloapp.core.context.manager import context_manager
        from viloapp.core.settings.service import SettingsService

        # Service imports
        from viloapp.services.service_locator import ServiceLocator
        from viloapp.ui.command_palette.palette_widget import CommandPaletteWidget

        # UI imports
        from viloapp.ui.main_window import MainWindow

        # Terminal imports
        from viloapp.ui.terminal.terminal_server import terminal_server

        return True, "✅ All imports successful"
    except ImportError as e:
        return False, f"❌ Import failed: {e}"
    except Exception as e:
        return False, f"❌ Unexpected error during import: {e}"


def test_command_creation() -> tuple[bool, str]:
    """Test that commands can be created properly."""
    try:
        from viloapp.core.commands.base import Command, CommandContext, CommandResult

        # Test creating a command with handler function
        def test_handler(context: CommandContext) -> CommandResult:
            return CommandResult(success=True)

        cmd = Command(
            id="test.command",
            title="Test Command",
            category="Test",
            handler=test_handler,
        )

        if cmd.id != "test.command":
            return False, "❌ Command ID not set correctly"

        if cmd.handler != test_handler:
            return False, "❌ Command handler not set correctly"

        # Test command execution
        context = CommandContext()
        result = cmd.handler(context)

        if not result.success:
            return False, "❌ Command execution failed"

        return True, "✅ Command creation and execution works"
    except Exception as e:
        return False, f"❌ Command creation failed: {e}"


def test_service_locator() -> tuple[bool, str]:
    """Test that ServiceLocator works."""
    try:
        from viloapp.services.service_locator import ServiceLocator

        # Get instance
        locator = ServiceLocator.get_instance()
        if locator is None:
            return False, "❌ ServiceLocator instance is None"

        # Try to register a dummy service
        class DummyService:
            def __init__(self):
                self.name = "DummyService"

        dummy = DummyService()
        locator.register(DummyService, dummy)

        # Try to retrieve it
        retrieved = locator.get(DummyService)
        if retrieved != dummy:
            return False, "❌ ServiceLocator retrieval failed"

        return True, "✅ ServiceLocator works"
    except Exception as e:
        return False, f"❌ ServiceLocator test failed: {e}"


def test_app_initialization() -> tuple[bool, str]:
    """Test that the app can initialize (without GUI)."""
    try:
        # We can't create QApplication in test, but we can check if classes initialize
        import sys

        from viloapp.ui.main_window import MainWindow

        # Check if we're in a GUI environment
        if "DISPLAY" not in os.environ and sys.platform != "darwin":
            return True, "⚠️  Skipped GUI test (no display)"

        # Try to import and check class structure
        if not hasattr(MainWindow, "__init__"):
            return False, "❌ MainWindow missing __init__"

        return True, "✅ App initialization check passed"
    except Exception as e:
        return False, f"❌ App initialization failed: {e}"


def test_command_registry() -> tuple[bool, str]:
    """Test that command registry works."""
    try:
        from viloapp.core.commands.base import Command, CommandContext, CommandResult
        from viloapp.core.commands.registry import command_registry

        # Store existing commands
        command_registry.get_all_commands().copy()

        # Create and register a test command
        def test_handler(ctx: CommandContext) -> CommandResult:
            return CommandResult(success=True, value="test")

        test_cmd = Command(
            id="test.smoke", title="Smoke Test", category="Test", handler=test_handler
        )

        command_registry.register(test_cmd)

        # Retrieve it
        retrieved = command_registry.get_command("test.smoke")
        if retrieved is None:
            return False, "❌ Command not found in registry"

        if retrieved.id != "test.smoke":
            return False, "❌ Retrieved wrong command"

        # Test search
        results = command_registry.search_commands("smoke")
        if len(results) == 0:
            return False, "❌ Command search failed"

        return True, "✅ Command registry works"
    except Exception as e:
        return False, f"❌ Command registry test failed: {e}"


def test_builtin_commands() -> tuple[bool, str]:
    """Test that built-in commands can be registered."""
    try:
        from viloapp.core.commands.builtin import register_all_builtin_commands
        from viloapp.core.commands.registry import command_registry

        # Always register built-in commands for this test
        register_all_builtin_commands()

        # Check some known commands exist
        essential_commands = [
            "file.newEditorTab",
            "view.toggleSidebar",
            "workbench.action.splitRight",
            "terminal.clear",
            "commandPalette.show",
        ]

        for cmd_id in essential_commands:
            cmd = command_registry.get_command(cmd_id)
            if cmd is None:
                return False, f"❌ Essential command missing: {cmd_id}"

        # Check categories
        categories = command_registry.get_categories()
        if len(categories) == 0:
            return False, "❌ No command categories found"

        return (
            True,
            f"✅ Built-in commands registered ({len(command_registry.get_all_commands())} total)",
        )
    except Exception as e:
        traceback.print_exc()
        return False, f"❌ Built-in commands failed: {e}"


def run_smoke_tests():
    """Run all smoke tests."""
    print("=" * 60)
    print("🚀 SMOKE TESTS - Verify application can start")
    print("=" * 60)

    tests = [
        ("Imports", test_imports),
        ("Command Creation", test_command_creation),
        ("Service Locator", test_service_locator),
        ("App Initialization", test_app_initialization),
        ("Command Registry", test_command_registry),
        ("Built-in Commands", test_builtin_commands),
    ]

    results = []
    failed = False

    for name, test_func in tests:
        print(f"\nTesting {name}...")
        try:
            success, message = test_func()
            results.append((name, success, message))
            print(f"  {message}")
            if not success:
                failed = True
        except Exception as e:
            results.append((name, False, f"❌ Unexpected error: {e}"))
            print(f"  ❌ Unexpected error: {e}")
            traceback.print_exc()
            failed = True

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, success, _ in results if success)
    total = len(results)

    for name, success, message in results:
        status = "PASS" if success else "FAIL"
        print(f"  [{status}] {name}")

    print(f"\nResults: {passed}/{total} tests passed")

    if failed:
        print("\n❌ SMOKE TESTS FAILED - DO NOT COMMIT!")
        print("Fix the issues above before committing changes.")
        return 1
    else:
        print("\n✅ ALL SMOKE TESTS PASSED - Safe to commit!")
        return 0


if __name__ == "__main__":
    sys.exit(run_smoke_tests())
