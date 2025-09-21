#!/usr/bin/env python3
"""Test plugin discovery with local packages."""

import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Add SDK to path
sdk_path = Path(__file__).parent / "packages" / "viloapp-sdk" / "src"
if sdk_path.exists():
    sys.path.insert(0, str(sdk_path))

def test_plugin_discovery():
    """Test plugin discovery including local packages."""
    print("=== Testing Plugin Discovery ===\n")

    try:
        from core.plugin_system import PluginDiscovery, PluginRegistry

        registry = PluginRegistry()
        discovery = PluginDiscovery(registry)

        # Discover all plugins
        print("Discovering all plugins...")
        plugins = discovery.discover_all()

        print(f"\nFound {len(plugins)} plugins:")
        for plugin in plugins:
            print(f"  - {plugin.metadata.id}: {plugin.metadata.name} v{plugin.metadata.version}")
            print(f"    Path: {plugin.path}")
            print(f"    State: {plugin.state}")

        # Check specifically for our plugins
        plugin_ids = [p.metadata.id for p in plugins]

        print("\n=== Checking for Expected Plugins ===")
        expected = ["viloxterm", "viloedit"]
        for pid in expected:
            if pid in plugin_ids:
                print(f"  ✓ {pid} found")
            else:
                print(f"  ✗ {pid} NOT found")

        return len(plugins) > 0

    except Exception as e:
        print(f"Error during discovery: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_plugin_discovery()
    sys.exit(0 if success else 1)