"""Tests for base model classes."""

import pytest

from viloapp.models.base import OperationResult


class TestOperationResult:
    """Test cases for OperationResult class."""

    def test_successful_result_creation(self):
        """Test creation of successful operation result."""
        result = OperationResult(success=True)
        assert result.success is True
        assert result.error is None
        assert result.data is None

    def test_error_result_creation(self):
        """Test creation of error operation result."""
        error_msg = "Something went wrong"
        result = OperationResult(success=False, error=error_msg)
        assert result.success is False
        assert result.error == error_msg
        assert result.data is None

    def test_result_with_data(self):
        """Test operation result with data."""
        data = {"tab_id": "123", "count": 5}
        result = OperationResult(success=True, data=data)
        assert result.success is True
        assert result.data == data
        assert result.error is None

    def test_success_result_class_method(self):
        """Test success_result class method."""
        data = {"created_id": "abc123"}
        result = OperationResult.success_result(data)
        assert result.success is True
        assert result.data == data
        assert result.error is None

    def test_success_result_without_data(self):
        """Test success_result without data."""
        result = OperationResult.success_result()
        assert result.success is True
        assert result.data is None
        assert result.error is None

    def test_error_result_class_method(self):
        """Test error_result class method."""
        error_msg = "Validation failed"
        data = {"field": "name", "value": ""}
        result = OperationResult.error_result(error_msg, data)
        assert result.success is False
        assert result.error == error_msg
        assert result.data == data

    def test_error_result_without_data(self):
        """Test error_result without data."""
        error_msg = "Operation failed"
        result = OperationResult.error_result(error_msg)
        assert result.success is False
        assert result.error == error_msg
        assert result.data is None

    def test_boolean_conversion_success(self):
        """Test that successful results are truthy."""
        result = OperationResult(success=True)
        assert bool(result) is True
        assert result  # Should be truthy

    def test_boolean_conversion_error(self):
        """Test that error results are falsy."""
        result = OperationResult(success=False, error="Failed")
        assert bool(result) is False
        assert not result  # Should be falsy

    def test_operation_result_in_conditions(self):
        """Test using OperationResult in conditional statements."""
        success_result = OperationResult.success_result()
        error_result = OperationResult.error_result("Failed")

        # Test in if conditions
        if success_result:
            success_executed = True
        else:
            success_executed = False

        if error_result:
            error_executed = True
        else:
            error_executed = False

        assert success_executed is True
        assert error_executed is False

    def test_dataclass_equality(self):
        """Test that OperationResults with same values are equal."""
        result1 = OperationResult(success=True, data={"key": "value"})
        result2 = OperationResult(success=True, data={"key": "value"})
        result3 = OperationResult(success=False, error="Different")

        assert result1 == result2
        assert result1 != result3

    def test_dataclass_representation(self):
        """Test string representation of OperationResult."""
        result = OperationResult(success=True, data={"id": "123"})
        repr_str = repr(result)
        assert "OperationResult" in repr_str
        assert "success=True" in repr_str
        assert "data={'id': '123'}" in repr_str
