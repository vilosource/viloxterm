"""Example Hello World plugin."""

from viloapp_sdk import (
    IPlugin, PluginMetadata, IWidget, WidgetMetadata,
    WidgetPosition, EventType
)
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QTextEdit

class HelloWorldWidget(IWidget):
    """Hello World widget."""

    def get_metadata(self) -> WidgetMetadata:
        return WidgetMetadata(
            id="hello-world",
            title="Hello World",
            position=WidgetPosition.MAIN,
            icon="smile"
        )

    def create_widget(self, parent=None) -> QWidget:
        """Create the widget."""
        widget = QWidget(parent)
        layout = QVBoxLayout()

        self.text_edit = QTextEdit()
        self.text_edit.setPlainText("Hello from ViloxTerm Plugin!")

        button = QPushButton("Click Me!")
        button.clicked.connect(self._on_button_click)

        layout.addWidget(self.text_edit)
        layout.addWidget(button)
        widget.setLayout(layout)

        return widget

    def _on_button_click(self):
        """Handle button click."""
        self.text_edit.append("Button clicked!")

    def get_state(self):
        """Get widget state."""
        return {"text": self.text_edit.toPlainText()}

    def restore_state(self, state):
        """Restore widget state."""
        if "text" in state:
            self.text_edit.setPlainText(state["text"])

class HelloWorldPlugin(IPlugin):
    """Hello World plugin."""

    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            id="hello-world",
            name="Hello World Plugin",
            version="1.0.0",
            description="A simple Hello World plugin for ViloxTerm",
            author="ViloxTerm Team",
            homepage="https://github.com/viloxterm/hello-world",
            contributes={
                "widgets": [
                    {
                        "id": "hello-world",
                        "factory": "HelloWorldWidget"
                    }
                ],
                "commands": [
                    {
                        "id": "hello.sayHello",
                        "title": "Say Hello",
                        "category": "Hello World"
                    }
                ]
            }
        )

    def activate(self, context):
        """Activate the plugin."""
        self.context = context

        # Register command handler
        command_service = context.get_service("command")
        if command_service:
            command_service.register_command(
                "hello.sayHello",
                self._say_hello
            )

        # Subscribe to events
        context.subscribe_event(
            EventType.THEME_CHANGED,
            self._on_theme_changed
        )

        # Show notification
        notify_service = context.get_service("notification")
        if notify_service:
            notify_service.info("Hello World plugin activated!")

    def deactivate(self):
        """Deactivate the plugin."""
        # Unregister command
        command_service = self.context.get_service("command")
        if command_service:
            command_service.unregister_command("hello.sayHello")

    def _say_hello(self):
        """Say hello command handler."""
        notify_service = self.context.get_service("notification")
        if notify_service:
            notify_service.info("Hello from the plugin!")

    def _on_theme_changed(self, event):
        """Handle theme change."""
        print(f"Theme changed: {event.data}")