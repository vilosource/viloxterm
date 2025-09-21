"""
New architecture implementation for ViloxTerm.

This package contains the clean, model-driven architecture
being built as part of the Big Bang refactor.
"""

from .model import WorkspaceModel, WorkspaceState

__all__ = ["WorkspaceModel", "WorkspaceState"]
