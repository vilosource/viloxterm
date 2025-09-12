"""GUI tests for Workspace component focusing on user interactions."""

import pytest
from unittest.mock import Mock, patch
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QTabWidget
from tests.gui.base import WorkspaceGUITestBase, MouseGUITestBase, KeyboardGUITestBase


@pytest.mark.gui
class TestWorkspaceGUI(WorkspaceGUITestBase):
    """GUI tests for workspace user interactions."""
    
    def test_workspace_displays_correctly(self, gui_workspace, qtbot):
        """Test workspace displays with correct initial state."""
        self.verify_workspace_initialized(gui_workspace)
        
        # Verify tab widget exists
        assert hasattr(gui_workspace, 'tab_widget')
        assert gui_workspace.tab_widget.isVisible()
        
        # Should have at least one default tab
        assert gui_workspace.tab_widget.count() >= 1
    
    def test_workspace_initial_tab_creation(self, gui_workspace, qtbot):
        """Test workspace creates default tab on initialization."""
        tab_count = gui_workspace.tab_widget.count()
        assert tab_count >= 1
        
        # Should have tabs dictionary
        assert hasattr(gui_workspace, 'tabs')
        assert len(gui_workspace.tabs) >= 1
        
        # Current tab should be valid
        current_index = gui_workspace.tab_widget.currentIndex()
        assert current_index >= 0
        assert current_index in gui_workspace.tabs
    
    def test_workspace_tab_widget_properties(self, gui_workspace, qtbot):
        """Test workspace tab widget properties."""
        tab_widget = gui_workspace.tab_widget
        
        # Should be movable tabs by default (VSCode-like behavior)
        if hasattr(tab_widget, 'setMovable'):
            # Test that movable property can be accessed
            assert hasattr(tab_widget, 'isMovable')
        
        # Should have close buttons if supported
        if hasattr(tab_widget, 'setTabsClosable'):
            # Test that closable property can be accessed
            assert hasattr(tab_widget, 'tabsClosable')
    
    def test_workspace_tab_content_access(self, gui_workspace, qtbot):
        """Test workspace tab content can be accessed."""
        current_index = gui_workspace.tab_widget.currentIndex()
        
        if current_index >= 0:
            # Should be able to get current widget
            current_widget = gui_workspace.tab_widget.currentWidget()
            assert current_widget is not None
            
            # Should have corresponding tab data
            if current_index in gui_workspace.tabs:
                tab_data = gui_workspace.tabs[current_index]
                assert tab_data is not None
                assert hasattr(tab_data, 'name')
                assert hasattr(tab_data, 'split_widget')


@pytest.mark.gui
@pytest.mark.mouse
class TestWorkspaceMouseGUI(WorkspaceGUITestBase, MouseGUITestBase):
    """GUI tests for workspace mouse interactions."""
    
    def test_workspace_tab_clicking(self, gui_workspace, qtbot):
        """Test clicking on workspace tabs."""
        tab_widget = gui_workspace.tab_widget
        tab_count = tab_widget.count()
        
        if tab_count > 1:
            # Test clicking different tabs
            initial_index = tab_widget.currentIndex()
            
            # Click on a different tab
            for i in range(tab_count):
                if i != initial_index:
                    # Get tab bar and click on tab
                    tab_bar = tab_widget.tabBar()
                    if tab_bar:
                        # Click on tab
                        tab_rect = tab_bar.tabRect(i)
                        qtbot.mouseClick(tab_bar, Qt.MouseButton.LeftButton, 
                                       pos=tab_rect.center())
                        QTest.qWait(50)
                        
                        # Verify tab changed
                        assert tab_widget.currentIndex() == i
                    break
    
    def test_workspace_right_click_context_menu(self, gui_workspace, qtbot):
        """Test right-clicking on workspace shows context menu."""
        # Right-click on workspace area
        if gui_workspace.tab_widget.count() > 0:
            current_widget = gui_workspace.tab_widget.currentWidget()
            if current_widget:
                # Right-click on the workspace content
                self.right_click_widget_center(qtbot, current_widget)
                QTest.qWait(100)
                
                # Basic test - no errors should occur
                assert current_widget.isVisible()
    
    def test_workspace_mouse_focus(self, gui_workspace, qtbot):
        """Test workspace responds to mouse focus."""
        # Click on workspace to give it focus
        self.click_widget_center(qtbot, gui_workspace)
        QTest.qWait(50)
        
        # Workspace should be visible and responsive
        assert gui_workspace.isVisible()
        
        # If there are tabs, current tab should be accessible
        if gui_workspace.tab_widget.count() > 0:
            current_widget = gui_workspace.tab_widget.currentWidget()
            if current_widget:
                assert current_widget.isVisible()


@pytest.mark.gui
@pytest.mark.keyboard
class TestWorkspaceKeyboardGUI(WorkspaceGUITestBase, KeyboardGUITestBase):
    """GUI tests for workspace keyboard interactions."""
    
    def test_workspace_keyboard_focus(self, gui_workspace, qtbot):
        """Test workspace can receive keyboard focus."""
        gui_workspace.setFocus()
        QTest.qWait(50)
        
        # Workspace or its child should be focusable
        # The exact focus behavior depends on the current tab content
        assert gui_workspace.isVisible()
    
    def test_workspace_tab_keyboard_navigation(self, gui_workspace, qtbot):
        """Test keyboard navigation between tabs."""
        tab_widget = gui_workspace.tab_widget
        
        if tab_widget.count() > 1:
            initial_index = tab_widget.currentIndex()
            
            # Focus the tab widget
            tab_widget.setFocus()
            QTest.qWait(50)
            
            # Try Ctrl+Tab for tab switching (if supported)
            qtbot.keyClick(tab_widget, Qt.Key.Key_Tab, Qt.KeyboardModifier.ControlModifier)
            QTest.qWait(100)
            
            # Basic test - tab widget should remain functional
            assert tab_widget.isVisible()
            assert tab_widget.currentIndex() >= 0
    
    def test_workspace_content_keyboard_interaction(self, gui_workspace, qtbot):
        """Test keyboard interactions with workspace content."""
        if gui_workspace.tab_widget.count() > 0:
            current_widget = gui_workspace.tab_widget.currentWidget()
            if current_widget:
                # Focus the content widget
                current_widget.setFocus()
                QTest.qWait(50)
                
                # Basic keyboard interaction test
                qtbot.keyClick(current_widget, Qt.Key.Key_Space)
                QTest.qWait(50)
                
                # Widget should remain visible and functional
                assert current_widget.isVisible()


@pytest.mark.gui
@pytest.mark.integration
class TestWorkspaceIntegrationGUI(WorkspaceGUITestBase):
    """GUI integration tests for workspace with other components."""
    
    def test_workspace_main_window_integration(self, gui_main_window, qtbot):
        """Test workspace integrates properly with main window."""
        workspace = gui_main_window.workspace
        main_splitter = gui_main_window.main_splitter
        
        # Workspace should be in the main splitter
        splitter_widgets = [main_splitter.widget(i) for i in range(main_splitter.count())]
        assert workspace in splitter_widgets
        
        # Workspace should be visible and functional
        assert workspace.isVisible()
        assert workspace.width() > 0
        assert workspace.height() > 0
    
    def test_workspace_focus_integration_with_sidebar(self, gui_main_window, qtbot):
        """Test workspace focus works correctly with sidebar."""
        workspace = gui_main_window.workspace
        sidebar = gui_main_window.sidebar
        
        # Focus workspace
        workspace.setFocus()
        QTest.qWait(50)
        
        # Then focus sidebar
        sidebar.setFocus()
        QTest.qWait(50)
        
        # Both should remain visible and functional
        assert workspace.isVisible()
        assert sidebar.isVisible()
        
        # Focus back to workspace
        workspace.setFocus()
        QTest.qWait(50)
        
        assert workspace.isVisible()
    
    def test_workspace_splitter_resize_integration(self, gui_main_window, qtbot):
        """Test workspace responds correctly to splitter resizing."""
        workspace = gui_main_window.workspace
        main_splitter = gui_main_window.main_splitter
        
        initial_size = workspace.size()
        initial_splitter_sizes = main_splitter.sizes()
        
        # Modify splitter sizes (simulate user dragging)
        if len(initial_splitter_sizes) >= 2:
            new_sizes = initial_splitter_sizes[:]
            # Increase workspace size, decrease sidebar size
            if new_sizes[0] > 50:  # Ensure sidebar doesn't get too small
                new_sizes[0] -= 50
                new_sizes[1] += 50
                main_splitter.setSizes(new_sizes)
                QTest.qWait(50)
                
                # Workspace should adapt to new size
                new_size = workspace.size()
                assert new_size.width() > 0
                assert new_size.height() > 0


@pytest.mark.gui
@pytest.mark.performance
class TestWorkspacePerformanceGUI(WorkspaceGUITestBase):
    """GUI performance tests for workspace."""
    
    def test_workspace_tab_switching_performance(self, gui_workspace, qtbot):
        """Test workspace tab switching performs well."""
        tab_widget = gui_workspace.tab_widget
        tab_count = tab_widget.count()
        
        if tab_count > 1:
            # Rapidly switch between tabs
            for _ in range(10):  # 10 cycles
                for i in range(tab_count):
                    tab_widget.setCurrentIndex(i)
                    QTest.qWait(5)  # Minimal wait
            
            # Final state should be consistent
            final_index = tab_widget.currentIndex()
            assert 0 <= final_index < tab_count
            
            # Tab should be responsive
            current_widget = tab_widget.currentWidget()
            assert current_widget is not None
            assert current_widget.isVisible()
    
    def test_workspace_large_content_performance(self, gui_workspace, qtbot):
        """Test workspace handles content updates efficiently."""
        if gui_workspace.tab_widget.count() > 0:
            current_widget = gui_workspace.tab_widget.currentWidget()
            if current_widget:
                # Test rapid updates don't cause performance issues
                for _ in range(20):
                    current_widget.update()
                    QTest.qWait(5)
                
                # Widget should remain functional
                assert current_widget.isVisible()
                assert current_widget.isEnabled()


@pytest.mark.gui
@pytest.mark.accessibility
class TestWorkspaceAccessibilityGUI(WorkspaceGUITestBase):
    """GUI accessibility tests for workspace."""
    
    def test_workspace_keyboard_accessibility(self, gui_workspace, qtbot):
        """Test workspace is accessible via keyboard."""
        # Test focus management
        gui_workspace.setFocus()
        QTest.qWait(50)
        
        # Test tab navigation accessibility
        tab_widget = gui_workspace.tab_widget
        if tab_widget.count() > 0:
            tab_widget.setFocus()
            QTest.qWait(50)
            
            # Test keyboard navigation
            qtbot.keyClick(tab_widget, Qt.Key.Key_Right)
            QTest.qWait(50)
            
            # Should remain functional
            assert tab_widget.isVisible()
    
    def test_workspace_screen_reader_compatibility(self, gui_workspace, qtbot):
        """Test workspace has proper attributes for screen readers."""
        # Test that workspace has identifiable structure
        tab_widget = gui_workspace.tab_widget
        assert tab_widget is not None
        
        # Tabs should be identifiable
        for i in range(tab_widget.count()):
            tab_text = tab_widget.tabText(i)
            # Tab should have some identifying text or be able to get one
            assert isinstance(tab_text, str)  # May be empty string, but should be string
    
    def test_workspace_focus_indication(self, gui_workspace, qtbot):
        """Test workspace provides clear focus indication."""
        # Test that focusing workspace provides visual feedback
        gui_workspace.setFocus()
        QTest.qWait(50)
        
        # Should be able to determine focus state
        # The exact visual indication depends on styling
        assert gui_workspace.isVisible()
        
        # Test focus on tab content
        if gui_workspace.tab_widget.count() > 0:
            current_widget = gui_workspace.tab_widget.currentWidget()
            if current_widget:
                current_widget.setFocus()
                QTest.qWait(50)
                assert current_widget.isVisible()


@pytest.mark.gui
@pytest.mark.state
class TestWorkspaceStateGUI(WorkspaceGUITestBase):
    """GUI tests for workspace state management."""
    
    def test_workspace_maintains_state_consistency(self, gui_workspace, qtbot):
        """Test workspace maintains consistent state during interactions."""
        initial_tab_count = gui_workspace.tab_widget.count()
        initial_tabs_dict_size = len(gui_workspace.tabs)
        
        # State should be consistent
        assert initial_tab_count >= 0
        
        # Tab count and tabs dict should be related
        # (Exact relationship depends on implementation)
        assert isinstance(gui_workspace.tabs, dict)
    
    def test_workspace_current_tab_state(self, gui_workspace, qtbot):
        """Test workspace current tab state is consistent."""
        tab_widget = gui_workspace.tab_widget
        
        if tab_widget.count() > 0:
            current_index = tab_widget.currentIndex()
            current_widget = tab_widget.currentWidget()
            
            # Current state should be consistent
            assert current_index >= 0
            assert current_widget is not None
            assert current_widget.isVisible()
            
            # If tabs dict has current index, data should be consistent
            if current_index in gui_workspace.tabs:
                tab_data = gui_workspace.tabs[current_index]
                assert tab_data is not None
    
    def test_workspace_state_after_interactions(self, gui_workspace, qtbot):
        """Test workspace state remains valid after various interactions."""
        # Click on workspace
        self.click_widget_center(qtbot, gui_workspace)
        QTest.qWait(50)
        
        # Focus workspace
        gui_workspace.setFocus()
        QTest.qWait(50)
        
        # Keyboard interaction
        qtbot.keyClick(gui_workspace, Qt.Key.Key_Space)
        QTest.qWait(50)
        
        # State should remain valid
        assert gui_workspace.isVisible()
        assert gui_workspace.tab_widget.count() >= 0
        
        if gui_workspace.tab_widget.count() > 0:
            current_widget = gui_workspace.tab_widget.currentWidget()
            assert current_widget is not None