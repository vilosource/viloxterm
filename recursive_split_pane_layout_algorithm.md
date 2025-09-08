# Recursive Split‑Pane Layout Algorithms (Qt/PySide)

> Scope: No tabs. Each pane (leaf) hosts one widget. Users can split a pane **right** (vertical split) or **bottom** (horizontal split) recursively, and close panes. This doc specifies the **data model**, **operations**, **merge/close behavior**, **focus**, **ratio management**, **persistence**, and **testing**.

---

## 1) Core Concepts & Invariants

* **Tree structure**

  * **Leaf**: `{ type: leaf, id, widgetRef }`
  * **Split**: `{ type: split, id, orientation ∈ {vertical|horizontal}, ratio ∈ (0,1), first, second }`

    * `vertical` ⇒ left (first) | right (second)
    * `horizontal` ⇒ top (first) | bottom (second)
* **Invariants**

  * Root is either a **Leaf** or a **Split with exactly two children**.
  * Leaves contain **exactly one** user widget.
  * No one‑child splits exist after any operation.
  * Ratios are maintained per split and reflect current user‑visible geometry.

---

## 2) Rendering Model (View Realization)

* **Split node →** `QSplitter(orientation)`
* **Leaf node →** container `QWidget` holding the single user widget
* **Realize (build)**: recursively materialize widgets from the model tree.
* **Derive sizes**: apply `ratio` to `QSplitter::setSizes([ratio*total, (1-ratio)*total])` after insertion; then let Qt do final layout.

---

## 3) Operations (High Level)

### 3.1 Split Right (on a Leaf)

**Intent:** keep the existing widget on the **left**; create a new, empty widget on the **right**.

1. Input: target **Leaf L**, `newWidget`, initial `ratio` (default 0.5 or pointer‑based).
2. Create `S = Split(vertical, ratio)`.
3. Set `S.first = L`, `S.second = Leaf(newWidget)`.
4. Replace `L` with `S` in its parent (or make `S` the new root if `L` was root).
5. Realize: replace L’s container with a new `QSplitter(Qt::Vertical)`; reparent L’s widget as index 0; add new widget as index 1; apply sizes.

### 3.2 Split Bottom (on a Leaf)

**Intent:** keep the existing widget on the **top**; create a new, empty widget on the **bottom**.

1. Input: **Leaf L**, `newWidget`, initial `ratio`.
2. Create `S = Split(horizontal, ratio)`.
3. `S.first = L`, `S.second = Leaf(newWidget)`.
4. Replace `L` with `S` in parent (or make root), realize, apply sizes.

### 3.3 Close Pane (Remove a Leaf)

**Intent:** remove the target leaf and **promote its sibling**; remove degenerate splits.

1. If target `L` is the **root Leaf**: either (a) disallow, or (b) replace its widget with a default widget (keeps single‑pane workspace). Stop.
2. Let `P = parent(L)` (a Split), `S = sibling(L)`, `G = parent(P)` (may be null).
3. **Promote S**: replace `P` in `G` with `S`. If `G == null`, `S` becomes the **root**.
4. **Collapse upwards**: while any ancestor split now has one child (due to attach/detach mechanics), replace it with its sole child.
5. **Focus**: move focus to `S`’s nearest leaf (see §5).
6. **Realization**: remove `L`’s widget from `P`’s `QSplitter`; insert `S`’s widget into `G`’s splitter at `P`’s index; `deleteLater(P)`; apply sizes once on `G`.

### 3.4 Close Specific Side of a Split (Local Close)

**Intent:** user closes **left/right** (vertical) or **top/bottom** (horizontal) pane of a chosen split `P`.

1. Identify `P` and target child index `i ∈ {0,1}` by side.
2. `target = P.child[i]`, `sibling = P.child[1-i]`.
3. Promote `sibling` to `P`’s parent (`G`). If `P` was root, `sibling` becomes root.
4. Collapse upwards and handle focus as in §3.3.

### 3.5 Replace Pane’s Widget (Non‑structural)

**Intent:** swap the widget in a leaf without altering tree shape.

1. Find leaf by `id`.
2. Replace `widgetRef` and reparent view; leave ratios and structure unchanged.

### 3.6 Resize Handling (User Drags Splitter)

**Intent:** persist user geometry.

1. On `QSplitter::splitterMoved`, read `sizes = splitter->sizes()`.
2. Update node’s `ratio = sizes[0] / (sizes[0] + sizes[1])` (clamp to `(ε, 1-ε)`).

---

## 4) Merge/Close Correctness Rules

* Promotion must produce no intermediate one‑child splits after the collapse pass.
* Discard the removed split’s ratio; keep unaffected ancestors’ ratios.
* When replacing a subtree at `G`’s child index, **do not** recompute `G`’s ratio—only its children changed.
* Use `deleteLater()` for removed split widgets to avoid mid‑event destruction.

---

## 5) Focus Policy (Deterministic & Intuitive)

* On close of leaf `L`:

  * If sibling `S` is a **Leaf** → focus its widget.
  * If `S` is a **Split** → descend to its **nearest** leaf:

    * For `vertical` sibling, pick the **leftmost** leaf.
    * For `horizontal` sibling, pick the **topmost** leaf.
* Maintain a `lastFocusedLeafId` to fall back if needed.

---

## 6) Constraints & Edge Cases

* **Minimum sizes**: reject splits that would produce a child below `minimumSizeHint()`; or adjust initial `ratio` to the smallest valid.
* **Last two panes**: closing one promotes the other to root; closing again either resets to default widget or is disallowed—pick one policy.
* **Programmatic destruction**: if a widget dies externally, treat as a close on its leaf.
* **Hidden/disabled panes**: closing should skip disabled descendants when choosing focus.

---

## 7) Persistence Format (Suggested)

A compact JSON/YAML representation of the tree:

```json
{
  "type": "split",
  "id": "n1",
  "orientation": "vertical",
  "ratio": 0.56,
  "first": { "type": "leaf", "id": "a1", "widget": "Editor#42" },
  "second": {
    "type": "split",
    "id": "n2",
    "orientation": "horizontal",
    "ratio": 0.62,
    "first": { "type": "leaf", "id": "b1", "widget": "Viewer#7" },
    "second": { "type": "leaf", "id": "b2", "widget": "Console#9" }
  }
}
```

* Persist **IDs** to restore focus and stable references.
* Widgets can be restored via a factory keyed by widget descriptor.

---

## 8) MVC/MVVM Integration

* **Domain Model(s)**: your app’s data; independent of layout.
* **Layout Model**: this tree; pure data, no Qt widgets.
* **View**: the realized `QSplitter`/container widgets.
* **Controller/ViewModel**: translates user actions (split, close, resize) into mutations on the layout model, then rebinds/reconciles the view.

---

## 9) Reconciliation Strategy (Model ⇄ View)

* Prefer **surgical updates**: mutate only the affected subtree and corresponding widgets.
* For complex changes (e.g., undo many steps), you may **rebuild** the whole view from the model—safe if widgets are lightweight or state is external.
* Keep a **map**: `nodeId → QWidget* or QSplitter*` for O(1) lookup during ops.

---

## 10) Undo/Redo (Command Pattern)

* **Split command** stores: `leafId`, `orientation`, `insertedLeafId`, `oldParentId`, and **pre/post ratios**.
* **Close command** stores: `closedSubtree` (full subtree snapshot), `parentId`, `grandParentId`, `slotIndex`, `parentOrientation`, `parentRatio`, and `priorFocusId`.
* Redo/undo reapply mutations on the layout model and reconcile view.

---

## 11) Complexity & Performance

* Split/close are **O(h)** where `h` is tree height (typically small).
* Rendering is proportional to mutated subtree; keep reconciles local.
* Memory is linear in number of nodes.

---

## 12) Testing Matrix

* **Structure**

  * Deeply nested splits: V‑H‑V and H‑V‑H sequences.
  * Close left/right/top/bottom at every depth.
  * Repeated closes along one branch; ensure no one‑child splits remain.
* **Geometry**

  * Ratios persist after unrelated operations.
  * Minimum sizes enforced on split and preserved after close.
* **Focus**

  * Focus moves to sibling or nearest leaf as specified.
  * Focus restoration after undo/redo and after deserialization.
* **Persistence**

  * Serialize → deserialize → rebuild view → equality of structure/ratios.

---

## 13) Implementation Tips (Qt/PySide)

* Use `deleteLater()` when removing `QSplitter`s.
* Batch UI updates with `setUpdatesEnabled(false/true)` around complex edits.
* Clamp ratios to `[ε, 1-ε]` (e.g., ε = 0.03) to avoid zero‑size panes.
* Listen to `QSplitter::splitterMoved` to refresh ratios in the model.
* Keep a `QPointer` to widgets to safely detect external deletions.

---

## 14) Optional Enhancements

* **Drop‑to‑split**: show directional drop zones; convert to right/bottom split accordingly.
* **Keyboard ops**: shortcuts for split right/bottom, close, focus move.
* **Ghost preview**: preview outline when choosing split ratios before committing.
* **Animated merges**: fade/slide on promote for user feedback.

---

## 15) Quick Reference (Operation Outcomes)

* **Split Right**: Leaf → Split(vertical) with existing on **left**, new on **right**.
* **Split Bottom**: Leaf → Split(horizontal) with existing on **top**, new on **bottom**.
* **Close Leaf**: Promote sibling; collapse degenerate splits; focus sibling/nearest.
* **Close Side of Split**: Remove chosen side; promote other side; collapse; focus.
* **Resize**: Update only the affected split’s ratio.

