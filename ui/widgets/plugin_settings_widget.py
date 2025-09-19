"""Plugin settings widget."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget,
    QPushButton, QLabel, QGroupBox, QTextEdit,
    QListWidgetItem, QMessageBox
)
from PySide6.QtCore import Qt

class PluginSettingsWidget(QWidget):
    """Widget for managing plugins."""

    def __init__(self, plugin_manager, parent=None):
        super().__init__(parent)
        self.plugin_manager = plugin_manager
        self.setup_ui()
        self.load_plugins()

    def setup_ui(self):
        """Setup the UI."""
        layout = QVBoxLayout()

        # Plugin list
        self.plugin_list = QListWidget()
        self.plugin_list.currentItemChanged.connect(self.on_plugin_selected)

        # Plugin details
        self.details_group = QGroupBox("Plugin Details")
        details_layout = QVBoxLayout()

        self.name_label = QLabel()
        self.version_label = QLabel()
        self.author_label = QLabel()
        self.description_text = QTextEdit()
        self.description_text.setReadOnly(True)
        self.description_text.setMaximumHeight(100)

        details_layout.addWidget(self.name_label)
        details_layout.addWidget(self.version_label)
        details_layout.addWidget(self.author_label)
        details_layout.addWidget(self.description_text)

        self.details_group.setLayout(details_layout)

        # Control buttons
        button_layout = QHBoxLayout()

        self.enable_button = QPushButton("Enable")
        self.enable_button.clicked.connect(self.enable_plugin)

        self.disable_button = QPushButton("Disable")
        self.disable_button.clicked.connect(self.disable_plugin)

        self.reload_button = QPushButton("Reload")
        self.reload_button.clicked.connect(self.reload_plugin)

        self.discover_button = QPushButton("Discover New")
        self.discover_button.clicked.connect(self.discover_plugins)

        button_layout.addWidget(self.enable_button)
        button_layout.addWidget(self.disable_button)
        button_layout.addWidget(self.reload_button)
        button_layout.addStretch()
        button_layout.addWidget(self.discover_button)

        # Add to main layout
        layout.addWidget(QLabel("Installed Plugins:"))
        layout.addWidget(self.plugin_list)
        layout.addWidget(self.details_group)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def load_plugins(self):
        """Load plugin list."""
        self.plugin_list.clear()

        plugins = self.plugin_manager.list_plugins()
        for plugin in plugins:
            item = QListWidgetItem(plugin['name'])
            item.setData(Qt.UserRole, plugin)

            # Set icon based on state
            if plugin['state'] == 'ACTIVATED':
                item.setText(f"✓ {plugin['name']}")
            elif plugin['state'] == 'FAILED':
                item.setText(f"✗ {plugin['name']}")

            self.plugin_list.addItem(item)

    def on_plugin_selected(self, current, previous):
        """Handle plugin selection."""
        if not current:
            return

        plugin_data = current.data(Qt.UserRole)
        if not plugin_data:
            return

        # Get full metadata
        metadata = self.plugin_manager.get_plugin_metadata(plugin_data['id'])
        if metadata:
            self.name_label.setText(f"Name: {metadata['name']}")
            self.version_label.setText(f"Version: {metadata['version']}")
            self.author_label.setText(f"Author: {metadata['author']}")
            self.description_text.setPlainText(metadata['description'])

            # Update button states
            state = metadata['state']
            self.enable_button.setEnabled(state not in ['ACTIVATED', 'LOADED'])
            self.disable_button.setEnabled(state == 'ACTIVATED')
            self.reload_button.setEnabled(state in ['ACTIVATED', 'FAILED'])

    def enable_plugin(self):
        """Enable selected plugin."""
        current = self.plugin_list.currentItem()
        if current:
            plugin_data = current.data(Qt.UserRole)
            if self.plugin_manager.enable_plugin(plugin_data['id']):
                QMessageBox.information(self, "Success", f"Plugin {plugin_data['name']} enabled")
                self.load_plugins()
            else:
                QMessageBox.warning(self, "Error", f"Failed to enable {plugin_data['name']}")

    def disable_plugin(self):
        """Disable selected plugin."""
        current = self.plugin_list.currentItem()
        if current:
            plugin_data = current.data(Qt.UserRole)
            if self.plugin_manager.disable_plugin(plugin_data['id']):
                QMessageBox.information(self, "Success", f"Plugin {plugin_data['name']} disabled")
                self.load_plugins()
            else:
                QMessageBox.warning(self, "Error", f"Failed to disable {plugin_data['name']}")

    def reload_plugin(self):
        """Reload selected plugin."""
        current = self.plugin_list.currentItem()
        if current:
            plugin_data = current.data(Qt.UserRole)
            if self.plugin_manager.reload_plugin(plugin_data['id']):
                QMessageBox.information(self, "Success", f"Plugin {plugin_data['name']} reloaded")
                self.load_plugins()
            else:
                QMessageBox.warning(self, "Error", f"Failed to reload {plugin_data['name']}")

    def discover_plugins(self):
        """Discover new plugins."""
        new_plugins = self.plugin_manager.discover_plugins()
        if new_plugins:
            QMessageBox.information(
                self, "Plugins Discovered",
                f"Found {len(new_plugins)} new plugins"
            )
            self.load_plugins()
        else:
            QMessageBox.information(self, "No New Plugins", "No new plugins found")