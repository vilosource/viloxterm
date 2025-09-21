"""Testing utilities for plugin development."""

from .mock_host import MockPluginHost, MockService
from .fixtures import *
from .harness import (
    PluginTestCase,
    WidgetTestCase,
    ServiceTestCase,
    CommandTestCase,
    IntegrationTestCase,
    create_test_plugin_manifest,
    assert_plugin_interface_compliance,
    assert_widget_interface_compliance,
    assert_service_interface_compliance,
)

__all__ = [
    'MockPluginHost',
    'MockService',
    'PluginTestCase',
    'WidgetTestCase',
    'ServiceTestCase',
    'CommandTestCase',
    'IntegrationTestCase',
    'create_test_plugin_manifest',
    'assert_plugin_interface_compliance',
    'assert_widget_interface_compliance',
    'assert_service_interface_compliance',
    # Fixtures are imported via * and available when using testing module
]