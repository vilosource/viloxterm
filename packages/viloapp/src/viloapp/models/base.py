"""Base classes for data models."""

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class OperationResult:
    """Standard result for all operations.

    This class provides a consistent interface for all operations in the system,
    replacing direct exceptions and varying return types with a structured result.
    """

    success: bool
    error: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

    @classmethod
    def success_result(cls, data: Optional[Dict[str, Any]] = None) -> "OperationResult":
        """Create a successful operation result."""
        return cls(success=True, data=data)

    @classmethod
    def error_result(cls, error: str, data: Optional[Dict[str, Any]] = None) -> "OperationResult":
        """Create a failed operation result with error message."""
        return cls(success=False, error=error, data=data)

    def __bool__(self) -> bool:
        """Allow using OperationResult in boolean contexts."""
        return self.success
