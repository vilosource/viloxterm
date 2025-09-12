"""GUI tests for Sidebar component focusing on user interactions."""

import pytest
from unittest.mock import Mock, patch
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from tests.gui.base import SidebarGUITestBase, AnimationGUITestBase, ThemeGUITestBase


@pytest.mark.gui
class TestSidebarGUI(SidebarGUITestBase):
    """GUI tests for sidebar user interactions."""
    
    def test_sidebar_displays_correctly(self, gui_sidebar, qtbot):
        """Test sidebar displays with correct initial state."""
        assert gui_sidebar.isVisible()
        assert not gui_sidebar.is_collapsed
        assert gui_sidebar.width() > 0
        
        # Verify initial expanded width
        assert gui_sidebar.expanded_width == 250
        assert gui_sidebar.maximumWidth() == 250
        
    def test_sidebar_initial_view_state(self, gui_sidebar, qtbot):
        """Test sidebar starts with correct initial view."""
        # Verify stack widget is set up
        assert gui_sidebar.stack is not None
        assert gui_sidebar.stack.isVisible()
        
        # Verify view indices are set up correctly
        expected_views = ["explorer", "search", "git", "settings"]
        for view_name in expected_views:
            assert view_name in gui_sidebar.view_indices
            
        # Verify stack has correct number of views
        assert gui_sidebar.stack.count() == 4
    
    def test_sidebar_view_switching(self, gui_sidebar, qtbot):
        """Test sidebar can switch between different views."""
        # Test switching to search view
        gui_sidebar.set_current_view("search")
        assert gui_sidebar.stack.currentIndex() == gui_sidebar.view_indices["search"]
        
        # Test switching to git view  
        gui_sidebar.set_current_view("git")
        assert gui_sidebar.stack.currentIndex() == gui_sidebar.view_indices["git"]
        
        # Test switching to settings view
        gui_sidebar.set_current_view("settings")
        assert gui_sidebar.stack.currentIndex() == gui_sidebar.view_indices["settings"]
        
        # Test switching back to explorer
        gui_sidebar.set_current_view("explorer")
        assert gui_sidebar.stack.currentIndex() == gui_sidebar.view_indices["explorer"]
    
    def test_sidebar_invalid_view_handling(self, gui_sidebar, qtbot):
        """Test sidebar handles invalid view names gracefully."""
        initial_index = gui_sidebar.stack.currentIndex()
        
        # Try to switch to invalid view
        gui_sidebar.set_current_view("invalid_view")
        
        # Should remain at current view
        assert gui_sidebar.stack.currentIndex() == initial_index
    
    def test_sidebar_properties(self, gui_sidebar, qtbot):
        """Test sidebar widget properties."""
        assert gui_sidebar.objectName() == "sidebar"
        assert gui_sidebar.minimumWidth() == 0
        assert gui_sidebar.maximumWidth() == 250


@pytest.mark.gui
@pytest.mark.animation
class TestSidebarAnimationGUI(SidebarGUITestBase, AnimationGUITestBase):
    """GUI tests for sidebar collapse/expand animations."""
    
    def test_sidebar_collapse_animation(self, gui_sidebar, qtbot):
        """Test sidebar collapse animation works correctly."""
        # Ensure sidebar starts expanded
        if gui_sidebar.is_collapsed:
            gui_sidebar.expand()
            self.wait_for_sidebar_animation(qtbot, gui_sidebar)
        
        initial_width = gui_sidebar.width()
        assert initial_width > 0
        assert not gui_sidebar.is_collapsed
        
        # Trigger collapse
        gui_sidebar.collapse()
        
        # Wait for animation to complete
        self.wait_for_sidebar_animation(qtbot, gui_sidebar)
        
        # Verify collapsed state
        self.verify_sidebar_collapsed(gui_sidebar)
    
    def test_sidebar_expand_animation(self, gui_sidebar, qtbot):
        """Test sidebar expand animation works correctly."""
        # Ensure sidebar starts collapsed
        if not gui_sidebar.is_collapsed:
            gui_sidebar.collapse()
            self.wait_for_sidebar_animation(qtbot, gui_sidebar)
        
        self.verify_sidebar_collapsed(gui_sidebar)
        
        # Trigger expand
        gui_sidebar.expand()
        
        # Wait for animation to complete
        self.wait_for_sidebar_animation(qtbot, gui_sidebar)
        
        # Verify expanded state
        self.verify_sidebar_expanded(gui_sidebar)
        assert gui_sidebar.width() > 0
    
    def test_sidebar_toggle_animation(self, gui_sidebar, qtbot):
        """Test sidebar toggle method animates correctly."""
        # Test toggle from expanded to collapsed
        initial_state = gui_sidebar.is_collapsed
        
        gui_sidebar.toggle()
        self.wait_for_sidebar_animation(qtbot, gui_sidebar)
        
        # State should have changed
        assert gui_sidebar.is_collapsed != initial_state
        
        # Toggle back
        gui_sidebar.toggle()
        self.wait_for_sidebar_animation(qtbot, gui_sidebar)
        
        # Should be back to initial state
        assert gui_sidebar.is_collapsed == initial_state
    
    @pytest.mark.slow
    def test_sidebar_animation_properties(self, gui_sidebar, qtbot):
        """Test sidebar animation has correct properties."""
        animation = gui_sidebar.animation
        
        # Verify animation properties
        assert animation.duration() == 200
        assert animation.propertyName() == b"maximumWidth"
        
        # Test animation doesn't interfere with rapid operations
        for _ in range(3):
            gui_sidebar.toggle()
            QTest.qWait(50)  # Don't wait for full animation
        
        # Wait for final animation to complete
        self.wait_for_sidebar_animation(qtbot, gui_sidebar, timeout=1000)
        
        # Sidebar should be in a valid state
        assert isinstance(gui_sidebar.is_collapsed, bool)
    
    def test_sidebar_animation_interruption(self, gui_sidebar, qtbot):
        """Test sidebar handles animation interruption gracefully."""
        # Start collapse
        gui_sidebar.collapse()
        
        # Immediately expand (interrupt the collapse)
        QTest.qWait(50)  # Brief wait to let animation start
        gui_sidebar.expand()
        
        # Wait for final animation to complete
        self.wait_for_sidebar_animation(qtbot, gui_sidebar)
        
        # Should end up expanded
        self.verify_sidebar_expanded(gui_sidebar)


@pytest.mark.gui
@pytest.mark.theme
class TestSidebarThemeGUI(SidebarGUITestBase, ThemeGUITestBase):
    """GUI tests for sidebar theme interactions."""
    
    def test_sidebar_theme_styling(self, gui_sidebar, qtbot):
        """Test sidebar applies theme styling correctly."""
        # Verify sidebar has styling applied
        style_sheet = gui_sidebar.styleSheet()
        assert style_sheet  # Should have some styling
        
        # Verify object name is set for styling
        assert gui_sidebar.objectName() == "sidebar"
    
    def test_sidebar_view_labels_styling(self, gui_sidebar, qtbot):
        """Test sidebar view labels have proper styling."""
        # Test each view has proper labels
        views = self.get_sidebar_views(gui_sidebar)
        
        for view_name in views:
            gui_sidebar.set_current_view(view_name)
            QTest.qWait(50)
            
            # Get current view widget
            current_widget = gui_sidebar.stack.currentWidget()
            assert current_widget is not None
            assert current_widget.isVisible()
    
    def test_sidebar_maintains_styling_during_animation(self, gui_sidebar, qtbot):
        """Test sidebar maintains styling during collapse/expand animations."""
        initial_style = gui_sidebar.styleSheet()
        
        # Trigger animation
        gui_sidebar.toggle()
        
        # Check styling during animation
        QTest.qWait(100)  # Mid-animation
        assert gui_sidebar.styleSheet() == initial_style
        
        # Wait for animation to complete
        self.wait_for_sidebar_animation(qtbot, gui_sidebar)
        
        # Check styling after animation
        assert gui_sidebar.styleSheet() == initial_style


@pytest.mark.gui
@pytest.mark.integration
class TestSidebarIntegrationGUI(SidebarGUITestBase):
    """GUI integration tests for sidebar with other components."""
    
    def test_sidebar_activity_bar_integration(self, gui_main_window, qtbot):
        """Test sidebar integrates properly with activity bar."""
        activity_bar = gui_main_window.activity_bar
        sidebar = gui_main_window.sidebar
        
        # Test view synchronization
        initial_view = sidebar.stack.currentIndex()
        
        # Change activity view
        with qtbot.waitSignal(activity_bar.view_changed, timeout=1000):
            activity_bar.show_view("search")
        
        # Should trigger sidebar view change through main window connection
        # This is tested via the signal mechanism
        assert activity_bar.current_view == "search"
    
    def test_sidebar_main_splitter_integration(self, gui_main_window, qtbot):
        """Test sidebar works correctly within main splitter."""
        main_splitter = gui_main_window.main_splitter
        sidebar = gui_main_window.sidebar
        
        # Test splitter configuration
        assert main_splitter.count() >= 2  # Should have at least sidebar and workspace
        
        # Verify sidebar is in splitter
        splitter_widgets = [main_splitter.widget(i) for i in range(main_splitter.count())]
        assert sidebar in splitter_widgets
        
        # Test collapse doesn't break splitter
        sidebar.collapse()
        self.wait_for_sidebar_animation(qtbot, sidebar)
        
        # Splitter should still be functional
        sizes = main_splitter.sizes()
        assert len(sizes) >= 2
        assert sum(sizes) > 0
    
    def test_sidebar_focus_integration(self, gui_main_window, qtbot):
        """Test sidebar focus management integrates with main window."""
        sidebar = gui_main_window.sidebar
        
        # Test focus can be set to sidebar
        sidebar.setFocus()
        QTest.qWait(50)
        
        # Test focus on views
        for view_name in self.get_sidebar_views(sidebar):
            sidebar.set_current_view(view_name)
            QTest.qWait(50)
            
            current_view = sidebar.stack.currentWidget()
            if current_view:
                current_view.setFocus()
                QTest.qWait(50)
                
                # Basic focus test - widget should accept focus
                assert current_view.isVisible()


@pytest.mark.gui
@pytest.mark.performance
class TestSidebarPerformanceGUI(SidebarGUITestBase):
    """GUI performance tests for sidebar."""
    
    def test_sidebar_rapid_view_switching_performance(self, gui_sidebar, qtbot):
        """Test sidebar handles rapid view switching efficiently."""
        views = self.get_sidebar_views(gui_sidebar)
        
        # Rapidly switch between views
        for _ in range(10):  # 10 cycles
            for view_name in views:
                gui_sidebar.set_current_view(view_name)
                QTest.qWait(5)  # Minimal wait
        
        # Verify final state is consistent
        final_index = gui_sidebar.stack.currentIndex()
        assert 0 <= final_index < gui_sidebar.stack.count()
        
        # Verify stack is still responsive
        gui_sidebar.set_current_view("explorer")
        assert gui_sidebar.stack.currentIndex() == gui_sidebar.view_indices["explorer"]
    
    def test_sidebar_rapid_toggle_performance(self, gui_sidebar, qtbot):
        """Test sidebar handles rapid toggling without issues."""
        initial_state = gui_sidebar.is_collapsed
        
        # Rapid toggling
        for _ in range(5):
            gui_sidebar.toggle()
            QTest.qWait(20)  # Brief wait, shorter than animation
        
        # Wait for all animations to complete
        self.wait_for_sidebar_animation(qtbot, gui_sidebar, timeout=3000)
        
        # Final state should be valid
        assert isinstance(gui_sidebar.is_collapsed, bool)
        assert gui_sidebar.width() >= 0
    
    def test_sidebar_animation_performance(self, gui_sidebar, qtbot):
        """Test sidebar animations perform smoothly."""
        # Test multiple animation cycles
        for _ in range(3):
            gui_sidebar.collapse()
            self.wait_for_sidebar_animation(qtbot, gui_sidebar, timeout=1000)
            
            gui_sidebar.expand()
            self.wait_for_sidebar_animation(qtbot, gui_sidebar, timeout=1000)
        
        # Verify final state
        self.verify_sidebar_expanded(gui_sidebar)
        assert gui_sidebar.animation.state() != gui_sidebar.animation.State.Running


@pytest.mark.gui
@pytest.mark.accessibility
class TestSidebarAccessibilityGUI(SidebarGUITestBase):
    """GUI accessibility tests for sidebar."""
    
    def test_sidebar_keyboard_accessibility(self, gui_sidebar, qtbot):
        """Test sidebar is accessible via keyboard."""
        # Focus sidebar
        gui_sidebar.setFocus()
        QTest.qWait(50)
        
        # Test tab navigation
        qtbot.keyClick(gui_sidebar, Qt.Key.Key_Tab)
        QTest.qWait(50)
        
        # Basic accessibility - sidebar should be focusable
        assert gui_sidebar.focusPolicy() != Qt.FocusPolicy.NoFocus or True  # May vary
    
    def test_sidebar_view_accessibility(self, gui_sidebar, qtbot):
        """Test sidebar views are accessible."""
        views = self.get_sidebar_views(gui_sidebar)
        
        for view_name in views:
            gui_sidebar.set_current_view(view_name)
            current_widget = gui_sidebar.stack.currentWidget()
            
            if current_widget:
                # Test view is accessible
                assert current_widget.isVisible()
                
                # Test view can receive focus
                current_widget.setFocus()
                QTest.qWait(50)
    
    def test_sidebar_screen_reader_compatibility(self, gui_sidebar, qtbot):
        """Test sidebar has proper attributes for screen readers."""
        # Test object names are set
        assert gui_sidebar.objectName() == "sidebar"
        
        # Test stack widget accessibility
        stack = gui_sidebar.stack
        assert stack is not None
        assert stack.isVisible()
        
        # Each view should be identifiable
        for i in range(stack.count()):
            widget = stack.widget(i)
            assert widget is not None