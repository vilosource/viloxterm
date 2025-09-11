# Directional Pane Navigation with Alt+Arrow Keys

## Overview

This document describes the algorithm for navigating between split panes using Alt+Arrow keys. The navigation system uses the tree structure of splits combined with position tracking to find the most intuitive target pane.

## Core Concepts

### 1. Tree Structure Encodes Spatial Layout

The split tree inherently represents spatial relationships:
- **Horizontal Split**: `first` child is LEFT, `second` child is RIGHT
- **Vertical Split**: `first` child is TOP, `second` child is BOTTOM

### 2. Position Range Tracking

Each pane has normalized position bounds [x1, y1, x2, y2] where:
- Coordinates range from 0.0 to 1.0
- Calculated by accumulating split ratios during tree traversal
- Used to determine spatial relationships and overlap

### 3. Navigation Algorithm

When user presses Alt+Arrow:
1. Calculate current pane's position bounds
2. Find candidate panes in the target direction
3. Select the best candidate based on overlap/proximity

## Detailed Algorithm

### Step 1: Calculate Pane Bounds

Starting from root with bounds [0, 0, 1, 1], recursively:
- For horizontal splits: divide X range by ratio
- For vertical splits: divide Y range by ratio

Example with 50/50 splits:
```
Root (Horizontal 0.5)
├── Left [0.0, 0.0, 0.5, 1.0]
└── Right [0.5, 0.0, 1.0, 1.0]
```

### Step 2: Find Direction Candidates

#### For LEFT/RIGHT Navigation:
1. Traverse up to find horizontal split where current pane is on opposite side
2. Enter the sibling subtree
3. Collect all leaf nodes as candidates

#### For UP/DOWN Navigation:
1. Traverse up to find vertical split where current pane is on opposite side
2. Enter the sibling subtree
3. Collect all leaf nodes as candidates

### Step 3: Select Best Candidate

When multiple candidates exist:
1. Calculate overlap between source and each candidate
2. For LEFT/RIGHT: use Y-axis overlap
3. For UP/DOWN: use X-axis overlap
4. Choose candidate with maximum overlap
5. Break ties by preferring leftmost/topmost

## Examples

### Example 1: Simple Quad Grid

```
Layout:
┌─────────┬─────────┐
│    A    │    B    │
├─────────┼─────────┤
│    C    │    D    │
└─────────┴─────────┘

Tree:
Root (H 0.5)
├── Left (V 0.5)
│   ├── A [0.0, 0.0, 0.5, 0.5]
│   └── C [0.0, 0.5, 0.5, 1.0]
└── Right (V 0.5)
    ├── B [0.5, 0.0, 1.0, 0.5]
    └── D [0.5, 0.5, 1.0, 1.0]
```

Navigation:
- A → Right → B (direct sibling via root horizontal)
- A → Down → C (direct sibling via left vertical)
- C → Right → D (via root, same Y range)
- B → Down → D (direct sibling via right vertical)

### Example 2: Complex Nested Splits

```
Layout:
┌───────┬───────────┐
│   A   │           │
├───────┤     C     │
│   B   │           │
├───────┴───────────┤
│         D         │
└───────────────────┘

Tree:
Root (V 0.67)
├── Top (H 0.4)
│   ├── Left (V 0.5)
│   │   ├── A [0.0, 0.0, 0.4, 0.335]
│   │   └── B [0.0, 0.335, 0.4, 0.67]
│   └── C [0.4, 0.0, 1.0, 0.67]
└── D [0.0, 0.67, 1.0, 1.0]
```

Navigation from A:
- Alt+Right → C (only candidate to the right)
- Alt+Down → B (direct sibling in vertical split)

Navigation from B:
- Alt+Right → C (shares more Y-overlap than D)
- Alt+Down → D (only candidate below)
- Alt+Up → A (direct sibling)

Navigation from C:
- Alt+Left → Chooses between A and B based on Y-overlap
  - A: Y-range [0.0, 0.335] overlaps [0.0, 0.67] = 0.335
  - B: Y-range [0.335, 0.67] overlaps [0.0, 0.67] = 0.335
  - Equal overlap, choose A (topmost)
- Alt+Down → D (only candidate below)

### Example 3: Asymmetric Splits

```
Layout (A|B split at 30/70):
┌─────┬─────────────┐
│  A  │             │
│ 30% │      B      │
│     │     70%     │
├─────┴─────────────┤
│         C         │
└───────────────────┘

Tree:
Root (V 0.6)
├── Top (H 0.3)
│   ├── A [0.0, 0.0, 0.3, 0.6]
│   └── B [0.3, 0.0, 1.0, 0.6]
└── C [0.0, 0.6, 1.0, 1.0]
```

Navigation from C:
- Alt+Up → B (larger X-overlap)
  - A overlaps [0.0, 0.3] = 0.3 width
  - B overlaps [0.3, 1.0] = 0.7 width
  - B wins due to larger overlap

## Edge Cases

### No Pane in Direction
When no valid split exists in the requested direction, no navigation occurs.

### Single Pane
Alt+Arrow keys have no effect when only one pane exists.

### Equal Overlap
When candidates have equal overlap, prefer:
- LEFT navigation: rightmost candidate
- RIGHT navigation: leftmost candidate
- UP navigation: bottommost candidate
- DOWN navigation: topmost candidate

## Implementation Notes

### Performance
- Tree traversal is O(log n) for finding splits
- Candidate collection is O(n) worst case
- Overall complexity: O(n) where n is number of panes

### State Management
- No additional state needed beyond existing tree structure
- Position bounds calculated on-demand
- No dependency on actual widget geometry

### Future Enhancements
1. Wrap-around navigation (optional)
2. Diagonal navigation with Alt+Shift+Arrow
3. Visual indicators showing navigation path
4. Customizable navigation strategy