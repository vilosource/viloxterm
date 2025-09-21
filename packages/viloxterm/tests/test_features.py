"""Tests for terminal advanced features."""

from unittest.mock import Mock
import platform

from viloxterm.features import (
    TerminalProfile, TerminalProfileManager,
    TerminalSessionManager, TerminalSearch
)
from viloxterm.settings import TerminalSettings, TerminalSettingsManager


class TestTerminalProfile:
    """Test terminal profile functionality."""

    def test_profile_creation(self):
        """Test profile creation."""
        profile = TerminalProfile(
            name="Test Shell",
            shell="/bin/test",
            args=["-l"],
            env={"TEST": "value"},
            cwd="/tmp"
        )

        assert profile.name == "Test Shell"
        assert profile.shell == "/bin/test"
        assert profile.args == ["-l"]
        assert profile.env == {"TEST": "value"}
        assert profile.cwd == "/tmp"


class TestTerminalProfileManager:
    """Test terminal profile manager."""

    def setup_method(self):
        """Setup test environment."""
        self.manager = TerminalProfileManager()

    def test_default_profiles_loaded(self):
        """Test that default profiles are loaded."""
        profiles = self.manager.list_profiles()
        assert len(profiles) > 0

        # Check platform-specific profiles
        if platform.system() == "Windows":
            profile_names = [p.name for p in profiles]
            assert "PowerShell" in profile_names or "Command Prompt" in profile_names
        else:
            profile_names = [p.name for p in profiles]
            assert "Bash" in profile_names or "Shell" in profile_names

    def test_add_custom_profile(self):
        """Test adding custom profile."""
        custom_profile = TerminalProfile(
            name="Custom Shell",
            shell="/bin/custom"
        )

        initial_count = len(self.manager.list_profiles())
        self.manager.add_profile("custom", custom_profile)

        profiles = self.manager.list_profiles()
        assert len(profiles) == initial_count + 1

        retrieved_profile = self.manager.get_profile("custom")
        assert retrieved_profile.name == "Custom Shell"

    def test_get_default_profile(self):
        """Test getting default profile."""
        default_profile = self.manager.get_default_profile()
        assert default_profile is not None
        assert default_profile.shell is not None


class TestTerminalSessionManager:
    """Test terminal session manager."""

    def setup_method(self):
        """Setup test environment."""
        self.mock_server = Mock()
        self.mock_server.create_session.return_value = "session_123"
        self.manager = TerminalSessionManager(self.mock_server)

    def test_create_session_with_profile(self):
        """Test creating session with profile."""
        profile = TerminalProfile(
            name="Test Shell",
            shell="/bin/test",
            args=["-l"]
        )

        session_id = self.manager.create_session(profile, "Test Session")

        assert session_id == "session_123"
        self.mock_server.create_session.assert_called_once_with(
            command="/bin/test",
            cmd_args="-l",
            cwd=None
        )

        # Check session is tracked
        session_info = self.manager.get_session_info(session_id)
        assert session_info["name"] == "Test Session"
        assert session_info["profile"].name == "Test Shell"

    def test_create_session_default_profile(self):
        """Test creating session with default profile."""
        session_id = self.manager.create_session()

        assert session_id == "session_123"
        self.mock_server.create_session.assert_called_once()

    def test_rename_session(self):
        """Test renaming session."""
        # Create session first
        session_id = self.manager.create_session(name="Original Name")

        # Rename session
        self.manager.rename_session(session_id, "New Name")

        # Check name was updated
        session_info = self.manager.get_session_info(session_id)
        assert session_info["name"] == "New Name"

    def test_list_sessions(self):
        """Test listing sessions."""
        # Create multiple sessions
        session1 = self.manager.create_session(name="Session 1")
        self.mock_server.create_session.return_value = "session_456"
        session2 = self.manager.create_session(name="Session 2")

        # List sessions
        sessions = self.manager.list_sessions()
        assert len(sessions) == 2

        session_names = [s["name"] for s in sessions]
        assert "Session 1" in session_names
        assert "Session 2" in session_names


class TestTerminalSearch:
    """Test terminal search functionality."""

    def setup_method(self):
        """Setup test environment."""
        self.search = TerminalSearch()

    def test_search_history(self):
        """Test search history tracking."""
        mock_terminal = Mock()
        mock_terminal.web_view.page.return_value.runJavaScript = Mock()

        # Perform searches
        self.search.search_in_terminal(mock_terminal, "pattern1")
        self.search.search_in_terminal(mock_terminal, "pattern2")

        # Check history
        assert "pattern1" in self.search.search_history
        assert "pattern2" in self.search.search_history

        # Don't add duplicates
        self.search.search_in_terminal(mock_terminal, "pattern1")
        assert self.search.search_history.count("pattern1") == 1

    def test_search_execution(self):
        """Test search execution."""
        mock_terminal = Mock()
        mock_page = Mock()
        mock_terminal.web_view.page.return_value = mock_page

        self.search.search_in_terminal(mock_terminal, "test_pattern", True)

        # Verify JavaScript was executed
        mock_page.runJavaScript.assert_called_once()
        call_args = mock_page.runJavaScript.call_args[0][0]
        assert "test_pattern" in call_args
        assert "caseSensitive: true" in call_args

    def test_find_next_previous(self):
        """Test find next/previous functionality."""
        mock_terminal = Mock()
        mock_page = Mock()
        mock_terminal.web_view.page.return_value = mock_page

        # Test find next
        self.search.find_next(mock_terminal)
        mock_page.runJavaScript.assert_called_with(
            "if (term.searchAddon) term.searchAddon.findNext();"
        )

        # Test find previous
        mock_page.reset_mock()
        self.search.find_previous(mock_terminal)
        mock_page.runJavaScript.assert_called_with(
            "if (term.searchAddon) term.searchAddon.findPrevious();"
        )


class TestTerminalSettings:
    """Test terminal settings functionality."""

    def test_settings_creation(self):
        """Test settings creation with defaults."""
        settings = TerminalSettings()

        assert settings.font_family == "monospace"
        assert settings.font_size == 14
        assert settings.use_theme_colors is True
        assert settings.scrollback_lines == 1000

    def test_settings_serialization(self):
        """Test settings to/from dict."""
        settings = TerminalSettings(
            font_size=16,
            cursor_blink=False
        )

        # Test to_dict
        data = settings.to_dict()
        assert data["font_size"] == 16
        assert data["cursor_blink"] is False

        # Test from_dict
        new_settings = TerminalSettings.from_dict(data)
        assert new_settings.font_size == 16
        assert new_settings.cursor_blink is False


class TestTerminalSettingsManager:
    """Test terminal settings manager."""

    def setup_method(self):
        """Setup test environment."""
        self.mock_config = Mock()
        self.manager = TerminalSettingsManager(self.mock_config)

    def test_get_setting(self):
        """Test getting individual setting."""
        # Test getting existing setting
        value = self.manager.get_setting("font_size")
        assert value == 14  # default value from TerminalSettings

        # Test with default for nonexistent setting
        value = self.manager.get_setting("nonexistent", "default")
        assert value == "default"

    def test_set_setting(self):
        """Test setting individual setting."""
        self.manager.set_setting("font_size", 16)

        assert self.manager.settings.font_size == 16
        # Should call save_settings
        self.mock_config.set.assert_called()

    def test_apply_to_terminal(self):
        """Test applying settings to terminal widget."""
        mock_terminal = Mock()
        mock_page = Mock()
        mock_terminal.web_view.page.return_value = mock_page

        self.manager.apply_to_terminal(mock_terminal)

        # Verify JavaScript was executed
        mock_page.runJavaScript.assert_called_once()
        call_args = mock_page.runJavaScript.call_args[0][0]
        assert "fontFamily" in call_args
        assert "fontSize" in call_args

    def test_sync_with_theme(self):
        """Test syncing with theme colors."""
        theme_colors = {
            "terminal.background": "#000000",
            "terminal.foreground": "#ffffff"
        }

        self.manager.sync_with_theme(theme_colors)

        assert self.manager.settings.background == "#000000"
        assert self.manager.settings.foreground == "#ffffff"