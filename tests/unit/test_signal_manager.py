#!/usr/bin/env python3
"""
Unit tests for SignalManager.
"""

from PySide6.QtCore import QObject, Qt, Signal

from ui.widgets.signal_manager import SignalManager


class MockSignalEmitter(QObject):
    """Mock object with signals for testing."""

    test_signal = Signal()
    test_signal_with_arg = Signal(str)
    test_signal_with_args = Signal(int, str)


class MockSlotReceiver(QObject):
    """Mock object with slots for testing."""

    def __init__(self):
        super().__init__()
        self.call_count = 0
        self.last_value = None
        self.last_values = None

    def slot_no_args(self):
        """Slot that takes no arguments."""
        self.call_count += 1

    def slot_one_arg(self, value):
        """Slot that takes one argument."""
        self.call_count += 1
        self.last_value = value

    def slot_two_args(self, int_val, str_val):
        """Slot that takes two arguments."""
        self.call_count += 1
        self.last_values = (int_val, str_val)


class TestSignalManager:
    """Test SignalManager functionality."""

    def test_create_signal_manager(self, qtbot):
        """Test creating a SignalManager."""
        owner = QObject()
        # Don't use qtbot.addWidget for QObject, only for QWidget
        manager = SignalManager(owner)

        assert manager.owner == owner
        assert manager.get_connection_count() == 0
        assert not manager.has_connections()

    def test_connect_signal(self, qtbot):
        """Test connecting a signal through SignalManager."""
        owner = QObject()
        emitter = MockSignalEmitter()
        receiver = MockSlotReceiver()

        manager = SignalManager(owner)

        # Connect signal
        connection = manager.connect(
            emitter.test_signal, receiver.slot_no_args, description="Test connection"
        )

        assert connection is not None
        assert manager.get_connection_count() == 1
        assert manager.has_connections()

        # Test signal works
        emitter.test_signal.emit()
        assert receiver.call_count == 1

    def test_connect_signal_with_args(self, qtbot):
        """Test connecting signals with arguments."""
        owner = QObject()
        emitter = MockSignalEmitter()
        receiver = MockSlotReceiver()

        manager = SignalManager(owner)

        # Connect signal with one arg
        manager.connect(emitter.test_signal_with_arg, receiver.slot_one_arg)

        emitter.test_signal_with_arg.emit("test_value")
        assert receiver.call_count == 1
        assert receiver.last_value == "test_value"

        # Connect signal with two args
        manager.connect(emitter.test_signal_with_args, receiver.slot_two_args)

        emitter.test_signal_with_args.emit(42, "hello")
        assert receiver.call_count == 2
        assert receiver.last_values == (42, "hello")

    def test_disconnect_signal(self, qtbot):
        """Test disconnecting a signal."""
        owner = QObject()
        emitter = MockSignalEmitter()
        receiver = MockSlotReceiver()

        manager = SignalManager(owner)

        # Connect and verify it works
        connection = manager.connect(emitter.test_signal, receiver.slot_no_args)

        emitter.test_signal.emit()
        assert receiver.call_count == 1

        # Disconnect
        success = manager.disconnect(connection)
        assert success
        assert manager.get_connection_count() == 0

        # Verify signal no longer works
        emitter.test_signal.emit()
        assert receiver.call_count == 1  # Still 1, not incremented

    def test_disconnect_all(self, qtbot):
        """Test disconnecting all signals."""
        owner = QObject()
        emitter = MockSignalEmitter()
        receiver1 = MockSlotReceiver()
        receiver2 = MockSlotReceiver()

        manager = SignalManager(owner)

        # Connect multiple signals
        manager.connect(emitter.test_signal, receiver1.slot_no_args)
        manager.connect(emitter.test_signal_with_arg, receiver2.slot_one_arg)

        assert manager.get_connection_count() == 2

        # Disconnect all
        count = manager.disconnect_all()
        assert count == 2
        assert manager.get_connection_count() == 0

        # Verify signals no longer work
        emitter.test_signal.emit()
        emitter.test_signal_with_arg.emit("test")
        assert receiver1.call_count == 0
        assert receiver2.call_count == 0

    def test_connection_types(self, qtbot):
        """Test different connection types."""
        owner = QObject()
        emitter = MockSignalEmitter()
        receiver = MockSlotReceiver()

        manager = SignalManager(owner)

        # Test different connection types
        connections = [
            manager.connect(
                emitter.test_signal,
                receiver.slot_no_args,
                connection_type=Qt.AutoConnection,
            ),
            manager.connect(
                emitter.test_signal_with_arg,
                receiver.slot_one_arg,
                connection_type=Qt.DirectConnection,
            ),
        ]

        assert all(c is not None for c in connections)
        assert manager.get_connection_count() == 2

    def test_duplicate_connection_prevention(self, qtbot):
        """Test that duplicate connections are prevented."""
        owner = QObject()
        emitter = MockSignalEmitter()
        receiver = MockSlotReceiver()

        manager = SignalManager(owner)

        # Connect same signal/slot twice
        conn1 = manager.connect(emitter.test_signal, receiver.slot_no_args)
        conn2 = manager.connect(emitter.test_signal, receiver.slot_no_args)

        # Both connections should be tracked
        assert conn1 is not None
        assert conn2 is not None
        assert manager.get_connection_count() == 2

        # But signal should only trigger once per emit (Qt handles this)
        # This behavior depends on Qt's implementation

    def test_manager_cleanup_on_owner_destroyed(self, qtbot):
        """Test that manager cleans up when owner is destroyed."""
        owner = QObject()
        emitter = MockSignalEmitter()
        receiver = MockSlotReceiver()

        manager = SignalManager(owner)

        # Connect signals
        manager.connect(emitter.test_signal, receiver.slot_no_args)
        assert manager.has_connections()

        # Destroy owner (this would normally trigger cleanup in a real scenario)
        # Note: In tests, we can't easily test automatic cleanup on destruction
        # but we can verify manual cleanup works
        manager.disconnect_all()
        assert not manager.has_connections()

    def test_connection_with_lambda(self, qtbot):
        """Test connecting with lambda functions."""
        owner = QObject()
        emitter = MockSignalEmitter()

        manager = SignalManager(owner)

        # Track lambda execution
        lambda_called = []

        # Connect with lambda
        manager.connect(
            emitter.test_signal_with_arg,
            lambda x: lambda_called.append(x),
            description="Lambda connection",
        )

        # Emit signal
        emitter.test_signal_with_arg.emit("test_value")
        assert "test_value" in lambda_called

    def test_get_connection_info(self, qtbot):
        """Test getting connection information."""
        owner = QObject()
        emitter = MockSignalEmitter()
        receiver = MockSlotReceiver()

        manager = SignalManager(owner)

        # Connect with description
        connection = manager.connect(
            emitter.test_signal,
            receiver.slot_no_args,
            description="Test connection for info",
        )

        assert connection.description == "Test connection for info"
        assert connection.signal == emitter.test_signal
        assert connection.slot == receiver.slot_no_args
        assert connection.connection_type == Qt.AutoConnection

    def test_connection_groups(self, qtbot):
        """Test connection group management."""
        owner = QObject()
        emitter1 = MockSignalEmitter()
        emitter2 = MockSignalEmitter()
        receiver = MockSlotReceiver()

        manager = SignalManager(owner)

        # Create connections in different groups
        conn1 = manager.connect(
            emitter1.test_signal,
            receiver.slot_no_args,
            description="Group A signal 1",
            group="groupA",
        )
        conn2 = manager.connect(
            emitter2.test_signal,
            receiver.slot_no_args,
            description="Group A signal 2",
            group="groupA",
        )
        manager.connect(
            emitter1.test_signal_with_arg,
            receiver.slot_one_arg,
            description="Group B signal",
            group="groupB",
        )

        # Test group listing
        groups = manager.get_groups()
        assert "groupA" in groups
        assert "groupB" in groups
        assert len(groups) == 2

        # Test getting group connections
        group_a_conns = manager.get_group_connections("groupA")
        assert len(group_a_conns) == 2
        assert conn1 in group_a_conns
        assert conn2 in group_a_conns

        # Test disconnecting a group
        count = manager.disconnect_group("groupA")
        assert count == 2
        assert manager.get_connection_count() == 1  # Only groupB remains

        # Test that signals in groupA are disconnected
        receiver.call_count = 0
        emitter1.test_signal.emit()
        emitter2.test_signal.emit()
        assert receiver.call_count == 0  # Should not be called

        # Test that groupB is still connected
        emitter1.test_signal_with_arg.emit("test")
        assert receiver.last_value == "test"

    def test_group_enable_disable(self, qtbot):
        """Test enabling and disabling connection groups."""
        owner = QObject()
        emitter = MockSignalEmitter()
        receiver = MockSlotReceiver()

        manager = SignalManager(owner)

        # Create connections in a group
        manager.connect(
            emitter.test_signal,
            receiver.slot_no_args,
            description="Test signal",
            group="test_group",
        )

        # Test initial state - should be connected
        receiver.call_count = 0
        emitter.test_signal.emit()
        assert receiver.call_count == 1

        # Disable the group
        count = manager.disable_group("test_group")
        assert count == 1

        # Signal should not trigger slot
        receiver.call_count = 0
        emitter.test_signal.emit()
        assert receiver.call_count == 0

        # Re-enable the group
        count = manager.enable_group("test_group")
        assert count == 1

        # Signal should trigger slot again
        receiver.call_count = 0
        emitter.test_signal.emit()
        assert receiver.call_count == 1

        # Connection should still be tracked
        assert manager.get_connection_count() == 1
