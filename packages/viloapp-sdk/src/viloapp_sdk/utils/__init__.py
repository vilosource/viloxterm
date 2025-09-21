"""SDK utilities for plugin development."""

from .decorators import (
    plugin,
    command,
    widget,
    service,
    activation_event,
    contribution,
)

from .validators import (
    ManifestValidator,
    VersionCompatibilityChecker,
    DependencyValidator,
    PermissionValidator,
    ConfigurationSchemaValidator,
    validate_manifest,
    validate_version_compatibility,
    validate_dependencies,
    validate_permissions,
    validate_configuration_schema,
)

__all__ = [
    # Decorators
    "plugin",
    "command",
    "widget",
    "service",
    "activation_event",
    "contribution",
    # Validators
    "ManifestValidator",
    "VersionCompatibilityChecker",
    "DependencyValidator",
    "PermissionValidator",
    "ConfigurationSchemaValidator",
    "validate_manifest",
    "validate_version_compatibility",
    "validate_dependencies",
    "validate_permissions",
    "validate_configuration_schema",
]
