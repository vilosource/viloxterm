#!/usr/bin/env python3
"""
Debug why we get a white empty tab on startup.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "packages/viloapp/src"))

import logging
from PySide6.QtWidgets import QApplication
from viloapp.ui.workspace import Workspace
from viloapp.core.app_widget_registry import register_builtin_widgets

logging.basicConfig(level=logging.DEBUG, format="%(name)s - %(levelname)s - %(message)s")


def test_white_tab():
    print("\n" + "=" * 60)
    print("Debugging White Tab Issue")
    print("=" * 60)

    QApplication.instance() or QApplication(sys.argv)

    # Register widgets first
    register_builtin_widgets()

    # Create workspace
    workspace = Workspace()
    workspace.ensure_has_tab()

    # Check model state
    model = workspace.model
    tabs = model.state.tabs

    print("\n1. Model State:")
    print(f"   - Tabs: {len(tabs)}")

    if tabs:
        tab = tabs[0]
        print(f"   - Tab name: {tab.name}")
        print(f"   - Tab ID: {tab.id[:8]}")
        print(f"   - Tree exists: {tab.tree is not None}")

        if tab.tree and tab.tree.root:
            print(f"   - Root node type: {tab.tree.root.node_type}")
            print(f"   - Root is leaf: {tab.tree.root.is_leaf()}")
            print(f"   - Root has pane: {tab.tree.root.pane is not None}")

            if tab.tree.root.pane:
                pane = tab.tree.root.pane
                print(f"   - Pane ID: {pane.id[:8]}")
                print(f"   - Widget ID: {pane.widget_id}")

    print("\n2. UI State:")
    print(f"   - Tab views: {len(workspace.tab_views)}")

    if tabs and tabs[0].id in workspace.tab_views:
        tab_view = workspace.tab_views[tabs[0].id]
        print("   - TabView exists: True")
        print(f"   - Has tree_view: {hasattr(tab_view, 'tree_view')}")

        if hasattr(tab_view, "tree_view") and tab_view.tree_view:
            tree_view = tab_view.tree_view
            print("   - TreeView exists: True")
            print(f"   - TreeView.root: {tree_view.root is not None}")
            print(f"   - TreeView.current_root_widget: {tree_view.current_root_widget}")

            # Try to manually call render_node
            if tree_view.root:
                print("\n3. Manual render_node test:")
                widget = tree_view.render_node(tree_view.root)
                print(f"   - render_node returned: {widget}")
                print(f"   - Widget type: {type(widget).__name__ if widget else 'None'}")

    print("\n" + "=" * 60)

    workspace.show()
    return 0


if __name__ == "__main__":
    sys.exit(test_white_tab())
