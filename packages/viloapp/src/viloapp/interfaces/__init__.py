"""Interfaces package for defining contracts between layers."""

from .model_interfaces import (
    IModelObserver,
    IPaneModel,
    ITabModel,
    IWorkspaceModel,
)

__all__ = [
    "IWorkspaceModel",
    "ITabModel",
    "IPaneModel",
    "IModelObserver",
]
