#!/usr/bin/env python3
"""Test running the application with plugins."""

import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_app_startup():
    """Test if the app can start with plugins."""
    print("=== Testing App Startup with Plugins ===\n")

    # Import app modules
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QTimer, QCoreApplication

    # Set app metadata
    QCoreApplication.setApplicationName("ViloxTerm-Test")
    QCoreApplication.setOrganizationName("ViloxTerm")

    # Create app
    app = QApplication(sys.argv)

    try:
        # Import services
        print("1. Initializing services...")
        from services import initialize_services

        # Create mock components
        class MockMainWindow:
            def __init__(self):
                self.isVisible = lambda: True

        class MockWorkspace:
            pass

        # Initialize services with mock components
        service_locator = initialize_services(
            main_window=MockMainWindow(),
            workspace=MockWorkspace(),
            sidebar=None,
            activity_bar=None
        )

        # Check if plugin manager was created
        plugin_manager = service_locator.get('plugin_manager')
        if plugin_manager:
            print("  ✓ Plugin manager initialized")

            # Check loaded plugins
            from viloapp_sdk import LifecycleState
            all_plugins = plugin_manager.registry.get_all_plugins()

            print(f"\n2. Checking plugin states ({len(all_plugins)} plugins):")
            for plugin_info in all_plugins:
                state_symbol = "✓" if plugin_info.state in [LifecycleState.LOADED, LifecycleState.ACTIVATED] else "○"
                print(f"  {state_symbol} {plugin_info.metadata.id}: {plugin_info.state.name}")

            # Check if our plugins are discovered
            plugin_ids = [p.metadata.id for p in all_plugins]
            print("\n3. Checking for our plugins:")
            for pid in ["viloxterm", "viloedit"]:
                if pid in plugin_ids:
                    print(f"  ✓ {pid} discovered")
                    # Try to get the plugin
                    plugin_info = plugin_manager.registry.get_plugin(pid)
                    if plugin_info:
                        if plugin_info.state == LifecycleState.ACTIVATED:
                            print(f"    ✓ {pid} is activated")
                        elif plugin_info.state == LifecycleState.LOADED:
                            print(f"    ○ {pid} is loaded but not activated")
                        elif plugin_info.state == LifecycleState.FAILED:
                            print(f"    ✗ {pid} failed: {plugin_info.error}")
                        else:
                            print(f"    - {pid} state: {plugin_info.state.name}")
                else:
                    print(f"  ✗ {pid} NOT discovered")

            # Try to manually load a plugin
            print("\n4. Attempting to load viloxterm plugin...")
            if "viloxterm" in plugin_ids:
                if plugin_manager.load_plugin("viloxterm"):
                    print("  ✓ viloxterm loaded successfully")
                    if plugin_manager.activate_plugin("viloxterm"):
                        print("  ✓ viloxterm activated successfully")
                    else:
                        print("  ✗ viloxterm activation failed")
                else:
                    print("  ✗ viloxterm loading failed")
                    plugin_info = plugin_manager.registry.get_plugin("viloxterm")
                    if plugin_info and plugin_info.error:
                        print(f"    Error: {plugin_info.error}")

        else:
            print("  ✗ Plugin manager NOT initialized")

        print("\n=== Test Complete ===")
        return True

    except Exception as e:
        print(f"\n✗ Error during startup: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Clean exit
        QTimer.singleShot(100, app.quit)
        app.exec()

if __name__ == "__main__":
    success = test_app_startup()
    sys.exit(0 if success else 1)