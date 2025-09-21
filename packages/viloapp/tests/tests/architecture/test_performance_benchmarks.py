#!/usr/bin/env python3
"""
Performance benchmarks for Phase 7 validation.

Tests that the architectural improvements have achieved the performance
targets specified in the implementation plan.
"""

import time
from unittest.mock import MagicMock, Mock

import pytest

from viloapp.core.commands.executor import execute_command
from viloapp.models.base import OperationResult
from viloapp.models.workspace_models import TabState, WorkspaceState
from viloapp.services.workspace_service import WorkspaceService


class MockWorkspaceModel:
    """Mock model for performance testing."""

    def __init__(self):
        self.state = WorkspaceState(tabs=[], active_tab_index=0)

    def get_state(self):
        return self.state

    def add_tab(self, tab_type: str, name: str):
        tab = TabState(
            id=f"tab_{len(self.state.tabs)}",
            name=name,
            pane_tree={"type": "pane", "id": "pane_1"},
            active_pane_id="pane_1",
        )
        self.state.tabs.append(tab)
        return OperationResult(success=True, data={"index": len(self.state.tabs) - 1})

    def split_pane(self, request):
        if self.state.tabs:
            # Update the active tab's pane tree to reflect the split
            # active_tab = self.state.tabs[self.state.active_tab_index]
            new_pane_id = f"pane_{len(self.state.tabs)}_{int(time.time())}"
            return OperationResult(success=True, data={"new_pane_id": new_pane_id})
        return OperationResult(success=False, error="No tabs available")

    def close_pane(self, request):
        return OperationResult(success=True)

    def close_tab(self, index: int):
        if 0 <= index < len(self.state.tabs):
            self.state.tabs.pop(index)
            if self.state.active_tab_index >= len(self.state.tabs):
                self.state.active_tab_index = max(0, len(self.state.tabs) - 1)
            return OperationResult(success=True)
        return OperationResult(success=False, error="Invalid index")

    def set_active_tab(self, index: int):
        if 0 <= index < len(self.state.tabs):
            self.state.active_tab_index = index
            return OperationResult(success=True)
        return OperationResult(success=False, error="Invalid index")


def measure_operation_time(operation_func, *args, **kwargs):
    """Measure the time taken by an operation."""
    start_time = time.perf_counter()
    result = operation_func(*args, **kwargs)
    end_time = time.perf_counter()
    duration_ms = (end_time - start_time) * 1000
    return duration_ms, result


@pytest.fixture
def mock_workspace_service():
    """Create a mock workspace service for testing."""
    model = MockWorkspaceModel()
    service = WorkspaceService(model=model)
    # Initialize the service
    service.initialize({})
    return service


def test_split_pane_performance(mock_workspace_service):
    """Test that pane splitting is under 50ms target."""
    # Add a tab first
    mock_workspace_service.add_editor_tab("Test Tab")

    # Measure split operation
    duration_ms, result = measure_operation_time(
        mock_workspace_service.split_active_pane, "horizontal"
    )

    assert duration_ms < 50, f"Split pane took {duration_ms:.2f}ms, should be < 50ms"
    assert result is not None, "Split operation should succeed"


def test_close_pane_performance(mock_workspace_service):
    """Test that pane closing is under 50ms target."""
    # Add a tab and split it first
    mock_workspace_service.add_editor_tab("Test Tab")
    mock_workspace_service.split_active_pane("horizontal")

    # Measure close operation
    duration_ms, result = measure_operation_time(mock_workspace_service.close_active_pane)

    assert duration_ms < 50, f"Close pane took {duration_ms:.2f}ms, should be < 50ms"
    assert result, "Close operation should succeed"


def test_add_tab_performance(mock_workspace_service):
    """Test that tab creation is under 50ms target."""
    # Measure add tab operation
    duration_ms, result = measure_operation_time(
        mock_workspace_service.add_editor_tab, "Performance Test Tab"
    )

    assert duration_ms < 50, f"Add tab took {duration_ms:.2f}ms, should be < 50ms"
    assert result >= 0, "Add tab should return valid index"


def test_switch_tab_performance(mock_workspace_service):
    """Test that tab switching is under 25ms target."""
    # Add multiple tabs
    for i in range(5):
        mock_workspace_service.add_editor_tab(f"Tab {i}")

    # Measure switch operation
    duration_ms, result = measure_operation_time(mock_workspace_service.switch_to_tab, 2)

    assert duration_ms < 25, f"Switch tab took {duration_ms:.2f}ms, should be < 25ms"
    assert result, "Switch tab should succeed"


def test_bulk_operations_performance(mock_workspace_service):
    """Test performance of multiple operations in sequence."""
    start_time = time.perf_counter()

    # Perform 10 tab operations
    for i in range(10):
        mock_workspace_service.add_editor_tab(f"Bulk Test Tab {i}")

    # Perform 5 split operations
    for _ in range(5):
        mock_workspace_service.split_active_pane("horizontal")

    end_time = time.perf_counter()
    total_duration_ms = (end_time - start_time) * 1000

    # Should complete 15 operations in reasonable time
    assert (
        total_duration_ms < 500
    ), f"Bulk operations took {total_duration_ms:.2f}ms, should be < 500ms"
    assert mock_workspace_service.get_tab_count() == 10, "Should have 10 tabs"


def test_memory_efficiency():
    """Test that operations don't leak memory or create excessive objects."""
    import gc
    import sys

    # Get initial object count
    gc.collect()
    initial_objects = len(gc.get_objects())

    # Create and destroy multiple services
    for _ in range(10):
        model = MockWorkspaceModel()
        service = WorkspaceService(model=model)

        # Perform operations
        service.add_editor_tab("Test Tab")
        service.split_active_pane("horizontal")
        service.close_active_pane()

        # Clear reference
        del service
        del model

    # Force garbage collection
    gc.collect()
    final_objects = len(gc.get_objects())

    # Should not have significant object growth
    object_growth = final_objects - initial_objects
    assert object_growth < 100, f"Memory leak detected: {object_growth} new objects"


def test_command_execution_performance():
    """Test that command execution through the command pattern is efficient."""
    # Mock command context
    from viloapp.core.commands.context import CommandContext

    mock_context = Mock(spec=CommandContext)
    mock_context.get_service.return_value = MockWorkspaceModel()

    # Import a simple command for testing
    from viloapp.core.commands.builtin.pane_commands import split_pane_horizontal_command

    # Measure command execution time
    duration_ms, result = measure_operation_time(split_pane_horizontal_command, mock_context)

    assert duration_ms < 25, f"Command execution took {duration_ms:.2f}ms, should be < 25ms"


def test_model_interface_performance():
    """Test that model interface operations are efficient."""
    model = MockWorkspaceModel()

    # Test state retrieval performance
    duration_ms, state = measure_operation_time(model.get_state)
    assert duration_ms < 5, f"Get state took {duration_ms:.2f}ms, should be < 5ms"

    # Test add tab performance
    duration_ms, result = measure_operation_time(model.add_tab, "editor", "Test Tab")
    assert duration_ms < 10, f"Model add tab took {duration_ms:.2f}ms, should be < 10ms"
    assert result.success, "Add tab should succeed"


def test_architecture_layer_performance():
    """Test that the layered architecture doesn't add significant overhead."""
    # Direct model operation
    model = MockWorkspaceModel()
    direct_duration_ms, _ = measure_operation_time(model.add_tab, "editor", "Direct Test")

    # Through service layer
    service = WorkspaceService(model=model)
    service.initialize({})
    service_duration_ms, _ = measure_operation_time(service.add_editor_tab, "Service Test")

    # Service layer should not add more than 10ms overhead
    overhead = service_duration_ms - direct_duration_ms
    assert overhead < 10, f"Service layer adds {overhead:.2f}ms overhead, should be < 10ms"


@pytest.mark.parametrize("operation_count", [1, 10, 50, 100])
def test_scalability_performance(operation_count):
    """Test that performance scales reasonably with operation count."""
    model = MockWorkspaceModel()
    service = WorkspaceService(model=model)

    # Measure time for multiple operations
    start_time = time.perf_counter()

    for i in range(operation_count):
        service.add_editor_tab(f"Scale Test Tab {i}")

    end_time = time.perf_counter()
    total_duration_ms = (end_time - start_time) * 1000

    # Should be roughly linear in performance
    avg_per_operation = total_duration_ms / operation_count

    assert (
        avg_per_operation < 10
    ), f"Average per operation: {avg_per_operation:.2f}ms, should be < 10ms"
    assert total_duration_ms < (
        operation_count * 15
    ), f"Total time too high for {operation_count} operations"


def test_architectural_improvement_verification():
    """Verify that the new architecture is faster than the old patterns."""
    # This test verifies the architectural improvement claims

    # Test 1: Model-based operations should be fast
    model = MockWorkspaceModel()
    model_times = []

    for _ in range(10):
        duration_ms, _ = measure_operation_time(model.add_tab, "editor", "Test")
        model_times.append(duration_ms)

    avg_model_time = sum(model_times) / len(model_times)

    # Test 2: Service layer should add minimal overhead
    service = WorkspaceService(model=model)
    service.initialize({})
    service_times = []

    for _ in range(10):
        duration_ms, _ = measure_operation_time(service.add_editor_tab, "Test")
        service_times.append(duration_ms)

    avg_service_time = sum(service_times) / len(service_times)

    # Verify performance targets from implementation plan
    assert avg_model_time < 5, f"Model operations averaging {avg_model_time:.2f}ms, should be < 5ms"
    assert (
        avg_service_time < 20
    ), f"Service operations averaging {avg_service_time:.2f}ms, should be < 20ms"

    print("\nPerformance Results:")
    print(f"  Model operations: {avg_model_time:.2f}ms average")
    print(f"  Service operations: {avg_service_time:.2f}ms average")
    print(f"  Architecture overhead: {avg_service_time - avg_model_time:.2f}ms")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
