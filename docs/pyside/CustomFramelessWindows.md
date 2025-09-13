# Building a Custom Frameless Window in PySide6 That Works on Wayland

One of the first things many desktop developers want to do when building a polished application is **remove the default OS chrome** and implement their own window decorations. This allows for custom title bars, buttons, and a consistent cross-platform look.

On Windows and macOS, that’s relatively straightforward: you can make a window frameless, capture mouse events, and move the window around manually with `move()`.

But on **Wayland** — the modern Linux display server protocol — things work differently. In fact, if you try to drag a top-level window by calling `move()` during mouse events, you’ll run into limitations or outright failures.

So how do we do this correctly in **PySide6**?

---

## Why Manual Moving Doesn’t Work on Wayland

Wayland was designed to put window management in the hands of the **compositor** (the system component that draws and arranges windows). Applications aren’t allowed to reposition themselves arbitrarily, because that could break tiling, snapping, or even basic security guarantees.

That means if you remove the chrome and want your app to be draggable, you **must ask the compositor** to move or resize the window for you.

---

## The Qt Way: `startSystemMove()` and `startSystemResize()`

Fortunately, Qt 6 (and thus PySide6) provides the right APIs for this:

* `QWindow.startSystemMove()`
* `QWindow.startSystemResize(Qt.Edges)`

These tell the underlying OS or compositor:
*"Please start a drag or resize operation on this window, beginning at the current pointer location."*

On X11, macOS, and Windows, these map to native calls. On Wayland, they are **the only way** to implement client-side decorated windows that behave properly.

---

## Step 1: Create a Frameless Window

Start by removing the default system chrome:

```python
self.setWindowFlags(Qt.FramelessWindowHint)
self.setAttribute(Qt.WA_TranslucentBackground, True)  # optional
```

This gives you a clean canvas to draw your own borders and title bar.

> Tip: If you use a translucent background, draw your own rounded-rect background with anti-aliased painting to get crisp corners.

---

## Step 2: Build Your Own Title Bar

A simple `QWidget` with a label and a few buttons works well:

* **Minimize** → `window.showMinimized()`
* **Maximize / Restore** → toggle `showMaximized()` / `showNormal()`
* **Close** → `window.close()`

You can add hover effects and animations to match your brand.

---

## Step 3: Dragging the Window (Wayland-Safe)

Instead of faking movement with `move()`, hook into mouse press events on the title bar:

```python
def mousePressEvent(self, e):
    if e.button() == Qt.LeftButton:
        wh = self.window().windowHandle()
        if wh:
            wh.startSystemMove()
```

Now when the user clicks and drags your title bar, the compositor takes care of it. On Wayland this is not optional — it’s the *only* way.

---

## Step 4: Resizing with Hit-Test Borders

Implement custom resize borders by detecting the pointer near an edge/corner, then call:

```python
self.window().windowHandle().startSystemResize(Qt.LeftEdge)
```

or any combination of `Qt.Edges` (e.g. `Qt.TopEdge | Qt.LeftEdge` for top-left corner). The compositor will handle the resizing sequence.

> Practical border thickness: 5–8 px usually feels right. Provide visible affordances on hover if your UI allows.

---

## Step 5: Embrace the Wayland Rules

On Wayland you **cannot**:

* Force a window’s absolute screen position during interactive drag
* Warp the pointer to new coordinates
* Perform interactive resize by setting geometry manually

These limitations are intentional. Use `startSystemMove()`/`startSystemResize()` and let the compositor manage snapping, tiling, and multi-monitor behavior.

---

## Minimal Example: Custom Title Bar + System Move

```python
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget

class TitleBar(QWidget):
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            wh = self.window().windowHandle()
            if wh:
                wh.startSystemMove()
```

Combine this with your main layout (title bar at the top, central widget below) to form a fully custom-decorated window.

---

## Common Pitfalls & Fixes

* **Manual `move()` during drag causes jitter or no-op on Wayland** → Replace with `startSystemMove()`.
* **Resizing by `setGeometry()` feels wrong** → Switch to `startSystemResize()` from hit-tested edges.
* **Double-click to maximize** → Handle `mouseDoubleClickEvent` on the title bar and toggle `showMaximized()`/`showNormal()`.
* **Window shadows** → Compositors often draw shadows only for server-side decorations. For client-side, mimic shadows via drop-shadows in your background painting.
* **HiDPI** → Use device-independent units and test on multiple scale factors.

---

## Optional: Corner Cases (Pun Intended)

* **Rounded corners with live resize**: Clip your window painting to a rounded path to avoid artifacts.
* **Drag from anywhere**: If you want to allow dragging from empty regions of your UI (not just the title bar), forward those region events to the same `startSystemMove()` call.
* **Maximize vs. Fullscreen**: Prefer `showMaximized()` for standard behavior; use `showFullScreen()` only if you truly want to cover docks/panels.

---

## Conclusion

If you’re building a frameless PySide6 application and want it to work reliably across platforms — **especially Wayland** — rely on:

* `startSystemMove()` for dragging
* `startSystemResize()` for resizing

These APIs hand control to the OS compositor, ensuring your app plays nicely with modern desktop environments, window snapping, and multi‑monitor setups. With them, you can design your own chrome confidently across Linux (Wayland), Windows, and macOS.

