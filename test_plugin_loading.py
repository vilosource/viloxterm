#!/usr/bin/env python3
"""Test script to verify plugin loading functionality."""

import sys
import logging
from pathlib import Path

# Add packages to path
packages_dir = Path(__file__).parent / "packages"
for pkg in ["viloapp-sdk/src", "viloxterm/src"]:
    pkg_path = packages_dir / pkg
    if pkg_path.exists():
        sys.path.insert(0, str(pkg_path))

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_plugin_loading():
    """Test that plugins can be loaded."""
    print("=== Testing Plugin Loading ===\n")

    # Test 1: Import SDK
    print("1. Testing SDK import...")
    try:
        import viloapp_sdk
        print("   ✓ SDK imported successfully")
        print(f"   Version: {viloapp_sdk.__version__ if hasattr(viloapp_sdk, '__version__') else 'N/A'}")
    except ImportError as e:
        print(f"   ✗ Failed to import SDK: {e}")
        return False

    # Test 2: Import EventBus
    print("\n2. Testing EventBus...")
    try:
        from viloapp_sdk import EventBus, PluginEvent, EventType
        event_bus = EventBus()
        print("   ✓ EventBus created successfully")

        # Test event emission
        test_event = PluginEvent(
            type=EventType.CUSTOM,
            source="test",
            data={"message": "test"}
        )
        event_bus.emit(test_event)
        print("   ✓ Event emitted successfully")
    except Exception as e:
        print(f"   ✗ EventBus test failed: {e}")
        return False

    # Test 3: Create Plugin Manager
    print("\n3. Testing Plugin Manager...")
    try:
        from core.plugin_system import PluginManager

        # Create mock services
        mock_services = {
            'command_service': None,
            'settings_service': None,
            'workspace_service': None,
            'theme_service': None,
            'ui_service': None
        }

        # Create plugin manager
        manager = PluginManager(event_bus, mock_services)
        print("   ✓ Plugin Manager created successfully")
    except Exception as e:
        print(f"   ✗ Plugin Manager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test 4: Discover plugins
    print("\n4. Testing Plugin Discovery...")
    try:
        from core.plugin_system import PluginDiscovery, PluginRegistry

        registry = PluginRegistry()
        discovery = PluginDiscovery(registry)

        # Set plugin directories - discovery expects parent dir containing plugin dirs
        packages_dir = Path(__file__).parent / "packages"

        plugins = []
        if packages_dir.exists():
            discovered = discovery.discover_from_directory(packages_dir)
            plugins.extend(discovered)
            print(f"   ✓ Discovered {len(discovered)} plugin(s) in packages directory")

        if plugins:
            for plugin in plugins:
                print(f"      - {plugin.metadata.id}: {plugin.metadata.name}")
    except Exception as e:
        print(f"   ✗ Plugin Discovery test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test 5: Load Terminal Plugin
    print("\n5. Testing Terminal Plugin Loading...")
    try:
        # Try to import terminal plugin directly
        sys.path.insert(0, str(Path(__file__).parent / "packages" / "viloxterm" / "src"))

        import viloxterm.plugin
        print("   ✓ Terminal plugin module imported")

        # Create plugin instance
        plugin = viloxterm.plugin.TerminalPlugin()
        print("   ✓ Terminal plugin instantiated")

        # Get metadata
        metadata = plugin.get_metadata()
        print(f"   ✓ Plugin metadata: {metadata.id} v{metadata.version}")
    except Exception as e:
        print(f"   ✗ Terminal Plugin test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n=== All Tests Passed! ===")
    return True

if __name__ == "__main__":
    success = test_plugin_loading()
    sys.exit(0 if success else 1)