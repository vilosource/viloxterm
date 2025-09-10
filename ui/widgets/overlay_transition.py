#!/usr/bin/env python3
"""
Overlay transition system for seamless visual transitions.

This module provides an overlay widget that masks layout changes during
split operations, completely eliminating white flash by showing a
captured image of the current state while changes happen underneath.
"""

import logging
from typing import Optional
from PySide6.QtWidgets import QWidget, QLabel
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, Signal, QTimer, QPoint
from PySide6.QtGui import QPixmap, QPainter

logger = logging.getLogger(__name__)


class OverlayWidget(QLabel):
    """
    Overlay widget that displays a captured image during transitions.
    
    This widget:
    - Captures the current view as a pixmap
    - Displays it as an overlay during layout changes
    - Fades out smoothly when changes are complete
    - Completely eliminates visual artifacts
    """
    
    # Signal emitted when fade animation completes
    fade_finished = Signal()
    
    def __init__(self, parent=None):
        """
        Initialize the overlay widget.
        
        Args:
            parent: Parent widget to overlay
        """
        super().__init__(parent)
        
        # Configure overlay appearance - no window flags, just a child widget
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        
        # Animation for fade effect
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setEasingCurve(QEasingCurve.OutCubic)
        self.fade_animation.finished.connect(self._on_fade_finished)
        
        # Hide initially
        self.hide()
        
        logger.debug("OverlayWidget initialized")
    
    def capture_widget(self, widget: QWidget) -> bool:
        """
        Capture the current state of a widget as an image.
        
        Args:
            widget: Widget to capture
            
        Returns:
            True if capture was successful
        """
        if not widget or not widget.isVisible():
            logger.warning("Cannot capture: widget is None or not visible")
            return False
        
        try:
            # Get widget geometry
            rect = widget.rect()
            
            # Create pixmap of widget size
            pixmap = QPixmap(rect.size())
            pixmap.fill(Qt.transparent)
            
            # Render widget to pixmap
            painter = QPainter(pixmap)
            # render() requires a targetOffset parameter when using QPainter
            widget.render(painter, QPoint(0, 0))
            painter.end()
            
            # Set the pixmap
            self.setPixmap(pixmap)
            
            # Match widget geometry
            self.setGeometry(widget.geometry())
            
            logger.debug(f"Captured widget: size={rect.size()}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to capture widget: {e}")
            return False
    
    def show_overlay(self, duration: int = 0):
        """
        Show the overlay with optional fade-in.
        
        Args:
            duration: Fade-in duration in milliseconds (0 for instant)
        """
        if self.pixmap() and not self.pixmap().isNull():
            if duration > 0:
                # Fade in
                self.setWindowOpacity(0.0)
                self.show()
                self.raise_()
                
                self.fade_animation.setDuration(duration)
                self.fade_animation.setStartValue(0.0)
                self.fade_animation.setEndValue(1.0)
                self.fade_animation.start()
            else:
                # Instant show
                self.setWindowOpacity(1.0)
                self.show()
                self.raise_()
            
            logger.debug(f"Showing overlay (duration={duration}ms)")
        else:
            logger.warning("Cannot show overlay: no pixmap captured")
    
    def hide_overlay(self, duration: int = 150):
        """
        Hide the overlay with fade-out animation.
        
        Args:
            duration: Fade-out duration in milliseconds (0 for instant)
        """
        if not self.isVisible():
            return
        
        if duration > 0:
            # Fade out
            self.fade_animation.setDuration(duration)
            self.fade_animation.setStartValue(self.windowOpacity())
            self.fade_animation.setEndValue(0.0)
            self.fade_animation.start()
        else:
            # Instant hide
            self.hide()
            self.fade_finished.emit()
        
        logger.debug(f"Hiding overlay (duration={duration}ms)")
    
    def _on_fade_finished(self):
        """Handle fade animation completion."""
        if self.windowOpacity() <= 0.01:
            self.hide()
        self.fade_finished.emit()


class TransitionManager:
    """
    Manages overlay transitions for a widget.
    
    This class coordinates the overlay system to provide smooth transitions
    during layout changes, completely eliminating white flash.
    """
    
    def __init__(self, target_widget: QWidget):
        """
        Initialize the transition manager.
        
        Args:
            target_widget: Widget to manage transitions for
        """
        self.target_widget = target_widget
        self.overlay = OverlayWidget(target_widget)
        self.transition_active = False
        
        # Delay timer for ensuring changes are complete
        self.complete_timer = QTimer()
        self.complete_timer.setSingleShot(True)
        self.complete_timer.timeout.connect(self._complete_transition)
        
        logger.info("TransitionManager initialized")
    
    def begin_transition(self) -> bool:
        """
        Begin a transition by capturing current state and showing overlay.
        
        Returns:
            True if transition started successfully
        """
        if self.transition_active:
            logger.warning("Transition already active")
            return False
        
        # Capture current state
        if not self.overlay.capture_widget(self.target_widget):
            return False
        
        # Show overlay instantly (no fade-in for responsiveness)
        self.overlay.show_overlay(duration=0)
        self.transition_active = True
        
        logger.debug("Transition begun")
        return True
    
    def end_transition(self, delay: int = 10):
        """
        End a transition by fading out the overlay.
        
        Args:
            delay: Milliseconds to wait before fading (ensures changes render)
        """
        if not self.transition_active:
            return
        
        # Use timer to ensure changes have rendered
        self.complete_timer.stop()
        self.complete_timer.start(delay)
        
        logger.debug(f"Ending transition with {delay}ms delay")
    
    def _complete_transition(self):
        """Complete the transition by fading out overlay."""
        self.overlay.hide_overlay(duration=100)  # Faster fade
        self.transition_active = False
        logger.debug("Transition completed")
    
    def abort_transition(self):
        """Immediately abort any active transition."""
        self.complete_timer.stop()
        self.overlay.hide()
        self.transition_active = False
        logger.debug("Transition aborted")
    
    def with_transition(self, operation, delay: int = 10):
        """
        Execute an operation with transition overlay.
        
        This is a convenience method that wraps an operation with
        transition begin/end calls.
        
        Args:
            operation: Callable to execute during transition
            delay: Delay before ending transition
            
        Returns:
            Result of the operation
        """
        # Begin transition
        if not self.begin_transition():
            # If transition fails, just run operation
            logger.warning("Transition failed to start, running operation without overlay")
            return operation()
        
        try:
            # Execute operation while overlay is shown
            result = operation()
            
            # End transition
            self.end_transition(delay)
            
            return result
            
        except Exception as e:
            # Abort on error
            self.abort_transition()
            raise e