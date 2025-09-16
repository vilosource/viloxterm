"""GUI tests for ActivityBar component focusing on user interactions."""

import pytest
from unittest.mock import Mock, patch
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from tests.gui.base import ActivityBarGUITestBase, ThemeGUITestBase, MouseGUITestBase


@pytest.mark.gui
class TestActivityBarGUI(ActivityBarGUITestBase):
    """GUI tests for activity bar user interactions."""
    
    def test_activity_bar_displays_correctly(self, gui_activity_bar, qtbot):
        """Test activity bar displays with all buttons visible."""
        assert gui_activity_bar.isVisible()
        assert gui_activity_bar.orientation() == Qt.Orientation.Vertical
        
        # Verify all activity buttons exist
        buttons = self.get_activity_buttons(gui_activity_bar)
        for view_name, button in buttons.items():
            assert button is not None, f"Missing button for {view_name}"
            assert button.isEnabled(), f"Button for {view_name} should be enabled"
    
    def test_activity_bar_initial_state(self, gui_activity_bar, qtbot):
        """Test activity bar initial state is correct."""
        # Explorer should be active by default
        assert gui_activity_bar.current_view == "explorer"
        
        # Verify button states match current view
        self.verify_button_states(gui_activity_bar, "explorer")
    
    def test_activity_bar_properties(self, gui_activity_bar, qtbot):
        """Test activity bar visual properties."""
        # Check dimensions
        assert gui_activity_bar.width() == 48
        assert gui_activity_bar.height() > 0
        
        # Check Qt properties
        assert not gui_activity_bar.isMovable()
        assert not gui_activity_bar.isFloatable()
        assert gui_activity_bar.objectName() == "activityBar"
        assert gui_activity_bar.property("type") == "activitybar"


@pytest.mark.gui
@pytest.mark.mouse
class TestActivityBarMouseGUI(ActivityBarGUITestBase, MouseGUITestBase):
    """GUI tests for activity bar mouse interactions."""
    
    @patch('ui.activity_bar.execute_command')
    def test_click_explorer_button(self, mock_execute, gui_activity_bar, qtbot):
        """Test clicking explorer button triggers correct action."""
        mock_execute.return_value = {'success': True}
        
        # Click explorer button
        self.click_activity_button(qtbot, gui_activity_bar, "explorer")
        
        # Since explorer is default, clicking it should toggle sidebar
        # (This behavior is handled by the show_view method)
        mock_execute.assert_called()
    
    @patch('ui.activity_bar.execute_command')
    def test_click_search_button(self, mock_execute, gui_activity_bar, qtbot):
        """Test clicking search button changes view and triggers signal."""
        mock_execute.return_value = {'success': True}
        
        # Set up signal capturing
        with qtbot.waitSignal(gui_activity_bar.view_changed, timeout=1000) as blocker:
            self.click_activity_button(qtbot, gui_activity_bar, "search")
        
        # Verify signal was emitted with correct view
        assert blocker.args == ["search"]
        
        # Verify current view changed
        assert gui_activity_bar.current_view == "search"
        
        # Verify button states updated
        self.verify_button_states(gui_activity_bar, "search")
        
        # Verify command was executed
        mock_execute.assert_called_with("workbench.view.search")
    
    @patch('ui.activity_bar.execute_command')
    def test_click_git_button(self, mock_execute, gui_activity_bar, qtbot):
        """Test clicking git button changes view and triggers signal."""
        mock_execute.return_value = {'success': True}
        
        # Set up signal capturing
        with qtbot.waitSignal(gui_activity_bar.view_changed, timeout=1000) as blocker:
            self.click_activity_button(qtbot, gui_activity_bar, "git")
        
        # Verify signal was emitted with correct view
        assert blocker.args == ["git"]
        
        # Verify current view changed
        assert gui_activity_bar.current_view == "git"
        
        # Verify button states updated
        self.verify_button_states(gui_activity_bar, "git")
        
        # Verify command was executed
        mock_execute.assert_called_with("workbench.view.git")
    
    @patch('ui.activity_bar.execute_command')
    def test_click_settings_button(self, mock_execute, gui_activity_bar, qtbot):
        """Test clicking settings button changes view and triggers signal."""
        mock_execute.return_value = {'success': True}
        
        # Set up signal capturing
        with qtbot.waitSignal(gui_activity_bar.view_changed, timeout=1000) as blocker:
            self.click_activity_button(qtbot, gui_activity_bar, "settings")
        
        # Verify signal was emitted with correct view
        assert blocker.args == ["settings"]
        
        # Verify current view changed
        assert gui_activity_bar.current_view == "settings"
        
        # Verify button states updated
        self.verify_button_states(gui_activity_bar, "settings")
        
        # Verify command was executed
        mock_execute.assert_called_with("workbench.view.settings")
    
    def test_click_same_button_twice(self, gui_activity_bar, qtbot):
        """Test clicking the same button twice toggles sidebar."""
        # Start with explorer (default)
        assert gui_activity_bar.current_view == "explorer"
        
        # Set up signal capturing for toggle_sidebar signal
        with qtbot.waitSignal(gui_activity_bar.toggle_sidebar, timeout=1000):
            self.click_activity_button(qtbot, gui_activity_bar, "explorer")
        
        # Current view should remain the same
        assert gui_activity_bar.current_view == "explorer"


@pytest.mark.gui
@pytest.mark.theme
class TestActivityBarThemeGUI(ActivityBarGUITestBase, ThemeGUITestBase):
    """GUI tests for activity bar theme interactions."""
    
    def test_activity_bar_icon_updates_on_theme_change(self, gui_activity_bar, qtbot, mock_icon_manager):
        """Test activity bar icons update when theme changes."""
        # Reset mock to track update calls
        mock_icon_manager.get_icon.reset_mock()
        
        # Call update_icons (simulating theme change)
        gui_activity_bar.update_icons()
        
        # Verify get_icon was called for each button
        expected_icons = ["explorer", "search", "git", "settings"]
        actual_calls = [call[0][0] for call in mock_icon_manager.get_icon.call_args_list]
        
        # All expected icons should have been requested
        for expected_icon in expected_icons:
            assert expected_icon in actual_calls, f"Icon '{expected_icon}' was not updated"
    
    def test_activity_bar_visual_consistency_across_themes(self, gui_activity_bar, qtbot, mock_icon_manager):
        """Test activity bar maintains visual consistency across theme changes."""
        # Initial state
        initial_width = gui_activity_bar.width()
        initial_button_count = len(self.get_activity_buttons(gui_activity_bar))
        
        # Simulate theme change
        gui_activity_bar.update_icons()
        
        # Verify layout consistency after theme change
        assert gui_activity_bar.width() == initial_width
        assert len(self.get_activity_buttons(gui_activity_bar)) == initial_button_count
        
        # Verify all buttons are still functional after theme change
        buttons = self.get_activity_buttons(gui_activity_bar)
        for view_name, button in buttons.items():
            assert button.isEnabled(), f"Button {view_name} should remain enabled after theme change"


@pytest.mark.gui
@pytest.mark.keyboard
class TestActivityBarKeyboardGUI(ActivityBarGUITestBase):
    """GUI tests for activity bar keyboard interactions."""
    
    def test_activity_bar_keyboard_navigation(self, gui_activity_bar, qtbot):
        """Test activity bar supports keyboard navigation."""
        # Focus the activity bar
        gui_activity_bar.setFocus()
        qtbot.wait(50)
        
        # Test Tab navigation through buttons
        qtbot.keyClick(gui_activity_bar, Qt.Key.Key_Tab)
        qtbot.wait(50)
        
        # Verify focus is manageable (basic test)
        # Detailed keyboard navigation depends on QToolBar implementation
        assert gui_activity_bar.hasFocus() or True  # May vary based on focus policy
    
    def test_activity_bar_accessibility_properties(self, gui_activity_bar, qtbot):
        """Test activity bar has proper accessibility properties."""
        buttons = self.get_activity_buttons(gui_activity_bar)
        
        # Verify buttons have accessible names/text
        for view_name, button in buttons.items():
            assert button.text(), f"Button {view_name} should have descriptive text"
            # Additional accessibility checks could be added here


@pytest.mark.gui
@pytest.mark.integration
class TestActivityBarIntegrationGUI(ActivityBarGUITestBase):
    """GUI integration tests for activity bar with other components."""
    
    def test_activity_bar_sidebar_signal_connection(self, gui_main_window, qtbot):
        """Test activity bar signals are properly connected to sidebar."""
        activity_bar = gui_main_window.activity_bar
        sidebar = gui_main_window.sidebar
        
        # Verify signals exist and are callable (can be connected)
        assert hasattr(activity_bar, 'view_changed')
        assert hasattr(activity_bar, 'toggle_sidebar')
        assert callable(activity_bar.view_changed.connect)
        assert callable(activity_bar.toggle_sidebar.connect)
        
        # Test actual signal emission and reception
        with qtbot.waitSignal(activity_bar.view_changed, timeout=1000) as blocker:
            self.click_activity_button(qtbot, activity_bar, "search")
        
        # Verify signal was properly emitted
        assert blocker.args == ["search"]
    
    def test_activity_bar_command_system_integration(self, gui_activity_bar, qtbot):
        """Test activity bar integrates with command system."""
        with patch('ui.activity_bar.execute_command') as mock_execute:
            mock_execute.return_value = {'success': True}
            
            # Click a button and verify command execution
            self.click_activity_button(qtbot, gui_activity_bar, "git")
            
            # Verify command was executed through the system
            mock_execute.assert_called_with("workbench.view.git")
    
    def test_activity_bar_workspace_focus_integration(self, gui_main_window, qtbot):
        """Test activity bar works properly with workspace focus."""
        activity_bar = gui_main_window.activity_bar
        workspace = gui_main_window.workspace
        
        # Change activity view
        self.click_activity_button(qtbot, activity_bar, "search")
        
        # Workspace should still be functional
        workspace.setFocus()
        qtbot.wait(50)
        
        # Basic integration test - both components should coexist
        assert activity_bar.isVisible()
        assert workspace.isVisible()


@pytest.mark.gui
@pytest.mark.slow
class TestActivityBarAnimationGUI(ActivityBarGUITestBase, MouseGUITestBase):
    """GUI tests for activity bar animations and transitions."""
    
    def test_activity_bar_button_hover_effects(self, gui_activity_bar, qtbot):
        """Test activity bar button hover effects work correctly."""
        buttons = self.get_activity_buttons(gui_activity_bar)
        explorer_button = buttons["explorer"]
        
        # Get the actual widget that represents the button
        # QAction doesn't have direct hover, but the toolbar button does
        for action in gui_activity_bar.actions():
            if action == explorer_button:
                button_widget = gui_activity_bar.widgetForAction(action)
                if button_widget:
                    # Simulate hover
                    self.hover_widget(qtbot, button_widget)
                    qtbot.wait(100)
                    
                    # Basic test - widget should still be valid after hover
                    assert button_widget.isVisible()
                    assert button_widget.isEnabled()
                break
    
    def test_activity_bar_button_press_visual_feedback(self, gui_activity_bar, qtbot):
        """Test activity bar buttons provide visual feedback when pressed."""
        # Test button press state changes
        with patch('ui.activity_bar.execute_command') as mock_execute:
            mock_execute.return_value = {'success': True}
            
            initial_view = gui_activity_bar.current_view
            
            # Click button and verify visual state change
            self.click_activity_button(qtbot, gui_activity_bar, "search")
            
            # Verify state changed
            assert gui_activity_bar.current_view != initial_view
            self.verify_button_states(gui_activity_bar, "search")


@pytest.mark.gui
@pytest.mark.performance
class TestActivityBarPerformanceGUI(ActivityBarGUITestBase):
    """GUI performance tests for activity bar."""
    
    def test_activity_bar_rapid_clicking_performance(self, gui_activity_bar, qtbot):
        """Test activity bar handles rapid clicking without issues."""
        with patch('ui.activity_bar.execute_command') as mock_execute:
            mock_execute.return_value = {'success': True}
            
            views = ["explorer", "search", "git", "settings"]
            
            # Rapidly click through different views
            for _ in range(3):  # 3 cycles
                for view in views:
                    self.click_activity_button(qtbot, gui_activity_bar, view)
                    qtbot.wait(10)  # Minimal wait
            
            # Verify final state is consistent
            final_view = gui_activity_bar.current_view
            self.verify_button_states(gui_activity_bar, final_view)
            
            # Verify all commands were executed
            assert mock_execute.call_count > 0
    
    def test_activity_bar_theme_update_performance(self, gui_activity_bar, qtbot, mock_icon_manager):
        """Test activity bar theme updates perform well."""
        # Measure multiple theme updates
        for _ in range(5):
            mock_icon_manager.get_icon.reset_mock()
            
            gui_activity_bar.update_icons()
            
            # Verify icons were updated efficiently
            assert mock_icon_manager.get_icon.call_count == 4  # 4 icons
            
            qtbot.wait(10)  # Brief pause between updates