#!/usr/bin/env python3
"""
Request/Response patterns for UI communication.

Instead of services calling UI methods directly, they can send requests
through the event bus and receive responses asynchronously.
"""

import threading
import uuid
from dataclasses import dataclass
from typing import Any, Dict, Optional

from .event_bus import event_bus


@dataclass
class UIRequest:
    """Base class for UI requests."""

    request_id: str
    request_type: str
    data: Optional[Dict[str, Any]] = None
    timeout: float = 5.0  # 5 second timeout


@dataclass
class UIResponse:
    """Response to a UI request."""

    request_id: str
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class RequestResponseManager:
    """
    Manages request/response communication with UI.

    Services can send requests and wait for responses without
    directly calling UI methods.
    """

    def __init__(self):
        self._pending_requests: Dict[str, threading.Event] = {}
        self._responses: Dict[str, UIResponse] = {}
        self._lock = threading.Lock()

        # Subscribe to responses
        event_bus.subscribe("ui.response", self._handle_response)

    def send_request(
        self, request_type: str, data: Dict[str, Any] = None, timeout: float = 5.0
    ) -> UIResponse:
        """
        Send a request to the UI and wait for response.

        Args:
            request_type: Type of request
            data: Request data
            timeout: Timeout in seconds

        Returns:
            UIResponse with result
        """
        request_id = str(uuid.uuid4())
        request = UIRequest(
            request_id=request_id, request_type=request_type, data=data or {}, timeout=timeout
        )

        # Create event for waiting
        with self._lock:
            event = threading.Event()
            self._pending_requests[request_id] = event

        # Send request through event bus
        event_bus.publish("ui.request", request)

        # Wait for response
        if event.wait(timeout):
            # Response received
            with self._lock:
                response = self._responses.pop(request_id, None)
                self._pending_requests.pop(request_id, None)

            return response or UIResponse(
                request_id=request_id, success=False, error="No response received"
            )
        else:
            # Timeout
            with self._lock:
                self._pending_requests.pop(request_id, None)

            return UIResponse(
                request_id=request_id,
                success=False,
                error=f"Request timed out after {timeout} seconds",
            )

    def _handle_response(self, response: UIResponse) -> None:
        """Handle response from UI."""
        with self._lock:
            if response.request_id in self._pending_requests:
                self._responses[response.request_id] = response
                event = self._pending_requests[response.request_id]
                event.set()


# Global instance
request_manager = RequestResponseManager()


# Convenience functions for common requests
def request_pane_close(pane_id: str) -> bool:
    """Request UI to close a pane."""
    response = request_manager.send_request("pane.close", {"pane_id": pane_id})
    return response.success


def request_pane_numbers_toggle() -> bool:
    """Request UI to toggle pane numbers."""
    response = request_manager.send_request("pane.numbers.toggle")
    return response.success and response.data.get("visible", False)


def request_pane_numbers_state() -> Optional[bool]:
    """Request current state of pane numbers visibility."""
    response = request_manager.send_request("pane.numbers.state")
    if response.success:
        return response.data.get("visible")
    return None


def request_pane_split(pane_id: str, orientation: str) -> Optional[str]:
    """Request UI to split a pane."""
    response = request_manager.send_request(
        "pane.split", {"pane_id": pane_id, "orientation": orientation}
    )
    if response.success:
        return response.data.get("new_pane_id")
    return None
