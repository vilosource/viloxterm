"""Integration tests for terminal server."""


from viloxterm.server import TerminalServerManager
from viloxterm.backends import TerminalBackendFactory


def test_terminal_server_lifecycle():
    """Test terminal server lifecycle."""
    server = TerminalServerManager()

    # Start server
    port = server.start_server()
    assert port > 0
    assert server.running

    # Create session
    session_id = server.create_session(command="echo", cmd_args="test")
    assert session_id in server.sessions

    # Get URL
    url = server.get_terminal_url(session_id)
    assert f":{port}/terminal/{session_id}" in url

    # Destroy session
    server.destroy_session(session_id)
    assert session_id not in server.sessions

    # Shutdown server
    server.shutdown()
    assert not server.running


def test_backend_factory():
    """Test terminal backend factory."""
    backend = TerminalBackendFactory.create_backend()
    assert backend is not None

    # Reset factory
    TerminalBackendFactory.reset()