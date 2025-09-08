# VSCode-Style PySide6 Application Implementation Guide

## Comprehensive Research Summary for Collapsible Sidebar Layout Project

### **Core Architecture Requirements**

1. **QMainWindow** as the base - provides built-in support for:
   - QToolBar (Activity Bar)
   - QDockWidget (Collapsible Sidebar)
   - Central widget area (Workspace)
   - QStatusBar

2. **Key Widget Classes**:
   - **QToolBar** - vertical, icon-only activity bar (44-56px width)
   - **QDockWidget** or **QSplitter** - collapsible sidebar container
   - **QStackedWidget** - switch between sidebar views (Explorer, Search, Git)
   - **Nested QSplitters** - recursive split pane functionality
   - **QTabWidget** - tabs within each pane

### **Critical Implementation Insights**

**For Split Panes (Workspace)**:
- Use nested QSplitters for recursive splitting
- Add widgets using `addWidget()` only (not layouts)
- Each splitter can be horizontal or vertical
- QSplitters naturally support resize handles

**For Collapsible Sidebar**:
- Two approaches:
  1. QDockWidget with `setFeatures()` to disable floating/moving
  2. QSplitter with width animation to 0 for collapse

**For Activity Bar**:
- QToolBar with `setOrientation(Qt.Vertical)`
- Set property `"type": "activitybar"` for VSCode styling
- Make non-movable and non-floatable

### **Essential Libraries & Tools**

1. **QtVSCodeStyle** - Provides authentic VSCode theming
   ```python
   activitybar.setProperty("type", "activitybar")
   ```

2. **Qt-Advanced-Docking-System** - Professional docking framework with Python bindings

3. **PySide6-Collapsible-Widget** - Ready-made collapsible components

### **Animation Implementation**

```python
# Smooth sidebar collapse/expand
from PySide6.QtCore import QPropertyAnimation, QEasingCurve

self.sidebar_anim = QPropertyAnimation(self.sidebar, b"maximumWidth")
self.sidebar_anim.setDuration(300)
self.sidebar_anim.setEasingCurve(QEasingCurve.InOutCubic)

# Collapse
self.sidebar_anim.setEndValue(0)

# Expand
self.sidebar_anim.setEndValue(250)
```

### **State Persistence**

```python
from PySide6.QtCore import QSettings

# Save state
settings = QSettings("YourCompany", "YourApp")
settings.setValue("geometry", self.saveGeometry())
settings.setValue("windowState", self.saveState())
settings.setValue("splitterSizes", self.splitter.saveState())
settings.setValue("sidebarWidth", self.sidebar.width())
settings.setValue("sidebarVisible", self.sidebar.isVisible())

# Restore state
self.restoreGeometry(settings.value("geometry"))
self.restoreState(settings.value("windowState"))
self.splitter.restoreState(settings.value("splitterSizes"))
```

### **Project Structure Recommendations**

```
viloapp/
├── main.py                 # Application entry point
├── ui/
│   ├── main_window.py      # QMainWindow subclass
│   ├── activity_bar.py     # Vertical toolbar implementation
│   ├── sidebar.py          # Collapsible sidebar
│   ├── workspace.py        # Split pane manager
│   └── widgets/
│       ├── split_tree.py   # Recursive splitter logic
│       └── tab_container.py # Tab management
├── models/
│   └── layout_state.py     # JSON serialization for layout
└── resources/
    └── styles/              # QtVSCodeStyle integration
```

### **Key Implementation Patterns**

1. **Split Tree Model**: Maintain a tree structure representing splits
2. **View Contribution System**: Allow plugins to register custom views
3. **Command Pattern**: For actions like split, close, move tabs
4. **Observer Pattern**: For activity bar button ↔ sidebar synchronization

### **Common Pitfalls to Avoid**

- Don't use `setLayout()` on QSplitter - use `addWidget()`
- First splitter handle is always invisible
- QDockWidget geometry isn't directly saveable when floating
- Animations need Qt properties (use `setMaximumWidth` not `resize`)

### **Implementation Steps**

1. Start with basic QMainWindow + QToolBar + QSplitter layout
2. Implement collapsible sidebar with animation
3. Add recursive splitter functionality
4. Integrate QTabWidget for each pane
5. Implement QSettings persistence
6. Apply QtVSCodeStyle for authentic look

### **Code Examples from Research**

#### Nested Splitters Pattern
```python
# Create horizontal splitter
h_splitter = QSplitter(Qt.Horizontal)
h_splitter.addWidget(widget1)
h_splitter.addWidget(widget2)

# Create vertical splitter containing the horizontal one
v_splitter = QSplitter(Qt.Vertical)
v_splitter.addWidget(h_splitter)
v_splitter.addWidget(widget3)

# Set as central widget
self.setCentralWidget(v_splitter)
```

#### Activity Bar Setup
```python
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QToolBar, QAction

activity_bar = QToolBar()
activity_bar.setOrientation(Qt.Vertical)
activity_bar.setMovable(False)
activity_bar.setFloatable(False)
activity_bar.setIconSize(QSize(24, 24))
activity_bar.setFixedWidth(48)

# Add actions for each sidebar view
explorer_action = QAction(QIcon("explorer.svg"), "Explorer", self)
search_action = QAction(QIcon("search.svg"), "Search", self)
git_action = QAction(QIcon("git.svg"), "Git", self)

activity_bar.addAction(explorer_action)
activity_bar.addAction(search_action)
activity_bar.addAction(git_action)
```

#### Sidebar Toggle with Animation
```python
def toggle_sidebar(self):
    if self.sidebar.width() > 0:
        # Collapse
        self.sidebar_anim.setStartValue(self.sidebar.width())
        self.sidebar_anim.setEndValue(0)
        self.last_sidebar_width = self.sidebar.width()
    else:
        # Expand
        self.sidebar_anim.setStartValue(0)
        self.sidebar_anim.setEndValue(self.last_sidebar_width or 250)
    
    self.sidebar_anim.start()
```

### **References & Resources**

- **Official Documentation**:
  - Qt for Python (PySide6): https://doc.qt.io/qtforpython-6/
  - QMainWindow: https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QMainWindow.html
  - QSplitter: https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QSplitter.html
  - QDockWidget: https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QDockWidget.html

- **Libraries**:
  - QtVSCodeStyle: https://github.com/5yutan5/QtVSCodeStyle
  - Qt-Advanced-Docking-System: https://github.com/githubuser0xFFFF/Qt-Advanced-Docking-System
  - PySide6-Collapsible-Widget: https://github.com/EsoCoding/PySide6-Collapsible-Widget

- **Tutorials**:
  - PythonGUIs PySide6 Tutorial: https://www.pythonguis.com/pyside6-tutorial/
  - Animated Widgets: https://www.pythonguis.com/tutorials/pyside6-animated-widgets/

This implementation guide provides all the foundational knowledge needed to build a professional VSCode-style desktop application with PySide6.