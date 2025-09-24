#!/usr/bin/env python3
"""
Check if widgets are actually rendering with content.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "packages/viloapp/src"))

from PySide6.QtWidgets import QApplication
from viloapp.ui.workspace import Workspace
from viloapp.core.app_widget_registry import register_builtin_widgets
from viloapp.core.app_widget_manager import app_widget_manager


def test_widget_rendering():
    print("\n" + "=" * 60)
    print("Testing Widget Rendering")
    print("=" * 60)

    app = QApplication.instance() or QApplication(sys.argv)

    # Register widgets first
    register_builtin_widgets()

    # Create workspace
    workspace = Workspace()
    workspace.ensure_has_tab()

    # Check what widget was created
    model = workspace.model
    if model.state.tabs:
        tab = model.state.tabs[0]
        if tab.tree and tab.tree.root and tab.tree.root.pane:
            pane = tab.tree.root.pane
            print(f"\n✅ Pane widget ID: {pane.widget_id}")

            # Check if widget is in cache
            cached_widgets = app_widget_manager._widget_instances
            print(f"✅ Cached widgets: {len(cached_widgets)}")
            for pane_id, widget in cached_widgets.items():
                print(f"   - Pane {pane_id[:8]}: {type(widget).__name__}")

                # Check widget properties
                try:
                    is_visible = widget.isVisible()
                    has_children = widget.children()
                    print(f"     Visible: {is_visible}, Children: {len(has_children)}")

                    # Check if it has any content
                    if hasattr(widget, "layout"):
                        layout = widget.layout()
                        if layout:
                            count = layout.count()
                            print(f"     Layout items: {count}")
                except Exception as e:
                    print(f"     Error checking widget: {e}")

    # Check the tab view
    if workspace.tab_views:
        for tab_id, tab_view in workspace.tab_views.items():
            print(f"\n✅ TabView for {tab_id[:8]}:")
            if hasattr(tab_view, "tree_view") and tab_view.tree_view:
                tree_view = tab_view.tree_view
                if tree_view.current_root_widget:
                    widget = tree_view.current_root_widget
                    print(f"   Root widget type: {type(widget).__name__}")

                    # Check PaneView content
                    if hasattr(widget, "content_widget"):
                        content = widget.content_widget
                        print(f"   Content widget: {type(content).__name__ if content else 'None'}")
                        if content:
                            print(f"   Content visible: {content.isVisible()}")
                            print(f"   Content size: {content.size()}")
                    else:
                        print("   No content_widget attribute")

    print("\n" + "=" * 60)

    workspace.show()

    # After showing, check again
    print("\nAfter show():")
    if workspace.tab_views:
        for tab_id, tab_view in workspace.tab_views.items():
            if hasattr(tab_view, "tree_view") and tab_view.tree_view:
                if tree_view.current_root_widget and hasattr(
                    tree_view.current_root_widget, "content_widget"
                ):
                    content = tree_view.current_root_widget.content_widget
                    if content:
                        print(f"   Content size after show: {content.size()}")

    return app.exec() if len(sys.argv) > 1 and sys.argv[1] == "--run" else 0


if __name__ == "__main__":
    sys.exit(test_widget_rendering())
