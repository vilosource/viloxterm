"""Plugin sandboxing for security and isolation."""

import os
import time
import logging
import threading
from enum import Enum
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


class RestartPolicy(Enum):
    """Plugin restart policies."""
    NEVER = "never"
    ON_FAILURE = "on_failure"
    ALWAYS = "always"


@dataclass
class OperationRecord:
    """Record of a plugin operation for telemetry."""
    timestamp: float
    operation_type: str
    target: str
    success: bool = True
    details: Dict[str, Any] = field(default_factory=dict)


class PluginSandbox:
    """Provides sandboxing and isolation for plugins."""

    def __init__(
        self,
        plugin_id: str,
        permission_manager: Optional[Any] = None,
        resource_limiter: Optional[Any] = None,
        restart_policy: RestartPolicy = RestartPolicy.ON_FAILURE,
        max_restart_attempts: int = 3,
        crash_callback: Optional[Callable[[str, Exception], None]] = None,
        restart_callback: Optional[Callable[[str], None]] = None
    ):
        """
        Initialize plugin sandbox.

        Args:
            plugin_id: Plugin identifier
            permission_manager: Permission manager instance
            resource_limiter: Resource limiter instance
            restart_policy: How to handle plugin restarts
            max_restart_attempts: Maximum restart attempts
            crash_callback: Callback for plugin crashes
            restart_callback: Callback for plugin restarts
        """
        self.plugin_id = plugin_id
        self.permission_manager = permission_manager
        self.resource_limiter = resource_limiter
        self.restart_policy = restart_policy
        self.max_restart_attempts = max_restart_attempts
        self.crash_callback = crash_callback
        self.restart_callback = restart_callback

        # Isolation settings
        self._allowed_paths: List[str] = []
        self._allowed_hosts: List[str] = []
        self._environment_vars: Dict[str, str] = {}

        # Restart tracking
        self._restart_attempts = 0
        self._last_restart_time = 0.0

        # Telemetry
        self._telemetry_enabled = False
        self._operations: List[OperationRecord] = []
        self._lock = threading.Lock()

        # Default allowed paths for plugins
        self._setup_default_allowed_paths()

    def _setup_default_allowed_paths(self) -> None:
        """Setup default allowed paths for the plugin."""
        # Plugin-specific temporary directory
        plugin_temp = f"/tmp/{self.plugin_id}"

        # Plugin-specific config directory
        config_dir = f"/home/{os.getenv('USER', 'user')}/.config/viloapp/plugins/{self.plugin_id}"

        # Plugin-specific data directory
        data_dir = f"/home/{os.getenv('USER', 'user')}/.local/share/viloapp/plugins/{self.plugin_id}"

        self._allowed_paths = [plugin_temp, config_dir, data_dir]

    def set_allowed_paths(self, paths: List[str]) -> None:
        """Set allowed file system paths for the plugin."""
        self._allowed_paths = paths.copy()

    def add_allowed_path(self, path: str) -> None:
        """Add an allowed file system path."""
        if path not in self._allowed_paths:
            self._allowed_paths.append(path)

    def is_path_allowed(self, path: str) -> bool:
        """
        Check if a file system path is allowed.

        Args:
            path: Path to check

        Returns:
            True if path is allowed
        """
        path = os.path.abspath(path)

        for allowed_path in self._allowed_paths:
            # Handle wildcards and directory matching
            if path.startswith(allowed_path):
                return True

            # Handle parent directory access
            if path == allowed_path:
                return True

        return False

    def set_allowed_hosts(self, hosts: List[str]) -> None:
        """Set allowed network hosts for the plugin."""
        self._allowed_hosts = hosts.copy()

    def add_allowed_host(self, host: str) -> None:
        """Add an allowed network host."""
        if host not in self._allowed_hosts:
            self._allowed_hosts.append(host)

    def is_host_allowed(self, host: str) -> bool:
        """
        Check if a network host is allowed.

        Args:
            host: Host to check

        Returns:
            True if host is allowed
        """
        # Exact match
        if host in self._allowed_hosts:
            return True

        # Check for wildcard matches
        for allowed_host in self._allowed_hosts:
            if allowed_host.startswith("*."):
                domain = allowed_host[2:]
                if host.endswith(domain):
                    return True

        return False

    def get_isolated_environment(self, additional_vars: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """
        Get environment variables for isolated plugin execution.

        Args:
            additional_vars: Additional environment variables

        Returns:
            Environment variables dictionary
        """
        # Start with minimal safe environment
        isolated_env = {
            "PATH": "/usr/bin:/bin",
            "PLUGIN_ID": self.plugin_id,
            "PLUGIN_DATA_DIR": f"/home/{os.getenv('USER', 'user')}/.local/share/viloapp/plugins/{self.plugin_id}",
            "PLUGIN_CONFIG_DIR": f"/home/{os.getenv('USER', 'user')}/.config/viloapp/plugins/{self.plugin_id}",
            "PLUGIN_TEMP_DIR": f"/tmp/{self.plugin_id}",
        }

        # Add plugin-specific environment variables
        isolated_env.update(self._environment_vars)

        # Add additional variables if provided
        if additional_vars:
            isolated_env.update(additional_vars)

        return isolated_env

    def set_environment_variable(self, key: str, value: str) -> None:
        """Set an environment variable for the plugin."""
        self._environment_vars[key] = value

    def handle_plugin_crash(self, exception: Exception) -> None:
        """
        Handle a plugin crash.

        Args:
            exception: Exception that caused the crash
        """
        logger.error(f"Plugin {self.plugin_id} crashed: {exception}")

        # Call crash callback if provided
        if self.crash_callback:
            try:
                self.crash_callback(self.plugin_id, exception)
            except Exception as e:
                logger.error(f"Error in crash callback: {e}")

        # Handle restart policy
        self._handle_restart_policy(exception)

        # Record crash in telemetry
        if self._telemetry_enabled:
            self.record_operation("crash", str(exception), success=False)

    def _handle_restart_policy(self, exception: Exception) -> None:
        """Handle restart policy after a crash."""
        if self.restart_policy == RestartPolicy.NEVER:
            return

        if self.restart_policy == RestartPolicy.ALWAYS or (
            self.restart_policy == RestartPolicy.ON_FAILURE and isinstance(exception, Exception)
        ):
            self._attempt_restart()

    def _attempt_restart(self) -> None:
        """Attempt to restart the plugin."""
        current_time = time.time()

        # Reset restart count if enough time has passed
        if current_time - self._last_restart_time > 300:  # 5 minutes
            self._restart_attempts = 0

        if self._restart_attempts >= self.max_restart_attempts:
            logger.warning(
                f"Plugin {self.plugin_id} has exceeded maximum restart attempts "
                f"({self.max_restart_attempts})"
            )
            return

        self._restart_attempts += 1
        self._last_restart_time = current_time

        logger.info(
            f"Attempting to restart plugin {self.plugin_id} "
            f"(attempt {self._restart_attempts}/{self.max_restart_attempts})"
        )

        # Call restart callback if provided
        if self.restart_callback:
            try:
                self.restart_callback(self.plugin_id)
            except Exception as e:
                logger.error(f"Error in restart callback: {e}")

    def has_permission(self, category, scope, resource: str) -> bool:
        """
        Check if plugin has a specific permission.

        Args:
            category: Permission category
            scope: Permission scope
            resource: Resource identifier

        Returns:
            True if plugin has permission
        """
        if not self.permission_manager:
            return True  # No permission manager means no restrictions

        return self.permission_manager.can_access(
            self.plugin_id, category, scope, resource
        )

    def check_resource_limits(self):
        """
        Check if plugin is violating resource limits.

        Returns:
            ResourceViolation if limits are exceeded, None otherwise
        """
        if not self.resource_limiter:
            return None

        return self.resource_limiter.check_limits()

    def enable_telemetry(self) -> None:
        """Enable telemetry collection."""
        self._telemetry_enabled = True

    def disable_telemetry(self) -> None:
        """Disable telemetry collection."""
        self._telemetry_enabled = False

    def record_operation(self, operation_type: str, target: str, success: bool = True, **details) -> None:
        """
        Record a plugin operation for telemetry.

        Args:
            operation_type: Type of operation
            target: Target of operation
            success: Whether operation was successful
            **details: Additional operation details
        """
        if not self._telemetry_enabled:
            return

        operation = OperationRecord(
            timestamp=time.time(),
            operation_type=operation_type,
            target=target,
            success=success,
            details=details
        )

        with self._lock:
            self._operations.append(operation)

            # Limit telemetry history size
            if len(self._operations) > 1000:
                self._operations = self._operations[-500:]  # Keep last 500

    def get_telemetry(self) -> Dict[str, Any]:
        """
        Get telemetry data for the plugin.

        Returns:
            Telemetry data dictionary
        """
        with self._lock:
            return {
                "plugin_id": self.plugin_id,
                "timestamp": time.time(),
                "operations": [
                    {
                        "timestamp": op.timestamp,
                        "type": op.operation_type,
                        "target": op.target,
                        "success": op.success,
                        "details": op.details
                    }
                    for op in self._operations
                ],
                "restart_attempts": self._restart_attempts,
                "last_restart_time": self._last_restart_time
            }

    def get_security_summary(self) -> Dict[str, Any]:
        """
        Get a summary of security settings and status.

        Returns:
            Security summary dictionary
        """
        return {
            "plugin_id": self.plugin_id,
            "isolation": {
                "allowed_paths": self._allowed_paths,
                "allowed_hosts": self._allowed_hosts,
                "environment_vars": list(self._environment_vars.keys())
            },
            "restart_policy": {
                "policy": self.restart_policy.value,
                "max_attempts": self.max_restart_attempts,
                "current_attempts": self._restart_attempts
            },
            "telemetry": {
                "enabled": self._telemetry_enabled,
                "operation_count": len(self._operations)
            },
            "managers": {
                "has_permission_manager": self.permission_manager is not None,
                "has_resource_limiter": self.resource_limiter is not None
            }
        }

    def cleanup(self) -> None:
        """Clean up sandbox resources."""
        with self._lock:
            self._operations.clear()

        logger.info(f"Cleaned up sandbox for plugin {self.plugin_id}")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()