"""Simplified split manager for the new architecture."""

from typing import Optional, Dict, Any, List
from PySide6.QtWidgets import QWidget, QSplitter, QVBoxLayout
from PySide6.QtCore import Qt, Signal, QObject
from .content_pane import ContentPane


class SimpleSplitManager(QObject):
    """Manages the split layout for a single tab."""
    
    # Signals
    pane_added = Signal(str)      # pane_id
    pane_removed = Signal(str)    # pane_id
    active_pane_changed = Signal(str)  # pane_id
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.root_widget = None
        self.panes: Dict[str, ContentPane] = {}
        self.active_pane_id = None
        self.next_pane_id = 1
        
        # Create initial pane
        self._create_initial_pane()
    
    def _create_initial_pane(self):
        """Create the initial pane."""
        pane_id = self._generate_pane_id()
        pane = ContentPane(pane_id, widget_type="placeholder")
        self._connect_pane_signals(pane)
        
        self.root_widget = pane
        self.panes[pane_id] = pane
        self.active_pane_id = pane_id
        
        self.pane_added.emit(pane_id)
    
    def _generate_pane_id(self) -> str:
        """Generate a unique pane ID."""
        pane_id = f"pane_{self.next_pane_id}"
        self.next_pane_id += 1
        return pane_id
    
    def _connect_pane_signals(self, pane: ContentPane):
        """Connect signals from a pane."""
        pane.split_horizontal_requested.connect(self.split_pane_horizontal)
        pane.split_vertical_requested.connect(self.split_pane_vertical)
        pane.close_pane_requested.connect(self.close_pane)
        pane.pane_activated.connect(self.set_active_pane)
    
    def split_pane_horizontal(self, pane_id: str) -> Optional[str]:
        """Split a pane horizontally."""
        return self._split_pane(pane_id, Qt.Horizontal)
    
    def split_pane_vertical(self, pane_id: str) -> Optional[str]:
        """Split a pane vertically."""
        return self._split_pane(pane_id, Qt.Vertical)
    
    def _split_pane(self, pane_id: str, orientation: Qt.Orientation) -> Optional[str]:
        """Split a pane in the specified orientation."""
        if pane_id not in self.panes:
            return None
        
        old_pane = self.panes[pane_id]
        parent = old_pane.parent()
        
        # Create new pane
        new_pane_id = self._generate_pane_id()
        new_pane = ContentPane(new_pane_id, widget_type="placeholder")
        self._connect_pane_signals(new_pane)
        
        # Create new splitter
        new_splitter = QSplitter(orientation)
        
        # Handle different parent cases
        if old_pane == self.root_widget:
            # Old pane is the root - simple case
            new_splitter.addWidget(old_pane)
            new_splitter.addWidget(new_pane)
            self.root_widget = new_splitter
            
        elif isinstance(parent, QSplitter):
            # Old pane is in a splitter - need to replace it with new splitter
            index = parent.indexOf(old_pane)
            if index >= 0:
                # Save the sizes before manipulation
                sizes = parent.sizes()
                
                # Don't add widgets to new_splitter yet
                # First replace old_pane with new_splitter in parent
                parent.replaceWidget(index, new_splitter)
                
                # Now add the widgets to new_splitter
                # old_pane is no longer in parent, so we can safely add it
                new_splitter.addWidget(old_pane)
                new_splitter.addWidget(new_pane)
                
                # Try to restore sizes
                parent.setSizes(sizes)
        else:
            # Shouldn't happen, but handle it
            new_splitter.addWidget(old_pane)
            new_splitter.addWidget(new_pane)
            self.root_widget = new_splitter
        
        # Update tracking
        self.panes[new_pane_id] = new_pane
        
        # Make both widgets visible
        old_pane.show()
        new_pane.show()
        new_splitter.show()
        
        # Set equal sizes for the new splitter
        # Use a deferred call to ensure the splitter has been laid out
        from PySide6.QtCore import QTimer
        QTimer.singleShot(0, lambda: new_splitter.setSizes([500, 500]))
        
        # Make the new pane active
        self.set_active_pane(new_pane_id)
        
        self.pane_added.emit(new_pane_id)
        return new_pane_id
    
    def _replace_widget_in_parent(self, old_widget: QWidget, new_widget: QWidget):
        """Replace a widget in its parent container."""
        if old_widget == self.root_widget:
            # Replacing root
            self.root_widget = new_widget
            return
        
        parent = old_widget.parent()
        if isinstance(parent, QSplitter):
            index = parent.indexOf(old_widget)
            if index >= 0:
                # Save sizes before replacing
                sizes = parent.sizes()
                parent.replaceWidget(index, new_widget)
                # Restore sizes
                parent.setSizes(sizes)
    
    def close_pane(self, pane_id: str) -> bool:
        """Close a pane."""
        if pane_id not in self.panes:
            return False
        
        # Don't close if it's the last pane
        if len(self.panes) == 1:
            return False
        
        pane = self.panes[pane_id]
        parent = pane.parent()
        
        # Remove from tracking first
        del self.panes[pane_id]
        
        if isinstance(parent, QSplitter):
            # Remove pane from splitter (setParent(None) removes it)
            pane.setParent(None)
            
            # Check if splitter needs to be collapsed
            if parent.count() == 1:
                # Get the remaining child
                remaining_widget = parent.widget(0)
                
                # Get the splitter's parent
                grandparent = parent.parent()
                
                if parent == self.root_widget:
                    # Parent splitter is the root - make remaining widget the new root
                    remaining_widget.setParent(None)
                    self.root_widget = remaining_widget
                    
                elif isinstance(grandparent, QSplitter):
                    # Parent splitter is inside another splitter
                    index = grandparent.indexOf(parent)
                    if index >= 0:
                        # Save sizes
                        sizes = grandparent.sizes()
                        
                        # Use replaceWidget to replace the collapsing splitter with the remaining widget
                        # This avoids index issues
                        grandparent.replaceWidget(index, remaining_widget)
                        
                        # Restore sizes
                        grandparent.setSizes(sizes)
                
                # Clean up the collapsed splitter
                parent.deleteLater()
            
            # If splitter still has 2+ children, nothing more to do
        
        # Clean up the pane
        pane.deleteLater()
        
        # Update active pane if needed
        if self.active_pane_id == pane_id:
            # Set first available pane as active
            if self.panes:
                self.active_pane_id = next(iter(self.panes.keys()))
                self.active_pane_changed.emit(self.active_pane_id)
        
        self.pane_removed.emit(pane_id)
        return True
    
    def set_active_pane(self, pane_id: str) -> bool:
        """Set the active pane."""
        if pane_id not in self.panes:
            return False
        
        # Deactivate previous
        if self.active_pane_id and self.active_pane_id in self.panes:
            self.panes[self.active_pane_id].set_active(False)
        
        # Activate new
        self.active_pane_id = pane_id
        self.panes[pane_id].set_active(True)
        
        self.active_pane_changed.emit(pane_id)
        return True
    
    def get_active_pane_id(self) -> Optional[str]:
        """Get the active pane ID."""
        return self.active_pane_id
    
    def get_pane(self, pane_id: str) -> Optional[ContentPane]:
        """Get a pane by ID."""
        return self.panes.get(pane_id)
    
    def get_all_pane_ids(self) -> List[str]:
        """Get all pane IDs."""
        return list(self.panes.keys())
    
    def set_pane_widget(self, pane_id: str, widget_type: str, 
                       widget_state: Optional[Dict[str, Any]] = None) -> bool:
        """Set the widget type for a pane."""
        pane = self.panes.get(pane_id)
        if pane:
            pane.set_widget_type(widget_type, widget_state)
            return True
        return False
    
    def get_layout_state(self) -> Dict[str, Any]:
        """Get the current layout state for serialization."""
        def serialize_widget(widget: QWidget) -> Dict[str, Any]:
            if isinstance(widget, ContentPane):
                return {
                    'type': 'pane',
                    'pane_id': widget.get_pane_id(),
                    'widget_type': widget.get_widget_type(),
                    'widget_state': widget.get_widget_state()
                }
            elif isinstance(widget, QSplitter):
                return {
                    'type': 'splitter',
                    'orientation': 'horizontal' if widget.orientation() == Qt.Horizontal else 'vertical',
                    'sizes': widget.sizes(),
                    'children': [serialize_widget(widget.widget(i)) for i in range(widget.count())]
                }
            return {}
        
        return {
            'root': serialize_widget(self.root_widget) if self.root_widget else None,
            'active_pane_id': self.active_pane_id
        }
    
    def restore_layout_state(self, state: Dict[str, Any]) -> bool:
        """Restore layout from saved state."""
        # This would rebuild the entire widget tree from the saved state
        # For now, just return False to indicate not implemented
        return False