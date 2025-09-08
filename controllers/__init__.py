"""
Controllers package for MVC architecture.

This package contains controller classes that provide clean separation
between UI components (View) and state data (Model), following MVC
architectural patterns.
"""

from .state_controller import (
    StateController,
    ApplicationStateController,
    StateModel,
    SplitPaneStateModel,
    WorkspaceStateModel
)

__all__ = [
    'StateController',
    'ApplicationStateController', 
    'StateModel',
    'SplitPaneStateModel',
    'WorkspaceStateModel'
]