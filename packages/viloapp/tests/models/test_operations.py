"""Tests for operation DTO classes."""

import pytest

from viloapp.models.operations import (
    ClosePaneRequest,
    PaneFocusRequest,
    SplitPaneRequest,
    SplitPaneResponse,
    TabOperationRequest,
    TabOperationResponse,
    WidgetStateUpdateRequest,
)
from viloapp.models.workspace_models import WidgetType


class TestSplitPaneRequest:
    """Test cases for SplitPaneRequest."""

    def test_split_pane_request_creation(self):
        """Test creation of SplitPaneRequest."""
        request = SplitPaneRequest(
            pane_id="pane_1",
            orientation="horizontal",
            ratio=0.7,
            new_widget_type=WidgetType.TERMINAL,
        )

        assert request.pane_id == "pane_1"
        assert request.orientation == "horizontal"
        assert request.ratio == 0.7
        assert request.new_widget_type == WidgetType.TERMINAL

    def test_split_pane_request_defaults(self):
        """Test SplitPaneRequest with default values."""
        request = SplitPaneRequest(pane_id="pane_2", orientation="vertical")

        assert request.ratio == 0.5  # Default
        assert request.new_widget_type == WidgetType.EMPTY  # Default

    def test_invalid_orientation_raises_error(self):
        """Test that invalid orientation raises ValueError."""
        with pytest.raises(ValueError, match="Invalid orientation"):
            SplitPaneRequest(pane_id="pane_1", orientation="diagonal")

    def test_invalid_ratio_raises_error(self):
        """Test that invalid ratio raises ValueError."""
        with pytest.raises(ValueError, match="Invalid ratio"):
            SplitPaneRequest(pane_id="pane_1", orientation="horizontal", ratio=1.5)

        with pytest.raises(ValueError, match="Invalid ratio"):
            SplitPaneRequest(pane_id="pane_1", orientation="horizontal", ratio=0.05)

    def test_boundary_ratios(self):
        """Test boundary ratio values."""
        request1 = SplitPaneRequest(pane_id="pane_1", orientation="horizontal", ratio=0.1)
        request2 = SplitPaneRequest(pane_id="pane_1", orientation="horizontal", ratio=0.9)

        assert request1.ratio == 0.1
        assert request2.ratio == 0.9


class TestClosePaneRequest:
    """Test cases for ClosePaneRequest."""

    def test_close_pane_request_creation(self):
        """Test creation of ClosePaneRequest."""
        request = ClosePaneRequest(pane_id="pane_1", force=True)

        assert request.pane_id == "pane_1"
        assert request.force is True

    def test_close_pane_request_defaults(self):
        """Test ClosePaneRequest with default values."""
        request = ClosePaneRequest(pane_id="pane_2")

        assert request.force is False  # Default


class TestTabOperationRequest:
    """Test cases for TabOperationRequest."""

    def test_add_tab_request(self):
        """Test creation of add tab request."""
        request = TabOperationRequest(
            operation="add", tab_name="New Tab", widget_type=WidgetType.EDITOR
        )

        assert request.operation == "add"
        assert request.tab_name == "New Tab"
        assert request.widget_type == WidgetType.EDITOR

    def test_close_tab_request(self):
        """Test creation of close tab request."""
        request = TabOperationRequest(operation="close", tab_index=2)

        assert request.operation == "close"
        assert request.tab_index == 2

    def test_rename_tab_request(self):
        """Test creation of rename tab request."""
        request = TabOperationRequest(operation="rename", tab_index=1, tab_name="Renamed Tab")

        assert request.operation == "rename"
        assert request.tab_index == 1
        assert request.tab_name == "Renamed Tab"

    def test_duplicate_tab_request(self):
        """Test creation of duplicate tab request."""
        request = TabOperationRequest(operation="duplicate", tab_index=0)

        assert request.operation == "duplicate"
        assert request.tab_index == 0

    def test_tab_operation_defaults(self):
        """Test TabOperationRequest with default values."""
        request = TabOperationRequest(operation="add")

        assert request.tab_index is None
        assert request.tab_name is None
        assert request.tab_type is None
        assert request.widget_type == WidgetType.EMPTY

    def test_invalid_operation_raises_error(self):
        """Test that invalid operation raises ValueError."""
        with pytest.raises(ValueError, match="Invalid operation"):
            TabOperationRequest(operation="invalid_op")

    def test_close_without_index_raises_error(self):
        """Test that close operation without index raises error."""
        with pytest.raises(ValueError, match="tab_index is required for close"):
            TabOperationRequest(operation="close")

    def test_rename_without_index_or_name_raises_error(self):
        """Test that rename operation without required fields raises error."""
        with pytest.raises(ValueError, match="tab_index and tab_name are required for rename"):
            TabOperationRequest(operation="rename")

        with pytest.raises(ValueError, match="tab_index and tab_name are required for rename"):
            TabOperationRequest(operation="rename", tab_index=1)

        with pytest.raises(ValueError, match="tab_index and tab_name are required for rename"):
            TabOperationRequest(operation="rename", tab_name="New Name")

    def test_duplicate_without_index_raises_error(self):
        """Test that duplicate operation without index raises error."""
        with pytest.raises(ValueError, match="tab_index is required for duplicate"):
            TabOperationRequest(operation="duplicate")


class TestPaneFocusRequest:
    """Test cases for PaneFocusRequest."""

    def test_pane_focus_request_creation(self):
        """Test creation of PaneFocusRequest."""
        request = PaneFocusRequest(pane_id="pane_1", tab_index=2)

        assert request.pane_id == "pane_1"
        assert request.tab_index == 2

    def test_pane_focus_request_defaults(self):
        """Test PaneFocusRequest with default values."""
        request = PaneFocusRequest(pane_id="pane_2")

        assert request.tab_index is None  # Default


class TestWidgetStateUpdateRequest:
    """Test cases for WidgetStateUpdateRequest."""

    def test_widget_state_update_creation(self):
        """Test creation of WidgetStateUpdateRequest."""
        state_updates = {"theme": "dark", "font_size": 12}
        request = WidgetStateUpdateRequest(
            pane_id="pane_1", state_updates=state_updates, merge=False
        )

        assert request.pane_id == "pane_1"
        assert request.state_updates == state_updates
        assert request.merge is False

    def test_widget_state_update_defaults(self):
        """Test WidgetStateUpdateRequest with default values."""
        state_updates = {"setting": "value"}
        request = WidgetStateUpdateRequest(pane_id="pane_2", state_updates=state_updates)

        assert request.merge is True  # Default

    def test_empty_state_updates_raises_error(self):
        """Test that empty state_updates raises ValueError."""
        with pytest.raises(ValueError, match="state_updates cannot be empty"):
            WidgetStateUpdateRequest(pane_id="pane_1", state_updates={})


class TestSplitPaneResponse:
    """Test cases for SplitPaneResponse."""

    def test_split_pane_response_creation(self):
        """Test creation of SplitPaneResponse."""
        split_config = {"orientation": "horizontal", "ratio": 0.6}
        response = SplitPaneResponse(
            original_pane_id="pane_1", new_pane_id="pane_2", split_config=split_config
        )

        assert response.original_pane_id == "pane_1"
        assert response.new_pane_id == "pane_2"
        assert response.split_config == split_config


class TestTabOperationResponse:
    """Test cases for TabOperationResponse."""

    def test_tab_operation_response_creation(self):
        """Test creation of TabOperationResponse."""
        operation_data = {"previous_name": "Old Tab"}
        response = TabOperationResponse(tab_id="tab_1", tab_index=2, operation_data=operation_data)

        assert response.tab_id == "tab_1"
        assert response.tab_index == 2
        assert response.operation_data == operation_data

    def test_tab_operation_response_defaults(self):
        """Test TabOperationResponse with default values."""
        response = TabOperationResponse(tab_id="tab_2", tab_index=0)

        assert response.operation_data is None  # Default
