"""Integration tests for state persistence across application restarts."""

from unittest.mock import Mock, patch

import pytest

from viloapp.ui.main_window import MainWindow


@pytest.mark.integration
class TestStatePersistence:
    """Test cases for application state persistence."""

    @patch("viloapp.ui.main_window.QSettings")
    def test_window_geometry_persistence(self, mock_settings_class, qtbot):
        """Test window geometry is saved and restored."""
        mock_settings = Mock()
        mock_settings_class.return_value = mock_settings

        # Test saving geometry
        main_window = MainWindow()
        qtbot.addWidget(main_window)

        # Mock geometry data
        mock_geometry = b"mock_geometry_data"
        main_window.saveGeometry = Mock(return_value=mock_geometry)

        # Save state
        main_window.save_state()

        # Verify geometry was saved
        mock_settings.setValue.assert_any_call("geometry", mock_geometry)

        # Test restoring geometry
        mock_settings.value.side_effect = lambda key, default=None, type=None: {
            "geometry": mock_geometry
        }.get(key, default)

        main_window.restoreGeometry = Mock()
        main_window.restore_state()

        # Verify geometry was restored
        main_window.restoreGeometry.assert_called_once_with(mock_geometry)

    @patch("viloapp.ui.main_window.QSettings")
    def test_window_state_persistence(self, mock_settings_class, qtbot):
        """Test window state is saved and restored."""
        mock_settings = Mock()
        mock_settings_class.return_value = mock_settings

        main_window = MainWindow()
        qtbot.addWidget(main_window)

        # Mock window state data
        mock_state = b"mock_window_state"
        main_window.saveState = Mock(return_value=mock_state)

        # Save state
        main_window.save_state()

        # Verify window state was saved
        mock_settings.setValue.assert_any_call("windowState", mock_state)

        # Test restoring state
        mock_settings.value.side_effect = lambda key, default=None, type=None: {
            "windowState": mock_state
        }.get(key, default)

        main_window.restoreState = Mock()
        main_window.restore_state()

        # Verify window state was restored
        main_window.restoreState.assert_called_once_with(mock_state)

    @patch("viloapp.ui.main_window.QSettings")
    def test_splitter_state_persistence(self, mock_settings_class, qtbot):
        """Test splitter state is saved and restored."""
        mock_settings = Mock()
        mock_settings_class.return_value = mock_settings

        main_window = MainWindow()
        qtbot.addWidget(main_window)

        # Mock splitter state data
        mock_splitter_state = b"mock_splitter_state"
        main_window.main_splitter.saveState = Mock(return_value=mock_splitter_state)

        # Save state
        main_window.save_state()

        # Verify splitter state was saved
        mock_settings.setValue.assert_any_call("splitterSizes", mock_splitter_state)

        # Test restoring splitter state
        mock_settings.value.side_effect = lambda key, default=None, type=None: {
            "splitterSizes": mock_splitter_state
        }.get(key, default)

        main_window.main_splitter.restoreState = Mock()
        main_window.restore_state()

        # Verify splitter state was restored
        main_window.main_splitter.restoreState.assert_called_once_with(mock_splitter_state)

    @patch("viloapp.ui.main_window.QSettings")
    def test_menu_bar_visibility_persistence(self, mock_settings_class, qtbot):
        """Test menu bar visibility is saved and restored."""
        mock_settings = Mock()
        mock_settings_class.return_value = mock_settings

        main_window = MainWindow()
        qtbot.addWidget(main_window)

        # Test saving menu bar visibility
        main_window.menuBar().isVisible = Mock(return_value=False)
        main_window.save_state()

        # Verify menu bar visibility was saved
        mock_settings.setValue.assert_any_call("menuBarVisible", False)

        # Test restoring menu bar visibility
        mock_settings.value.side_effect = lambda key, default=None, type=None: {
            "menuBarVisible": False
        }.get(key, default if type is None else type(default))

        main_window.menuBar().setVisible = Mock()
        main_window.restore_state()

        # Verify menu bar visibility was restored
        main_window.menuBar().setVisible.assert_called_once_with(False)

    @patch("viloapp.ui.main_window.QSettings")
    def test_settings_group_usage(self, mock_settings_class, qtbot):
        """Test settings are properly grouped under MainWindow."""
        mock_settings = Mock()
        mock_settings_class.return_value = mock_settings

        main_window = MainWindow()
        qtbot.addWidget(main_window)

        # Test save state
        main_window.save_state()

        # Verify beginGroup and endGroup called
        mock_settings.beginGroup.assert_called_with("MainWindow")
        mock_settings.endGroup.assert_called()

        # Test restore state
        main_window.restore_state()

        # Verify beginGroup and endGroup called again
        assert mock_settings.beginGroup.call_count == 2
        assert mock_settings.endGroup.call_count == 2

    @patch("viloapp.ui.main_window.QSettings")
    def test_restore_with_no_saved_data(self, mock_settings_class, qtbot):
        """Test restore works correctly with no saved data."""
        mock_settings = Mock()
        mock_settings_class.return_value = mock_settings

        # Mock settings to return None for all values
        mock_settings.value.return_value = None

        main_window = MainWindow()
        qtbot.addWidget(main_window)

        # Mock restore methods
        main_window.restoreGeometry = Mock()
        main_window.restoreState = Mock()
        main_window.main_splitter.restoreState = Mock()

        # Restore state
        main_window.restore_state()

        # Verify no restoration methods called
        main_window.restoreGeometry.assert_not_called()
        main_window.restoreState.assert_not_called()
        main_window.main_splitter.restoreState.assert_not_called()

    @patch("viloapp.ui.main_window.QSettings")
    def test_close_event_saves_state(self, mock_settings_class, qtbot):
        """Test close event automatically saves state."""
        mock_settings = Mock()
        mock_settings_class.return_value = mock_settings

        main_window = MainWindow()
        qtbot.addWidget(main_window)

        # Mock save methods
        main_window.saveGeometry = Mock(return_value=b"geometry")
        main_window.saveState = Mock(return_value=b"state")
        main_window.main_splitter.saveState = Mock(return_value=b"splitter")
        main_window.menuBar().isVisible = Mock(return_value=True)

        # Create mock close event
        close_event = Mock()
        close_event.accept = Mock()

        # Trigger close event
        main_window.closeEvent(close_event)

        # Verify state was saved
        assert mock_settings.beginGroup.called
        assert mock_settings.setValue.call_count >= 4
        assert mock_settings.endGroup.called
        assert close_event.accept.called

    @patch("viloapp.ui.main_window.QSettings")
    def test_multiple_save_restore_cycles(self, mock_settings_class, qtbot):
        """Test multiple save/restore cycles work correctly."""
        mock_settings = Mock()
        mock_settings_class.return_value = mock_settings

        main_window = MainWindow()
        qtbot.addWidget(main_window)

        # Mock data for multiple cycles
        geometries = [b"geo1", b"geo2", b"geo3"]
        states = [b"state1", b"state2", b"state3"]

        for i, (geo, state) in enumerate(zip(geometries, states)):
            # Mock save methods
            main_window.saveGeometry = Mock(return_value=geo)
            main_window.saveState = Mock(return_value=state)

            # Save state
            main_window.save_state()

            # Mock restore methods for next iteration
            mock_settings.value.side_effect = lambda key, default=None, type=None: {
                "geometry": geo,
                "windowState": state,
            }.get(key, default)

            main_window.restoreGeometry = Mock()
            main_window.restoreState = Mock()

            # Restore state
            main_window.restore_state()

            # Verify correct data used
            if i < len(geometries) - 1:  # Don't check on last iteration
                main_window.restoreGeometry.assert_called_with(geo)
                main_window.restoreState.assert_called_with(state)

    @patch("viloapp.ui.main_window.QSettings")
    def test_theme_persistence_integration(self, mock_settings_class, qtbot):
        """Test theme state integrates with other persistence."""
        mock_settings = Mock()
        mock_settings_class.return_value = mock_settings

        main_window = MainWindow()
        qtbot.addWidget(main_window)

        # Mock theme manager
        with patch("viloapp.ui.main_window.get_icon_manager") as mock_get_manager:
            mock_manager = Mock()
            mock_manager.theme = "dark"
            mock_get_manager.return_value = mock_manager

            # Note: Theme persistence would need to be implemented in IconManager
            # This test verifies the integration points exist

            # Toggle theme
            main_window.toggle_theme()

            # Verify theme manager was called
            mock_manager.toggle_theme.assert_called_once()

    @patch("viloapp.ui.main_window.QSettings")
    def test_settings_error_handling(self, mock_settings_class, qtbot):
        """Test error handling in settings operations."""
        # Mock settings that raises exception
        mock_settings = Mock()
        mock_settings.setValue.side_effect = Exception("Settings error")
        mock_settings_class.return_value = mock_settings

        main_window = MainWindow()
        qtbot.addWidget(main_window)

        # Mock save methods
        main_window.saveGeometry = Mock(return_value=b"geometry")
        main_window.saveState = Mock(return_value=b"state")

        # Save state should not crash even if settings fail
        try:
            main_window.save_state()
            # If we get here, the error was handled gracefully
        except Exception:
            pytest.fail("save_state should handle settings errors gracefully")
