#!/usr/bin/env python3
"""
State service for managing application state persistence.

This service handles saving and restoring application state,
including window geometry, workspace layouts, and user preferences.
"""

import json
import logging
from typing import Any, Optional

from PySide6.QtCore import QSettings

from services.base import Service

logger = logging.getLogger(__name__)


class StateService(Service):
    """
    Service for managing application state persistence.

    Handles saving and restoring window state, workspace layouts,
    user preferences, and session management.
    """

    def __init__(self):
        """Initialize the state service."""
        super().__init__("StateService")
        self._settings = QSettings("ViloxTerm", "State")
        self._main_window = None
        self._workspace = None
        self._autosave_enabled = True
        self._autosave_interval = 60000  # 1 minute in ms
        # Tab & Pane naming storage
        self._pane_names: dict[str, str] = {}  # pane_id -> custom_name

    def initialize(self, context: dict[str, Any]) -> None:
        """Initialize the service with application context."""
        super().initialize(context)

        self._main_window = context.get('main_window')
        self._workspace = context.get('workspace')

        # Load autosave preferences
        self._autosave_enabled = self._settings.value("autosave_enabled", True, type=bool)
        self._autosave_interval = self._settings.value("autosave_interval", 60000, type=int)

        logger.info(f"StateService initialized (autosave: {self._autosave_enabled})")

    def cleanup(self) -> None:
        """Cleanup service resources."""
        # Save current state before cleanup
        self.save_all_state()

        self._main_window = None
        self._workspace = None
        super().cleanup()

    # ============= Window State =============

    def save_window_state(self) -> None:
        """Save window geometry and state."""
        if not self._main_window:
            return

        try:
            # Save geometry
            self._settings.setValue("window_geometry", self._main_window.saveGeometry())

            # Save window state (toolbars, docks, etc.)
            self._settings.setValue("window_state", self._main_window.saveState())

            # Save splitter sizes
            if hasattr(self._main_window, 'main_splitter'):
                self._settings.setValue("splitter_sizes", self._main_window.main_splitter.sizes())

            # Save maximized/fullscreen state
            self._settings.setValue("window_maximized", self._main_window.isMaximized())
            self._settings.setValue("window_fullscreen", self._main_window.isFullScreen())

            self._settings.sync()

            logger.debug("Window state saved")

        except Exception as e:
            logger.error(f"Failed to save window state: {e}")

    def restore_window_state(self) -> bool:
        """
        Restore window geometry and state.

        Returns:
            True if state was restored successfully
        """
        if not self._main_window:
            return False

        try:
            # Restore geometry
            geometry = self._settings.value("window_geometry")
            if geometry:
                self._main_window.restoreGeometry(geometry)

            # Restore window state
            state = self._settings.value("window_state")
            if state:
                self._main_window.restoreState(state)

            # Restore splitter sizes
            if hasattr(self._main_window, 'main_splitter'):
                sizes = self._settings.value("splitter_sizes")
                if sizes:
                    self._main_window.main_splitter.setSizes(sizes)

            # Restore maximized/fullscreen state
            if self._settings.value("window_maximized", False, type=bool):
                self._main_window.showMaximized()
            elif self._settings.value("window_fullscreen", False, type=bool):
                self._main_window.showFullScreen()

            logger.info("Window state restored")
            return True

        except Exception as e:
            logger.error(f"Failed to restore window state: {e}")
            return False

    # ============= Workspace State =============

    def save_workspace_state(self) -> dict[str, Any]:
        """
        Save workspace state (tabs, panes, layouts).

        Returns:
            Workspace state dictionary
        """
        if not self._workspace:
            return {}

        try:
            state = self._workspace.get_state()

            # Convert to JSON-serializable format
            json_state = json.dumps(state)
            self._settings.setValue("workspace_state", json_state)

            self._settings.sync()

            logger.debug("Workspace state saved")
            return state

        except Exception as e:
            logger.error(f"Failed to save workspace state: {e}")
            return {}

    def restore_workspace_state(self) -> bool:
        """
        Restore workspace state.

        Returns:
            True if state was restored successfully
        """
        if not self._workspace:
            return False

        try:
            json_state = self._settings.value("workspace_state")
            if not json_state:
                return False

            state = json.loads(json_state)
            self._workspace.set_state(state)

            logger.info("Workspace state restored")
            return True

        except Exception as e:
            logger.error(f"Failed to restore workspace state: {e}")
            return False

    # ============= User Preferences =============

    def save_preference(self, key: str, value: Any) -> None:
        """
        Save a user preference.

        Args:
            key: Preference key
            value: Preference value
        """
        try:
            self._settings.setValue(f"preferences/{key}", value)
            self._settings.sync()

            # Notify observers
            self.notify('preference_saved', {'key': key, 'value': value})

        except Exception as e:
            logger.error(f"Failed to save preference {key}: {e}")

    def get_preference(self, key: str, default: Any = None) -> Any:
        """
        Get a user preference.

        Args:
            key: Preference key
            default: Default value if not found

        Returns:
            Preference value or default
        """
        return self._settings.value(f"preferences/{key}", default)

    def save_preferences(self, preferences: dict[str, Any]) -> None:
        """
        Save multiple preferences.

        Args:
            preferences: Dictionary of preferences
        """
        for key, value in preferences.items():
            self.save_preference(key, value)

    def get_all_preferences(self) -> dict[str, Any]:
        """
        Get all user preferences.

        Returns:
            Dictionary of all preferences
        """
        preferences = {}
        self._settings.beginGroup("preferences")
        for key in self._settings.allKeys():
            preferences[key] = self._settings.value(key)
        self._settings.endGroup()
        return preferences

    # ============= Session Management =============

    def save_session(self, name: str = "default") -> bool:
        """
        Save the current session.

        Args:
            name: Session name

        Returns:
            True if session was saved
        """
        try:
            session = {
                'window_state': self._get_window_state_dict(),
                'workspace_state': self._workspace.get_state() if self._workspace else {},
                'ui_state': self._get_ui_state(),
                'timestamp': self._get_timestamp()
            }

            json_session = json.dumps(session)
            self._settings.setValue(f"sessions/{name}", json_session)
            self._settings.sync()

            # Notify observers
            self.notify('session_saved', {'name': name})

            logger.info(f"Session '{name}' saved")
            return True

        except Exception as e:
            logger.error(f"Failed to save session '{name}': {e}")
            return False

    def restore_session(self, name: str = "default") -> bool:
        """
        Restore a saved session.

        Args:
            name: Session name

        Returns:
            True if session was restored
        """
        try:
            json_session = self._settings.value(f"sessions/{name}")
            if not json_session:
                logger.warning(f"Session '{name}' not found")
                return False

            session = json.loads(json_session)

            # Restore components
            if 'window_state' in session:
                self._restore_window_state_dict(session['window_state'])

            if 'workspace_state' in session and self._workspace:
                self._workspace.set_state(session['workspace_state'])

            if 'ui_state' in session:
                self._restore_ui_state(session['ui_state'])

            # Notify observers
            self.notify('session_restored', {'name': name})

            logger.info(f"Session '{name}' restored")
            return True

        except Exception as e:
            logger.error(f"Failed to restore session '{name}': {e}")
            return False

    def list_sessions(self) -> list[str]:
        """
        List all saved sessions.

        Returns:
            List of session names
        """
        self._settings.beginGroup("sessions")
        sessions = self._settings.allKeys()
        self._settings.endGroup()
        return sessions

    def delete_session(self, name: str) -> bool:
        """
        Delete a saved session.

        Args:
            name: Session name

        Returns:
            True if session was deleted
        """
        self._settings.remove(f"sessions/{name}")
        self._settings.sync()

        # Notify observers
        self.notify('session_deleted', {'name': name})

        logger.info(f"Session '{name}' deleted")
        return True

    # ============= Comprehensive State =============

    def save_all_state(self) -> None:
        """Save all application state."""
        self.save_window_state()
        self.save_workspace_state()

        # Save to default session
        self.save_session("last_state")

        logger.info("All state saved")

    def restore_all_state(self) -> bool:
        """
        Restore all application state.

        Returns:
            True if any state was restored
        """
        success = False

        if self.restore_window_state():
            success = True

        if self.restore_workspace_state():
            success = True

        logger.info(f"State restoration {'successful' if success else 'failed'}")
        return success

    def reset_all_state(self) -> None:
        """Reset all saved state to defaults."""
        try:
            self._settings.clear()
            self._settings.sync()

            # Notify observers
            self.notify('state_reset', {})

            logger.info("All state reset to defaults")

        except Exception as e:
            logger.error(f"Failed to reset state: {e}")

    # ============= Utility Methods =============

    def _get_window_state_dict(self) -> dict[str, Any]:
        """Get window state as dictionary."""
        if not self._main_window:
            return {}

        return {
            'geometry': self._main_window.geometry().getRect(),
            'maximized': self._main_window.isMaximized(),
            'fullscreen': self._main_window.isFullScreen()
        }

    def _restore_window_state_dict(self, state: dict[str, Any]) -> None:
        """Restore window state from dictionary."""
        if not self._main_window or not state:
            return

        if 'geometry' in state:
            rect = state['geometry']
            self._main_window.setGeometry(rect[0], rect[1], rect[2], rect[3])

        if state.get('maximized'):
            self._main_window.showMaximized()
        elif state.get('fullscreen'):
            self._main_window.showFullScreen()

    def _get_ui_state(self) -> dict[str, Any]:
        """Get UI state from UIService."""
        try:
            from services.service_locator import ServiceLocator
            from services.ui_service import UIService

            locator = ServiceLocator.get_instance()
            ui_service = locator.get(UIService)

            if ui_service:
                return ui_service.get_ui_state()
        except (ImportError, AttributeError, Exception) as e:
            logger.error(f"Failed to get UI state: {e}")
            # Continue execution as UI state is optional

        return {}

    def _restore_ui_state(self, state: dict[str, Any]) -> None:
        """Restore UI state via UIService."""
        try:
            from services.service_locator import ServiceLocator
            from services.ui_service import UIService

            locator = ServiceLocator.get_instance()
            ui_service = locator.get(UIService)

            if ui_service:
                ui_service.restore_ui_state(state)
        except (ImportError, AttributeError, Exception) as e:
            logger.error(f"Failed to restore UI state: {e}")
            # Continue execution as UI state restore is optional

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()

    def get_autosave_enabled(self) -> bool:
        """Check if autosave is enabled."""
        return self._autosave_enabled

    def set_autosave_enabled(self, enabled: bool) -> None:
        """Enable or disable autosave."""
        self._autosave_enabled = enabled
        self._settings.setValue("autosave_enabled", enabled)

        # Notify observers
        self.notify('autosave_changed', {'enabled': enabled})

    # ============= Tab & Pane Naming =============

    def set_pane_name(self, pane_id: str, name: str) -> None:
        """Set custom name for a pane."""
        self._pane_names[pane_id] = name
        self._settings.setValue(f"pane_names/{pane_id}", name)
        self._settings.sync()

    def get_pane_name(self, pane_id: str) -> Optional[str]:
        """Get custom name for a pane, or None if not set."""
        return self._pane_names.get(pane_id)
