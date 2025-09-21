"""Editor widget factory."""

import logging
from typing import Optional, Dict, Any

from PySide6.QtWidgets import QWidget
from viloapp_sdk import IWidget, WidgetMetadata, WidgetPosition

from .editor import CodeEditor

logger = logging.getLogger(__name__)


class EditorWidgetFactory(IWidget):
    """Factory for creating editor widgets."""

    def __init__(self):
        self._instances = {}  # Track widget instances

    def get_widget_id(self) -> str:
        """Get unique widget identifier."""
        return "editor"

    def get_title(self) -> str:
        """Get widget display title."""
        return "Editor"

    def get_icon(self) -> Optional[str]:
        """Get widget icon identifier."""
        return "file-text"

    def create_instance(self, instance_id: str) -> QWidget:
        """Create widget instance with unique ID."""
        widget = CodeEditor()
        self._instances[instance_id] = widget
        return widget

    def destroy_instance(self, instance_id: str) -> None:
        """Destroy widget instance and clean up resources."""
        if instance_id in self._instances:
            widget = self._instances[instance_id]
            # Save any unsaved changes before destroying
            if hasattr(widget, 'close_file'):
                widget.close_file()
            widget.deleteLater()
            del self._instances[instance_id]

    def handle_command(self, command: str, args: Dict[str, Any]) -> Any:
        """Handle widget-specific commands."""
        if command == "open_file":
            # Open file in specific editor instance
            instance_id = args.get("instance_id")
            file_path = args.get("file_path", "")

            if instance_id in self._instances:
                widget = self._instances[instance_id]
                if hasattr(widget, 'open_file'):
                    widget.open_file(file_path)
                    return True
            return False

        elif command == "save_file":
            # Save file in specific editor instance
            instance_id = args.get("instance_id")

            if instance_id in self._instances:
                widget = self._instances[instance_id]
                if hasattr(widget, 'save_file'):
                    widget.save_file()
                    return True
            return False

        elif command == "get_text":
            # Get text content from specific editor instance
            instance_id = args.get("instance_id")

            if instance_id in self._instances:
                widget = self._instances[instance_id]
                if hasattr(widget, 'toPlainText'):
                    return widget.toPlainText()
            return ""

        elif command == "set_text":
            # Set text content in specific editor instance
            instance_id = args.get("instance_id")
            text = args.get("text", "")

            if instance_id in self._instances:
                widget = self._instances[instance_id]
                if hasattr(widget, 'setPlainText'):
                    widget.setPlainText(text)
                    return True
            return False

        elif command == "find_text":
            # Find text in specific editor instance
            instance_id = args.get("instance_id")
            pattern = args.get("pattern", "")

            if instance_id in self._instances:
                widget = self._instances[instance_id]
                if hasattr(widget, 'find'):
                    return widget.find(pattern)
            return False

        elif command == "replace_text":
            # Replace text in specific editor instance
            instance_id = args.get("instance_id")
            find_text = args.get("find", "")
            replace_text = args.get("replace", "")

            if instance_id in self._instances:
                widget = self._instances[instance_id]
                # Basic replace functionality
                if hasattr(widget, 'toPlainText') and hasattr(widget, 'setPlainText'):
                    current_text = widget.toPlainText()
                    new_text = current_text.replace(find_text, replace_text)
                    widget.setPlainText(new_text)
                    return True
            return False

        elif command == "get_instances":
            # Get list of active editor instances
            return {
                instance_id: {
                    "has_content": bool(widget.toPlainText() if hasattr(widget, 'toPlainText') else False),
                    "file_path": getattr(widget, 'current_file', None)
                }
                for instance_id, widget in self._instances.items()
            }

        return None

    def get_state(self) -> Dict[str, Any]:
        """Get widget state."""
        return {
            "instance_count": len(self._instances),
            "instances": {
                instance_id: {
                    "file_path": getattr(widget, 'current_file', None),
                    "has_unsaved_changes": getattr(widget, 'document', lambda: None)().isModified() if hasattr(widget, 'document') else False
                }
                for instance_id, widget in self._instances.items()
            }
        }

    def restore_state(self, state: Dict[str, Any]) -> None:
        """Restore widget state."""
        # Could restore open files and content
        # For now, just log that state was provided
        if "instances" in state:
            logger.info(f"Could restore {len(state['instances'])} editor instances")
        pass