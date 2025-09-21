"""Tests for plugin validators."""

import json
import tempfile
from pathlib import Path

from viloapp_sdk.utils.validators import (
    ManifestValidator, VersionCompatibilityChecker, DependencyValidator,
    PermissionValidator, ConfigurationSchemaValidator,
    validate_manifest, validate_version_compatibility, validate_dependencies,
    validate_permissions, validate_configuration_schema, validate_plugin_complete,
    ValidationResult
)


class TestValidationResult:
    """Test cases for ValidationResult class."""

    def test_validation_result_init(self):
        """Test ValidationResult initialization."""
        result = ValidationResult(valid=True)
        assert result.valid is True
        assert result.errors == []
        assert result.warnings == []

    def test_add_error(self):
        """Test adding errors."""
        result = ValidationResult(valid=True)
        result.add_error("field", "error message", "value")

        assert result.valid is False
        assert len(result.errors) == 1
        assert result.errors[0].field == "field"
        assert result.errors[0].message == "error message"
        assert result.errors[0].value == "value"
        assert result.errors[0].severity == "error"

    def test_add_warning(self):
        """Test adding warnings."""
        result = ValidationResult(valid=True)
        result.add_warning("field", "warning message")

        assert result.valid is True  # Warnings don't affect validity
        assert len(result.warnings) == 1
        assert result.warnings[0].field == "field"
        assert result.warnings[0].message == "warning message"
        assert result.warnings[0].severity == "warning"

    def test_merge(self):
        """Test merging validation results."""
        result1 = ValidationResult(valid=True)
        result1.add_warning("field1", "warning1")

        result2 = ValidationResult(valid=False)
        result2.add_error("field2", "error2")
        result2.add_warning("field3", "warning2")

        result1.merge(result2)

        assert result1.valid is False
        assert len(result1.errors) == 1
        assert len(result1.warnings) == 2

    def test_get_all_issues(self):
        """Test getting all issues."""
        result = ValidationResult(valid=False)
        result.add_error("field1", "error1")
        result.add_warning("field2", "warning1")

        issues = result.get_all_issues()
        assert len(issues) == 2

    def test_format_errors(self):
        """Test formatting errors."""
        result = ValidationResult(valid=False)
        result.add_error("field1", "error message")
        result.add_warning("field2", "warning message")

        formatted = result.format_errors()
        assert "Errors:" in formatted
        assert "field1: error message" in formatted
        assert "Warnings:" in formatted
        assert "field2: warning message" in formatted

    def test_format_errors_empty(self):
        """Test formatting when no errors or warnings."""
        result = ValidationResult(valid=True)
        formatted = result.format_errors()
        assert formatted == "No validation issues found."


class TestManifestValidator:
    """Test cases for ManifestValidator."""

    def test_valid_manifest(self):
        """Test validation of a valid manifest."""
        manifest = {
            "name": "test-plugin",
            "displayName": "Test Plugin",
            "version": "1.0.0",
            "description": "A test plugin",
            "author": {"name": "John Doe", "email": "john@example.com"},
            "license": "MIT",
            "engines": {"viloapp": ">=2.0.0"}
        }

        validator = ManifestValidator()
        result = validator.validate(manifest)

        assert result.valid is True
        assert len(result.errors) == 0

    def test_missing_required_fields(self):
        """Test validation with missing required fields."""
        manifest = {
            "name": "test-plugin",
            # Missing displayName, version, description, author, license, engines
        }

        validator = ManifestValidator()
        result = validator.validate(manifest)

        assert result.valid is False
        error_fields = [error.field for error in result.errors]
        assert "displayName" in error_fields
        assert "version" in error_fields
        assert "description" in error_fields
        assert "author" in error_fields
        assert "license" in error_fields
        assert "engines" in error_fields

    def test_invalid_name_format(self):
        """Test validation with invalid name format."""
        manifest = {
            "name": "Invalid@Name",
            "displayName": "Test Plugin",
            "version": "1.0.0",
            "description": "A test plugin",
            "author": "John Doe",
            "license": "MIT",
            "engines": {"viloapp": ">=2.0.0"}
        }

        validator = ManifestValidator()
        result = validator.validate(manifest)

        assert result.valid is False
        name_errors = [e for e in result.errors if e.field == "name"]
        assert len(name_errors) > 0

    def test_invalid_version_format(self):
        """Test validation with invalid version format."""
        manifest = {
            "name": "test-plugin",
            "displayName": "Test Plugin",
            "version": "invalid-version",
            "description": "A test plugin",
            "author": "John Doe",
            "license": "MIT",
            "engines": {"viloapp": ">=2.0.0"}
        }

        validator = ManifestValidator()
        result = validator.validate(manifest)

        assert result.valid is False
        version_errors = [e for e in result.errors if e.field == "version"]
        assert len(version_errors) > 0

    def test_author_validation(self):
        """Test author field validation."""
        # Valid string author
        manifest1 = {
            "name": "test-plugin",
            "displayName": "Test Plugin",
            "version": "1.0.0",
            "description": "A test plugin",
            "author": "John Doe",
            "license": "MIT",
            "engines": {"viloapp": ">=2.0.0"}
        }

        validator = ManifestValidator()
        result1 = validator.validate(manifest1)
        assert result1.valid is True

        # Valid dict author
        manifest2 = manifest1.copy()
        manifest2["author"] = {"name": "John Doe", "email": "john@example.com"}
        result2 = validator.validate(manifest2)
        assert result2.valid is True

        # Invalid dict author (missing name)
        manifest3 = manifest1.copy()
        manifest3["author"] = {"email": "john@example.com"}
        result3 = validator.validate(manifest3)
        assert result3.valid is False

    def test_activation_events_validation(self):
        """Test activation events validation."""
        manifest = {
            "name": "test-plugin",
            "displayName": "Test Plugin",
            "version": "1.0.0",
            "description": "A test plugin",
            "author": "John Doe",
            "license": "MIT",
            "engines": {"viloapp": ">=2.0.0"},
            "activationEvents": [
                "onStartup",
                "onCommand:test.command",
                "onLanguage:python",
                "invalid-event"
            ]
        }

        validator = ManifestValidator()
        result = validator.validate(manifest)

        assert result.valid is False
        event_errors = [e for e in result.errors if "activationEvents" in e.field]
        assert len(event_errors) > 0  # Should have error for invalid-event

    def test_commands_contribution_validation(self):
        """Test commands contribution validation."""
        manifest = {
            "name": "test-plugin",
            "displayName": "Test Plugin",
            "version": "1.0.0",
            "description": "A test plugin",
            "author": "John Doe",
            "license": "MIT",
            "engines": {"viloapp": ">=2.0.0"},
            "contributes": {
                "commands": [
                    {
                        "command": "test.validCommand",
                        "title": "Valid Command"
                    },
                    {
                        "command": "invalid@command",
                        "title": "Invalid Command"
                    },
                    {
                        # Missing command field
                        "title": "Missing Command ID"
                    }
                ]
            }
        }

        validator = ManifestValidator()
        result = validator.validate(manifest)

        assert result.valid is False
        command_errors = [e for e in result.errors if "contributes.commands" in e.field]
        assert len(command_errors) >= 2  # Invalid command ID and missing command ID

    def test_strict_mode(self):
        """Test strict mode validation."""
        manifest = {
            "name": "test-plugin",
            "displayName": "Test Plugin",
            "version": "1.0.0",
            "description": "A test plugin",
            "author": "John Doe",
            "license": "MIT",
            "engines": {"viloapp": ">=2.0.0"}
            # Missing keywords, categories in strict mode
        }

        validator = ManifestValidator(strict=True)
        result = validator.validate(manifest)

        # Should be valid but have warnings
        assert result.valid is True
        warning_fields = [w.field for w in result.warnings]
        assert "keywords" in warning_fields
        assert "categories" in warning_fields

    def test_validate_from_file(self):
        """Test validating manifest from file."""
        manifest_data = {
            "name": "test-plugin",
            "displayName": "Test Plugin",
            "version": "1.0.0",
            "description": "A test plugin",
            "author": "John Doe",
            "license": "MIT",
            "engines": {"viloapp": ">=2.0.0"}
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(manifest_data, f)
            manifest_path = f.name

        try:
            validator = ManifestValidator()
            result = validator.validate(manifest_path)
            assert result.valid is True
        finally:
            Path(manifest_path).unlink()

    def test_validate_from_json_string(self):
        """Test validating manifest from JSON string."""
        manifest_data = {
            "name": "test-plugin",
            "displayName": "Test Plugin",
            "version": "1.0.0",
            "description": "A test plugin",
            "author": "John Doe",
            "license": "MIT",
            "engines": {"viloapp": ">=2.0.0"}
        }

        json_string = json.dumps(manifest_data)

        validator = ManifestValidator()
        result = validator.validate(json_string)
        assert result.valid is True


class TestVersionCompatibilityChecker:
    """Test cases for VersionCompatibilityChecker."""

    def test_compatible_viloapp_version(self):
        """Test compatible ViloxTerm version."""
        checker = VersionCompatibilityChecker(host_version="2.1.0")
        constraints = {"viloapp": ">=2.0.0"}

        result = checker.validate(constraints)
        assert result.valid is True

    def test_incompatible_viloapp_version(self):
        """Test incompatible ViloxTerm version."""
        checker = VersionCompatibilityChecker(host_version="1.9.0")
        constraints = {"viloapp": ">=2.0.0"}

        result = checker.validate(constraints)
        assert result.valid is False
        assert len(result.errors) > 0

    def test_caret_constraint(self):
        """Test caret constraint compatibility."""
        checker = VersionCompatibilityChecker(host_version="2.1.5")
        constraints = {"viloapp": "^2.1.0"}

        result = checker.validate(constraints)
        assert result.valid is True

        # Test incompatible major version
        checker2 = VersionCompatibilityChecker(host_version="3.0.0")
        result2 = checker2.validate(constraints)
        assert result2.valid is False

    def test_unknown_engine(self):
        """Test unknown engine handling."""
        checker = VersionCompatibilityChecker()
        constraints = {"unknown-engine": "1.0.0"}

        result = checker.validate(constraints)
        assert result.valid is True  # Should not fail, just warn
        assert len(result.warnings) > 0

    def test_invalid_constraint(self):
        """Test invalid version constraint."""
        checker = VersionCompatibilityChecker()
        constraints = {"viloapp": "invalid-constraint"}

        result = checker.validate(constraints)
        assert result.valid is False


class TestDependencyValidator:
    """Test cases for DependencyValidator."""

    def test_valid_dependencies_list(self):
        """Test valid dependencies as list."""
        validator = DependencyValidator(available_plugins={"plugin1", "plugin2"})
        dependencies = ["plugin1", "plugin2"]

        result = validator.validate(dependencies)
        assert result.valid is True

    def test_valid_dependencies_dict(self):
        """Test valid dependencies as dict."""
        validator = DependencyValidator(available_plugins={"plugin1", "plugin2"})
        dependencies = {"plugin1": ">=1.0.0", "plugin2": "^2.0.0"}

        result = validator.validate(dependencies)
        assert result.valid is True

    def test_invalid_plugin_id(self):
        """Test invalid plugin ID format."""
        validator = DependencyValidator()
        dependencies = ["invalid@plugin"]

        result = validator.validate(dependencies)
        assert result.valid is False

    def test_unavailable_plugin(self):
        """Test unavailable plugin warning."""
        validator = DependencyValidator(available_plugins={"available-plugin"})
        dependencies = ["unavailable-plugin"]

        result = validator.validate(dependencies)
        assert result.valid is True  # Should not fail, just warn
        assert len(result.warnings) > 0

    def test_invalid_version_constraint(self):
        """Test invalid version constraint."""
        validator = DependencyValidator()
        dependencies = {"plugin1": "invalid-constraint"}

        result = validator.validate(dependencies)
        assert result.valid is False


class TestPermissionValidator:
    """Test cases for PermissionValidator."""

    def test_valid_permission_strings(self):
        """Test valid permission strings."""
        validator = PermissionValidator()
        permissions = [
            "filesystem:read",
            "network:write",
            "ui:create:dialog",
            "system:execute"
        ]

        result = validator.validate(permissions)
        assert result.valid is True

    def test_valid_permission_dict(self):
        """Test valid permission dictionary."""
        validator = PermissionValidator()
        permissions = {
            "filesystem": ["read", "write"],
            "network": ["read"],
            "ui": ["create", "modify"]
        }

        result = validator.validate(permissions)
        assert result.valid is True

    def test_invalid_permission_format(self):
        """Test invalid permission string format."""
        validator = PermissionValidator()
        permissions = ["invalid-format"]

        result = validator.validate(permissions)
        assert result.valid is False

    def test_invalid_permission_category(self):
        """Test invalid permission category."""
        validator = PermissionValidator()
        permissions = ["invalid-category:read"]

        result = validator.validate(permissions)
        assert result.valid is False

    def test_invalid_permission_scope(self):
        """Test invalid permission scope."""
        validator = PermissionValidator()
        permissions = ["filesystem:invalid-scope"]

        result = validator.validate(permissions)
        assert result.valid is False

    def test_invalid_permission_dict_format(self):
        """Test invalid permission dictionary format."""
        validator = PermissionValidator()
        permissions = {
            "filesystem": "not-a-list",
            "invalid-category": ["read"]
        }

        result = validator.validate(permissions)
        assert result.valid is False


class TestConfigurationSchemaValidator:
    """Test cases for ConfigurationSchemaValidator."""

    def test_valid_schema(self):
        """Test valid configuration schema."""
        validator = ConfigurationSchemaValidator()
        schema = {
            "type": "object",
            "properties": {
                "timeout": {
                    "type": "number",
                    "description": "Timeout in seconds"
                },
                "enabled": {
                    "type": "boolean",
                    "description": "Whether feature is enabled"
                }
            }
        }

        result = validator.validate(schema)
        assert result.valid is True

    def test_nested_object_schema(self):
        """Test nested object schema."""
        validator = ConfigurationSchemaValidator()
        schema = {
            "type": "object",
            "properties": {
                "server": {
                    "type": "object",
                    "properties": {
                        "host": {"type": "string"},
                        "port": {"type": "integer"}
                    }
                }
            }
        }

        result = validator.validate(schema)
        assert result.valid is True

    def test_array_schema(self):
        """Test array schema."""
        validator = ConfigurationSchemaValidator()
        schema = {
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    }
                }
            }
        }

        result = validator.validate(schema)
        assert result.valid is True

    def test_invalid_property_type(self):
        """Test invalid property type."""
        validator = ConfigurationSchemaValidator()
        schema = {
            "type": "object",
            "properties": {
                "field": {
                    "type": "invalid-type"
                }
            }
        }

        result = validator.validate(schema)
        assert result.valid is False

    def test_missing_type(self):
        """Test missing type in property."""
        validator = ConfigurationSchemaValidator()
        schema = {
            "type": "object",
            "properties": {
                "field": {
                    "description": "A field without type"
                }
            }
        }

        result = validator.validate(schema)
        assert result.valid is False

    def test_schema_without_properties(self):
        """Test schema without properties."""
        validator = ConfigurationSchemaValidator()
        schema = {"type": "object"}

        result = validator.validate(schema)
        assert result.valid is True
        assert len(result.warnings) > 0  # Should warn about missing properties


class TestConvenienceFunctions:
    """Test cases for convenience validation functions."""

    def test_validate_manifest_function(self):
        """Test validate_manifest convenience function."""
        manifest = {
            "name": "test-plugin",
            "displayName": "Test Plugin",
            "version": "1.0.0",
            "description": "A test plugin",
            "author": "John Doe",
            "license": "MIT",
            "engines": {"viloapp": ">=2.0.0"}
        }

        result = validate_manifest(manifest)
        assert result.valid is True

    def test_validate_version_compatibility_function(self):
        """Test validate_version_compatibility convenience function."""
        constraints = {"viloapp": ">=2.0.0"}

        result = validate_version_compatibility(constraints)
        assert result.valid is True

    def test_validate_dependencies_function(self):
        """Test validate_dependencies convenience function."""
        dependencies = ["plugin1", "plugin2"]

        result = validate_dependencies(dependencies)
        assert result.valid is True

    def test_validate_permissions_function(self):
        """Test validate_permissions convenience function."""
        permissions = ["filesystem:read", "network:write"]

        result = validate_permissions(permissions)
        assert result.valid is True

    def test_validate_configuration_schema_function(self):
        """Test validate_configuration_schema convenience function."""
        schema = {
            "type": "object",
            "properties": {
                "setting": {"type": "string"}
            }
        }

        result = validate_configuration_schema(schema)
        assert result.valid is True


class TestCompletePluginValidation:
    """Test cases for complete plugin validation."""

    def test_validate_plugin_complete(self):
        """Test complete plugin validation."""
        manifest_data = {
            "name": "test-plugin",
            "displayName": "Test Plugin",
            "version": "1.0.0",
            "description": "A test plugin",
            "author": {"name": "John Doe"},
            "license": "MIT",
            "engines": {"viloapp": ">=2.0.0"},
            "extensionDependencies": ["other-plugin"],
            "contributes": {
                "configuration": {
                    "type": "object",
                    "properties": {
                        "setting": {"type": "string"}
                    }
                }
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(manifest_data, f)
            manifest_path = f.name

        try:
            result = validate_plugin_complete(manifest_path)
            assert result.valid is True
        finally:
            Path(manifest_path).unlink()

    def test_validate_plugin_complete_with_errors(self):
        """Test complete plugin validation with errors."""
        manifest_data = {
            "name": "test-plugin",
            "displayName": "Test Plugin",
            "version": "invalid-version",  # Invalid version
            "description": "A test plugin",
            "author": {"name": "John Doe"},
            "license": "MIT",
            "engines": {"viloapp": ">=999.0.0"},  # Incompatible version
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(manifest_data, f)
            manifest_path = f.name

        try:
            result = validate_plugin_complete(manifest_path)
            assert result.valid is False
            assert len(result.errors) > 0
        finally:
            Path(manifest_path).unlink()

    def test_validate_plugin_complete_invalid_file(self):
        """Test complete plugin validation with invalid file."""
        result = validate_plugin_complete("/nonexistent/file.json")
        assert result.valid is False