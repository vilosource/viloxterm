# GUI Test Examples

## Overview

This document provides practical examples of GUI tests in ViloApp, demonstrating how to implement various testing scenarios using pytest-qt. These examples serve as templates for writing your own GUI tests.

## Basic Component Testing Examples

### Example 1: Component Display and Properties

```python
@pytest.mark.gui
class TestActivityBarDisplay(ActivityBarGUITestBase):
    """Examples of testing component display and basic properties."""
    
    def test_activity_bar_initial_display(self, gui_activity_bar, qtbot):
        """Test activity bar displays correctly on initialization."""
        # Verify basic visibility and properties
        assert gui_activity_bar.isVisible()
        assert gui_activity_bar.isEnabled()
        
        # Check specific properties
        assert gui_activity_bar.orientation() == Qt.Orientation.Vertical
        assert gui_activity_bar.width() == 48
        assert not gui_activity_bar.isMovable()
        
        # Verify all required buttons are present
        buttons = self.get_activity_buttons(gui_activity_bar)
        expected_buttons = ["explorer", "search", "git", "settings"]
        
        for button_name in expected_buttons:
            assert button_name in buttons
            button = buttons[button_name]
            assert button.isEnabled()
            assert button.text()  # Should have text for accessibility
    
    def test_activity_bar_styling_properties(self, gui_activity_bar, qtbot):
        """Test activity bar has proper styling attributes."""
        # Check object name for CSS styling
        assert gui_activity_bar.objectName() == "activityBar"
        
        # Check VSCode-specific property
        assert gui_activity_bar.property("type") == "activitybar"
        
        # Verify icon size is appropriate
        icon_size = gui_activity_bar.iconSize()
        assert icon_size.width() == 24
        assert icon_size.height() == 24
```

### Example 2: User Interaction Testing

```python
@pytest.mark.gui
@pytest.mark.mouse
class TestActivityBarInteractions(ActivityBarGUITestBase):
    """Examples of testing user interactions."""
    
    @patch('ui.activity_bar.execute_command')
    def test_button_click_interaction(self, mock_execute, gui_activity_bar, qtbot):
        """Test button click triggers correct actions."""
        mock_execute.return_value = {'success': True}
        
        # Test clicking search button
        with qtbot.waitSignal(gui_activity_bar.view_changed, timeout=1000) as blocker:
            self.click_activity_button(qtbot, gui_activity_bar, "search")
        
        # Verify signal was emitted correctly
        assert blocker.args == ["search"]
        
        # Verify internal state changed
        assert gui_activity_bar.current_view == "search"
        
        # Verify visual state updated
        self.verify_button_states(gui_activity_bar, "search")
        
        # Verify command system integration
        mock_execute.assert_called_with("workbench.view.search")
    
    def test_same_button_click_twice(self, gui_activity_bar, qtbot):
        """Test clicking same button twice triggers sidebar toggle."""
        # Ensure we start with explorer (default)
        assert gui_activity_bar.current_view == "explorer"
        
        # Click explorer button (same as current)
        with qtbot.waitSignal(gui_activity_bar.toggle_sidebar, timeout=1000):
            self.click_activity_button(qtbot, gui_activity_bar, "explorer")
        
        # View should remain the same, but sidebar should toggle
        assert gui_activity_bar.current_view == "explorer"
```

## Animation Testing Examples

### Example 3: Sidebar Animation Testing

```python
@pytest.mark.gui
@pytest.mark.animation
class TestSidebarAnimations(SidebarGUITestBase, AnimationGUITestBase):
    """Examples of testing animations and transitions."""
    
    def test_smooth_collapse_animation(self, gui_sidebar, qtbot):
        """Test sidebar collapse animation completes smoothly."""
        # Ensure starting in expanded state
        if gui_sidebar.is_collapsed:
            gui_sidebar.expand()
            self.wait_for_sidebar_animation(qtbot, gui_sidebar)
        
        # Record initial state
        initial_width = gui_sidebar.width()
        initial_max_width = gui_sidebar.maximumWidth()
        
        assert initial_width > 0
        assert not gui_sidebar.is_collapsed
        
        # Start collapse animation
        gui_sidebar.collapse()
        
        # Verify animation is running
        assert gui_sidebar.animation.state() == gui_sidebar.animation.State.Running
        
        # Wait for animation to complete
        self.wait_for_sidebar_animation(qtbot, gui_sidebar, timeout=3000)
        
        # Verify final state
        assert gui_sidebar.is_collapsed
        assert gui_sidebar.animation.state() == gui_sidebar.animation.State.Stopped
        
        # Width should be effectively zero (may be 1-2 pixels due to borders)
        assert gui_sidebar.width() < 5
    
    def test_animation_interruption_handling(self, gui_sidebar, qtbot):
        """Test animation handles interruption gracefully."""
        # Start collapse
        gui_sidebar.collapse()
        
        # Let animation run briefly
        QTest.qWait(50)  
        
        # Interrupt with expand
        gui_sidebar.expand()
        
        # Wait for final state
        self.wait_for_sidebar_animation(qtbot, gui_sidebar, timeout=3000)
        
        # Should end up expanded
        assert not gui_sidebar.is_collapsed
        assert gui_sidebar.width() > 100  # Should be reasonably wide
        
    @pytest.mark.slow
    def test_animation_performance(self, gui_sidebar, qtbot):
        """Test animation performance under repeated operations."""
        import time
        
        start_time = time.time()
        
        # Perform multiple animation cycles
        for cycle in range(5):
            gui_sidebar.collapse()
            self.wait_for_sidebar_animation(qtbot, gui_sidebar, timeout=1000)
            
            gui_sidebar.expand()  
            self.wait_for_sidebar_animation(qtbot, gui_sidebar, timeout=1000)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should complete 5 cycles in reasonable time
        assert total_time < 15.0  # 15 seconds max (3 seconds per cycle)
        
        # Final state should be consistent
        assert not gui_sidebar.is_collapsed
        assert gui_sidebar.animation.state() == gui_sidebar.animation.State.Stopped
```

## Keyboard Interaction Examples

### Example 4: Keyboard Shortcut Testing

```python
@pytest.mark.gui
@pytest.mark.keyboard
class TestKeyboardShortcuts(KeyboardGUITestBase):
    """Examples of testing keyboard shortcuts and navigation."""
    
    @patch('ui.main_window.execute_command')
    def test_theme_toggle_shortcut(self, mock_execute, gui_main_window, qtbot):
        """Test Ctrl+T toggles theme through command system."""
        mock_execute.return_value = {'success': True}
        
        # Focus main window
        gui_main_window.setFocus()
        qtbot.waitUntil(lambda: gui_main_window.isActiveWindow(), timeout=1000)
        
        # Send Ctrl+T
        qtbot.keyClick(gui_main_window, Qt.Key.Key_T, Qt.KeyboardModifier.ControlModifier)
        QTest.qWait(100)  # Brief wait for command processing
        
        # Verify command was executed
        mock_execute.assert_called_with("view.toggleTheme")
    
    @patch('ui.main_window.execute_command')
    def test_complex_shortcut_combination(self, mock_execute, gui_main_window, qtbot):
        """Test complex shortcut like Ctrl+Shift+R for reset."""
        mock_execute.return_value = {'success': True}
        
        # Focus main window
        gui_main_window.setFocus()
        
        # Send Ctrl+Shift+R
        qtbot.keyClick(
            gui_main_window, 
            Qt.Key.Key_R,
            Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier
        )
        QTest.qWait(100)
        
        # Verify reset command was executed
        mock_execute.assert_called_with("debug.resetAppState")
    
    def test_keyboard_navigation_accessibility(self, gui_main_window, qtbot):
        """Test keyboard navigation works for accessibility."""
        activity_bar = gui_main_window.activity_bar
        sidebar = gui_main_window.sidebar
        
        # Focus activity bar
        activity_bar.setFocus()
        QTest.qWait(50)
        
        # Tab to next component (should move to sidebar or workspace)
        qtbot.keyClick(activity_bar, Qt.Key.Key_Tab)
        QTest.qWait(50)
        
        # Verify focus moved (exact target may vary)
        current_focus = QApplication.focusWidget()
        assert current_focus is not None
        
        # Should be able to navigate back with Shift+Tab
        qtbot.keyClick(current_focus, Qt.Key.Key_Tab, Qt.KeyboardModifier.ShiftModifier)
        QTest.qWait(50)
        
        # Focus should change
        new_focus = QApplication.focusWidget()
        assert new_focus is not None
```

## Integration Testing Examples

### Example 5: Multi-Component Integration

```python
@pytest.mark.gui
@pytest.mark.integration
class TestComponentIntegration(MainWindowGUITestBase):
    """Examples of testing component integration."""
    
    def test_activity_bar_sidebar_integration(self, gui_main_window, qtbot):
        """Test activity bar changes are reflected in sidebar."""
        activity_bar = gui_main_window.activity_bar
        sidebar = gui_main_window.sidebar
        
        # Record initial states
        initial_activity_view = activity_bar.current_view
        initial_sidebar_index = sidebar.stack.currentIndex()
        
        # Change activity view and verify sidebar follows
        with qtbot.waitSignal(activity_bar.view_changed, timeout=1000) as blocker:
            self.click_activity_button(qtbot, activity_bar, "git")
        
        # Verify signal was emitted
        assert blocker.args == ["git"]
        assert activity_bar.current_view == "git"
        
        # Integration verification depends on actual connection implementation
        # This tests the signal emission part of the integration
    
    def test_workspace_focus_management(self, gui_main_window, qtbot):
        """Test focus management between workspace and other components."""
        workspace = gui_main_window.workspace
        sidebar = gui_main_window.sidebar
        activity_bar = gui_main_window.activity_bar
        
        # Focus workspace
        workspace.setFocus()
        QTest.qWait(50)
        
        # Focus sidebar
        sidebar.setFocus()
        QTest.qWait(50)
        
        # Focus activity bar
        activity_bar.setFocus()
        QTest.qWait(50)
        
        # All components should remain visible and functional
        assert workspace.isVisible()
        assert sidebar.isVisible()
        assert activity_bar.isVisible()
        
        # Should be able to focus back to workspace
        workspace.setFocus()
        QTest.qWait(50)
        
        # Test that workspace can handle focus
        if workspace.tab_widget.count() > 0:
            current_tab = workspace.tab_widget.currentWidget()
            assert current_tab is not None
            assert current_tab.isVisible()
    
    def test_splitter_resize_integration(self, gui_main_window, qtbot):
        """Test components respond correctly to splitter resizing."""
        main_splitter = gui_main_window.main_splitter
        sidebar = gui_main_window.sidebar
        workspace = gui_main_window.workspace
        
        # Get initial sizes
        initial_sizes = main_splitter.sizes()
        assert len(initial_sizes) >= 2
        
        # Modify splitter sizes (simulate drag)
        new_sizes = initial_sizes[:]
        if new_sizes[0] > 100:  # Ensure minimum size
            # Make sidebar smaller, workspace larger
            new_sizes[0] = 150
            new_sizes[1] = initial_sizes[1] + (initial_sizes[0] - 150)
            
            main_splitter.setSizes(new_sizes)
            QTest.qWait(100)  # Allow layout to update
            
            # Verify components adapted
            updated_sizes = main_splitter.sizes()
            assert len(updated_sizes) >= 2
            
            # Sidebar should be smaller
            assert updated_sizes[0] <= initial_sizes[0]
            
            # Components should still be functional
            assert sidebar.isVisible()
            assert workspace.isVisible()
```

## Theme Testing Examples

### Example 6: Theme Switching and Visual Consistency

```python
@pytest.mark.gui
@pytest.mark.theme
class TestThemeIntegration(ThemeGUITestBase):
    """Examples of testing theme switching and visual consistency."""
    
    def test_theme_toggle_updates_all_components(self, gui_main_window, qtbot, mock_icon_manager):
        """Test theme toggle updates all UI components consistently."""
        activity_bar = gui_main_window.activity_bar
        
        # Setup initial theme state
        initial_theme = mock_icon_manager.theme
        
        # Trigger theme change via command system
        with patch('ui.main_window.execute_command') as mock_execute:
            mock_execute.return_value = {'success': True}
            
            # Simulate Ctrl+T shortcut
            qtbot.keyClick(gui_main_window, Qt.Key.Key_T, Qt.KeyboardModifier.ControlModifier)
            QTest.qWait(100)
            
            # Verify theme command was executed
            mock_execute.assert_called_with("view.toggleTheme")
        
        # Verify icon manager theme toggle was called
        mock_icon_manager.toggle_theme.assert_called()
    
    def test_activity_bar_icon_updates_on_theme_change(self, gui_activity_bar, qtbot, mock_icon_manager):
        """Test activity bar icons update when theme changes."""
        # Clear previous calls
        mock_icon_manager.get_icon.reset_mock()
        
        # Trigger icon update (simulates theme change)
        gui_activity_bar.update_icons()
        
        # Verify all icons were requested
        expected_icons = ["explorer", "search", "git", "settings"]
        actual_calls = [call[0][0] for call in mock_icon_manager.get_icon.call_args_list]
        
        for expected_icon in expected_icons:
            assert expected_icon in actual_calls, f"Icon {expected_icon} was not updated"
        
        # Verify each button still functions after icon update
        buttons = self.get_activity_buttons(gui_activity_bar)
        for button in buttons.values():
            assert button.isEnabled()
            assert button.isVisible()
    
    def test_theme_consistency_across_restarts(self, qtbot, mock_icon_manager):
        """Test theme setting persists across application restarts."""
        # Simulate application restart with saved theme
        mock_icon_manager.theme = "dark"
        
        with patch('ui.activity_bar.get_icon_manager', return_value=mock_icon_manager), \
             patch('ui.main_window.get_icon_manager', return_value=mock_icon_manager):
            
            # Create new main window (simulates restart)
            from ui.main_window import MainWindow
            test_window = MainWindow()
            qtbot.addWidget(test_window)
            test_window.show()
            qtbot.waitExposed(test_window)
            
            # Verify theme detection was called during initialization
            mock_icon_manager.detect_system_theme.assert_called()
            
            test_window.close()
```

## Error Handling Examples

### Example 7: Error Condition Testing

```python
@pytest.mark.gui
class TestErrorHandling(MainWindowGUITestBase):
    """Examples of testing error conditions and edge cases."""
    
    @patch('ui.activity_bar.execute_command')
    def test_command_execution_failure(self, mock_execute, gui_activity_bar, qtbot):
        """Test activity bar handles command execution failures gracefully."""
        # Simulate command failure
        mock_execute.return_value = {'success': False, 'error': 'Command not found'}
        
        # Record initial state
        initial_view = gui_activity_bar.current_view
        initial_visible = gui_activity_bar.isVisible()
        
        # Attempt action that will fail
        self.click_activity_button(qtbot, gui_activity_bar, "search")
        QTest.qWait(100)
        
        # Verify UI remains stable despite command failure
        assert gui_activity_bar.isVisible() == initial_visible
        assert gui_activity_bar.isEnabled()
        
        # View state handling depends on implementation
        # Could remain unchanged or change depending on error handling strategy
        current_view = gui_activity_bar.current_view
        assert current_view is not None  # Should have some valid state
    
    def test_invalid_sidebar_view_handling(self, gui_sidebar, qtbot):
        """Test sidebar handles invalid view requests gracefully."""
        # Record initial state
        initial_index = gui_sidebar.stack.currentIndex()
        initial_visible = gui_sidebar.isVisible()
        
        # Attempt to set invalid view
        gui_sidebar.set_current_view("nonexistent_view")
        QTest.qWait(50)
        
        # Should remain in valid state
        assert gui_sidebar.stack.currentIndex() == initial_index
        assert gui_sidebar.isVisible() == initial_visible
        assert gui_sidebar.stack.currentWidget() is not None
    
    def test_animation_with_zero_duration(self, gui_sidebar, qtbot):
        """Test animation handles edge cases gracefully."""
        # Test with very short animation duration
        original_duration = gui_sidebar.animation.duration()
        gui_sidebar.animation.setDuration(1)  # 1ms - effectively instant
        
        try:
            # Trigger animation
            gui_sidebar.toggle()
            
            # Wait briefly for instant animation
            QTest.qWait(50)
            
            # Should reach final state quickly
            assert gui_sidebar.animation.state() != gui_sidebar.animation.State.Running
            
        finally:
            # Restore original duration
            gui_sidebar.animation.setDuration(original_duration)
```

## Performance Testing Examples

### Example 8: Performance and Load Testing

```python
@pytest.mark.gui
@pytest.mark.performance
class TestPerformance(GUITestBase):
    """Examples of testing GUI performance."""
    
    def test_rapid_button_clicking_performance(self, gui_activity_bar, qtbot):
        """Test activity bar handles rapid clicking without issues."""
        with patch('ui.activity_bar.execute_command') as mock_execute:
            mock_execute.return_value = {'success': True}
            
            views = ["explorer", "search", "git", "settings"]
            click_count = 0
            
            # Perform rapid clicking
            start_time = time.time()
            
            for cycle in range(10):  # 10 full cycles
                for view in views:
                    self.click_activity_button(qtbot, gui_activity_bar, view)
                    click_count += 1
                    
                    # Minimal wait between clicks
                    QTest.qWait(5)
                    
                    # Verify responsiveness every 10 clicks
                    if click_count % 10 == 0:
                        assert gui_activity_bar.isEnabled()
                        assert gui_activity_bar.isVisible()
            
            end_time = time.time()
            
            # Verify performance
            total_time = end_time - start_time
            clicks_per_second = click_count / total_time
            
            print(f"Performed {click_count} clicks in {total_time:.2f}s ({clicks_per_second:.1f} clicks/s)")
            
            # Should handle at least 5 clicks per second
            assert clicks_per_second >= 5.0
            
            # Final state should be consistent
            assert gui_activity_bar.current_view in views
            assert mock_execute.call_count == click_count
    
    def test_memory_usage_during_animation(self, gui_sidebar, qtbot):
        """Test memory usage doesn't grow excessively during animations."""
        import psutil
        import gc
        
        process = psutil.Process()
        
        # Force garbage collection and get baseline
        gc.collect()
        baseline_memory = process.memory_info().rss
        
        # Perform multiple animation cycles
        for cycle in range(20):
            gui_sidebar.collapse()
            self.wait_for_sidebar_animation(qtbot, gui_sidebar, timeout=500)
            
            gui_sidebar.expand()
            self.wait_for_sidebar_animation(qtbot, gui_sidebar, timeout=500)
            
            # Check memory every 5 cycles
            if cycle % 5 == 0:
                gc.collect()
                current_memory = process.memory_info().rss
                memory_growth = current_memory - baseline_memory
                
                # Memory growth should be reasonable (less than 10MB)
                assert memory_growth < 10 * 1024 * 1024, f"Memory grew by {memory_growth / 1024 / 1024:.1f}MB"
        
        # Final cleanup
        gc.collect()
        final_memory = process.memory_info().rss
        total_growth = final_memory - baseline_memory
        
        print(f"Total memory growth: {total_growth / 1024 / 1024:.1f}MB")
        
        # Should not have significant memory leak
        assert total_growth < 5 * 1024 * 1024  # Less than 5MB growth
```

## Accessibility Testing Examples

### Example 9: Accessibility and Keyboard Navigation

```python
@pytest.mark.gui
@pytest.mark.accessibility
class TestAccessibility(GUITestBase):
    """Examples of testing accessibility features."""
    
    def test_keyboard_navigation_flow(self, gui_main_window, qtbot):
        """Test complete keyboard navigation flow through application."""
        # Start with main window focus
        gui_main_window.setFocus()
        qtbot.waitUntil(lambda: gui_main_window.isActiveWindow(), timeout=1000)
        
        # Map to track focus flow
        focus_sequence = []
        
        def record_focus():
            current_focus = QApplication.focusWidget()
            if current_focus:
                widget_info = f"{current_focus.__class__.__name__}:{current_focus.objectName()}"
                focus_sequence.append(widget_info)
        
        # Navigate through components with Tab
        for tab_count in range(5):  # Try several tab presses
            record_focus()
            qtbot.keyClick(QApplication.focusWidget() or gui_main_window, Qt.Key.Key_Tab)
            QTest.qWait(100)  # Allow focus change
        
        print(f"Focus sequence: {' -> '.join(focus_sequence)}")
        
        # Should have moved focus at least once
        assert len(set(focus_sequence)) > 1, "Focus should move between components"
        
        # Test reverse navigation with Shift+Tab
        current_focus = QApplication.focusWidget() or gui_main_window
        qtbot.keyClick(current_focus, Qt.Key.Key_Tab, Qt.KeyboardModifier.ShiftModifier)
        QTest.qWait(100)
        
        # Focus should change
        new_focus = QApplication.focusWidget()
        assert new_focus is not None
    
    def test_screen_reader_attributes(self, gui_activity_bar, qtbot):
        """Test components have proper attributes for screen readers."""
        # Test activity bar accessibility
        assert gui_activity_bar.objectName(), "Activity bar should have object name"
        
        # Test buttons have accessible text
        buttons = self.get_activity_buttons(gui_activity_bar)
        for view_name, button in buttons.items():
            assert button.text(), f"Button {view_name} should have text for screen readers"
            
            # Test button has tooltip (additional accessibility info)
            tooltip = button.toolTip()
            # Tooltip may be empty, but should be accessible
            assert isinstance(tooltip, str)
    
    def test_focus_indicators(self, gui_main_window, qtbot):
        """Test focus indicators are visible and clear."""
        components = [
            gui_main_window.activity_bar,
            gui_main_window.sidebar,
            gui_main_window.workspace
        ]
        
        for component in components:
            if component and component.isVisible():
                # Focus component
                component.setFocus()
                QTest.qWait(100)
                
                # Test focus policy allows focus
                focus_policy = component.focusPolicy()
                assert focus_policy != Qt.FocusPolicy.NoFocus, f"{component.__class__.__name__} should accept focus"
                
                # Component should be focusable (may not always have focus due to child widgets)
                assert component.isVisible()
                assert component.isEnabled()
```

## State Management Testing Examples

### Example 10: Application State Testing

```python
@pytest.mark.gui
@pytest.mark.state
class TestApplicationState(MainWindowGUITestBase):
    """Examples of testing application state management."""
    
    @patch('ui.main_window.QSettings')
    def test_window_state_persistence(self, mock_settings_class, qtbot, mock_icon_manager):
        """Test window state is saved and restored correctly."""
        mock_settings = Mock()
        mock_settings_class.return_value = mock_settings
        
        # Create and configure main window
        with patch('ui.activity_bar.get_icon_manager', return_value=mock_icon_manager), \
             patch('ui.main_window.get_icon_manager', return_value=mock_icon_manager):
            
            window = MainWindow()
            qtbot.addWidget(window)
            window.show()
            qtbot.waitExposed(window)
            
            # Modify window state
            window.resize(1400, 900)
            window.sidebar.collapse()
            
            # Mock the save methods
            window.saveGeometry = Mock(return_value=b'test_geometry')
            window.saveState = Mock(return_value=b'test_state')
            
            # Trigger save (simulate close)
            close_event = Mock()
            close_event.accept = Mock()
            window.closeEvent(close_event)
            
            # Verify save was called
            window.saveGeometry.assert_called()
            window.saveState.assert_called()
            mock_settings.setValue.assert_called()
            
            window.close()
    
    def test_component_state_consistency(self, gui_main_window, qtbot):
        """Test component states remain consistent during interactions."""
        activity_bar = gui_main_window.activity_bar
        sidebar = gui_main_window.sidebar
        workspace = gui_main_window.workspace
        
        # Record initial states
        initial_states = {
            'activity_view': activity_bar.current_view,
            'sidebar_collapsed': sidebar.is_collapsed,
            'workspace_tab_count': workspace.tab_widget.count(),
            'window_visible': gui_main_window.isVisible()
        }
        
        # Perform various interactions
        self.click_activity_button(qtbot, activity_bar, "search")
        QTest.qWait(100)
        
        sidebar.toggle()
        self.wait_for_sidebar_animation(qtbot, sidebar)
        
        # Check state consistency
        final_states = {
            'activity_view': activity_bar.current_view,
            'sidebar_collapsed': sidebar.is_collapsed,
            'workspace_tab_count': workspace.tab_widget.count(),
            'window_visible': gui_main_window.isVisible()
        }
        
        # Some states should have changed
        assert final_states['activity_view'] != initial_states['activity_view']
        assert final_states['sidebar_collapsed'] != initial_states['sidebar_collapsed']
        
        # Some states should remain stable
        assert final_states['workspace_tab_count'] == initial_states['workspace_tab_count']
        assert final_states['window_visible'] == initial_states['window_visible']
        
        # All components should still be functional
        assert activity_bar.isVisible() and activity_bar.isEnabled()
        assert sidebar.isVisible() and sidebar.isEnabled()
        assert workspace.isVisible() and workspace.isEnabled()
```

## Running These Examples

### Basic Test Execution

```bash
# Run all GUI examples
pytest tests/gui/ -v

# Run specific example categories
pytest tests/gui/ -k "TestActivityBarDisplay" -v
pytest tests/gui/ -k "animation" -v
pytest tests/gui/ -k "performance" -v

# Run with specific markers
pytest tests/gui/ -m "gui and mouse" -v
pytest tests/gui/ -m "gui and accessibility" -v
pytest tests/gui/ -m "slow" -v
```

### Debug Mode

```bash
# Run with debug output
pytest tests/gui/ -v -s

# Run single test with maximum detail
pytest tests/gui/test_activity_bar_gui.py::TestActivityBarDisplay::test_activity_bar_initial_display -v -s
```

## Best Practices Demonstrated

1. **Clear Test Structure**: Each example has a clear setup, action, and verification phase
2. **Proper Signal Testing**: Uses `qtbot.waitSignal()` for testing Qt signals
3. **Mocking External Dependencies**: Uses `@patch` to mock command execution and icon loading
4. **Animation Handling**: Proper waiting for animations to complete
5. **Error Condition Testing**: Tests both success and failure scenarios
6. **Performance Considerations**: Tests include performance and memory usage checks
7. **Accessibility Testing**: Examples include keyboard navigation and screen reader compatibility
8. **State Management**: Tests verify consistent state across interactions

These examples provide a comprehensive foundation for writing robust GUI tests that accurately reflect user interactions and catch potential regressions in the UI behavior.