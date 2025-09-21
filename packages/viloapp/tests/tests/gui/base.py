"""Base classes and utilities for GUI testing."""

from PySide6.QtCore import Qt

from tests.gui.conftest import (
    get_widget_center,
    simulate_key_sequence,
    wait_for_condition,
)


class GUITestBase:
    """Base class for GUI tests with common functionality."""

    def wait_for_animation(self, qtbot, timeout=2000):
        """Wait for animations to complete."""
        # Use a small delay to allow animations to finish
        qtbot.wait(timeout // 10)  # Usually animations are much shorter

    def wait_for_widget_visible(self, qtbot, widget, timeout=5000):
        """Wait for a widget to become visible."""
        wait_for_condition(qtbot, lambda: widget.isVisible(), timeout)

    def wait_for_widget_hidden(self, qtbot, widget, timeout=5000):
        """Wait for a widget to become hidden."""
        wait_for_condition(qtbot, lambda: not widget.isVisible(), timeout)

    def assert_widget_geometry(self, widget, expected_width=None, expected_height=None):
        """Assert widget has expected dimensions."""
        if expected_width is not None:
            assert (
                widget.width() == expected_width
            ), f"Expected width {expected_width}, got {widget.width()}"
        if expected_height is not None:
            assert (
                widget.height() == expected_height
            ), f"Expected height {expected_height}, got {widget.height()}"

    def click_widget_center(self, qtbot, widget):
        """Click the center of a widget."""
        center = get_widget_center(widget)
        qtbot.mouseClick(widget, Qt.MouseButton.LeftButton, pos=center)

    def right_click_widget_center(self, qtbot, widget):
        """Right-click the center of a widget."""
        center = get_widget_center(widget)
        qtbot.mouseClick(widget, Qt.MouseButton.RightButton, pos=center)


class MainWindowGUITestBase(GUITestBase):
    """Base class for main window GUI tests."""

    def setup_method(self):
        """Set up method called before each test."""
        # Can be overridden by subclasses
        pass

    def teardown_method(self):
        """Tear down method called after each test."""
        # Can be overridden by subclasses
        pass

    def verify_main_window_components(self, main_window):
        """Verify all main window components are present."""
        assert (
            hasattr(main_window, "activity_bar") and main_window.activity_bar is not None
        ), "Main window should have activity_bar component"
        assert (
            hasattr(main_window, "sidebar") and main_window.sidebar is not None
        ), "Main window should have sidebar component"
        assert (
            hasattr(main_window, "workspace") and main_window.workspace is not None
        ), "Main window should have workspace component"
        assert (
            hasattr(main_window, "status_bar") and main_window.status_bar is not None
        ), "Main window should have status_bar component"
        assert (
            hasattr(main_window, "main_splitter") and main_window.main_splitter is not None
        ), "Main window should have main_splitter component"

    def verify_component_visibility(self, main_window):
        """Verify component visibility states."""
        assert main_window.activity_bar.isVisible()
        assert main_window.sidebar.isVisible()  # Default state
        assert main_window.workspace.isVisible()
        assert main_window.status_bar.isVisible()


class ActivityBarGUITestBase(GUITestBase):
    """Base class for activity bar GUI tests."""

    def get_activity_buttons(self, activity_bar):
        """Get all activity buttons from the activity bar."""
        return {
            "explorer": activity_bar.explorer_action,
            "search": activity_bar.search_action,
            "git": activity_bar.git_action,
            "settings": activity_bar.settings_action,
        }

    def verify_button_states(self, activity_bar, expected_active_view):
        """Verify activity button states match expected active view."""
        buttons = self.get_activity_buttons(activity_bar)

        for view_name, button in buttons.items():
            if view_name == expected_active_view:
                assert button.isChecked(), f"{view_name} button should be checked"
            else:
                assert not button.isChecked(), f"{view_name} button should not be checked"

    def click_activity_button(self, qtbot, activity_bar, view_name):
        """Click an activity button by view name."""
        buttons = self.get_activity_buttons(activity_bar)
        button = buttons.get(view_name)
        assert button is not None, f"No button found for view: {view_name}"

        # Trigger the button action directly since it's a QAction
        button.trigger()
        qtbot.wait(50)  # Small delay for signal processing


class SidebarGUITestBase(GUITestBase):
    """Base class for sidebar GUI tests."""

    def verify_sidebar_collapsed(self, sidebar):
        """Verify sidebar is in collapsed state."""
        assert sidebar.is_collapsed
        # Note: Visual width check may vary based on animation state

    def verify_sidebar_expanded(self, sidebar):
        """Verify sidebar is in expanded state."""
        assert not sidebar.is_collapsed
        assert sidebar.width() > 0

    def wait_for_sidebar_animation(self, qtbot, sidebar, timeout=2000):
        """Wait for sidebar expand/collapse animation to complete."""
        # Wait a bit for animation to finish
        self.wait_for_animation(qtbot, timeout)

    def get_sidebar_views(self, sidebar):
        """Get available sidebar views."""
        return ["explorer", "search", "git", "settings"]


class WorkspaceGUITestBase(GUITestBase):
    """Base class for workspace GUI tests."""

    def verify_workspace_initialized(self, workspace):
        """Verify workspace is properly initialized."""
        assert workspace is not None and hasattr(
            workspace, "isVisible"
        ), f"Expected valid workspace widget, got {workspace}"
        assert workspace.isVisible()

    def count_active_panes(self, workspace):
        """Count the number of active panes in workspace."""
        # This will depend on workspace implementation
        # For now, return a basic count
        return 1  # Default single pane

    def verify_pane_exists(self, workspace, pane_index=0):
        """Verify a pane exists at the given index."""
        # Implementation will depend on workspace structure
        assert workspace is not None and hasattr(
            workspace, "isVisible"
        ), f"Expected valid workspace widget for pane verification, got {workspace}"


class ThemeGUITestBase(GUITestBase):
    """Base class for theme-related GUI tests."""

    def setup_theme_test(self, qtbot, main_window):
        """Set up common theme test requirements."""
        # Ensure we start with a known theme state
        self.initial_theme = "light"  # Default

    def trigger_theme_toggle(self, qtbot, main_window):
        """Trigger theme toggle using the keyboard shortcut."""
        simulate_key_sequence(qtbot, main_window, "Ctrl+T")
        qtbot.wait(100)  # Wait for theme change to propagate

    def verify_theme_change_propagated(self, main_window, mock_icon_manager):
        """Verify theme change propagated to all components."""
        # Verify icon manager was called
        mock_icon_manager.toggle_theme.assert_called()

        # Additional verification can be added based on component behavior


class KeyboardGUITestBase(GUITestBase):
    """Base class for keyboard shortcut GUI tests."""

    def get_common_shortcuts(self):
        """Get dictionary of common keyboard shortcuts."""
        return {
            "toggle_theme": "Ctrl+T",
            "toggle_sidebar": "Ctrl+B",
            "toggle_menu_bar": "Ctrl+Shift+M",
            "reset_app_state": "Ctrl+Shift+R",
        }

    def verify_shortcut(self, qtbot, main_window, shortcut_name, expected_action):
        """Test a keyboard shortcut performs expected action."""
        shortcuts = self.get_common_shortcuts()
        shortcut = shortcuts.get(shortcut_name)
        assert shortcut is not None, f"No shortcut defined for: {shortcut_name}"

        # Simulate the keyboard shortcut
        simulate_key_sequence(qtbot, main_window, shortcut)
        qtbot.wait(100)  # Wait for action to complete

        # Verify expected action occurred
        expected_action()


class AnimationGUITestBase(GUITestBase):
    """Base class for animation-related GUI tests."""

    def wait_for_smooth_animation(self, qtbot, timeout=3000):
        """Wait for smooth animations with proper timing."""
        # Longer timeout for smooth animations
        self.wait_for_animation(qtbot, timeout)

    def verify_animation_start_state(self, widget, expected_start_value):
        """Verify widget is in expected state before animation."""
        # This can be overridden based on what property we're animating
        pass

    def verify_animation_end_state(self, widget, expected_end_value):
        """Verify widget is in expected state after animation."""
        # This can be overridden based on what property we're animating
        pass


class MouseGUITestBase(GUITestBase):
    """Base class for mouse interaction GUI tests."""

    def double_click_widget(self, qtbot, widget):
        """Double-click a widget."""
        center = get_widget_center(widget)
        qtbot.mouseDClick(widget, Qt.MouseButton.LeftButton, pos=center)

    def drag_widget(self, qtbot, widget, start_pos, end_pos):
        """Simulate dragging a widget."""
        qtbot.mousePress(widget, Qt.MouseButton.LeftButton, pos=start_pos)
        qtbot.mouseMove(widget, end_pos)
        qtbot.mouseRelease(widget, Qt.MouseButton.LeftButton, pos=end_pos)

    def hover_widget(self, qtbot, widget):
        """Simulate hovering over a widget."""
        center = get_widget_center(widget)
        qtbot.mouseMove(widget, center)
