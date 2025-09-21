"""Validation utilities for plugin development."""

import json
import re
import semver
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

from ..exceptions import PluginError


@dataclass
class ValidationError:
    """Represents a validation error."""
    field: str
    message: str
    severity: str = "error"  # error, warning, info
    value: Optional[Any] = None


@dataclass
class ValidationResult:
    """Result of a validation operation."""
    valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationError] = field(default_factory=list)

    def add_error(self, field: str, message: str, value: Any = None) -> None:
        """Add an error to the result."""
        self.errors.append(ValidationError(field, message, "error", value))
        self.valid = False

    def add_warning(self, field: str, message: str, value: Any = None) -> None:
        """Add a warning to the result."""
        self.warnings.append(ValidationError(field, message, "warning", value))

    def merge(self, other: 'ValidationResult') -> None:
        """Merge another validation result into this one."""
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        if not other.valid:
            self.valid = False

    def get_all_issues(self) -> List[ValidationError]:
        """Get all errors and warnings."""
        return self.errors + self.warnings

    def format_errors(self) -> str:
        """Format errors as a human-readable string."""
        if not self.errors and not self.warnings:
            return "No validation issues found."

        lines = []
        if self.errors:
            lines.append("Errors:")
            for error in self.errors:
                lines.append(f"  - {error.field}: {error.message}")

        if self.warnings:
            lines.append("Warnings:")
            for warning in self.warnings:
                lines.append(f"  - {warning.field}: {warning.message}")

        return "\n".join(lines)


class BaseValidator(ABC):
    """Base class for validators."""

    @abstractmethod
    def validate(self, data: Any) -> ValidationResult:
        """Validate the given data."""
        pass


class ManifestValidator(BaseValidator):
    """Validator for plugin manifest files (plugin.json)."""

    # Required fields in manifest
    REQUIRED_FIELDS = {
        "name", "displayName", "version", "description",
        "author", "license", "engines"
    }

    # Valid contribution points
    VALID_CONTRIBUTION_POINTS = {
        "commands", "menus", "keybindings", "languages", "grammars",
        "themes", "snippets", "debuggers", "breakpoints", "views",
        "viewsContainers", "problemMatchers", "problemPatterns",
        "taskDefinitions", "configuration"
    }

    # Valid activation event patterns
    ACTIVATION_EVENT_PATTERNS = {
        "onStartup": r"^onStartup$",
        "onCommand": r"^onCommand:[a-zA-Z0-9._-]+$",
        "onLanguage": r"^onLanguage:[a-zA-Z0-9._-]+$",
        "onScheme": r"^onScheme:[a-zA-Z0-9._-]+$",
        "onFileSystem": r"^onFileSystem:[a-zA-Z0-9._/-]+$",
        "onWorkspaceOpen": r"^onWorkspaceOpen$",
        "onWorkspaceContains": r"^onWorkspaceContains:[a-zA-Z0-9._/*?-]+$",
        "onUI": r"^onUI:[a-zA-Z0-9._-]+$",
        "onDebug": r"^onDebug(:|$)",
        "onTask": r"^onTask:[a-zA-Z0-9._-]+$",
    }

    def __init__(self, strict: bool = False):
        """
        Initialize validator.

        Args:
            strict: Whether to apply strict validation rules
        """
        self.strict = strict

    def validate(self, manifest: Union[str, Path, Dict[str, Any]]) -> ValidationResult:
        """
        Validate a plugin manifest.

        Args:
            manifest: Manifest data (dict), file path, or JSON string

        Returns:
            ValidationResult with errors and warnings
        """
        result = ValidationResult(valid=True)

        # Parse manifest data
        try:
            data = self._parse_manifest(manifest)
        except Exception as e:
            result.add_error("manifest", f"Failed to parse manifest: {e}")
            return result

        # Validate structure
        self._validate_structure(data, result)

        # Validate fields
        self._validate_required_fields(data, result)
        self._validate_name(data, result)
        self._validate_version(data, result)
        self._validate_author(data, result)
        self._validate_engines(data, result)
        self._validate_activation_events(data, result)
        self._validate_contributions(data, result)
        self._validate_categories(data, result)
        self._validate_keywords(data, result)

        # Strict mode validations
        if self.strict:
            self._validate_strict_requirements(data, result)

        return result

    def _parse_manifest(self, manifest: Union[str, Path, Dict[str, Any]]) -> Dict[str, Any]:
        """Parse manifest from various input types."""
        if isinstance(manifest, dict):
            return manifest
        elif isinstance(manifest, (str, Path)):
            path = Path(manifest)
            if path.exists():
                # File path
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # JSON string
                try:
                    return json.loads(str(manifest))
                except json.JSONDecodeError:
                    raise ValueError("Invalid JSON string or file path")
        else:
            raise ValueError("Manifest must be dict, file path, or JSON string")

    def _validate_structure(self, data: Dict[str, Any], result: ValidationResult) -> None:
        """Validate basic manifest structure."""
        if not isinstance(data, dict):
            result.add_error("manifest", "Manifest must be a JSON object")
            return

        # Check for unknown top-level fields in strict mode
        if self.strict:
            known_fields = {
                "name", "displayName", "version", "description", "author",
                "license", "keywords", "engines", "categories", "main",
                "icon", "galleryBanner", "preview", "extensionPack",
                "extensionDependencies", "activationEvents", "contributes"
            }
            unknown_fields = set(data.keys()) - known_fields
            if unknown_fields:
                result.add_warning(
                    "manifest",
                    f"Unknown fields in manifest: {', '.join(unknown_fields)}"
                )

    def _validate_required_fields(self, data: Dict[str, Any], result: ValidationResult) -> None:
        """Validate required fields are present."""
        for field in self.REQUIRED_FIELDS:
            if field not in data:
                result.add_error(field, f"Required field '{field}' is missing")
            elif not data[field]:
                result.add_error(field, f"Required field '{field}' cannot be empty")

    def _validate_name(self, data: Dict[str, Any], result: ValidationResult) -> None:
        """Validate plugin name."""
        name = data.get("name")
        if not name:
            return

        # Check format
        if not re.match(r'^[a-z0-9][a-z0-9-_.]*[a-z0-9]$', name):
            result.add_error(
                "name",
                "Name must be lowercase, start and end with alphanumeric characters, "
                "and contain only letters, numbers, hyphens, dots, and underscores"
            )

        # Check length
        if len(name) > 214:
            result.add_error("name", "Name cannot exceed 214 characters")

        if len(name) < 2:
            result.add_error("name", "Name must be at least 2 characters long")

        # Check for reserved names
        reserved_names = {"viloapp", "core", "system", "plugin"}
        if name.lower() in reserved_names:
            result.add_error("name", f"Name '{name}' is reserved")

    def _validate_version(self, data: Dict[str, Any], result: ValidationResult) -> None:
        """Validate version string."""
        version = data.get("version")
        if not version:
            return

        try:
            # Use semver for strict validation
            semver.VersionInfo.parse(version)
        except ValueError:
            result.add_error(
                "version",
                f"Version '{version}' is not a valid semantic version (e.g., '1.0.0')"
            )

    def _validate_author(self, data: Dict[str, Any], result: ValidationResult) -> None:
        """Validate author field."""
        author = data.get("author")
        if not author:
            return

        if isinstance(author, str):
            # String format is acceptable
            if len(author.strip()) == 0:
                result.add_error("author", "Author string cannot be empty")
        elif isinstance(author, dict):
            # Dict format validation
            if "name" not in author:
                result.add_error("author", "Author object must include 'name' field")

            # Validate email format if present
            if "email" in author:
                email = author["email"]
                if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
                    result.add_warning("author.email", f"Email '{email}' may not be valid")

            # Validate URL format if present
            if "url" in author:
                url = author["url"]
                if not re.match(r'^https?://', url):
                    result.add_warning("author.url", f"URL '{url}' should start with http:// or https://")
        else:
            result.add_error("author", "Author must be a string or object with 'name' field")

    def _validate_engines(self, data: Dict[str, Any], result: ValidationResult) -> None:
        """Validate engines field."""
        engines = data.get("engines")
        if not engines:
            return

        if not isinstance(engines, dict):
            result.add_error("engines", "Engines must be an object")
            return

        # Check for viloapp engine requirement
        if "viloapp" not in engines:
            result.add_warning("engines", "Should specify viloapp engine compatibility")

        # Validate version constraints
        for engine, constraint in engines.items():
            if not isinstance(constraint, str):
                result.add_error(f"engines.{engine}", "Engine version constraint must be a string")
                continue

            # Basic version constraint validation - allow for >=, <=, ~, ^, =, or just version
            if not re.match(r'^([><=^~]+)?[\d.]+', constraint):
                result.add_warning(
                    f"engines.{engine}",
                    f"Version constraint '{constraint}' may not be valid"
                )

    def _validate_activation_events(self, data: Dict[str, Any], result: ValidationResult) -> None:
        """Validate activation events."""
        events = data.get("activationEvents")
        if not events:
            return

        if not isinstance(events, list):
            result.add_error("activationEvents", "Activation events must be an array")
            return

        for i, event in enumerate(events):
            if not isinstance(event, str):
                result.add_error(f"activationEvents[{i}]", "Activation event must be a string")
                continue

            # Validate event format
            valid = False
            for pattern_name, pattern in self.ACTIVATION_EVENT_PATTERNS.items():
                if re.match(pattern, event):
                    valid = True
                    break

            if not valid:
                result.add_error(
                    f"activationEvents[{i}]",
                    f"Invalid activation event format: '{event}'"
                )

    def _validate_contributions(self, data: Dict[str, Any], result: ValidationResult) -> None:
        """Validate contribution points."""
        contributes = data.get("contributes")
        if not contributes:
            return

        if not isinstance(contributes, dict):
            result.add_error("contributes", "Contributes must be an object")
            return

        # Check contribution points
        for point, config in contributes.items():
            if point not in self.VALID_CONTRIBUTION_POINTS:
                result.add_warning(
                    f"contributes.{point}",
                    f"Unknown contribution point: '{point}'"
                )

            # Validate specific contribution types
            if point == "commands":
                self._validate_commands_contribution(config, result, f"contributes.{point}")
            elif point == "configuration":
                self._validate_configuration_contribution(config, result, f"contributes.{point}")

    def _validate_commands_contribution(self, commands: Any, result: ValidationResult, prefix: str) -> None:
        """Validate commands contribution."""
        if not isinstance(commands, list):
            result.add_error(prefix, "Commands contribution must be an array")
            return

        for i, cmd in enumerate(commands):
            cmd_prefix = f"{prefix}[{i}]"

            if not isinstance(cmd, dict):
                result.add_error(cmd_prefix, "Command must be an object")
                continue

            # Required fields
            if "command" not in cmd:
                result.add_error(f"{cmd_prefix}.command", "Command ID is required")
            else:
                # Check command ID format
                if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9._-]*$', cmd["command"]):
                    result.add_error(
                        f"{cmd_prefix}.command",
                        f"Invalid command ID format: '{cmd['command']}'"
                    )

            if "title" not in cmd:
                result.add_error(f"{cmd_prefix}.title", "Command title is required")

    def _validate_configuration_contribution(self, config: Any, result: ValidationResult, prefix: str) -> None:
        """Validate configuration contribution."""
        if not isinstance(config, dict):
            result.add_error(prefix, "Configuration contribution must be an object")
            return

        # Should have properties
        if "properties" not in config:
            result.add_warning(f"{prefix}.properties", "Configuration should have properties")

    def _validate_categories(self, data: Dict[str, Any], result: ValidationResult) -> None:
        """Validate categories field."""
        categories = data.get("categories")
        if not categories:
            return

        if not isinstance(categories, list):
            result.add_error("categories", "Categories must be an array")
            return

        valid_categories = {
            "Azure", "Data Science", "Debuggers", "Extension Packs",
            "Education", "Formatters", "Keymaps", "Language Packs",
            "Linters", "Machine Learning", "Notebooks", "Other",
            "Programming Languages", "SCM Providers", "Snippets",
            "Testing", "Themes", "Visualization"
        }

        for i, category in enumerate(categories):
            if not isinstance(category, str):
                result.add_error(f"categories[{i}]", "Category must be a string")
            elif category not in valid_categories:
                result.add_warning(
                    f"categories[{i}]",
                    f"Unknown category: '{category}'. Valid categories: {', '.join(sorted(valid_categories))}"
                )

    def _validate_keywords(self, data: Dict[str, Any], result: ValidationResult) -> None:
        """Validate keywords field."""
        keywords = data.get("keywords")
        if not keywords:
            return

        if not isinstance(keywords, list):
            result.add_error("keywords", "Keywords must be an array")
            return

        if len(keywords) > 5:
            result.add_warning("keywords", "Consider using 5 or fewer keywords")

        for i, keyword in enumerate(keywords):
            if not isinstance(keyword, str):
                result.add_error(f"keywords[{i}]", "Keyword must be a string")
            elif len(keyword.strip()) == 0:
                result.add_error(f"keywords[{i}]", "Keyword cannot be empty")

    def _validate_strict_requirements(self, data: Dict[str, Any], result: ValidationResult) -> None:
        """Apply strict validation requirements."""
        # Require specific fields in strict mode
        strict_required = {"displayName", "description", "keywords", "categories"}
        for field in strict_required:
            if field not in data or not data[field]:
                result.add_warning(field, f"Field '{field}' is recommended in strict mode")

        # Require homepage or repository
        if "homepage" not in data and "repository" not in data:
            result.add_warning(
                "metadata",
                "Consider adding 'homepage' or 'repository' field"
            )


class VersionCompatibilityChecker(BaseValidator):
    """Validator for version compatibility checking."""

    def __init__(self, host_version: str = "2.0.0"):
        """
        Initialize with host version.

        Args:
            host_version: The host application version
        """
        self.host_version = semver.VersionInfo.parse(host_version)

    def validate(self, version_constraints: Dict[str, str]) -> ValidationResult:
        """
        Validate version compatibility.

        Args:
            version_constraints: Dict of engine -> version constraint

        Returns:
            ValidationResult
        """
        result = ValidationResult(valid=True)

        for engine, constraint in version_constraints.items():
            if engine == "viloapp":
                self._check_viloapp_compatibility(constraint, result)
            elif engine == "python":
                self._check_python_compatibility(constraint, result)
            else:
                result.add_warning(
                    f"engines.{engine}",
                    f"Unknown engine '{engine}' - cannot verify compatibility"
                )

        return result

    def _check_viloapp_compatibility(self, constraint: str, result: ValidationResult) -> None:
        """Check ViloxTerm compatibility."""
        try:
            # Parse constraint and check against host version
            if constraint.startswith(">="):
                min_version = semver.VersionInfo.parse(constraint[2:].strip())
                if self.host_version < min_version:
                    result.add_error(
                        "engines.viloapp",
                        f"Host version {self.host_version} is below minimum required {min_version}"
                    )
            elif constraint.startswith("^"):
                base_version = semver.VersionInfo.parse(constraint[1:].strip())
                if not (base_version.major == self.host_version.major and
                       self.host_version >= base_version):
                    result.add_error(
                        "engines.viloapp",
                        f"Host version {self.host_version} is not compatible with ^{base_version}"
                    )
            else:
                # Try to parse as a direct version constraint
                # If it doesn't start with a known operator, validate the format at least
                if not re.match(r'^([><=^~]+)?[\d.]+', constraint):
                    result.add_error("engines.viloapp", f"Invalid version constraint format: '{constraint}'")
            # Add more constraint types as needed
        except ValueError as e:
            result.add_error("engines.viloapp", f"Invalid version constraint: {e}")

    def _check_python_compatibility(self, constraint: str, result: ValidationResult) -> None:
        """Check Python compatibility."""
        # This would check against current Python version
        result.add_warning(
            "engines.python",
            "Python version compatibility checking not fully implemented"
        )


class DependencyValidator(BaseValidator):
    """Validator for plugin dependencies."""

    def __init__(self, available_plugins: Optional[Set[str]] = None):
        """
        Initialize with available plugins.

        Args:
            available_plugins: Set of available plugin IDs
        """
        self.available_plugins = available_plugins or set()

    def validate(self, dependencies: Union[List[str], Dict[str, str]]) -> ValidationResult:
        """
        Validate plugin dependencies.

        Args:
            dependencies: List of plugin IDs or dict of plugin -> version

        Returns:
            ValidationResult
        """
        result = ValidationResult(valid=True)

        if isinstance(dependencies, list):
            dep_dict = {dep: "*" for dep in dependencies}
        else:
            dep_dict = dependencies

        for plugin_id, version_constraint in dep_dict.items():
            self._validate_dependency(plugin_id, version_constraint, result)

        return result

    def _validate_dependency(self, plugin_id: str, version_constraint: str, result: ValidationResult) -> None:
        """Validate a single dependency."""
        # Check plugin ID format
        if not re.match(r'^[a-z0-9][a-z0-9-_.]*[a-z0-9]$', plugin_id):
            result.add_error(
                f"dependencies.{plugin_id}",
                f"Invalid plugin ID format: '{plugin_id}'"
            )

        # Check if plugin is available
        if self.available_plugins and plugin_id not in self.available_plugins:
            result.add_warning(
                f"dependencies.{plugin_id}",
                f"Plugin '{plugin_id}' is not available"
            )

        # Validate version constraint format - allow *, >=, <=, ~, ^, =, or just version
        if version_constraint != "*" and not re.match(r'^([><=^~]+)?[\d.]+.*', version_constraint):
            result.add_error(
                f"dependencies.{plugin_id}",
                f"Invalid version constraint: '{version_constraint}'"
            )


class PermissionValidator(BaseValidator):
    """Validator for plugin permissions."""

    VALID_PERMISSION_CATEGORIES = {
        "filesystem", "network", "system", "ui", "clipboard",
        "notification", "workspace", "editor", "terminal", "debug"
    }

    VALID_PERMISSION_SCOPES = {
        "read", "write", "execute", "create", "delete", "modify"
    }

    def validate(self, permissions: Union[List[str], Dict[str, Any]]) -> ValidationResult:
        """
        Validate plugin permissions.

        Args:
            permissions: List of permission strings or dict with detailed permissions

        Returns:
            ValidationResult
        """
        result = ValidationResult(valid=True)

        if isinstance(permissions, list):
            for i, permission in enumerate(permissions):
                self._validate_permission_string(permission, result, f"permissions[{i}]")
        elif isinstance(permissions, dict):
            for category, scopes in permissions.items():
                self._validate_permission_category(category, scopes, result)
        else:
            result.add_error("permissions", "Permissions must be an array or object")

        return result

    def _validate_permission_string(self, permission: str, result: ValidationResult, field: str) -> None:
        """Validate a permission string."""
        if not isinstance(permission, str):
            result.add_error(field, "Permission must be a string")
            return

        # Parse permission format: category:scope:resource
        parts = permission.split(":")
        if len(parts) < 2:
            result.add_error(field, f"Invalid permission format: '{permission}'. Expected 'category:scope' or 'category:scope:resource'")
            return

        category, scope = parts[0], parts[1]

        if category not in self.VALID_PERMISSION_CATEGORIES:
            result.add_error(
                field,
                f"Invalid permission category: '{category}'. Valid categories: {', '.join(sorted(self.VALID_PERMISSION_CATEGORIES))}"
            )

        if scope not in self.VALID_PERMISSION_SCOPES:
            result.add_error(
                field,
                f"Invalid permission scope: '{scope}'. Valid scopes: {', '.join(sorted(self.VALID_PERMISSION_SCOPES))}"
            )

    def _validate_permission_category(self, category: str, scopes: Any, result: ValidationResult) -> None:
        """Validate a permission category."""
        field = f"permissions.{category}"

        if category not in self.VALID_PERMISSION_CATEGORIES:
            result.add_error(
                field,
                f"Invalid permission category: '{category}'"
            )

        if not isinstance(scopes, list):
            result.add_error(field, "Permission scopes must be an array")
            return

        for i, scope in enumerate(scopes):
            if scope not in self.VALID_PERMISSION_SCOPES:
                result.add_error(
                    f"{field}[{i}]",
                    f"Invalid permission scope: '{scope}'"
                )


class ConfigurationSchemaValidator(BaseValidator):
    """Validator for plugin configuration schemas."""

    VALID_TYPES = {
        "string", "number", "integer", "boolean", "array", "object", "null"
    }

    def validate(self, schema: Dict[str, Any]) -> ValidationResult:
        """
        Validate a configuration schema.

        Args:
            schema: JSON schema for configuration

        Returns:
            ValidationResult
        """
        result = ValidationResult(valid=True)

        if not isinstance(schema, dict):
            result.add_error("schema", "Configuration schema must be an object")
            return result

        # Validate top-level structure
        if "properties" not in schema:
            result.add_warning("schema", "Configuration schema should have 'properties'")

        if "type" in schema and schema["type"] != "object":
            result.add_warning("schema.type", "Top-level configuration should be of type 'object'")

        # Validate properties
        if "properties" in schema:
            self._validate_properties(schema["properties"], result, "schema.properties")

        return result

    def _validate_properties(self, properties: Any, result: ValidationResult, prefix: str) -> None:
        """Validate schema properties."""
        if not isinstance(properties, dict):
            result.add_error(prefix, "Properties must be an object")
            return

        for prop_name, prop_schema in properties.items():
            prop_prefix = f"{prefix}.{prop_name}"
            self._validate_property_schema(prop_schema, result, prop_prefix)

    def _validate_property_schema(self, schema: Any, result: ValidationResult, prefix: str) -> None:
        """Validate a single property schema."""
        if not isinstance(schema, dict):
            result.add_error(prefix, "Property schema must be an object")
            return

        # Check required fields
        if "type" not in schema:
            result.add_error(f"{prefix}.type", "Property must have a 'type' field")
        else:
            prop_type = schema["type"]
            if prop_type not in self.VALID_TYPES:
                result.add_error(
                    f"{prefix}.type",
                    f"Invalid type: '{prop_type}'. Valid types: {', '.join(sorted(self.VALID_TYPES))}"
                )

        # Validate type-specific constraints
        if schema.get("type") == "array" and "items" in schema:
            self._validate_property_schema(schema["items"], result, f"{prefix}.items")

        if schema.get("type") == "object" and "properties" in schema:
            self._validate_properties(schema["properties"], result, f"{prefix}.properties")


# Convenience functions for validation

def validate_manifest(manifest: Union[str, Path, Dict[str, Any]], strict: bool = False) -> ValidationResult:
    """
    Validate a plugin manifest.

    Args:
        manifest: Manifest data, file path, or JSON string
        strict: Whether to apply strict validation

    Returns:
        ValidationResult
    """
    validator = ManifestValidator(strict=strict)
    return validator.validate(manifest)


def validate_version_compatibility(version_constraints: Dict[str, str], host_version: str = "2.0.0") -> ValidationResult:
    """
    Validate version compatibility.

    Args:
        version_constraints: Engine version constraints
        host_version: Host application version

    Returns:
        ValidationResult
    """
    validator = VersionCompatibilityChecker(host_version=host_version)
    return validator.validate(version_constraints)


def validate_dependencies(dependencies: Union[List[str], Dict[str, str]], available_plugins: Optional[Set[str]] = None) -> ValidationResult:
    """
    Validate plugin dependencies.

    Args:
        dependencies: Plugin dependencies
        available_plugins: Set of available plugin IDs

    Returns:
        ValidationResult
    """
    validator = DependencyValidator(available_plugins=available_plugins)
    return validator.validate(dependencies)


def validate_permissions(permissions: Union[List[str], Dict[str, Any]]) -> ValidationResult:
    """
    Validate plugin permissions.

    Args:
        permissions: Plugin permissions

    Returns:
        ValidationResult
    """
    validator = PermissionValidator()
    return validator.validate(permissions)


def validate_configuration_schema(schema: Dict[str, Any]) -> ValidationResult:
    """
    Validate a configuration schema.

    Args:
        schema: Configuration schema

    Returns:
        ValidationResult
    """
    validator = ConfigurationSchemaValidator()
    return validator.validate(schema)


def validate_plugin_complete(manifest_path: Union[str, Path], strict: bool = False) -> ValidationResult:
    """
    Perform complete validation of a plugin.

    Args:
        manifest_path: Path to plugin manifest
        strict: Whether to apply strict validation

    Returns:
        Combined ValidationResult
    """
    result = ValidationResult(valid=True)

    # Validate manifest
    manifest_result = validate_manifest(manifest_path, strict=strict)
    result.merge(manifest_result)

    if not manifest_result.valid:
        return result

    # Parse manifest for additional validations
    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest_data = json.load(f)
    except Exception as e:
        result.add_error("manifest", f"Failed to parse manifest: {e}")
        return result

    # Validate engines if present
    if "engines" in manifest_data:
        engine_result = validate_version_compatibility(manifest_data["engines"])
        result.merge(engine_result)

    # Validate dependencies if present
    if "extensionDependencies" in manifest_data:
        dep_result = validate_dependencies(manifest_data["extensionDependencies"])
        result.merge(dep_result)

    # Validate configuration schema if present
    if "contributes" in manifest_data and "configuration" in manifest_data["contributes"]:
        config_result = validate_configuration_schema(manifest_data["contributes"]["configuration"])
        result.merge(config_result)

    return result