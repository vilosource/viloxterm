# Split Pane Tree Structure Documentation

## Overview

The split pane system uses a **binary tree data structure** where:
- **Leaf nodes** contain actual widgets (terminals, editors, etc.)
- **Split nodes** represent the division between two panes
- The tree dynamically grows with splits and shrinks with closes

## Tree Node Types

### LeafNode
```python
@dataclass
class LeafNode:
    type: str = "leaf"
    id: str                           # Unique identifier (8-char UUID)
    widget_type: WidgetType           # TERMINAL, TEXT_EDITOR, PLACEHOLDER, etc.
    app_widget: Optional[AppWidget]   # The actual content widget
    parent: Optional[SplitNode]       # Parent split node (None for root)
```

### SplitNode
```python
@dataclass
class SplitNode:
    type: str = "split"
    id: str                           # Unique identifier (8-char UUID)
    orientation: str                  # "horizontal" or "vertical"
    ratio: float = 0.5               # Split ratio (0.0 to 1.0)
    first: Optional[Node]            # Left/Top child
    second: Optional[Node]           # Right/Bottom child
    parent: Optional[SplitNode]      # Parent split node (None for root)
```

## Visual Tree Representation

### Initial State (Single Pane)
```
[Root: Leaf-A]
     │
     A (Terminal)
```

### After First Horizontal Split
```
      [Root: Split-H]
           /    \
      Leaf-A    Leaf-B
         │        │
    A (Term)  B (Term)

Visual Layout:
┌─────────┬─────────┐
│    A    │    B    │
└─────────┴─────────┘
```

### After Vertical Split on B
```
         [Root: Split-H]
              /    \
         Leaf-A   Split-V
            │       /  \
       A (Term) Leaf-B Leaf-C
                  │      │
              B (Term) C (Term)

Visual Layout:
┌─────────┬─────────┐
│         │    B    │
│    A    ├─────────┤
│         │    C    │
└─────────┴─────────┘
```

### Complex Layout Example
```
                [Root: Split-H]
                    /      \
              Split-V      Split-V
               /  \         /  \
           Leaf-A Leaf-B Leaf-C Split-H
              │      │      │     /  \
          A (Term) B (Ed) C (Term) D  E

Visual Layout:
┌─────────┬─────────┐
│    A    │    C    │
├─────────┼────┬────┤
│    B    │ D  │ E  │
└─────────┴────┴────┘
```

## Tree Operations

### 1. Split Operation (`split_pane`)

**Algorithm:**
```
1. Find target leaf node by ID
2. Create new leaf node with same widget type
3. Create new split node with specified orientation
4. Replace target leaf with split node in tree:
   - Split becomes parent of both old and new leaf
   - If target had parent, update parent's child reference
   - If target was root, split becomes new root
5. Set split ratio to 0.5 (50/50 split)
6. Update parent references
7. Trigger view refresh
```

**Example: Splitting Leaf-A Horizontally**
```
Before:           After:
  [A]      →    [Split-H]
                  /    \
                [A]    [B]
```

### 2. Close Operation (`close_pane`)

**Algorithm:**
```
1. Find target leaf node by ID
2. Cannot close if it's the only pane (root)
3. Find parent split node
4. Find sibling node (other child of parent)
5. Clean up target leaf's AppWidget
6. Promote sibling to parent's position:
   - If parent has grandparent, replace parent with sibling
   - If parent is root, sibling becomes new root
7. Update parent references
8. Remove target leaf from leaves dictionary
9. Trigger view refresh
```

**Example: Closing Leaf-B**
```
Before:                After:
  [Split-H]              [A]
    /    \         →
  [A]    [B]
```

### 3. Tree Traversal (`traverse_tree`)

**Algorithm (Depth-First Search):**
```python
def traverse(node):
    if node is LeafNode:
        yield node
    elif node is SplitNode:
        yield from traverse(node.first)
        yield from traverse(node.second)
```

**Traversal Order Example:**
```
     [Split-H]
      /     \
    [A]    [Split-V]
             /    \
           [B]    [C]

Order: A → B → C
```

## Split Orientation Behavior

### Horizontal Split (`Ctrl+\`)
- Creates **side-by-side** panes
- Split node orientation: `"horizontal"`
- First child: Left pane
- Second child: Right pane
- Splitter: Vertical line

```
Before:        After:
┌─────┐      ┌──┬──┐
│  A  │  →   │A │B │
└─────┘      └──┴──┘
```

### Vertical Split (`Ctrl+Shift+\`)
- Creates **top-and-bottom** panes
- Split node orientation: `"vertical"`
- First child: Top pane
- Second child: Bottom pane
- Splitter: Horizontal line

```
Before:        After:
┌─────┐      ┌─────┐
│  A  │  →   │  A  │
└─────┘      ├─────┤
             │  B  │
             └─────┘
```

## Model-View Synchronization

### Model → View Flow
1. **Model Update**: Tree structure changes (split/close)
2. **Signal Emission**: Model notifies view of change
3. **View Refresh**: `refresh_view()` called
4. **Tree Walk**: View traverses model tree
5. **Widget Creation**: Creates QSplitters and PaneContent wrappers
6. **Layout Update**: Arranges widgets to match tree structure

### View → Model Flow
1. **User Action**: Click split button or press hotkey
2. **Signal Emission**: PaneContent emits request signal
3. **AppWidget Relay**: AppWidget calls model operation
4. **Model Update**: Tree structure modified
5. **Refresh Trigger**: Model triggers view refresh

## Tree Invariants

1. **Binary Tree**: Each split node has exactly 2 children
2. **Leaf Content**: Only leaf nodes contain AppWidgets
3. **Parent References**: All non-root nodes have valid parent
4. **ID Uniqueness**: Each node has a unique ID
5. **Root Rule**: Exactly one root node (leaf or split)
6. **Widget Ownership**: AppWidgets owned by model, not view

## Performance Characteristics

- **Split**: O(1) - Direct node replacement
- **Close**: O(1) - Direct sibling promotion  
- **Find Leaf**: O(1) - Hash map lookup
- **Find Node**: O(n) - Tree traversal
- **Traverse**: O(n) - Visit all nodes
- **Refresh View**: O(n) - Rebuild all widgets

## Edge Cases Handled

1. **Cannot close last pane** - Prevents empty window
2. **Split maintains widget type** - New pane inherits type
3. **Sibling promotion on close** - Tree remains valid
4. **Root replacement** - Handles root node changes
5. **Parent reference updates** - Maintains bidirectional links
6. **AppWidget cleanup** - Prevents memory leaks

## State Persistence

The tree structure can be serialized to JSON:
```json
{
  "type": "split",
  "orientation": "horizontal",
  "ratio": 0.6,
  "first": {
    "type": "leaf",
    "id": "a1b2c3d4",
    "widget_type": "terminal"
  },
  "second": {
    "type": "split",
    "orientation": "vertical",
    "ratio": 0.5,
    "first": {...},
    "second": {...}
  }
}
```

This allows complete layout restoration on application restart.