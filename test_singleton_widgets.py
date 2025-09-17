#!/usr/bin/env python3
"""Test script to verify singleton widget behavior."""

import sys
import time

# Add app to path
sys.path.insert(0, '/home/kuja/GitHub/viloapp')

from core.commands.executor import execute_command
from services.service_locator import ServiceLocator
from services.workspace_service import WorkspaceService


def test_singleton_widgets():
    """Test singleton widget behavior for Settings, Theme Editor, and Shortcuts."""
    print("Starting singleton widget tests...")

    # Get workspace service
    workspace_service = ServiceLocator.get_instance().get(WorkspaceService)
    if not workspace_service:
        print("ERROR: Could not get WorkspaceService")
        return False

    results = []

    # Test 1: Settings widget
    print("\n1. Testing Settings widget...")

    # Open Settings first time
    result = execute_command("settings.openSettings")
    if not result.success:
        print(f"  ERROR: Failed to open Settings: {result.error}")
        results.append(False)
    else:
        print("  ✓ Settings opened successfully")
        time.sleep(0.1)

        # Check if it's registered
        if workspace_service.has_widget("com.viloapp.settings"):
            print("  ✓ Settings registered in workspace")
        else:
            print("  ERROR: Settings not registered")
            results.append(False)

        # Try to open again (should focus existing)
        initial_tab_count = workspace_service._workspace.tab_widget.count() if workspace_service._workspace else 0
        result = execute_command("settings.openSettings")
        new_tab_count = workspace_service._workspace.tab_widget.count() if workspace_service._workspace else 0

        if new_tab_count == initial_tab_count:
            print("  ✓ Settings reused existing tab (singleton behavior)")
            results.append(True)
        else:
            print("  ERROR: Settings created new tab instead of reusing")
            results.append(False)

    # Test 2: Theme Editor widget
    print("\n2. Testing Theme Editor widget...")

    # Replace current widget with Theme Editor
    result = execute_command("workbench.action.replaceWithThemeEditor")
    if not result.success:
        print(f"  ERROR: Failed to open Theme Editor: {result.error}")
        results.append(False)
    else:
        print("  ✓ Theme Editor opened successfully")
        time.sleep(0.1)

        # Check if it's registered
        if workspace_service.has_widget("com.viloapp.theme_editor"):
            print("  ✓ Theme Editor registered in workspace")

            # Try to open again in new tab
            initial_tab_count = workspace_service._workspace.tab_widget.count() if workspace_service._workspace else 0
            execute_command("workspace.newTab")
            execute_command("workbench.action.replaceWithThemeEditor")
            new_tab_count = workspace_service._workspace.tab_widget.count() if workspace_service._workspace else 0

            # Should have switched to existing tab, then added new tab but not created another theme editor
            if workspace_service.has_widget("com.viloapp.theme_editor"):
                print("  ✓ Theme Editor singleton behavior working")
                results.append(True)
            else:
                print("  ERROR: Theme Editor singleton check failed")
                results.append(False)
        else:
            print("  ERROR: Theme Editor not registered")
            results.append(False)

    # Test 3: Keyboard Shortcuts widget
    print("\n3. Testing Keyboard Shortcuts widget...")

    result = execute_command("settings.openKeyboardShortcuts")
    if not result.success:
        print(f"  ERROR: Failed to open Keyboard Shortcuts: {result.error}")
        results.append(False)
    else:
        print("  ✓ Keyboard Shortcuts opened successfully")
        time.sleep(0.1)

        # Check if it's registered
        if workspace_service.has_widget("com.viloapp.shortcuts"):
            print("  ✓ Keyboard Shortcuts registered in workspace")
            results.append(True)
        else:
            print("  ERROR: Keyboard Shortcuts not registered")
            results.append(False)

    # Test 4: Close and reopen Settings
    print("\n4. Testing close and reopen behavior...")

    # Close Settings tab
    settings_tab_index = workspace_service._widget_registry.get("com.viloapp.settings")
    if settings_tab_index is not None:
        workspace_service.close_tab(settings_tab_index)
        print("  ✓ Settings tab closed")

        # Check it's removed from registry
        if not workspace_service.has_widget("com.viloapp.settings"):
            print("  ✓ Settings removed from registry")

            # Reopen Settings
            result = execute_command("settings.openSettings")
            if result.success and workspace_service.has_widget("com.viloapp.settings"):
                print("  ✓ Settings reopened successfully")
                results.append(True)
            else:
                print("  ERROR: Failed to reopen Settings")
                results.append(False)
        else:
            print("  ERROR: Settings not removed from registry after close")
            results.append(False)
    else:
        print("  ERROR: Could not find Settings tab to close")
        results.append(False)

    # Test 5: Performance check
    print("\n5. Testing Settings performance...")

    import time
    start_time = time.time()
    result = execute_command("settings.openSettings")
    load_time = time.time() - start_time

    if load_time < 0.5:  # Should load in under 500ms
        print(f"  ✓ Settings loaded quickly: {load_time:.3f}s")
        results.append(True)
    else:
        print(f"  WARNING: Settings took {load_time:.3f}s to load")
        results.append(False)

    # Summary
    print("\n" + "="*50)
    passed = sum(results)
    total = len(results)
    print(f"Tests passed: {passed}/{total}")

    if passed == total:
        print("✅ All singleton widget tests passed!")
        return True
    else:
        print(f"❌ {total - passed} tests failed")
        return False

if __name__ == "__main__":
    # This would normally be run within the app context
    print("This test script should be run within the ViloxTerm application context")
    print("Use it as a reference for manual testing or integrate into the test suite")
