"""Qt/PySide6 compatibility utilities for handling version differences."""

import logging

from PySide6 import __version__ as pyside_version
from PySide6.QtCore import QObject, Signal

logger = logging.getLogger(__name__)


def get_pyside_version():
    """Get PySide6 version as a tuple of integers."""
    try:
        parts = pyside_version.split('.')
        return tuple(int(p) for p in parts[:3])
    except Exception as e:
        logger.warning(f"Failed to parse PySide6 version: {e}")
        return (6, 0, 0)  # Default fallback


def check_signal_receivers(signal: Signal) -> bool:
    """Check if a signal has any receivers/connections.

    This handles the difference between PyQt5 and PySide6 where
    the receivers() method doesn't exist in PySide6.

    Args:
        signal: The signal to check

    Returns:
        True if the signal can accept connections (always true for valid signals)
    """
    # In PySide6, we can't directly check receiver count
    # But we can verify the signal is valid and connectable
    try:
        # Check if signal has the connect method
        return hasattr(signal, 'connect') and callable(signal.connect)
    except Exception as e:
        logger.warning(f"Failed to check signal receivers: {e}")
        return False


def safe_key_sequence_to_key(key_sequence_str: str):
    """Safely convert a key sequence string to Qt key and modifiers.

    This avoids the overflow issues with QKeySequence.toCombined() in some
    PySide6 versions.

    Args:
        key_sequence_str: String like "Ctrl+T" or "Ctrl+Shift+M"

    Returns:
        Tuple of (key, modifiers) suitable for qtbot.keyClick()
    """
    from PySide6.QtCore import Qt

    parts = key_sequence_str.split('+')
    if not parts:
        raise ValueError(f"Invalid key sequence: {key_sequence_str}")

    # Build modifier flags
    modifiers = Qt.KeyboardModifier.NoModifier
    key = None

    for part in parts:
        part = part.strip().lower()
        if part in ('ctrl', 'control'):
            modifiers |= Qt.KeyboardModifier.ControlModifier
        elif part == 'alt':
            modifiers |= Qt.KeyboardModifier.AltModifier
        elif part == 'shift':
            modifiers |= Qt.KeyboardModifier.ShiftModifier
        elif part in ('meta', 'cmd', 'command'):
            modifiers |= Qt.KeyboardModifier.MetaModifier
        else:
            # This should be the actual key
            key_name = f"Key_{part.upper()}"
            if hasattr(Qt.Key, key_name):
                key = getattr(Qt.Key, key_name)
            else:
                # Try single character
                if len(part) == 1:
                    key = ord(part.upper())
                else:
                    raise ValueError(f"Unknown key: {part}")

    if key is None:
        raise ValueError(f"No key found in sequence: {key_sequence_str}")

    return key, modifiers


def safe_splitter_collapse_setting(splitter, collapsible: bool):
    """Safely set splitter children collapsible property.

    Some Qt versions may not properly respect this setting when
    state is restored, so this ensures it's applied correctly.

    Args:
        splitter: QSplitter instance
        collapsible: Whether children should be collapsible
    """
    try:
        splitter.setChildrenCollapsible(collapsible)

        # For older Qt versions, we might need to set minimum sizes
        if not collapsible:
            # Ensure each widget has a minimum size to prevent collapse
            for i in range(splitter.count()):
                widget = splitter.widget(i)
                if widget and widget.minimumWidth() == 0:
                    widget.setMinimumWidth(50)  # Reasonable minimum

    except Exception as e:
        logger.warning(f"Failed to set splitter collapse settings: {e}")


def get_qt_version_info():
    """Get comprehensive Qt/PySide6 version information.

    Returns:
        Dict with version information
    """
    from PySide6.QtCore import qVersion

    return {
        'pyside_version': pyside_version,
        'pyside_tuple': get_pyside_version(),
        'qt_runtime': qVersion(),
        'qt_compiled': QObject.staticMetaObject.className()  # Just to verify Qt is loaded
    }


# Version-specific feature flags
FEATURES = {
    'signal_receivers': get_pyside_version() < (6, 0, 0),  # Not available in PySide6
    'key_sequence_combined': get_pyside_version() < (6, 5, 0),  # Overflow issues in some versions
    'splitter_restore_respect': get_pyside_version() >= (6, 2, 0),  # Better state restoration
}


def log_qt_versions():
    """Log Qt/PySide6 version information for debugging."""
    info = get_qt_version_info()
    logger.info(f"Qt/PySide6 versions - PySide: {info['pyside_version']}, Qt Runtime: {info['qt_runtime']}")
    logger.debug(f"Feature flags: {FEATURES}")
