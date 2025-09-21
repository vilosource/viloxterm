"""Tests for workspace model classes."""

import pytest
from viloapp.models.workspace_models import (
    WidgetType,
    PaneState,
    SplitConfiguration,
    TabState,
    WorkspaceState,
)
from viloapp.models.base import OperationResult


class TestWidgetType:
    """Test cases for WidgetType enum."""

    def test_widget_types_available(self):
        """Test that all expected widget types are available."""
        assert WidgetType.TERMINAL.value == "terminal"
        assert WidgetType.EDITOR.value == "editor"
        assert WidgetType.BROWSER.value == "browser"
        assert WidgetType.SETTINGS.value == "settings"
        assert WidgetType.EMPTY.value == "empty"

    def test_widget_type_enumeration(self):
        """Test that widget types can be enumerated."""
        types = list(WidgetType)
        assert len(types) == 5
        assert WidgetType.TERMINAL in types
        assert WidgetType.EDITOR in types


class TestPaneState:
    """Test cases for PaneState dataclass."""

    def test_pane_state_creation(self):
        """Test creation of PaneState."""
        state = {"content": "Hello World"}
        pane = PaneState(
            id="pane_1",
            widget_type=WidgetType.EDITOR,
            widget_state=state,
            is_active=True
        )

        assert pane.id == "pane_1"
        assert pane.widget_type == WidgetType.EDITOR
        assert pane.widget_state == state
        assert pane.is_active is True

    def test_pane_state_with_empty_state(self):
        """Test PaneState with empty widget state."""
        pane = PaneState(
            id="pane_2",
            widget_type=WidgetType.TERMINAL,
            widget_state={},
            is_active=False
        )

        assert pane.widget_state == {}
        assert pane.is_active is False

    def test_pane_state_post_init_none_state(self):
        """Test that None widget_state is converted to empty dict."""
        pane = PaneState(
            id="pane_3",
            widget_type=WidgetType.EMPTY,
            widget_state=None,
            is_active=False
        )

        assert pane.widget_state == {}


class TestSplitConfiguration:
    """Test cases for SplitConfiguration."""

    def test_horizontal_split_creation(self):
        """Test creation of horizontal split configuration."""
        config = SplitConfiguration(
            orientation="horizontal",
            ratio=0.6,
            left_pane_id="left_pane",
            right_pane_id="right_pane"
        )

        assert config.orientation == "horizontal"
        assert config.ratio == 0.6
        assert config.left_pane_id == "left_pane"
        assert config.right_pane_id == "right_pane"

    def test_vertical_split_creation(self):
        """Test creation of vertical split configuration."""
        config = SplitConfiguration(orientation="vertical")

        assert config.orientation == "vertical"
        assert config.ratio == 0.5  # Default ratio
        assert config.left_pane_id is None
        assert config.right_pane_id is None

    def test_invalid_orientation_raises_error(self):
        """Test that invalid orientation raises ValueError."""
        with pytest.raises(ValueError, match="Invalid orientation"):
            SplitConfiguration(orientation="diagonal")

    def test_invalid_ratio_raises_error(self):
        """Test that invalid ratio raises ValueError."""
        with pytest.raises(ValueError, match="Invalid ratio"):
            SplitConfiguration(orientation="horizontal", ratio=1.5)

        with pytest.raises(ValueError, match="Invalid ratio"):
            SplitConfiguration(orientation="horizontal", ratio=0.05)

    def test_boundary_ratios(self):
        """Test boundary ratio values."""
        # Should work
        config1 = SplitConfiguration(orientation="horizontal", ratio=0.1)
        config2 = SplitConfiguration(orientation="horizontal", ratio=0.9)

        assert config1.ratio == 0.1
        assert config2.ratio == 0.9


class TestTabState:
    """Test cases for TabState dataclass."""

    def test_tab_state_creation(self):
        """Test creation of TabState."""
        panes = {
            "pane_1": PaneState("pane_1", WidgetType.EDITOR, {}, True)
        }
        pane_tree = {"root": "pane_1"}

        tab = TabState(
            id="tab_1",
            name="Main Tab",
            pane_tree=pane_tree,
            active_pane_id="pane_1",
            panes=panes
        )

        assert tab.id == "tab_1"
        assert tab.name == "Main Tab"
        assert tab.pane_tree == pane_tree
        assert tab.active_pane_id == "pane_1"
        assert tab.panes == panes

    def test_tab_state_with_defaults(self):
        """Test TabState with default values."""
        tab = TabState(
            id="tab_2",
            name="Empty Tab",
            pane_tree={},
            active_pane_id="none"
        )

        assert tab.panes == {}  # Default factory

    def test_tab_state_post_init_none_values(self):
        """Test that None values are handled in post_init."""
        tab = TabState(
            id="tab_3",
            name="Test Tab",
            pane_tree=None,
            active_pane_id="pane_1",
            panes=None
        )

        assert tab.pane_tree == {}
        assert tab.panes == {}


class TestWorkspaceState:
    """Test cases for WorkspaceState dataclass."""

    def test_workspace_state_creation(self):
        """Test creation of WorkspaceState."""
        tab1 = TabState("tab_1", "Tab 1", {}, "pane_1")
        tab2 = TabState("tab_2", "Tab 2", {}, "pane_2")

        workspace = WorkspaceState(
            tabs=[tab1, tab2],
            active_tab_index=1
        )

        assert len(workspace.tabs) == 2
        assert workspace.active_tab_index == 1

    def test_workspace_state_with_defaults(self):
        """Test WorkspaceState with default values."""
        workspace = WorkspaceState()

        assert workspace.tabs == []
        assert workspace.active_tab_index == 0

    def test_can_close_tab_last_tab(self):
        """Test that last tab cannot be closed."""
        tab = TabState("tab_1", "Only Tab", {}, "pane_1")
        workspace = WorkspaceState(tabs=[tab])

        result = workspace.can_close_tab(0)

        assert result.success is False
        assert "last remaining tab" in result.error

    def test_can_close_tab_multiple_tabs(self):
        """Test that tab can be closed when multiple tabs exist."""
        tab1 = TabState("tab_1", "Tab 1", {}, "pane_1")
        tab2 = TabState("tab_2", "Tab 2", {}, "pane_2")
        workspace = WorkspaceState(tabs=[tab1, tab2])

        result = workspace.can_close_tab(0)

        assert result.success is True
        assert result.error is None

    def test_can_close_tab_invalid_index(self):
        """Test closing tab with invalid index."""
        tab = TabState("tab_1", "Tab 1", {}, "pane_1")
        workspace = WorkspaceState(tabs=[tab])

        result = workspace.can_close_tab(5)

        assert result.success is False
        assert "Invalid tab index" in result.error

    def test_can_split_pane_no_tabs(self):
        """Test splitting pane when no tabs exist."""
        workspace = WorkspaceState()

        result = workspace.can_split_pane("pane_1")

        assert result.success is False
        assert "No tabs available" in result.error

    def test_can_split_pane_pane_not_found(self):
        """Test splitting non-existent pane."""
        panes = {"pane_1": PaneState("pane_1", WidgetType.EDITOR, {}, True)}
        tab = TabState("tab_1", "Tab 1", {}, "pane_1", panes)
        workspace = WorkspaceState(tabs=[tab])

        result = workspace.can_split_pane("nonexistent_pane")

        assert result.success is False
        assert "Pane not found" in result.error

    def test_can_split_pane_success(self):
        """Test successful pane split validation."""
        panes = {"pane_1": PaneState("pane_1", WidgetType.EDITOR, {}, True)}
        tab = TabState("tab_1", "Tab 1", {}, "pane_1", panes)
        workspace = WorkspaceState(tabs=[tab])

        result = workspace.can_split_pane("pane_1")

        assert result.success is True

    def test_get_active_tab_empty_workspace(self):
        """Test getting active tab from empty workspace."""
        workspace = WorkspaceState()

        active_tab = workspace.get_active_tab()

        assert active_tab is None

    def test_get_active_tab_valid_index(self):
        """Test getting active tab with valid index."""
        tab1 = TabState("tab_1", "Tab 1", {}, "pane_1")
        tab2 = TabState("tab_2", "Tab 2", {}, "pane_2")
        workspace = WorkspaceState(tabs=[tab1, tab2], active_tab_index=1)

        active_tab = workspace.get_active_tab()

        assert active_tab == tab2

    def test_get_active_tab_invalid_index(self):
        """Test getting active tab with invalid index."""
        tab = TabState("tab_1", "Tab 1", {}, "pane_1")
        workspace = WorkspaceState(tabs=[tab], active_tab_index=5)

        active_tab = workspace.get_active_tab()

        assert active_tab is None

    def test_get_active_pane_no_active_tab(self):
        """Test getting active pane when no active tab."""
        workspace = WorkspaceState()

        active_pane = workspace.get_active_pane()

        assert active_pane is None

    def test_get_active_pane_success(self):
        """Test getting active pane successfully."""
        pane = PaneState("pane_1", WidgetType.EDITOR, {}, True)
        panes = {"pane_1": pane}
        tab = TabState("tab_1", "Tab 1", {}, "pane_1", panes)
        workspace = WorkspaceState(tabs=[tab])

        active_pane = workspace.get_active_pane()

        assert active_pane == pane

    def test_get_active_pane_pane_not_found(self):
        """Test getting active pane when pane doesn't exist."""
        tab = TabState("tab_1", "Tab 1", {}, "nonexistent_pane", {})
        workspace = WorkspaceState(tabs=[tab])

        active_pane = workspace.get_active_pane()

        assert active_pane is None