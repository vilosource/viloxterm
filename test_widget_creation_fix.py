#!/usr/bin/env python3
"""
Test that widgets are properly created on startup.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "packages/viloapp/src"))

from PySide6.QtWidgets import QApplication
from viloapp.ui.workspace import Workspace
from viloapp.core.app_widget_registry import register_builtin_widgets


def test_widget_creation():
    print("\n" + "=" * 60)
    print("Testing Widget Creation on Startup")
    print("=" * 60)

    app = QApplication.instance() or QApplication(sys.argv)

    # Register widgets first
    register_builtin_widgets()

    # Create workspace
    workspace = Workspace()
    workspace.ensure_has_tab()

    # Check if we have a tab
    model = workspace.model
    tabs = model.state.tabs

    print(f"\n✅ Number of tabs: {len(tabs)}")

    if tabs:
        tab = tabs[0]
        print(f"✅ Tab name: {tab.name}")
        print(f"✅ Tab has tree: {tab.tree is not None}")

        if tab.tree and tab.tree.root:
            panes = tab.tree.root.get_all_panes()
            print(f"✅ Number of panes: {len(panes)}")

            if panes:
                pane = panes[0]
                print(f"✅ Pane widget ID: {pane.widget_id}")

                # Check if the widget was actually created
                from viloapp.core.app_widget_manager import app_widget_manager

                # Check cached instances
                cached = len(app_widget_manager._widget_instances)
                print(f"✅ Widgets in cache: {cached}")

                # Try to verify the widget was rendered
                if tab.id in workspace.tab_views:
                    tab_view = workspace.tab_views[tab.id]
                    print(f"✅ Tab view exists: {tab_view is not None}")

                    if hasattr(tab_view, "tree_view"):
                        tree_view = tab_view.tree_view
                        if tree_view and hasattr(tree_view, "current_root_widget"):
                            has_widget = tree_view.current_root_widget is not None
                            print(f"✅ Tree has root widget: {has_widget}")
                            if not has_widget:
                                print("   Widget is None!")
                        else:
                            print("❌ Tree view has no current_root_widget attribute")
                    else:
                        print("❌ Tab view has no tree_view attribute")
                else:
                    print("❌ Tab not in tab_views")

    else:
        print("❌ No tabs created!")

    print("\n" + "=" * 60)
    print("Test Complete")
    print("=" * 60)

    workspace.show()
    return app.exec() if len(sys.argv) > 1 and sys.argv[1] == "--run" else 0


if __name__ == "__main__":
    sys.exit(test_widget_creation())
