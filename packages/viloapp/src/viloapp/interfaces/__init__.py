"""Interfaces package for defining contracts between layers."""

from .model_interfaces import (
    IWorkspaceModel,
    ITabModel,
    IPaneModel,
    IModelObserver,
)

__all__ = [
    "IWorkspaceModel",
    "ITabModel",
    "IPaneModel",
    "IModelObserver",
]