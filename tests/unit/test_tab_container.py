"""Unit tests for enhanced tab container."""

import pytest
from unittest.mock import Mock, patch
from pytestqt.qt_compat import qt_api
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QWidget, QPushButton
from ui.widgets.tab_container import TabContainer, PlaceholderWidget


@pytest.mark.unit
class TestPlaceholderWidget:
    """Test cases for PlaceholderWidget class."""

    def test_placeholder_creation(self, qtbot):
        """Test creating a placeholder widget."""
        widget = PlaceholderWidget("Test Text")
        qtbot.addWidget(widget)
        
        # Should have a button with the text
        button = widget.layout().itemAt(0).widget()
        assert isinstance(button, QPushButton)
        assert button.text() == "Test Text"
        assert not button.isEnabled()  # Should be disabled
        
    def test_placeholder_set_text(self, qtbot):
        """Test updating placeholder text."""
        widget = PlaceholderWidget("Initial")
        qtbot.addWidget(widget)
        
        widget.set_text("Updated")
        
        button = widget.layout().itemAt(0).widget()
        assert button.text() == "Updated"


@pytest.mark.unit  
class TestTabContainer:
    """Test cases for TabContainer class."""

    def test_tab_container_creation(self, qtbot):
        """Test creating a tab container."""
        container = TabContainer("test-pane-id")
        qtbot.addWidget(container)
        
        assert container.get_pane_id() == "test-pane-id"
        assert container.tabsClosable()
        assert container.isMovable()
        assert container.documentMode()
        
    def test_add_placeholder_tab(self, qtbot):
        """Test adding a placeholder tab."""
        container = TabContainer("test-pane")
        qtbot.addWidget(container)
        
        index = container.add_placeholder_tab("Test Tab")
        
        assert container.count() == 1
        assert container.tabText(index) == "Test Tab"
        assert container.currentIndex() == index
        
        # Widget should be a PlaceholderWidget
        widget = container.widget(index)
        assert isinstance(widget, PlaceholderWidget)
        
    def test_add_tab_with_widget(self, qtbot):
        """Test adding a tab with a custom widget."""
        container = TabContainer("test-pane")
        qtbot.addWidget(container)
        
        custom_widget = QWidget()
        index = container.add_tab_with_widget(custom_widget, "Custom Tab")
        
        assert container.count() == 1
        assert container.tabText(index) == "Custom Tab"
        assert container.widget(index) == custom_widget
        assert container.currentIndex() == index
        
    def test_close_tab_multiple(self, qtbot):
        """Test closing tabs when multiple exist."""
        container = TabContainer("test-pane")
        qtbot.addWidget(container)
        
        # Add multiple tabs
        container.add_placeholder_tab("Tab 1")
        container.add_placeholder_tab("Tab 2")
        container.add_placeholder_tab("Tab 3")
        
        assert container.count() == 3
        
        # Close middle tab
        container.close_tab(1)
        
        assert container.count() == 2
        assert container.tabText(0) == "Tab 1"
        assert container.tabText(1) == "Tab 3"
        
    def test_close_last_tab(self, qtbot):
        """Test closing the last tab adds a placeholder."""
        container = TabContainer("test-pane")
        qtbot.addWidget(container)
        
        # Should start with no tabs, add one
        container.add_placeholder_tab("Only Tab")
        assert container.count() == 1
        
        # Close the only tab
        container.close_tab(0)
        
        # Should still have 1 tab (placeholder added)
        assert container.count() == 1
        assert container.tabText(0) == "New Tab"  # Default placeholder name
        
    def test_context_menu_creation(self, qtbot):
        """Test context menu is created with correct actions."""
        container = TabContainer("test-pane")
        qtbot.addWidget(container)
        
        assert hasattr(container, 'context_menu')
        assert hasattr(container, 'split_horizontal_action')
        assert hasattr(container, 'split_vertical_action')
        assert hasattr(container, 'close_pane_action')
        
        # Check action properties
        assert container.split_horizontal_action.text() == "Split Right"
        assert container.split_vertical_action.text() == "Split Down"
        assert container.close_pane_action.text() == "Close Pane"
        
    def test_split_signals_emitted(self, qtbot):
        """Test that split signals are emitted correctly."""
        container = TabContainer("test-pane")
        qtbot.addWidget(container)
        
        # Connect signal receivers
        horizontal_receiver = Mock()
        vertical_receiver = Mock()
        close_receiver = Mock()
        
        container.split_horizontal_requested.connect(horizontal_receiver)
        container.split_vertical_requested.connect(vertical_receiver)
        container.close_pane_requested.connect(close_receiver)
        
        # Trigger actions
        container.split_horizontal_action.trigger()
        container.split_vertical_action.trigger()
        container.close_pane_action.trigger()
        
        # Verify signals emitted
        horizontal_receiver.assert_called_once_with("test-pane")
        vertical_receiver.assert_called_once_with("test-pane")
        close_receiver.assert_called_once_with("test-pane")
        
    def test_pane_activation_on_click(self, qtbot):
        """Test that pane activation signal is emitted on click."""
        container = TabContainer("test-pane")
        qtbot.addWidget(container)
        container.add_placeholder_tab("Test")
        
        # Connect signal receiver
        activation_receiver = Mock()
        container.pane_activated.connect(activation_receiver)
        
        # Simulate mouse click
        event = QMouseEvent(
            QMouseEvent.MouseButtonPress,
            QPoint(10, 10),
            Qt.LeftButton,
            Qt.LeftButton,
            Qt.NoModifier
        )
        container.mousePressEvent(event)
        
        # Verify signal emitted
        activation_receiver.assert_called_once_with("test-pane")
        
    def test_tab_changed_activation(self, qtbot):
        """Test that pane activation occurs on tab change."""
        container = TabContainer("test-pane")
        qtbot.addWidget(container)
        
        container.add_placeholder_tab("Tab 1")
        container.add_placeholder_tab("Tab 2")
        
        # Connect signal receiver
        activation_receiver = Mock()
        container.pane_activated.connect(activation_receiver)
        
        # Change to first tab
        container.setCurrentIndex(0)
        
        # Verify signal emitted
        activation_receiver.assert_called_with("test-pane")
        
    def test_close_other_tabs(self, qtbot):
        """Test closing other tabs functionality."""
        container = TabContainer("test-pane")
        qtbot.addWidget(container)
        
        # Add multiple tabs
        container.add_placeholder_tab("Tab 1")
        container.add_placeholder_tab("Tab 2") 
        container.add_placeholder_tab("Tab 3")
        
        # Set current tab to middle one
        container.setCurrentIndex(1)
        
        # Close other tabs
        container.close_other_tabs()
        
        # Should only have the current tab left
        assert container.count() == 1
        assert container.tabText(0) == "Tab 2"
        
    def test_close_all_tabs(self, qtbot):
        """Test close all tabs with confirmation."""
        container = TabContainer("test-pane")
        qtbot.addWidget(container)
        
        # Add multiple tabs
        container.add_placeholder_tab("Tab 1")
        container.add_placeholder_tab("Tab 2")
        container.add_placeholder_tab("Tab 3")
        
        # Mock the message box to return Yes
        with patch('ui.widgets.tab_container.QMessageBox.question') as mock_question:
            from PySide6.QtWidgets import QMessageBox
            mock_question.return_value = QMessageBox.Yes
            
            container.close_all_tabs()
            
            # All tabs should be closed
            assert container.count() == 0
            mock_question.assert_called_once()
            
    def test_close_all_tabs_cancelled(self, qtbot):
        """Test close all tabs cancelled."""
        container = TabContainer("test-pane")
        qtbot.addWidget(container)
        
        # Add multiple tabs
        container.add_placeholder_tab("Tab 1")
        container.add_placeholder_tab("Tab 2")
        
        # Mock the message box to return No
        with patch('ui.widgets.tab_container.QMessageBox.question') as mock_question:
            from PySide6.QtWidgets import QMessageBox
            mock_question.return_value = QMessageBox.No
            
            container.close_all_tabs()
            
            # Tabs should remain
            assert container.count() == 2
            
    def test_move_tab_to_new_pane_signals(self, qtbot):
        """Test move tab to new pane signals."""
        container = TabContainer("test-pane")
        qtbot.addWidget(container)
        
        container.add_placeholder_tab("Tab 1")
        container.add_placeholder_tab("Tab 2")
        container.setCurrentIndex(1)
        
        # Connect signal receiver
        move_receiver = Mock()
        container.tab_moved_to_new_pane.connect(move_receiver)
        
        # Test horizontal move
        container.move_current_tab_to_new_pane_right()
        move_receiver.assert_called_with("test-pane_tab_1", "horizontal")
        
        # Test vertical move
        container.move_current_tab_to_new_pane_down()
        move_receiver.assert_called_with("test-pane_tab_1", "vertical")
        
    def test_get_tab_info_list(self, qtbot):
        """Test getting tab info list."""
        container = TabContainer("test-pane")
        qtbot.addWidget(container)
        
        container.add_placeholder_tab("Tab 1")
        container.add_placeholder_tab("Tab 2")
        
        tab_infos = container.get_tab_info_list()
        
        assert len(tab_infos) == 2
        assert tab_infos[0].title == "Tab 1"
        assert tab_infos[1].title == "Tab 2" 
        assert all(info.widget_type == "placeholder" for info in tab_infos)
        assert all(info.is_closable for info in tab_infos)
        
    def test_set_active_tab(self, qtbot):
        """Test setting active tab."""
        container = TabContainer("test-pane")
        qtbot.addWidget(container)
        
        container.add_placeholder_tab("Tab 1")
        container.add_placeholder_tab("Tab 2")
        container.add_placeholder_tab("Tab 3")
        
        # Set middle tab as active
        success = container.set_active_tab(1)
        
        assert success
        assert container.currentIndex() == 1
        
        # Test invalid index
        success = container.set_active_tab(10)
        assert not success
        
    def test_pane_id_management(self, qtbot):
        """Test pane ID getter/setter."""
        container = TabContainer("initial-id")
        qtbot.addWidget(container)
        
        assert container.get_pane_id() == "initial-id"
        
        container.set_pane_id("new-id")
        assert container.get_pane_id() == "new-id"
        
    def test_context_menu_show(self, qtbot):
        """Test context menu display."""
        container = TabContainer("test-pane")
        qtbot.addWidget(container)
        
        container.add_placeholder_tab("Tab 1")
        
        # Mock the menu exec method to avoid showing actual menu
        with patch.object(container.context_menu, 'exec') as mock_exec:
            container.show_context_menu(QPoint(10, 10))
            mock_exec.assert_called_once()
            
    def test_tab_close_signal_connection(self, qtbot):
        """Test that tab close request signal is properly emitted."""
        container = TabContainer("test-pane")
        qtbot.addWidget(container)
        
        # Connect signal receiver for tab_close_requested
        close_request_receiver = Mock()
        container.tab_close_requested.connect(close_request_receiver)
        
        container.add_placeholder_tab("Tab 1")
        container.add_placeholder_tab("Tab 2")
        
        # Emit the tab close requested signal from Qt
        container.tabCloseRequested.emit(1)
        
        # Verify tab_close_requested signal was emitted
        close_request_receiver.assert_called_once_with("test-pane", 1)
        
    def test_tab_closed_signal_emission(self, qtbot):
        """Test that tab_closed signal is emitted."""
        container = TabContainer("test-pane")
        qtbot.addWidget(container)
        
        container.add_placeholder_tab("Tab 1")
        container.add_placeholder_tab("Tab 2")
        
        # Connect signal receiver
        close_receiver = Mock()
        container.tab_closed.connect(close_receiver)
        
        # Close a tab
        container.close_tab(1)
        
        # Verify signal was emitted
        close_receiver.assert_called_once_with("test-pane", 1)