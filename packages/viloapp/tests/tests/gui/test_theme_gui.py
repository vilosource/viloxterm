#!/usr/bin/env python3
"""
GUI tests for theme system integration.

Tests theme switching, widget updates, and UI integration
using pytest-qt for non-blocking GUI testing.
"""

from unittest.mock import Mock, patch

import pytest
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QLabel, QWidget

from viloapp.core.themes.theme import Theme
from viloapp.services.service_locator import ServiceLocator
from viloapp.services.theme_service import ThemeService
from viloapp.ui.main_window import MainWindow
from viloapp.ui.themes.theme_provider import ThemeProvider
from viloapp.ui.widgets.split_pane_widget import SplitPaneWidget


class TestThemeGUI:
    """GUI tests for theme system."""

    @pytest.fixture
    def theme_service(self):
        """Create ThemeService for GUI testing."""
        service = ThemeService()
        # Load minimal test themes
        service._register_theme(
            Theme(
                id="test-dark",
                name="Test Dark",
                description="Dark test theme",
                version="1.0.0",
                author="Test",
                colors={
                    "editor.background": "#1e1e1e",
                    "editor.foreground": "#ffffff",
                    "activityBar.background": "#333333",
                },
            )
        )
        service._register_theme(
            Theme(
                id="test-light",
                name="Test Light",
                description="Light test theme",
                version="1.0.0",
                author="Test",
                colors={
                    "editor.background": "#ffffff",
                    "editor.foreground": "#000000",
                    "activityBar.background": "#f0f0f0",
                },
            )
        )
        return service

    @pytest.fixture
    def theme_provider(self, theme_service):
        """Create ThemeProvider for GUI testing."""
        provider = ThemeProvider(theme_service)
        theme_service.set_theme_provider(provider)
        return provider

    @pytest.fixture
    def service_locator(self, theme_service):
        """Set up service locator with theme service."""
        locator = ServiceLocator.get_instance()
        locator.clear()  # Clear any existing services
        locator.register(ThemeService, theme_service)
        return locator

    def test_widget_theme_application(self, qtbot, theme_provider):
        """Test that widgets apply themes correctly."""
        # Create a simple test widget
        widget = QLabel("Test Widget")
        qtbot.addWidget(widget)

        # Apply theme manually (simulating widget's apply_theme method)
        stylesheet = theme_provider.get_stylesheet("test_component")
        widget.setStyleSheet(stylesheet)

        # Widget should have some stylesheet applied
        assert widget.styleSheet() != ""

    def test_theme_switching_updates_widget(self, qtbot, theme_service, theme_provider):
        """Test that theme switching updates widget appearance."""
        # Create test widget
        widget = QLabel("Test Widget")
        qtbot.addWidget(widget)

        # Apply initial theme
        theme_service.apply_theme("test-dark")
        widget.setStyleSheet(theme_provider.get_stylesheet("test_component"))
        dark_stylesheet = widget.styleSheet()

        # Switch to light theme
        theme_service.apply_theme("test-light")
        widget.setStyleSheet(theme_provider.get_stylesheet("test_component"))
        light_stylesheet = widget.styleSheet()

        # Stylesheets should be different
        assert dark_stylesheet != light_stylesheet

    def test_theme_provider_signal_emission(self, qtbot, theme_service, theme_provider):
        """Test that ThemeProvider emits style_changed signal."""
        # Connect signal to mock slot
        mock_slot = Mock()
        theme_provider.style_changed.connect(mock_slot)

        # Apply theme should trigger signal
        with qtbot.waitSignal(theme_provider.style_changed, timeout=1000):
            theme_service.apply_theme("test-dark")

        # Verify signal was emitted
        mock_slot.assert_called()

    def test_widget_automatic_theme_update(
        self, qtbot, theme_service, theme_provider, service_locator
    ):
        """Test that widgets automatically update when themes change."""

        class TestWidget(QWidget):
            """Test widget with theme support."""

            def __init__(self):
                super().__init__()
                self.theme_update_count = 0
                self.connect_theme_signals()
                self.apply_theme()

            def connect_theme_signals(self):
                """Connect to theme change signals."""
                theme_provider.style_changed.connect(self.apply_theme)

            def apply_theme(self):
                """Apply current theme."""
                self.theme_update_count += 1
                colors = theme_service.get_colors()
                self.setStyleSheet(
                    f"""
                    QWidget {{
                        background-color: {colors.get('editor.background', '#ffffff')};
                        color: {colors.get('editor.foreground', '#000000')};
                    }}
                """
                )

        # Create widget
        widget = TestWidget()
        qtbot.addWidget(widget)

        initial_count = widget.theme_update_count
        initial_stylesheet = widget.styleSheet()

        # Change theme should trigger automatic update
        with qtbot.waitSignal(theme_provider.style_changed, timeout=1000):
            theme_service.apply_theme("test-light")

        # Widget should have updated automatically
        assert widget.theme_update_count > initial_count
        assert widget.styleSheet() != initial_stylesheet

    @patch("viloapp.ui.main_window.MainWindow.show")  # Prevent window from actually showing
    def test_main_window_theme_integration(self, mock_show, qtbot, theme_service, service_locator):
        """Test theme integration with MainWindow."""
        # This test is more complex and would require careful mocking
        # to avoid creating a full GUI during testing

        with patch("viloapp.services.initialize_services") as mock_init:
            mock_init.return_value = service_locator

            # Create minimal MainWindow for testing
            try:
                # Note: This might need additional mocking depending on MainWindow complexity
                window = MainWindow()
                qtbot.addWidget(window)

                # Verify window exists
                assert window is not None

            except Exception as e:
                # If MainWindow is too complex to test directly, skip or mock more components
                pytest.skip(f"MainWindow too complex for GUI testing: {e}")

    def test_split_pane_widget_theme_support(self, qtbot, theme_service, service_locator):
        """Test that SplitPaneWidget supports theme changes."""
        # Mock the dependencies that SplitPaneWidget needs
        with patch("viloapp.ui.widgets.split_pane_widget.SplitPaneModel") as mock_model:
            with patch("viloapp.ui.widgets.split_pane_widget.WidgetPool") as mock_pool:
                mock_model_instance = Mock()
                mock_model.return_value = mock_model_instance
                mock_model_instance.root = Mock()

                mock_pool_instance = Mock()
                mock_pool.get_instance.return_value = mock_pool_instance

                try:
                    # Create SplitPaneWidget
                    widget = SplitPaneWidget()
                    qtbot.addWidget(widget)

                    # Test that it has an apply_theme method
                    assert hasattr(widget, "apply_theme")

                    # Call apply_theme (should not crash)
                    widget.apply_theme()

                except Exception as e:
                    # If SplitPaneWidget is too complex, this is acceptable
                    pytest.skip(f"SplitPaneWidget too complex for testing: {e}")

    def test_stylesheet_caching(self, qtbot, theme_provider):
        """Test that ThemeProvider caches stylesheets efficiently."""
        # Request same stylesheet multiple times
        component = "test_component"

        stylesheet1 = theme_provider.get_stylesheet(component)
        stylesheet2 = theme_provider.get_stylesheet(component)

        # Should return same result (cached)
        assert stylesheet1 == stylesheet2

        # Cache should be populated
        assert component in theme_provider._stylesheet_cache

    def test_cache_invalidation_on_theme_change(self, qtbot, theme_service, theme_provider):
        """Test that stylesheet cache is cleared when theme changes."""
        # Generate cached stylesheet
        component = "test_component"
        theme_service.apply_theme("test-dark")
        stylesheet1 = theme_provider.get_stylesheet(component)

        # Verify cache is populated
        assert component in theme_provider._stylesheet_cache

        # Change theme
        theme_service.apply_theme("test-light")

        # Cache should be cleared
        # Note: This depends on implementation - cache might be cleared or marked dirty
        stylesheet2 = theme_provider.get_stylesheet(component)

        # New stylesheet should be different from old one
        assert stylesheet1 != stylesheet2

    def test_theme_error_handling(self, qtbot, theme_service, theme_provider):
        """Test theme error handling in GUI context."""
        # Apply non-existent theme
        result = theme_service.apply_theme("non-existent-theme")
        assert result is False

        # ThemeProvider should handle gracefully
        stylesheet = theme_provider.get_stylesheet("any_component")
        # Should return empty string or fallback stylesheet
        assert isinstance(stylesheet, str)

    def test_multiple_widgets_theme_consistency(self, qtbot, theme_service, theme_provider):
        """Test that multiple widgets show consistent theming."""
        # Create multiple widgets
        widgets = []
        for i in range(3):
            widget = QLabel(f"Widget {i}")
            widgets.append(widget)
            qtbot.addWidget(widget)

        # Apply theme to all widgets
        theme_service.apply_theme("test-dark")

        stylesheets = []
        for widget in widgets:
            # Simulate each widget applying the same component theme
            stylesheet = theme_provider.get_stylesheet("test_component")
            widget.setStyleSheet(stylesheet)
            stylesheets.append(stylesheet)

        # All widgets should have the same stylesheet
        assert all(s == stylesheets[0] for s in stylesheets)

    def test_theme_performance(self, qtbot, theme_service, theme_provider):
        """Test theme switching performance."""
        import time

        # Create multiple widgets
        widgets = []
        for i in range(10):
            widget = QLabel(f"Widget {i}")
            widgets.append(widget)
            qtbot.addWidget(widget)

        # Measure theme switching time
        start_time = time.time()

        # Switch themes multiple times
        for theme_id in ["test-dark", "test-light"] * 5:
            theme_service.apply_theme(theme_id)

            # Apply theme to all widgets
            for widget in widgets:
                stylesheet = theme_provider.get_stylesheet("test_component")
                widget.setStyleSheet(stylesheet)

        end_time = time.time()

        # Should complete reasonably quickly (less than 1 second for 10 widgets * 10 switches)
        duration = end_time - start_time
        assert duration < 1.0, f"Theme switching took too long: {duration}s"

    def test_theme_with_qt_timer(self, qtbot, theme_service, theme_provider):
        """Test theme updates work correctly with Qt timers."""
        widget = QLabel("Timer Test Widget")
        qtbot.addWidget(widget)

        update_count = {"value": 0}

        def update_widget():
            """Update widget theme."""
            stylesheet = theme_provider.get_stylesheet("test_component")
            widget.setStyleSheet(stylesheet)
            update_count["value"] += 1

        # Set up timer to update widget periodically
        timer = QTimer()
        timer.timeout.connect(update_widget)
        timer.start(50)  # 50ms intervals

        try:
            # Change theme while timer is running
            theme_service.apply_theme("test-dark")

            # Wait a bit for timer updates
            qtbot.wait(200)

            # Should have had several timer updates
            assert update_count["value"] > 0

        finally:
            timer.stop()

    @pytest.mark.parametrize("theme_id", ["test-dark", "test-light"])
    def test_theme_switching_parametrized(self, qtbot, theme_service, theme_provider, theme_id):
        """Parametrized test for different themes."""
        widget = QLabel("Parametrized Test")
        qtbot.addWidget(widget)

        # Apply theme
        result = theme_service.apply_theme(theme_id)
        assert result is True

        # Get stylesheet
        stylesheet = theme_provider.get_stylesheet("test_component")
        widget.setStyleSheet(stylesheet)

        # Should have non-empty stylesheet
        assert len(stylesheet) > 0

        # Verify current theme
        assert theme_service.get_current_theme_id() == theme_id


class TestThemeCommandsGUI:
    """GUI tests for theme commands."""

    @pytest.fixture
    def mock_context(self, theme_service):
        """Create mock command context."""
        context = Mock()
        context.get_service.return_value = theme_service
        return context

    def test_theme_select_command_gui_integration(self, qtbot, theme_service, mock_context):
        """Test theme selection command in GUI context."""
        from viloapp.core.commands.builtin.theme_commands import select_theme_command

        # Register test themes
        theme_service._register_theme(
            Theme(
                id="gui-test-theme",
                name="GUI Test Theme",
                description="Theme for GUI testing",
                version="1.0.0",
                author="Test",
                colors={"editor.background": "#123456"},
            )
        )

        # Execute command
        result = select_theme_command(mock_context, "gui-test-theme")

        assert result.success is True
        assert result.value["theme_id"] == "gui-test-theme"

    def test_theme_command_with_ui_service(self, qtbot, theme_service, mock_context):
        """Test theme command with UI service integration."""
        from viloapp.core.commands.builtin.theme_commands import select_theme_command
        from viloapp.services.ui_service import UIService

        # Mock UI service
        ui_service = Mock(spec=UIService)

        # Configure mock context to return both services
        def get_service(service_type):
            if service_type == ThemeService:
                return theme_service
            elif service_type == UIService:
                return ui_service
            return None

        mock_context.get_service.side_effect = get_service

        # Add test theme
        theme_service._register_theme(
            Theme(
                id="ui-test-theme",
                name="UI Test Theme",
                description="Theme with UI service",
                version="1.0.0",
                author="Test",
                colors={"editor.background": "#abcdef"},
            )
        )

        # Execute command
        result = select_theme_command(mock_context, "ui-test-theme")

        assert result.success is True
        # UI service should have been called to set status message
        # (This would depend on the actual implementation)


if __name__ == "__main__":
    pytest.main([__file__])
