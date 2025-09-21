"""Tests for resource monitoring and limiting."""

import threading
import time
from unittest.mock import Mock, patch


def test_resource_type_enum():
    """Test ResourceType enumeration."""
    from viloapp.core.plugin_system.security import ResourceType

    expected_types = ["MEMORY", "CPU", "DISK", "NETWORK"]

    for resource_type in expected_types:
        assert hasattr(ResourceType, resource_type)


def test_resource_monitor_creation():
    """Test ResourceMonitor creation."""
    from viloapp.core.plugin_system.security import ResourceMonitor

    monitor = ResourceMonitor(plugin_id="test-plugin")
    assert monitor is not None
    assert monitor.plugin_id == "test-plugin"


def test_resource_monitor_memory_tracking():
    """Test memory usage tracking."""
    from viloapp.core.plugin_system.security import ResourceMonitor, ResourceType

    monitor = ResourceMonitor(plugin_id="test-plugin")

    # Start monitoring
    monitor.start_monitoring()

    # Check initial memory usage
    memory_usage = monitor.get_resource_usage(ResourceType.MEMORY)
    assert memory_usage >= 0

    # Memory usage should be in bytes
    assert isinstance(memory_usage, (int, float))


def test_resource_monitor_cpu_tracking():
    """Test CPU usage tracking."""
    from viloapp.core.plugin_system.security import ResourceMonitor, ResourceType

    monitor = ResourceMonitor(plugin_id="test-plugin")
    monitor.start_monitoring()

    # Get CPU usage (should be percentage)
    cpu_usage = monitor.get_resource_usage(ResourceType.CPU)
    assert 0 <= cpu_usage <= 100


def test_resource_monitor_disk_tracking():
    """Test disk usage tracking."""
    from viloapp.core.plugin_system.security import ResourceMonitor, ResourceType

    monitor = ResourceMonitor(plugin_id="test-plugin")
    monitor.start_monitoring()

    # Get disk usage
    disk_usage = monitor.get_resource_usage(ResourceType.DISK)
    assert disk_usage >= 0


def test_resource_monitor_network_tracking():
    """Test network usage tracking."""
    from viloapp.core.plugin_system.security import ResourceMonitor, ResourceType

    monitor = ResourceMonitor(plugin_id="test-plugin")
    monitor.start_monitoring()

    # Get network usage
    network_usage = monitor.get_resource_usage(ResourceType.NETWORK)
    assert network_usage >= 0


def test_resource_monitor_periodic_collection():
    """Test that resource monitor collects data periodically."""
    from viloapp.core.plugin_system.security import ResourceMonitor, ResourceType

    monitor = ResourceMonitor(plugin_id="test-plugin", collection_interval=0.1)
    monitor.start_monitoring()

    # Wait for a few collection cycles
    time.sleep(0.3)

    # Should have collected some data points
    history = monitor.get_usage_history(ResourceType.MEMORY)
    assert len(history) >= 2

    monitor.stop_monitoring()


def test_resource_monitor_stop_monitoring():
    """Test stopping resource monitoring."""
    from viloapp.core.plugin_system.security import ResourceMonitor

    monitor = ResourceMonitor(plugin_id="test-plugin")
    monitor.start_monitoring()

    assert monitor.is_monitoring()

    monitor.stop_monitoring()

    assert not monitor.is_monitoring()


def test_resource_limiter_creation():
    """Test ResourceLimiter creation."""
    from viloapp.core.plugin_system.security import ResourceLimiter, ResourceType

    limits = {
        ResourceType.MEMORY: 100 * 1024 * 1024,  # 100MB
        ResourceType.CPU: 50.0,  # 50%
    }

    limiter = ResourceLimiter(plugin_id="test-plugin", limits=limits)
    assert limiter is not None
    assert limiter.plugin_id == "test-plugin"


def test_resource_limiter_memory_limit_enforcement():
    """Test memory limit enforcement."""
    from viloapp.core.plugin_system.security import ResourceLimiter, ResourceType

    # Set a very low memory limit for testing
    limits = {ResourceType.MEMORY: 1024}  # 1KB
    limiter = ResourceLimiter(plugin_id="test-plugin", limits=limits)

    # Mock high memory usage
    with patch.object(limiter, "_get_current_usage", return_value=2048):
        violation = limiter.check_limits()
        assert violation is not None
        assert violation.resource_type == ResourceType.MEMORY
        assert violation.current_usage > violation.limit


def test_resource_limiter_cpu_limit_enforcement():
    """Test CPU limit enforcement."""
    from viloapp.core.plugin_system.security import ResourceLimiter, ResourceType

    # Set CPU limit
    limits = {ResourceType.CPU: 10.0}  # 10%
    limiter = ResourceLimiter(plugin_id="test-plugin", limits=limits)

    # Mock high CPU usage
    with patch.object(limiter, "_get_current_usage", return_value=50.0):
        violation = limiter.check_limits()
        assert violation is not None
        assert violation.resource_type == ResourceType.CPU
        assert violation.current_usage > violation.limit


def test_resource_limiter_no_violation():
    """Test resource limiter when usage is within limits."""
    from viloapp.core.plugin_system.security import ResourceLimiter, ResourceType

    limits = {
        ResourceType.MEMORY: 100 * 1024 * 1024,  # 100MB
        ResourceType.CPU: 50.0,  # 50%
    }
    limiter = ResourceLimiter(plugin_id="test-plugin", limits=limits)

    # Mock low usage
    with patch.object(limiter, "_get_current_usage") as mock_usage:
        mock_usage.side_effect = lambda rt: {
            ResourceType.MEMORY: 50 * 1024 * 1024,  # 50MB
            ResourceType.CPU: 25.0,  # 25%
        }.get(rt, 0)

        violation = limiter.check_limits()
        assert violation is None


def test_resource_violation_object():
    """Test ResourceViolation object properties."""
    from viloapp.core.plugin_system.security import ResourceType, ResourceViolation

    violation = ResourceViolation(
        plugin_id="test-plugin",
        resource_type=ResourceType.MEMORY,
        current_usage=200 * 1024 * 1024,  # 200MB
        limit=100 * 1024 * 1024,  # 100MB
        timestamp=time.time(),
    )

    assert violation.plugin_id == "test-plugin"
    assert violation.resource_type == ResourceType.MEMORY
    assert violation.current_usage == 200 * 1024 * 1024
    assert violation.limit == 100 * 1024 * 1024
    assert violation.current_usage > violation.limit


def test_resource_limiter_with_callback():
    """Test resource limiter with violation callback."""
    from viloapp.core.plugin_system.security import ResourceLimiter, ResourceType

    violation_callback = Mock()

    limits = {ResourceType.MEMORY: 1024}  # 1KB
    limiter = ResourceLimiter(
        plugin_id="test-plugin", limits=limits, violation_callback=violation_callback
    )

    # Mock high memory usage
    with patch.object(limiter, "_get_current_usage", return_value=2048):
        violation = limiter.check_limits()

        # Callback should be called with violation
        violation_callback.assert_called_once_with(violation)


def test_resource_monitor_with_limiter_integration():
    """Test integration between ResourceMonitor and ResourceLimiter."""
    from viloapp.core.plugin_system.security import ResourceLimiter, ResourceMonitor, ResourceType

    # Create monitor with limiter
    limits = {ResourceType.MEMORY: 50 * 1024 * 1024}  # 50MB
    limiter = ResourceLimiter(plugin_id="test-plugin", limits=limits)

    monitor = ResourceMonitor(
        plugin_id="test-plugin", resource_limiter=limiter, collection_interval=0.1
    )

    violation_callback = Mock()
    limiter.violation_callback = violation_callback

    monitor.start_monitoring()

    # Mock high memory usage to trigger violation
    with patch.object(monitor, "get_resource_usage", return_value=100 * 1024 * 1024):
        time.sleep(0.2)  # Wait for monitoring cycle

    monitor.stop_monitoring()

    # Should have detected violation
    assert violation_callback.called


def test_resource_monitor_graceful_degradation():
    """Test resource monitor handles errors gracefully."""
    from viloapp.core.plugin_system.security import ResourceMonitor, ResourceType

    monitor = ResourceMonitor(plugin_id="test-plugin")

    # Mock the process to be None (simulating failure to find process)
    monitor._process = None

    monitor.start_monitoring()

    # Should handle error gracefully and return 0
    memory_usage = monitor.get_resource_usage(ResourceType.MEMORY)
    assert memory_usage == 0

    monitor.stop_monitoring()


def test_resource_monitor_plugin_isolation():
    """Test that resource monitor only tracks specific plugin."""
    from viloapp.core.plugin_system.security import ResourceMonitor

    monitor1 = ResourceMonitor(plugin_id="plugin-1")
    monitor2 = ResourceMonitor(plugin_id="plugin-2")

    # Each monitor should track different plugin
    assert monitor1.plugin_id != monitor2.plugin_id

    # Resource usage should be tracked separately
    monitor1.start_monitoring()
    monitor2.start_monitoring()

    # They should be able to run independently
    assert monitor1.is_monitoring()
    assert monitor2.is_monitoring()

    monitor1.stop_monitoring()
    monitor2.stop_monitoring()


def test_resource_usage_history():
    """Test resource usage history collection."""
    from viloapp.core.plugin_system.security import ResourceMonitor, ResourceType

    monitor = ResourceMonitor(plugin_id="test-plugin", history_size=5)
    monitor.start_monitoring()

    # Wait for some data collection
    time.sleep(0.1)

    history = monitor.get_usage_history(ResourceType.MEMORY)
    assert isinstance(history, list)
    assert len(history) <= 5  # Should respect history size limit

    for entry in history:
        assert "timestamp" in entry
        assert "usage" in entry
        assert entry["usage"] >= 0

    monitor.stop_monitoring()


def test_resource_average_calculation():
    """Test resource usage average calculation."""
    from viloapp.core.plugin_system.security import ResourceMonitor, ResourceType

    monitor = ResourceMonitor(plugin_id="test-plugin")

    # Mock some usage history
    mock_history = [
        {"timestamp": time.time(), "usage": 100},
        {"timestamp": time.time(), "usage": 200},
        {"timestamp": time.time(), "usage": 300},
    ]

    with patch.object(monitor, "get_usage_history", return_value=mock_history):
        average = monitor.get_average_usage(ResourceType.MEMORY)
        assert average == 200  # (100 + 200 + 300) / 3


def test_resource_peak_usage():
    """Test resource peak usage tracking."""
    from viloapp.core.plugin_system.security import ResourceMonitor, ResourceType

    monitor = ResourceMonitor(plugin_id="test-plugin")

    # Mock some usage history
    mock_history = [
        {"timestamp": time.time(), "usage": 100},
        {"timestamp": time.time(), "usage": 300},
        {"timestamp": time.time(), "usage": 200},
    ]

    with patch.object(monitor, "get_usage_history", return_value=mock_history):
        peak = monitor.get_peak_usage(ResourceType.MEMORY)
        assert peak == 300  # Maximum usage


def test_resource_limiter_dynamic_limits():
    """Test dynamic limit adjustment."""
    from viloapp.core.plugin_system.security import ResourceLimiter, ResourceType

    initial_limits = {ResourceType.MEMORY: 100 * 1024 * 1024}
    limiter = ResourceLimiter(plugin_id="test-plugin", limits=initial_limits)

    # Update limits
    new_limits = {ResourceType.MEMORY: 200 * 1024 * 1024}
    limiter.update_limits(new_limits)

    # Check that limits were updated
    assert limiter.get_limit(ResourceType.MEMORY) == 200 * 1024 * 1024


def test_resource_monitor_thread_safety():
    """Test that resource monitor is thread-safe."""
    from viloapp.core.plugin_system.security import ResourceMonitor, ResourceType

    monitor = ResourceMonitor(plugin_id="test-plugin")
    monitor.start_monitoring()

    results = []

    def get_usage():
        for _ in range(10):
            usage = monitor.get_resource_usage(ResourceType.MEMORY)
            results.append(usage)

    # Start multiple threads accessing monitor
    threads = [threading.Thread(target=get_usage) for _ in range(3)]
    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    # Should have collected results from all threads
    assert len(results) == 30

    # All results should be valid
    for result in results:
        assert result >= 0

    monitor.stop_monitoring()
