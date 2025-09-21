"""Tests for the IMetadata interface."""

import pytest
from typing import Dict, List

from viloapp_sdk.interfaces import IMetadata
from viloapp_sdk.plugin import PluginMetadata


class TestIMetadataInterface:
    """Test the IMetadata interface specification."""

    def test_imetadata_is_abstract(self):
        """Test that IMetadata cannot be instantiated directly."""
        with pytest.raises(TypeError):
            IMetadata()

    def test_abstract_methods_exist(self):
        """Test that all required abstract methods are defined."""
        abstract_methods = IMetadata.__abstractmethods__

        required_methods = {
            "get_id",
            "get_name",
            "get_version",
            "get_description",
            "get_author",
            "get_license",
            "get_dependencies",
            "get_keywords",
        }

        for method in required_methods:
            assert method in abstract_methods, f"Missing abstract method: {method}"


class MockMetadata(IMetadata):
    """Mock implementation of IMetadata for testing."""

    def __init__(self, **kwargs):
        self.data = {
            "id": "test-plugin",
            "name": "Test Plugin",
            "version": "1.0.0",
            "description": "A test plugin",
            "author": {"name": "Test Author", "email": "test@example.com"},
            "license": "MIT",
            "dependencies": {"viloapp": ">=2.0.0", "python": ">=3.8"},
            "keywords": ["test", "plugin"],
            "homepage": "https://example.com",
            "repository": "https://github.com/example/test-plugin",
            "icon": "test-icon",
            "categories": ["testing", "development"],
            **kwargs,
        }

    def get_id(self) -> str:
        return self.data["id"]

    def get_name(self) -> str:
        return self.data["name"]

    def get_version(self) -> str:
        return self.data["version"]

    def get_description(self) -> str:
        return self.data["description"]

    def get_author(self) -> Dict[str, str]:
        return self.data["author"]

    def get_license(self) -> str:
        return self.data["license"]

    def get_dependencies(self) -> Dict[str, str]:
        return self.data["dependencies"]

    def get_keywords(self) -> List[str]:
        return self.data["keywords"]

    def get_homepage(self):
        return self.data.get("homepage")

    def get_repository(self):
        return self.data.get("repository")

    def get_icon(self):
        return self.data.get("icon")

    def get_categories(self) -> List[str]:
        return self.data.get("categories", [])


class TestIMetadataMethods:
    """Test the IMetadata interface methods."""

    @pytest.fixture
    def metadata(self):
        return MockMetadata()

    def test_get_id(self, metadata):
        """Test get_id returns string identifier."""
        plugin_id = metadata.get_id()
        assert isinstance(plugin_id, str)
        assert len(plugin_id) > 0
        assert plugin_id == "test-plugin"

    def test_get_name(self, metadata):
        """Test get_name returns display name."""
        name = metadata.get_name()
        assert isinstance(name, str)
        assert len(name) > 0
        assert name == "Test Plugin"

    def test_get_version(self, metadata):
        """Test get_version returns version string."""
        version = metadata.get_version()
        assert isinstance(version, str)
        assert len(version) > 0
        assert version == "1.0.0"

    def test_get_description(self, metadata):
        """Test get_description returns description."""
        description = metadata.get_description()
        assert isinstance(description, str)
        assert len(description) > 0
        assert description == "A test plugin"

    def test_get_author(self, metadata):
        """Test get_author returns author information dict."""
        author = metadata.get_author()
        assert isinstance(author, dict)
        assert "name" in author
        assert author["name"] == "Test Author"
        assert author.get("email") == "test@example.com"

    def test_get_license(self, metadata):
        """Test get_license returns license identifier."""
        license_id = metadata.get_license()
        assert isinstance(license_id, str)
        assert len(license_id) > 0
        assert license_id == "MIT"

    def test_get_dependencies(self, metadata):
        """Test get_dependencies returns dependency dict."""
        deps = metadata.get_dependencies()
        assert isinstance(deps, dict)
        assert "viloapp" in deps
        assert deps["viloapp"] == ">=2.0.0"
        assert "python" in deps
        assert deps["python"] == ">=3.8"

    def test_get_keywords(self, metadata):
        """Test get_keywords returns list of keywords."""
        keywords = metadata.get_keywords()
        assert isinstance(keywords, list)
        assert "test" in keywords
        assert "plugin" in keywords

    def test_optional_methods(self, metadata):
        """Test optional methods return correct types."""
        homepage = metadata.get_homepage()
        assert homepage is None or isinstance(homepage, str)
        assert homepage == "https://example.com"

        repository = metadata.get_repository()
        assert repository is None or isinstance(repository, str)
        assert repository == "https://github.com/example/test-plugin"

        icon = metadata.get_icon()
        assert icon is None or isinstance(icon, str)
        assert icon == "test-icon"

        categories = metadata.get_categories()
        assert isinstance(categories, list)
        assert "testing" in categories
        assert "development" in categories


class TestMetadataValidation:
    """Test metadata validation functionality."""

    def test_valid_metadata_passes(self):
        """Test that valid metadata passes validation."""
        metadata = MockMetadata()
        errors = metadata.validate()
        assert len(errors) == 0

    def test_missing_required_fields(self):
        """Test validation catches missing required fields."""
        # Test missing ID
        metadata = MockMetadata(id="")
        errors = metadata.validate()
        assert any("ID is required" in error for error in errors)

        # Test missing name
        metadata = MockMetadata(name="")
        errors = metadata.validate()
        assert any("name is required" in error for error in errors)

        # Test missing version
        metadata = MockMetadata(version="")
        errors = metadata.validate()
        assert any("version is required" in error for error in errors)

        # Test missing description
        metadata = MockMetadata(description="")
        errors = metadata.validate()
        assert any("description is required" in error for error in errors)

        # Test missing author
        metadata = MockMetadata(author={})
        errors = metadata.validate()
        assert any("author is required" in error for error in errors)

        # Test missing license
        metadata = MockMetadata(license="")
        errors = metadata.validate()
        assert any("license is required" in error for error in errors)

    def test_invalid_id_format(self):
        """Test validation catches invalid ID format."""
        metadata = MockMetadata(id="invalid id with spaces")
        errors = metadata.validate()
        assert any("alphanumeric" in error for error in errors)

        metadata = MockMetadata(id="invalid@id")
        errors = metadata.validate()
        assert any("alphanumeric" in error for error in errors)

    def test_invalid_version_format(self):
        """Test validation catches invalid version format."""
        metadata = MockMetadata(version="invalid")
        errors = metadata.validate()
        assert any("semantic versioning" in error for error in errors)

        metadata = MockMetadata(version="1.0")
        errors = metadata.validate()
        assert any("semantic versioning" in error for error in errors)

    def test_invalid_author_format(self):
        """Test validation catches invalid author format."""
        metadata = MockMetadata(author="string_author")
        errors = metadata.validate()
        assert any("dictionary" in error for error in errors)

        metadata = MockMetadata(author={"email": "test@example.com"})  # Missing name
        errors = metadata.validate()
        assert any("'name' field" in error for error in errors)


class TestPluginMetadataImplementation:
    """Test that PluginMetadata correctly implements IMetadata."""

    def test_plugin_metadata_is_imetadata(self):
        """Test that PluginMetadata implements IMetadata."""
        metadata = PluginMetadata(
            id="test-plugin",
            name="Test Plugin",
            version="1.0.0",
            description="Test description",
            author="Test Author",
        )

        assert isinstance(metadata, IMetadata)

    def test_plugin_metadata_interface_methods(self):
        """Test PluginMetadata implements all IMetadata methods."""
        metadata = PluginMetadata(
            id="test-plugin",
            name="Test Plugin",
            version="1.0.0",
            description="Test description",
            author="Test Author",
            license="MIT",
            homepage="https://example.com",
            repository="https://github.com/example/test",
            icon="test-icon",
            categories=["test"],
            keywords=["test", "plugin"],
            dependencies_dict={"viloapp": ">=2.0.0"},
        )

        # Test interface methods
        assert metadata.get_id() == "test-plugin"
        assert metadata.get_name() == "Test Plugin"
        assert metadata.get_version() == "1.0.0"
        assert metadata.get_description() == "Test description"
        assert metadata.get_author() == {"name": "Test Author"}
        assert metadata.get_license() == "MIT"
        assert metadata.get_dependencies() == {"viloapp": ">=2.0.0"}
        assert metadata.get_keywords() == ["test", "plugin"]
        assert metadata.get_homepage() == "https://example.com"
        assert metadata.get_repository() == "https://github.com/example/test"
        assert metadata.get_icon() == "test-icon"
        assert metadata.get_categories() == ["test"]

    def test_plugin_metadata_backward_compatibility(self):
        """Test PluginMetadata maintains backward compatibility."""
        # Test string author (legacy format)
        metadata = PluginMetadata(
            id="test-plugin",
            name="Test Plugin",
            version="1.0.0",
            description="Test description",
            author="Test Author",
        )

        author = metadata.get_author()
        assert isinstance(author, dict)
        assert author["name"] == "Test Author"

        # Test legacy dependencies list format
        metadata = PluginMetadata(
            id="test-plugin",
            name="Test Plugin",
            version="1.0.0",
            description="Test description",
            author="Test Author",
            dependencies=["viloapp", "python"],
            engines={"viloapp": ">=2.0.0"},
        )

        deps = metadata.get_dependencies()
        assert isinstance(deps, dict)
        assert deps["viloapp"] == ">=2.0.0"  # From engines
        assert deps["python"] == "*"  # From dependencies list

    def test_plugin_metadata_validation(self):
        """Test PluginMetadata validation."""
        # Valid metadata
        metadata = PluginMetadata(
            id="test-plugin",
            name="Test Plugin",
            version="1.0.0",
            description="Test description",
            author="Test Author",
        )

        errors = metadata.validate()
        assert len(errors) == 0

        # Invalid metadata
        metadata = PluginMetadata(id="", name="", version="invalid", description="", author="")

        errors = metadata.validate()
        assert len(errors) > 0
