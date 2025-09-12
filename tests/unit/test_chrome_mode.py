#!/usr/bin/env python3
"""
Unit tests for Chrome mode components.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtCore import Qt, QSettings, QPoint
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest

from ui.widgets.window_controls import WindowControls, WindowControlButton
from ui.widgets.chrome_title_bar import ChromeTitleBar, ChromeTabBar
from ui.chrome_main_window import ResizeDirection


class TestWindowControlButton:
    """Test the individual window control buttons."""
    
    def test_button_creation(self, qtbot):
        """Test creating window control buttons."""
        # Test minimize button
        min_btn = WindowControlButton('minimize')
        qtbot.addWidget(min_btn)
        assert min_btn.button_type == 'minimize'
        assert min_btn.isEnabled()
        assert min_btn.width() == 46
        assert min_btn.height() == 30
        
        # Test maximize button
        max_btn = WindowControlButton('maximize')
        qtbot.addWidget(max_btn)
        assert max_btn.button_type == 'maximize'
        assert not max_btn.is_maximized
        
        # Test close button
        close_btn = WindowControlButton('close')
        qtbot.addWidget(close_btn)
        assert close_btn.button_type == 'close'
    
    def test_maximize_button_state(self, qtbot):
        """Test maximize button state changes."""
        btn = WindowControlButton('maximize')
        qtbot.addWidget(btn)
        
        assert not btn.is_maximized
        
        # Set to maximized
        btn.set_maximized(True)
        assert btn.is_maximized
        
        # Set back to normal
        btn.set_maximized(False)
        assert not btn.is_maximized
    
    def test_button_hover_styles(self, qtbot):
        """Test that buttons have correct hover styles."""
        # Close button should have red hover
        close_btn = WindowControlButton('close')
        qtbot.addWidget(close_btn)
        assert '#e81123' in close_btn.styleSheet()  # Red hover color
        
        # Other buttons should have gray hover
        min_btn = WindowControlButton('minimize')
        qtbot.addWidget(min_btn)
        assert 'rgba(255, 255, 255, 0.1)' in min_btn.styleSheet()


class TestWindowControls:
    """Test the window controls container widget."""
    
    def test_controls_creation(self, qtbot):
        """Test creating the window controls widget."""
        controls = WindowControls()
        qtbot.addWidget(controls)
        
        # Check that all buttons exist
        assert hasattr(controls, 'minimize_btn')
        assert hasattr(controls, 'maximize_btn')
        assert hasattr(controls, 'close_btn')
        
        # Check layout
        assert controls.layout().count() == 3
        
        # Check size constraints
        assert controls.width() == 138  # 46 * 3
        assert controls.height() == 30
    
    def test_controls_signals(self, qtbot):
        """Test that control buttons emit correct signals."""
        controls = WindowControls()
        qtbot.addWidget(controls)
        
        # Test minimize signal
        with qtbot.waitSignal(controls.minimize_clicked):
            controls.minimize_btn.click()
        
        # Test maximize signal
        with qtbot.waitSignal(controls.maximize_clicked):
            controls.maximize_btn.click()
        
        # Test close signal
        with qtbot.waitSignal(controls.close_clicked):
            controls.close_btn.click()
    
    def test_maximize_state_update(self, qtbot):
        """Test updating maximize button state through controls."""
        controls = WindowControls()
        qtbot.addWidget(controls)
        
        # Initially not maximized
        assert not controls.maximize_btn.is_maximized
        
        # Set to maximized
        controls.set_maximized(True)
        assert controls.maximize_btn.is_maximized
        
        # Set back to normal
        controls.set_maximized(False)
        assert not controls.maximize_btn.is_maximized


class TestChromeTabBar:
    """Test the Chrome-style tab bar."""
    
    def test_tab_bar_creation(self, qtbot):
        """Test creating the Chrome tab bar."""
        tab_bar = ChromeTabBar()
        qtbot.addWidget(tab_bar)
        
        assert tab_bar.isMovable()
        assert tab_bar.tabsClosable()
        assert tab_bar.elideMode() == Qt.ElideRight
        assert not tab_bar.expanding()
        assert tab_bar.documentMode()
    
    def test_tab_operations(self, qtbot):
        """Test adding and removing tabs."""
        tab_bar = ChromeTabBar()
        qtbot.addWidget(tab_bar)
        
        # Add tabs
        idx1 = tab_bar.addTab("Tab 1")
        idx2 = tab_bar.addTab("Tab 2")
        idx3 = tab_bar.addTab("Tab 3")
        
        assert tab_bar.count() == 3
        assert tab_bar.tabText(idx1) == "Tab 1"
        assert tab_bar.tabText(idx2) == "Tab 2"
        assert tab_bar.tabText(idx3) == "Tab 3"
        
        # Remove a tab
        tab_bar.removeTab(idx2)
        assert tab_bar.count() == 2
        assert tab_bar.tabText(0) == "Tab 1"
        assert tab_bar.tabText(1) == "Tab 3"
    
    def test_new_tab_signal(self, qtbot):
        """Test that double-click on empty area emits new tab signal."""
        tab_bar = ChromeTabBar()
        qtbot.addWidget(tab_bar)
        
        # Add a tab so there's some content
        tab_bar.addTab("Tab 1")
        
        # Double-click on empty area should emit signal
        with qtbot.waitSignal(tab_bar.new_tab_requested):
            # Simulate double-click on empty area (past the last tab)
            pos = QPoint(200, 10)  # Assuming this is past the tab
            QTest.mouseDClick(tab_bar, Qt.LeftButton, Qt.NoModifier, pos)


class TestChromeTitleBar:
    """Test the Chrome-style title bar."""
    
    def test_title_bar_creation(self, qtbot):
        """Test creating the Chrome title bar."""
        title_bar = ChromeTitleBar()
        qtbot.addWidget(title_bar)
        
        # Check components exist
        assert hasattr(title_bar, 'tab_bar')
        assert hasattr(title_bar, 'window_controls')
        assert hasattr(title_bar, 'new_tab_btn')
        
        # Check height constraint
        assert title_bar.height() == 35
        from PySide6.QtWidgets import QSizePolicy
        assert title_bar.sizePolicy().verticalPolicy() == QSizePolicy.Fixed
    
    def test_tab_management(self, qtbot):
        """Test tab management through title bar."""
        title_bar = ChromeTitleBar()
        qtbot.addWidget(title_bar)
        
        # Add tabs
        idx1 = title_bar.add_tab("Tab 1")
        idx2 = title_bar.add_tab("Tab 2")
        
        assert title_bar.tab_count() == 2
        assert title_bar.tab_text(idx1) == "Tab 1"
        assert title_bar.tab_text(idx2) == "Tab 2"
        
        # Set current tab
        title_bar.set_current_tab(idx2)
        assert title_bar.current_tab() == idx2
        
        # Change tab text
        title_bar.set_tab_text(idx1, "Modified Tab")
        assert title_bar.tab_text(idx1) == "Modified Tab"
        
        # Remove tab
        title_bar.remove_tab(idx2)
        assert title_bar.tab_count() == 1
    
    def test_title_bar_signals(self, qtbot):
        """Test that title bar emits correct signals."""
        title_bar = ChromeTitleBar()
        qtbot.addWidget(title_bar)
        
        # Test minimize signal
        with qtbot.waitSignal(title_bar.minimize_window):
            title_bar.window_controls.minimize_btn.click()
        
        # Test maximize signal
        with qtbot.waitSignal(title_bar.maximize_window):
            title_bar.window_controls.maximize_btn.click()
        
        # Test close signal
        with qtbot.waitSignal(title_bar.close_window):
            title_bar.window_controls.close_btn.click()
        
        # Test new tab signal
        with qtbot.waitSignal(title_bar.new_tab_requested):
            title_bar.new_tab_btn.click()
    
    def test_tab_change_signal(self, qtbot):
        """Test tab change signal."""
        title_bar = ChromeTitleBar()
        qtbot.addWidget(title_bar)
        
        # Add tabs
        title_bar.add_tab("Tab 1")
        title_bar.add_tab("Tab 2")
        
        # Change tab should emit signal
        with qtbot.waitSignal(title_bar.tab_changed) as blocker:
            title_bar.set_current_tab(1)
        
        assert blocker.args == [1]
    
    def test_drag_detection(self, qtbot):
        """Test window drag detection using native system move."""
        from ui.widgets.chrome_title_bar_fixed import ChromeTitleBarFixed
        title_bar = ChromeTitleBarFixed()
        qtbot.addWidget(title_bar)
        
        # Test that we're using native move
        assert title_bar.use_native_move == True
        
        # Mouse press on empty area should prepare for drag
        pos = QPoint(100, 15)  # Middle of title bar
        
        # Create a mock window for testing
        from unittest.mock import MagicMock, patch
        mock_window = MagicMock()
        mock_window_handle = MagicMock()
        mock_window.windowHandle.return_value = mock_window_handle
        
        with patch.object(title_bar, 'window', return_value=mock_window):
            # Simulate mouse press on draggable area
            QTest.mousePress(title_bar, Qt.LeftButton, Qt.NoModifier, pos)
            
            # Verify that startSystemMove would be called
            mock_window_handle.startSystemMove.assert_called_once()
    
    def test_maximize_state(self, qtbot):
        """Test maximize state updates."""
        title_bar = ChromeTitleBar()
        qtbot.addWidget(title_bar)
        
        assert not title_bar.is_maximized
        
        # Set to maximized
        title_bar.set_maximized(True)
        assert title_bar.is_maximized
        assert title_bar.window_controls.maximize_btn.is_maximized
        
        # Set back to normal
        title_bar.set_maximized(False)
        assert not title_bar.is_maximized
        assert not title_bar.window_controls.maximize_btn.is_maximized


class TestChromeMainWindow:
    """Test the Chrome main window integration."""
    
    @patch('ui.chrome_main_window.QSettings')
    def test_chrome_mode_preference_loading(self, mock_settings):
        """Test that Chrome mode preference is loaded from settings."""
        # Mock settings to return Chrome mode enabled
        mock_instance = Mock()
        mock_instance.value.return_value = True
        mock_settings.return_value = mock_instance
        
        from ui.chrome_main_window import ChromeMainWindow
        
        # Patch MainWindow.__init__ to prevent full initialization
        with patch('ui.main_window.MainWindow.__init__', return_value=None):
            window = ChromeMainWindow()
            # Check that the preference was loaded
            assert window.chrome_mode_enabled == True
    
    def test_resize_direction_detection(self):
        """Test resize direction detection based on mouse position."""
        from ui.chrome_main_window import ChromeMainWindow, ResizeDirection
        
        with patch.object(ChromeMainWindow, '__init__', lambda x: None):
            window = ChromeMainWindow()
            window.resize_margin = 8
            window.rect = Mock(return_value=Mock(
                width=Mock(return_value=800),
                height=Mock(return_value=600)
            ))
            
            # Test corners
            assert window.get_resize_direction(QPoint(5, 5)) == ResizeDirection.TOP_LEFT
            assert window.get_resize_direction(QPoint(795, 5)) == ResizeDirection.TOP_RIGHT
            assert window.get_resize_direction(QPoint(5, 595)) == ResizeDirection.BOTTOM_LEFT
            assert window.get_resize_direction(QPoint(795, 595)) == ResizeDirection.BOTTOM_RIGHT
            
            # Test edges
            assert window.get_resize_direction(QPoint(5, 300)) == ResizeDirection.LEFT
            assert window.get_resize_direction(QPoint(795, 300)) == ResizeDirection.RIGHT
            assert window.get_resize_direction(QPoint(400, 5)) == ResizeDirection.TOP
            assert window.get_resize_direction(QPoint(400, 595)) == ResizeDirection.BOTTOM
            
            # Test center (no resize)
            assert window.get_resize_direction(QPoint(400, 300)) == ResizeDirection.NONE
    
    def test_toggle_chrome_mode(self):
        """Test toggling Chrome mode."""
        from ui.chrome_main_window import ChromeMainWindow
        
        with patch.object(ChromeMainWindow, '__init__', lambda x: None):
            window = ChromeMainWindow()
            window.chrome_mode_enabled = False
            
            # Mock QSettings and QMessageBox
            with patch('ui.chrome_main_window.QSettings') as mock_settings:
                with patch('PySide6.QtWidgets.QMessageBox') as mock_msgbox:
                    mock_instance = Mock()
                    mock_settings.return_value = mock_instance
                    mock_msgbox.information.return_value = mock_msgbox.No
                    
                    # Toggle Chrome mode
                    window.toggle_chrome_mode()
                    
                    # Check that mode was toggled
                    assert window.chrome_mode_enabled
                    
                    # Check that setting was saved
                    mock_instance.setValue.assert_called_with("UI/ChromeMode", True)
                    
                    # Check that message box was shown
                    mock_msgbox.information.assert_called_once()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])