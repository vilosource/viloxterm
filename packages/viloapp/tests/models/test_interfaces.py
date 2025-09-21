"""Tests for interface contracts."""

from abc import ABC

import pytest

from viloapp.interfaces.model_interfaces import (
    IModelObserver,
    IPaneModel,
    ITabModel,
    IWorkspaceModel,
)


class TestInterfaceContracts:
    """Test that interfaces are properly defined as abstract base classes."""

    def test_iworkspace_model_is_abstract(self):
        """Test that IWorkspaceModel is an abstract base class."""
        assert issubclass(IWorkspaceModel, ABC)

        # Should not be able to instantiate directly
        with pytest.raises(TypeError):
            IWorkspaceModel()

    def test_itab_model_is_abstract(self):
        """Test that ITabModel is an abstract base class."""
        assert issubclass(ITabModel, ABC)

        with pytest.raises(TypeError):
            ITabModel()

    def test_ipane_model_is_abstract(self):
        """Test that IPaneModel is an abstract base class."""
        assert issubclass(IPaneModel, ABC)

        with pytest.raises(TypeError):
            IPaneModel()

    def test_imodel_observer_is_abstract(self):
        """Test that IModelObserver is an abstract base class."""
        assert issubclass(IModelObserver, ABC)

        with pytest.raises(TypeError):
            IModelObserver()

    def test_iworkspace_model_required_methods(self):
        """Test that IWorkspaceModel has all required abstract methods."""
        required_methods = [
            "get_state",
            "add_observer",
            "remove_observer",
            "add_tab",
            "close_tab",
            "rename_tab",
            "duplicate_tab",
            "set_active_tab",
            "split_pane",
            "close_pane",
            "focus_pane",
            "update_widget_state",
            "get_tab_by_id",
            "get_pane_by_id",
            "get_active_pane",
        ]

        for method_name in required_methods:
            assert hasattr(IWorkspaceModel, method_name)
            method = getattr(IWorkspaceModel, method_name)
            assert getattr(
                method, "__isabstractmethod__", False
            ), f"{method_name} should be abstract"

    def test_itab_model_required_methods(self):
        """Test that ITabModel has all required abstract methods."""
        required_methods = [
            "get_state",
            "split_pane",
            "close_pane",
            "set_active_pane",
        ]

        for method_name in required_methods:
            assert hasattr(ITabModel, method_name)
            method = getattr(ITabModel, method_name)
            assert getattr(
                method, "__isabstractmethod__", False
            ), f"{method_name} should be abstract"

    def test_ipane_model_required_methods(self):
        """Test that IPaneModel has all required abstract methods."""
        required_methods = [
            "get_state",
            "update_widget_state",
            "set_widget_type",
        ]

        for method_name in required_methods:
            assert hasattr(IPaneModel, method_name)
            method = getattr(IPaneModel, method_name)
            assert getattr(
                method, "__isabstractmethod__", False
            ), f"{method_name} should be abstract"

    def test_imodel_observer_required_methods(self):
        """Test that IModelObserver has all required abstract methods."""
        required_methods = [
            "on_model_changed",
        ]

        for method_name in required_methods:
            assert hasattr(IModelObserver, method_name)
            method = getattr(IModelObserver, method_name)
            assert getattr(
                method, "__isabstractmethod__", False
            ), f"{method_name} should be abstract"


class MockWorkspaceModel(IWorkspaceModel):
    """Mock implementation for testing interface enforcement."""

    def get_state(self):
        return None

    def add_observer(self, callback):
        pass

    def remove_observer(self, callback):
        pass

    def add_tab(self, name, widget_type):
        pass

    def close_tab(self, index):
        pass

    def rename_tab(self, index, new_name):
        pass

    def duplicate_tab(self, index):
        pass

    def set_active_tab(self, index):
        pass

    def split_pane(self, request):
        pass

    def close_pane(self, request):
        pass

    def focus_pane(self, request):
        pass

    def update_widget_state(self, request):
        pass

    def get_tab_by_id(self, tab_id):
        pass

    def get_pane_by_id(self, pane_id):
        pass

    def get_active_pane(self):
        pass


class IncompleteWorkspaceModel(IWorkspaceModel):
    """Incomplete implementation to test abstract method enforcement."""

    def get_state(self):
        return None

    # Missing other required methods


class TestInterfaceImplementation:
    """Test that interface implementations work correctly."""

    def test_complete_implementation_works(self):
        """Test that complete implementation can be instantiated."""
        # Should not raise any errors
        model = MockWorkspaceModel()
        assert isinstance(model, IWorkspaceModel)

    def test_incomplete_implementation_fails(self):
        """Test that incomplete implementation cannot be instantiated."""
        with pytest.raises(TypeError):
            IncompleteWorkspaceModel()

    def test_interface_inheritance(self):
        """Test that implementations properly inherit from interfaces."""
        model = MockWorkspaceModel()

        assert isinstance(model, IWorkspaceModel)
        assert hasattr(model, "get_state")
        assert hasattr(model, "add_tab")
        assert hasattr(model, "split_pane")


class MockModelObserver(IModelObserver):
    """Mock observer for testing."""

    def __init__(self):
        self.events_received = []

    def on_model_changed(self, event_type, data):
        self.events_received.append((event_type, data))


class TestObserverInterface:
    """Test the observer interface works correctly."""

    def test_observer_implementation(self):
        """Test that observer implementation works."""
        observer = MockModelObserver()

        # Simulate model change notification
        observer.on_model_changed("tab_added", {"tab_id": "123"})
        observer.on_model_changed("pane_split", {"pane_id": "456"})

        assert len(observer.events_received) == 2
        assert observer.events_received[0] == ("tab_added", {"tab_id": "123"})
        assert observer.events_received[1] == ("pane_split", {"pane_id": "456"})
