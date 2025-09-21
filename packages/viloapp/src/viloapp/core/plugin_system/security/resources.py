"""Resource monitoring and limiting for plugin security."""

import time
import threading
import logging
from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional, Callable, Any
from collections import deque

try:
    import psutil
except ImportError:
    psutil = None

logger = logging.getLogger(__name__)


class ResourceType(Enum):
    """Types of resources that can be monitored."""
    MEMORY = "memory"
    CPU = "cpu"
    DISK = "disk"
    NETWORK = "network"


@dataclass
class ResourceViolation:
    """Represents a resource limit violation."""
    plugin_id: str
    resource_type: ResourceType
    current_usage: float
    limit: float
    timestamp: float

    def __str__(self) -> str:
        """String representation of violation."""
        return (
            f"Resource violation: Plugin '{self.plugin_id}' "
            f"exceeded {self.resource_type.value} limit "
            f"({self.current_usage:.2f} > {self.limit:.2f})"
        )


class ResourceMonitor:
    """Monitors resource usage for a plugin."""

    def __init__(
        self,
        plugin_id: str,
        collection_interval: float = 1.0,
        history_size: int = 100,
        resource_limiter: Optional['ResourceLimiter'] = None
    ):
        """
        Initialize resource monitor.

        Args:
            plugin_id: Plugin identifier
            collection_interval: How often to collect data (seconds)
            history_size: Maximum number of historical data points
            resource_limiter: Optional resource limiter
        """
        self.plugin_id = plugin_id
        self.collection_interval = collection_interval
        self.history_size = history_size
        self.resource_limiter = resource_limiter

        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

        # Resource usage history
        self._usage_history: Dict[ResourceType, deque] = {
            resource_type: deque(maxlen=history_size)
            for resource_type in ResourceType
        }

        # Try to find the plugin process
        self._process = self._find_plugin_process()

    def _find_plugin_process(self) -> Optional[Any]:
        """Find the process associated with this plugin."""
        if not psutil:
            logger.warning("psutil not available, resource monitoring will be limited")
            return None

        try:
            # For now, use current process as a fallback
            # In a real implementation, this would find the actual plugin process
            return psutil.Process()
        except Exception as e:
            logger.warning(f"Could not find process for plugin {self.plugin_id}: {e}")
            return None

    def start_monitoring(self) -> None:
        """Start resource monitoring."""
        with self._lock:
            if self._monitoring:
                return

            self._monitoring = True
            self._monitor_thread = threading.Thread(
                target=self._monitor_loop,
                daemon=True,
                name=f"ResourceMonitor-{self.plugin_id}"
            )
            self._monitor_thread.start()

        logger.info(f"Started resource monitoring for plugin {self.plugin_id}")

    def stop_monitoring(self) -> None:
        """Stop resource monitoring."""
        with self._lock:
            if not self._monitoring:
                return

            self._monitoring = False

        # Wait for monitor thread to finish
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5.0)
            if self._monitor_thread.is_alive():
                logger.warning(f"Monitor thread for {self.plugin_id} did not stop cleanly")

        logger.info(f"Stopped resource monitoring for plugin {self.plugin_id}")

    def is_monitoring(self) -> bool:
        """Check if monitoring is active."""
        return self._monitoring

    def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        while self._monitoring:
            try:
                self._collect_resource_data()

                # Check limits if limiter is configured
                if self.resource_limiter:
                    violation = self.resource_limiter.check_limits()
                    if violation and hasattr(self.resource_limiter, 'violation_callback'):
                        if self.resource_limiter.violation_callback:
                            self.resource_limiter.violation_callback(violation)

            except Exception as e:
                logger.error(f"Error in monitoring loop for {self.plugin_id}: {e}")

            # Sleep for collection interval
            time.sleep(self.collection_interval)

    def _collect_resource_data(self) -> None:
        """Collect current resource usage data."""
        timestamp = time.time()

        for resource_type in ResourceType:
            try:
                usage = self._get_resource_usage_internal(resource_type)
                entry = {
                    'timestamp': timestamp,
                    'usage': usage
                }

                with self._lock:
                    self._usage_history[resource_type].append(entry)

            except Exception as e:
                logger.error(f"Error collecting {resource_type.value} usage: {e}")

    def _get_resource_usage_internal(self, resource_type: ResourceType) -> float:
        """Get current resource usage for a specific type."""
        if not self._process:
            return 0.0

        try:
            if resource_type == ResourceType.MEMORY:
                # Memory usage in bytes
                memory_info = self._process.memory_info()
                return float(memory_info.rss)  # Resident Set Size

            elif resource_type == ResourceType.CPU:
                # CPU usage as percentage
                cpu_percent = self._process.cpu_percent()
                return float(cpu_percent)

            elif resource_type == ResourceType.DISK:
                # Disk I/O bytes read + written
                io_counters = self._process.io_counters()
                return float(io_counters.read_bytes + io_counters.write_bytes)

            elif resource_type == ResourceType.NETWORK:
                # Network I/O bytes sent + received
                # Note: psutil doesn't provide per-process network stats easily
                # This is a simplified implementation
                return 0.0

        except Exception as e:
            logger.warning(f"Error getting {resource_type.value} usage: {e}")
            return 0.0

        return 0.0

    def get_resource_usage(self, resource_type: ResourceType) -> float:
        """
        Get current resource usage for a specific type.

        Args:
            resource_type: Type of resource to query

        Returns:
            Current usage value
        """
        try:
            return self._get_resource_usage_internal(resource_type)
        except Exception:
            return 0.0

    def get_usage_history(self, resource_type: ResourceType) -> List[Dict[str, Any]]:
        """
        Get usage history for a resource type.

        Args:
            resource_type: Type of resource

        Returns:
            List of usage entries with timestamp and usage
        """
        with self._lock:
            return list(self._usage_history[resource_type])

    def get_average_usage(self, resource_type: ResourceType, window_seconds: Optional[float] = None) -> float:
        """
        Get average usage over a time window.

        Args:
            resource_type: Type of resource
            window_seconds: Time window in seconds (None for all history)

        Returns:
            Average usage value
        """
        history = self.get_usage_history(resource_type)
        if not history:
            return 0.0

        # Filter by time window if specified
        if window_seconds:
            cutoff_time = time.time() - window_seconds
            history = [entry for entry in history if entry['timestamp'] >= cutoff_time]

        if not history:
            return 0.0

        total_usage = sum(entry['usage'] for entry in history)
        return total_usage / len(history)

    def get_peak_usage(self, resource_type: ResourceType, window_seconds: Optional[float] = None) -> float:
        """
        Get peak usage over a time window.

        Args:
            resource_type: Type of resource
            window_seconds: Time window in seconds (None for all history)

        Returns:
            Peak usage value
        """
        history = self.get_usage_history(resource_type)
        if not history:
            return 0.0

        # Filter by time window if specified
        if window_seconds:
            cutoff_time = time.time() - window_seconds
            history = [entry for entry in history if entry['timestamp'] >= cutoff_time]

        if not history:
            return 0.0

        return max(entry['usage'] for entry in history)


class ResourceLimiter:
    """Enforces resource limits for plugins."""

    def __init__(
        self,
        plugin_id: str,
        limits: Dict[ResourceType, float],
        violation_callback: Optional[Callable[[ResourceViolation], None]] = None
    ):
        """
        Initialize resource limiter.

        Args:
            plugin_id: Plugin identifier
            limits: Resource limits by type
            violation_callback: Callback for limit violations
        """
        self.plugin_id = plugin_id
        self._limits = limits.copy()
        self.violation_callback = violation_callback
        self._lock = threading.Lock()

        # Try to find the plugin process for monitoring
        self._process = self._find_plugin_process()

    def _find_plugin_process(self) -> Optional[Any]:
        """Find the process associated with this plugin."""
        if not psutil:
            return None

        try:
            # For now, use current process as a fallback
            return psutil.Process()
        except Exception:
            return None

    def get_limit(self, resource_type: ResourceType) -> Optional[float]:
        """Get limit for a resource type."""
        with self._lock:
            return self._limits.get(resource_type)

    def set_limit(self, resource_type: ResourceType, limit: float) -> None:
        """Set limit for a resource type."""
        with self._lock:
            self._limits[resource_type] = limit

    def update_limits(self, new_limits: Dict[ResourceType, float]) -> None:
        """Update multiple limits at once."""
        with self._lock:
            self._limits.update(new_limits)

    def _get_current_usage(self, resource_type: ResourceType) -> float:
        """Get current usage for a resource type."""
        if not self._process:
            return 0.0

        try:
            if resource_type == ResourceType.MEMORY:
                memory_info = self._process.memory_info()
                return float(memory_info.rss)

            elif resource_type == ResourceType.CPU:
                cpu_percent = self._process.cpu_percent()
                return float(cpu_percent)

            elif resource_type == ResourceType.DISK:
                io_counters = self._process.io_counters()
                return float(io_counters.read_bytes + io_counters.write_bytes)

            elif resource_type == ResourceType.NETWORK:
                return 0.0

        except Exception:
            return 0.0

        return 0.0

    def check_limits(self) -> Optional[ResourceViolation]:
        """
        Check if any resource limits are violated.

        Returns:
            ResourceViolation if any limit is exceeded, None otherwise
        """
        with self._lock:
            for resource_type, limit in self._limits.items():
                current_usage = self._get_current_usage(resource_type)

                if current_usage > limit:
                    violation = ResourceViolation(
                        plugin_id=self.plugin_id,
                        resource_type=resource_type,
                        current_usage=current_usage,
                        limit=limit,
                        timestamp=time.time()
                    )

                    logger.warning(str(violation))

                    # Call violation callback if configured
                    if self.violation_callback:
                        self.violation_callback(violation)

                    return violation

        return None

    def check_resource_limit(self, resource_type: ResourceType) -> Optional[ResourceViolation]:
        """
        Check if a specific resource limit is violated.

        Args:
            resource_type: Type of resource to check

        Returns:
            ResourceViolation if limit is exceeded, None otherwise
        """
        limit = self.get_limit(resource_type)
        if limit is None:
            return None

        current_usage = self._get_current_usage(resource_type)

        if current_usage > limit:
            return ResourceViolation(
                plugin_id=self.plugin_id,
                resource_type=resource_type,
                current_usage=current_usage,
                limit=limit,
                timestamp=time.time()
            )

        return None

    def get_usage_summary(self) -> Dict[str, Any]:
        """
        Get a summary of current usage vs limits.

        Returns:
            Summary dictionary with usage and limits
        """
        summary = {
            'plugin_id': self.plugin_id,
            'timestamp': time.time(),
            'resources': {}
        }

        with self._lock:
            for resource_type, limit in self._limits.items():
                current_usage = self._get_current_usage(resource_type)
                usage_percent = (current_usage / limit * 100) if limit > 0 else 0

                summary['resources'][resource_type.value] = {
                    'current_usage': current_usage,
                    'limit': limit,
                    'usage_percent': usage_percent,
                    'is_violated': current_usage > limit
                }

        return summary