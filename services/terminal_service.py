#!/usr/bin/env python3
"""
Terminal service for managing terminal sessions and operations.

This service encapsulates terminal-related business logic,
providing a clean interface for terminal management.
"""

from typing import Optional, Dict, Any, List
import logging
import uuid

from services.base import Service

logger = logging.getLogger(__name__)


class TerminalService(Service):
    """
    Service for managing terminal operations.
    
    Handles terminal session creation, management, and cleanup.
    Works with the terminal server backend.
    """
    
    def __init__(self):
        """Initialize the terminal service."""
        super().__init__("TerminalService")
        self._terminal_server = None
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._active_session_id: Optional[str] = None
        
    def initialize(self, context: Dict[str, Any]) -> None:
        """Initialize the service with application context."""
        super().initialize(context)
        
        # Get terminal server instance
        try:
            from ui.terminal.terminal_server import terminal_server
            self._terminal_server = terminal_server
            
            # Ensure server is started
            if not self._terminal_server.is_running():
                self.start_server()
                
        except Exception as e:
            logger.error(f"Failed to initialize terminal server: {e}")
            self._terminal_server = None
    
    def cleanup(self) -> None:
        """Cleanup service resources."""
        # Close all sessions
        for session_id in list(self._sessions.keys()):
            self.close_session(session_id)
        
        # Stop server if running
        if self._terminal_server and self._terminal_server.is_running():
            self.stop_server()
        
        self._terminal_server = None
        super().cleanup()
    
    # ============= Server Management =============
    
    def start_server(self) -> bool:
        """
        Start the terminal server.
        
        Returns:
            True if server started successfully
        """
        self.validate_initialized()
        
        if not self._terminal_server:
            logger.error("Terminal server not available")
            return False
        
        try:
            self._terminal_server.start_server()
            
            # Notify observers
            self.notify('server_started', {
                'port': self._terminal_server.port
            })
            
            logger.info(f"Terminal server started on port {self._terminal_server.port}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start terminal server: {e}")
            return False
    
    def stop_server(self) -> bool:
        """
        Stop the terminal server.
        
        Returns:
            True if server stopped successfully
        """
        if not self._terminal_server:
            return False
        
        try:
            self._terminal_server.stop_server()
            
            # Notify observers
            self.notify('server_stopped', {})
            
            logger.info("Terminal server stopped")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop terminal server: {e}")
            return False
    
    def is_server_running(self) -> bool:
        """
        Check if the terminal server is running.
        
        Returns:
            True if server is running
        """
        return self._terminal_server and self._terminal_server.is_running()
    
    def get_server_url(self) -> Optional[str]:
        """
        Get the terminal server URL.
        
        Returns:
            Server URL or None if not running
        """
        if not self.is_server_running():
            return None
        
        return f"http://localhost:{self._terminal_server.port}"
    
    # ============= Session Management =============
    
    def create_session(self, 
                      command: Optional[str] = None,
                      args: Optional[List[str]] = None,
                      cwd: Optional[str] = None,
                      env: Optional[Dict[str, str]] = None) -> Optional[str]:
        """
        Create a new terminal session.
        
        Args:
            command: Command to run (default: shell)
            args: Command arguments
            cwd: Working directory
            env: Environment variables
            
        Returns:
            Session ID or None if failed
        """
        self.validate_initialized()
        
        if not self._terminal_server:
            logger.error("Terminal server not available")
            return None
        
        # Ensure server is running
        if not self.is_server_running():
            if not self.start_server():
                return None
        
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        try:
            # Create session via terminal server
            self._terminal_server.create_session(
                session_id,
                command=command or "bash",
                cmd_args=args or [],
                cwd=cwd
            )
            
            # Store session info
            self._sessions[session_id] = {
                'id': session_id,
                'command': command or "bash",
                'args': args or [],
                'cwd': cwd,
                'env': env or {},
                'active': True
            }
            
            self._active_session_id = session_id
            
            # Notify observers
            self.notify('session_created', {
                'session_id': session_id,
                'command': command or "bash"
            })
            
            logger.info(f"Created terminal session: {session_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"Failed to create terminal session: {e}")
            return None
    
    def close_session(self, session_id: str) -> bool:
        """
        Close a terminal session.
        
        Args:
            session_id: ID of the session to close
            
        Returns:
            True if session was closed
        """
        if session_id not in self._sessions:
            logger.warning(f"Session not found: {session_id}")
            return False
        
        try:
            # Close via terminal server
            if self._terminal_server:
                self._terminal_server.close_session(session_id)
            
            # Remove from tracking
            del self._sessions[session_id]
            
            # Update active session
            if self._active_session_id == session_id:
                self._active_session_id = None
                if self._sessions:
                    # Set another session as active
                    self._active_session_id = next(iter(self._sessions))
            
            # Notify observers
            self.notify('session_closed', {'session_id': session_id})
            
            logger.info(f"Closed terminal session: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to close session {session_id}: {e}")
            return False
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            Session information dictionary or None
        """
        return self._sessions.get(session_id)
    
    def get_all_sessions(self) -> List[Dict[str, Any]]:
        """
        Get information about all sessions.
        
        Returns:
            List of session information dictionaries
        """
        return list(self._sessions.values())
    
    def get_active_session_id(self) -> Optional[str]:
        """
        Get the ID of the active session.
        
        Returns:
            Active session ID or None
        """
        return self._active_session_id
    
    def set_active_session(self, session_id: str) -> bool:
        """
        Set the active session.
        
        Args:
            session_id: Session ID to make active
            
        Returns:
            True if session was set as active
        """
        if session_id not in self._sessions:
            logger.warning(f"Session not found: {session_id}")
            return False
        
        self._active_session_id = session_id
        
        # Notify observers
        self.notify('session_activated', {'session_id': session_id})
        
        return True
    
    # ============= Terminal Operations =============
    
    def send_input(self, session_id: str, data: str) -> bool:
        """
        Send input to a terminal session.
        
        Args:
            session_id: Session ID
            data: Input data to send
            
        Returns:
            True if input was sent
        """
        if not self._terminal_server:
            return False
        
        if session_id not in self._sessions:
            logger.warning(f"Session not found: {session_id}")
            return False
        
        try:
            # This would typically be handled via the WebSocket connection
            # from the terminal widget, but we provide this for programmatic access
            logger.debug(f"Sending input to session {session_id}: {repr(data)}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send input to session {session_id}: {e}")
            return False
    
    def resize_terminal(self, session_id: str, rows: int, cols: int) -> bool:
        """
        Resize a terminal session.
        
        Args:
            session_id: Session ID
            rows: Number of rows
            cols: Number of columns
            
        Returns:
            True if terminal was resized
        """
        if not self._terminal_server:
            return False
        
        if session_id not in self._sessions:
            logger.warning(f"Session not found: {session_id}")
            return False
        
        try:
            session = self._terminal_server.sessions.get(session_id)
            if session:
                self._terminal_server.resize_terminal(session_id, rows, cols)
                
                # Notify observers
                self.notify('terminal_resized', {
                    'session_id': session_id,
                    'rows': rows,
                    'cols': cols
                })
                
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to resize terminal {session_id}: {e}")
            return False
    
    def clear_terminal(self, session_id: str) -> bool:
        """
        Clear a terminal session.
        
        Args:
            session_id: Session ID
            
        Returns:
            True if terminal was cleared
        """
        # Send clear command
        return self.send_input(session_id, "\x0c")  # Ctrl+L
    
    # ============= Utility Methods =============
    
    def get_session_count(self) -> int:
        """
        Get the number of active sessions.
        
        Returns:
            Number of sessions
        """
        return len(self._sessions)
    
    def has_active_sessions(self) -> bool:
        """
        Check if there are any active sessions.
        
        Returns:
            True if there are active sessions
        """
        return bool(self._sessions)
    
    def get_service_info(self) -> Dict[str, Any]:
        """
        Get comprehensive service information.
        
        Returns:
            Dictionary with service state information
        """
        return {
            'server_running': self.is_server_running(),
            'server_url': self.get_server_url(),
            'session_count': self.get_session_count(),
            'active_session': self._active_session_id,
            'sessions': [
                {
                    'id': s['id'],
                    'command': s['command'],
                    'active': s['id'] == self._active_session_id
                }
                for s in self._sessions.values()
            ]
        }