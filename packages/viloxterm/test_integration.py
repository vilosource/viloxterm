#!/usr/bin/env python3
"""Test script to verify terminal plugin functionality."""

import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def test_plugin_discovery():
    """Test basic plugin discovery."""
    logger.info("Testing plugin entry point discovery...")

    try:
        import importlib.metadata
        entry_points = importlib.metadata.entry_points(group='viloapp.plugins')

        terminal_ep = None
        for ep in entry_points:
            if ep.name == 'terminal':
                terminal_ep = ep
                break

        if terminal_ep:
            logger.info(f"✓ Found terminal plugin entry point: {terminal_ep.value}")

            # Try to load the plugin class
            plugin_class = terminal_ep.load()
            plugin = plugin_class()
            metadata = plugin.get_metadata()

            logger.info("✓ Plugin loaded successfully:")
            logger.info(f"  ID: {metadata.id}")
            logger.info(f"  Name: {metadata.name}")
            logger.info(f"  Version: {metadata.version}")
            logger.info(f"  Categories: {metadata.categories}")

            return True
        else:
            logger.error("✗ Terminal plugin entry point not found")
            return False

    except Exception as e:
        logger.error(f"✗ Plugin discovery failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_widget_factory():
    """Test widget factory functionality."""
    logger.info("Testing widget factory...")

    try:
        from viloxterm.widget import TerminalWidgetFactory

        factory = TerminalWidgetFactory()
        metadata = factory.get_metadata()

        logger.info("✓ Widget factory created:")
        logger.info(f"  ID: {metadata.id}")
        logger.info(f"  Title: {metadata.title}")
        logger.info(f"  Position: {metadata.position}")

        return True

    except Exception as e:
        logger.error(f"✗ Widget factory test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_terminal_server():
    """Test terminal server functionality."""
    logger.info("Testing terminal server...")

    try:
        from viloxterm.server import terminal_server

        # Test server startup
        logger.info("Starting terminal server...")
        port = terminal_server.start_server()
        logger.info(f"✓ Server started on port {port}")

        # Test session creation
        logger.info("Creating test session...")
        session_id = terminal_server.create_session(command="echo", cmd_args="hello world")
        logger.info(f"✓ Session created: {session_id}")

        # Test URL generation
        url = terminal_server.get_terminal_url(session_id)
        logger.info(f"✓ Terminal URL: {url}")

        # Cleanup
        logger.info("Cleaning up...")
        terminal_server.destroy_session(session_id)
        terminal_server.shutdown()
        logger.info("✓ Server shutdown complete")

        return True

    except Exception as e:
        logger.error(f"✗ Terminal server test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    logger.info("=" * 60)
    logger.info("VILOXTERM PLUGIN INTEGRATION TEST")
    logger.info("=" * 60)

    tests = [
        ("Plugin Discovery", test_plugin_discovery),
        ("Widget Factory", test_widget_factory),
        ("Terminal Server", test_terminal_server),
    ]

    results = []
    for test_name, test_func in tests:
        logger.info("")
        logger.info("-" * 40)
        logger.info(f"RUNNING: {test_name}")
        logger.info("-" * 40)
        result = test_func()
        results.append((test_name, result))

    # Summary
    logger.info("")
    logger.info("=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)

    passed = 0
    failed = 0

    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1

    logger.info(f"\nTotal: {len(results)} tests")
    logger.info(f"Passed: {passed}")
    logger.info(f"Failed: {failed}")

    if failed == 0:
        logger.info("\n🎉 ALL TESTS PASSED! Plugin is ready for integration.")
        return 0
    else:
        logger.error(f"\n❌ {failed} TESTS FAILED. Please check the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())