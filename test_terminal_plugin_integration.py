#!/usr/bin/env python3
"""Test terminal plugin integration with the actual plugin system."""

import logging
import sys

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_plugin_system_integration():
    """Test that the terminal plugin works with the actual plugin system."""
    logger.info("Testing terminal plugin with actual plugin system...")

    try:
        # Import the plugin system components
        from core.plugin_system import PluginRegistry, PluginDiscovery
        from viloapp_sdk import EventBus

        # Create plugin infrastructure
        logger.info("Creating plugin infrastructure...")
        registry = PluginRegistry()
        discovery = PluginDiscovery(registry)
        event_bus = EventBus()

        # Discover plugins
        logger.info("Discovering plugins...")
        plugins = discovery.discover_entry_points()
        logger.info(f"Discovered {len(plugins)} plugins:")
        for p in plugins:
            logger.info(f"  - {p.metadata.id}: {p.metadata.name}")

        terminal_plugin = None
        for plugin_info in plugins:
            if plugin_info.metadata.id == "terminal":
                terminal_plugin = plugin_info
                break

        if terminal_plugin:
            logger.info(f"✓ Found terminal plugin: {terminal_plugin.metadata.name}")
            logger.info(f"  ID: {terminal_plugin.metadata.id}")
            logger.info(f"  Path: {terminal_plugin.path}")
            logger.info(f"  State: {terminal_plugin.state}")

            # Test loading the plugin class
            logger.info("Loading plugin class...")
            # For entry point plugins, we need to load through the entry point
            import importlib.metadata
            entry_points = importlib.metadata.entry_points(group='viloapp.plugins')
            terminal_ep = None
            for ep in entry_points:
                if ep.name == 'terminal':
                    terminal_ep = ep
                    break

            if terminal_ep:
                plugin_class = terminal_ep.load()
                plugin_instance = plugin_class()
            else:
                raise Exception("Could not find terminal entry point")

            metadata = plugin_instance.get_metadata()
            logger.info("✓ Plugin loaded with metadata:")
            logger.info(f"  Name: {metadata.name}")
            logger.info(f"  Version: {metadata.version}")
            logger.info(f"  Capabilities: {metadata.capabilities}")

            return True
        else:
            logger.error("✗ Terminal plugin not discovered")
            return False

    except Exception as e:
        logger.error(f"✗ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function."""
    logger.info("=" * 60)
    logger.info("TERMINAL PLUGIN SYSTEM INTEGRATION TEST")
    logger.info("=" * 60)

    success = test_plugin_system_integration()

    logger.info("")
    logger.info("=" * 60)
    if success:
        logger.info("🎉 INTEGRATION TEST PASSED!")
        logger.info("Terminal plugin is fully compatible with the plugin system.")
        return 0
    else:
        logger.error("❌ INTEGRATION TEST FAILED!")
        logger.error("Terminal plugin needs fixes for plugin system compatibility.")
        return 1

if __name__ == "__main__":
    sys.exit(main())