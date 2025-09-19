"""Plugin lifecycle management."""

from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Optional, List, Callable, Dict
from dataclasses import dataclass

class LifecycleState(Enum):
    """Plugin lifecycle states."""
    DISCOVERED = auto()  # Plugin found but not loaded
    LOADED = auto()      # Plugin code loaded
    ACTIVATED = auto()   # Plugin activated and running
    DEACTIVATED = auto() # Plugin deactivated
    FAILED = auto()      # Plugin failed to load/activate
    UNLOADED = auto()    # Plugin unloaded from memory

class LifecycleHook(Enum):
    """Lifecycle hook points."""
    BEFORE_LOAD = "before_load"
    AFTER_LOAD = "after_load"
    BEFORE_ACTIVATE = "before_activate"
    AFTER_ACTIVATE = "after_activate"
    BEFORE_DEACTIVATE = "before_deactivate"
    AFTER_DEACTIVATE = "after_deactivate"
    BEFORE_UNLOAD = "before_unload"
    AFTER_UNLOAD = "after_unload"

@dataclass
class LifecycleTransition:
    """Represents a state transition."""
    from_state: LifecycleState
    to_state: LifecycleState
    timestamp: float
    reason: Optional[str] = None
    error: Optional[Exception] = None

class ILifecycle(ABC):
    """Interface for lifecycle management."""

    @abstractmethod
    def get_state(self) -> LifecycleState:
        """Get current lifecycle state."""
        pass

    @abstractmethod
    def can_transition_to(self, state: LifecycleState) -> bool:
        """Check if transition to state is valid."""
        pass

    @abstractmethod
    def add_hook(self, hook: LifecycleHook, callback: Callable) -> None:
        """Add a lifecycle hook."""
        pass

    @abstractmethod
    def remove_hook(self, hook: LifecycleHook, callback: Callable) -> None:
        """Remove a lifecycle hook."""
        pass

    @abstractmethod
    def get_transition_history(self) -> List[LifecycleTransition]:
        """Get state transition history."""
        pass

class PluginLifecycle(ILifecycle):
    """Implementation of plugin lifecycle management."""

    # Valid state transitions
    VALID_TRANSITIONS = {
        LifecycleState.DISCOVERED: [LifecycleState.LOADED, LifecycleState.FAILED],
        LifecycleState.LOADED: [LifecycleState.ACTIVATED, LifecycleState.FAILED, LifecycleState.UNLOADED],
        LifecycleState.ACTIVATED: [LifecycleState.DEACTIVATED, LifecycleState.FAILED],
        LifecycleState.DEACTIVATED: [LifecycleState.ACTIVATED, LifecycleState.UNLOADED],
        LifecycleState.FAILED: [LifecycleState.UNLOADED],
        LifecycleState.UNLOADED: [LifecycleState.LOADED]
    }

    def __init__(self):
        self._state = LifecycleState.DISCOVERED
        self._hooks: Dict[LifecycleHook, List[Callable]] = {}
        self._history: List[LifecycleTransition] = []

    def get_state(self) -> LifecycleState:
        return self._state

    def can_transition_to(self, state: LifecycleState) -> bool:
        """Check if transition is valid."""
        return state in self.VALID_TRANSITIONS.get(self._state, [])

    def transition_to(
        self,
        state: LifecycleState,
        reason: Optional[str] = None,
        error: Optional[Exception] = None
    ) -> bool:
        """
        Transition to a new state.

        Returns:
            True if transition was successful
        """
        if not self.can_transition_to(state):
            return False

        # Create transition record
        import time
        transition = LifecycleTransition(
            from_state=self._state,
            to_state=state,
            timestamp=time.time(),
            reason=reason,
            error=error
        )

        # Execute hooks
        self._execute_hooks_for_transition(self._state, state)

        # Update state
        self._state = state
        self._history.append(transition)

        return True

    def add_hook(self, hook: LifecycleHook, callback: Callable) -> None:
        """Add a lifecycle hook."""
        if hook not in self._hooks:
            self._hooks[hook] = []
        self._hooks[hook].append(callback)

    def remove_hook(self, hook: LifecycleHook, callback: Callable) -> None:
        """Remove a lifecycle hook."""
        if hook in self._hooks:
            self._hooks[hook] = [h for h in self._hooks[hook] if h != callback]

    def get_transition_history(self) -> List[LifecycleTransition]:
        """Get state transition history."""
        return list(self._history)

    def _execute_hooks_for_transition(
        self,
        from_state: LifecycleState,
        to_state: LifecycleState
    ) -> None:
        """Execute relevant hooks for a state transition."""
        # Map transitions to hooks
        hook_mapping = {
            (LifecycleState.DISCOVERED, LifecycleState.LOADED): [
                LifecycleHook.BEFORE_LOAD, LifecycleHook.AFTER_LOAD
            ],
            (LifecycleState.LOADED, LifecycleState.ACTIVATED): [
                LifecycleHook.BEFORE_ACTIVATE, LifecycleHook.AFTER_ACTIVATE
            ],
            (LifecycleState.ACTIVATED, LifecycleState.DEACTIVATED): [
                LifecycleHook.BEFORE_DEACTIVATE, LifecycleHook.AFTER_DEACTIVATE
            ],
            (LifecycleState.DEACTIVATED, LifecycleState.UNLOADED): [
                LifecycleHook.BEFORE_UNLOAD, LifecycleHook.AFTER_UNLOAD
            ],
        }

        hooks_to_execute = hook_mapping.get((from_state, to_state), [])

        for hook in hooks_to_execute:
            if hook in self._hooks:
                for callback in self._hooks[hook]:
                    try:
                        callback()
                    except Exception as e:
                        # Log but don't fail the transition
                        print(f"Hook {hook} failed: {e}")