"""Qt renderer for tree-based split model."""

from typing import Optional, Dict
from PySide6.QtWidgets import QWidget, QSplitter, QLabel, QVBoxLayout
from PySide6.QtCore import Qt, Signal, QObject
from tree_split_model import TreeNode, LeafNode, SplitNode, TreeSplitModel


class LeafWidget(QWidget):
    """Widget representing a leaf node."""
    
    # Signals
    split_right_requested = Signal(str)
    split_bottom_requested = Signal(str)
    close_requested = Signal(str)
    activated = Signal(str)
    
    def __init__(self, leaf_id: str, widget_type: str = "placeholder", parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.leaf_id = leaf_id
        self.widget_type = widget_type
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create content based on widget type
        self.content = self.create_content_widget()
        layout.addWidget(self.content)
        
        # Enable context menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        
    def create_content_widget(self) -> QWidget:
        """Create the actual content widget."""
        label = QLabel(f"{self.widget_type}\n[{self.leaf_id}]")
        label.setAlignment(Qt.AlignCenter)
        
        # Style based on widget type
        styles = {
            "placeholder": "background: #2d2d30; color: #969696;",
            "editor": "background: #1e1e1e; color: #d4d4d4;",
            "terminal": "background: #0c0c0c; color: #cccccc;",
            "explorer": "background: #252526; color: #cccccc;",
            "output": "background: #1e1e1e; color: #cccccc;",
        }
        
        style = styles.get(self.widget_type, styles["placeholder"])
        label.setStyleSheet(f"""
            QLabel {{
                {style}
                border: 1px solid #3c3c3c;
                padding: 20px;
                font-size: 14px;
            }}
        """)
        
        return label
    
    def show_context_menu(self, pos):
        """Show context menu."""
        from PySide6.QtWidgets import QMenu
        
        menu = QMenu(self)
        
        # Split actions
        split_right = menu.addAction("Split Right")
        split_right.triggered.connect(lambda: self.split_right_requested.emit(self.leaf_id))
        
        split_bottom = menu.addAction("Split Bottom")
        split_bottom.triggered.connect(lambda: self.split_bottom_requested.emit(self.leaf_id))
        
        menu.addSeparator()
        
        # Widget type actions
        for widget_type in ["editor", "terminal", "explorer", "output", "placeholder"]:
            action = menu.addAction(f"Set {widget_type.title()}")
            action.triggered.connect(lambda checked, wt=widget_type: self.set_widget_type(wt))
        
        menu.addSeparator()
        
        # Close action
        close = menu.addAction("Close Pane")
        close.triggered.connect(lambda: self.close_requested.emit(self.leaf_id))
        
        menu.exec(self.mapToGlobal(pos))
    
    def set_widget_type(self, widget_type: str):
        """Change the widget type."""
        self.widget_type = widget_type
        # Replace content widget
        self.layout().removeWidget(self.content)
        self.content.deleteLater()
        self.content = self.create_content_widget()
        self.layout().addWidget(self.content)
    
    def set_active(self, active: bool):
        """Set active state."""
        if active:
            self.content.setStyleSheet(self.content.styleSheet() + """
                QLabel {
                    border: 2px solid #0078d4 !important;
                }
            """)
        else:
            # Reset to normal style
            self.set_widget_type(self.widget_type)
    
    def mousePressEvent(self, event):
        """Handle mouse press."""
        if event.button() == Qt.LeftButton:
            self.activated.emit(self.leaf_id)
        super().mousePressEvent(event)


class TreeQtRenderer(QObject):
    """Renders a tree model to Qt widgets."""
    
    # Signals
    split_right_requested = Signal(str)
    split_bottom_requested = Signal(str)
    close_requested = Signal(str)
    leaf_activated = Signal(str)
    
    def __init__(self, model: TreeSplitModel, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.model = model
        self.leaf_widgets: Dict[str, LeafWidget] = {}
        self.root_widget: Optional[QWidget] = None
        
    def render(self) -> QWidget:
        """Render the tree model to Qt widgets."""
        # Clear existing widgets
        self.leaf_widgets.clear()
        
        # Render from root
        self.root_widget = self._render_node(self.model.root)
        
        # Update active state
        if self.model.active_leaf_id:
            self._update_active_leaf(self.model.active_leaf_id)
        
        return self.root_widget
    
    def _render_node(self, node: TreeNode) -> QWidget:
        """Render a single node."""
        if isinstance(node, LeafNode):
            # Create leaf widget
            widget = LeafWidget(node.id, node.widget_type)
            
            # Connect signals
            widget.split_right_requested.connect(self.split_right_requested.emit)
            widget.split_bottom_requested.connect(self.split_bottom_requested.emit)
            widget.close_requested.connect(self.close_requested.emit)
            widget.activated.connect(self.leaf_activated.emit)
            
            # Track widget
            self.leaf_widgets[node.id] = widget
            
            return widget
            
        elif isinstance(node, SplitNode):
            # Create splitter
            orientation = Qt.Horizontal if node.orientation == "vertical" else Qt.Vertical
            splitter = QSplitter(orientation)
            
            # Render children
            if node.first:
                first_widget = self._render_node(node.first)
                splitter.addWidget(first_widget)
                
            if node.second:
                second_widget = self._render_node(node.second)
                splitter.addWidget(second_widget)
            
            # Apply ratio
            total = 1000  # Use fixed total for ratio calculation
            first_size = int(total * node.ratio)
            second_size = total - first_size
            splitter.setSizes([first_size, second_size])
            
            # Connect splitter move to update ratio
            splitter.splitterMoved.connect(
                lambda pos, index: self._on_splitter_moved(node, splitter)
            )
            
            return splitter
        
        # Fallback
        return QWidget()
    
    def _on_splitter_moved(self, split_node: SplitNode, splitter: QSplitter):
        """Handle splitter movement."""
        sizes = splitter.sizes()
        if sum(sizes) > 0:
            ratio = sizes[0] / sum(sizes)
            self.model.update_split_ratio(split_node, ratio)
    
    def _update_active_leaf(self, leaf_id: str):
        """Update active leaf visual state."""
        for lid, widget in self.leaf_widgets.items():
            widget.set_active(lid == leaf_id)
    
    def update_leaf_widget(self, leaf_id: str, widget_type: str):
        """Update a leaf widget's type."""
        if leaf_id in self.leaf_widgets:
            self.leaf_widgets[leaf_id].set_widget_type(widget_type)
            
            # Update model
            leaf = self.model.find_leaf(leaf_id)
            if leaf:
                leaf.widget_type = widget_type