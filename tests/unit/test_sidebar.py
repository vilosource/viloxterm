"""Unit tests for the sidebar component."""

from PySide6.QtCore import QPropertyAnimation

from ui.sidebar import Sidebar


def test_sidebar_initial_state(qtbot):
    """Test sidebar initial state."""
    sidebar = Sidebar()
    qtbot.addWidget(sidebar)

    assert not sidebar.is_collapsed
    assert sidebar.width() > 0
    assert sidebar.expanded_width == 250


def test_sidebar_collapse(qtbot):
    """Test sidebar collapse animation."""
    sidebar = Sidebar()
    qtbot.addWidget(sidebar)

    sidebar.width()
    sidebar.collapse()

    # Wait for animation to complete
    qtbot.waitUntil(
        lambda: sidebar.animation.state() == QPropertyAnimation.State.Stopped,
        timeout=1000,
    )
    assert sidebar.is_collapsed
    assert sidebar.maximumWidth() == 0


def test_sidebar_expand(qtbot):
    """Test sidebar expand animation."""
    sidebar = Sidebar()
    qtbot.addWidget(sidebar)

    # Sidebar starts expanded, so verify initial state
    assert not sidebar.is_collapsed
    assert sidebar.width() > 0

    # First collapse it
    sidebar.collapse()
    # Wait for animation to finish
    qtbot.waitUntil(
        lambda: sidebar.animation.state() == QPropertyAnimation.State.Stopped,
        timeout=1000,
    )
    assert sidebar.is_collapsed
    assert sidebar.maximumWidth() == 0

    # Then expand it
    sidebar.expand()
    # Wait for animation to finish
    qtbot.waitUntil(
        lambda: sidebar.animation.state() == QPropertyAnimation.State.Stopped,
        timeout=1000,
    )
    assert not sidebar.is_collapsed
    assert sidebar.maximumWidth() == sidebar.expanded_width


def test_sidebar_toggle(qtbot):
    """Test sidebar toggle functionality."""
    sidebar = Sidebar()
    qtbot.addWidget(sidebar)

    initial_state = sidebar.is_collapsed
    sidebar.toggle()
    assert sidebar.is_collapsed != initial_state

    sidebar.toggle()
    assert sidebar.is_collapsed == initial_state


def test_sidebar_view_switching(qtbot):
    """Test switching between sidebar views."""
    sidebar = Sidebar()
    qtbot.addWidget(sidebar)

    # Test switching to each view
    views = ["explorer", "search", "git", "settings"]
    for view in views:
        sidebar.set_current_view(view)
        expected_index = sidebar.view_indices[view]
        assert sidebar.stack.currentIndex() == expected_index
