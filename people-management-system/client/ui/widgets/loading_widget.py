"""
Loading and Progress Widgets for People Management System Client

Provides various loading indicators and progress feedback widgets for async operations.
"""

import logging
from typing import Optional, Callable
from datetime import datetime, timedelta

from PySide6.QtWidgets import (
    QWidget, QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QProgressBar, QFrame, QGraphicsOpacityEffect
)
from PySide6.QtCore import (
    Qt, Signal, QTimer, QPropertyAnimation, QEasingCurve,
    QRect, QPoint, Property, QParallelAnimationGroup
)
from PySide6.QtGui import QPainter, QColor, QPen, QFont

logger = logging.getLogger(__name__)


class SpinnerWidget(QWidget):
    """Animated spinner widget for indeterminate loading."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.angle = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.rotate)
        self.setFixedSize(50, 50)
        
    def start(self):
        """Start the spinner animation."""
        self.timer.start(50)  # Update every 50ms
        self.show()
        
    def stop(self):
        """Stop the spinner animation."""
        self.timer.stop()
        self.hide()
        
    def rotate(self):
        """Rotate the spinner."""
        self.angle = (self.angle + 10) % 360
        self.update()
        
    def paintEvent(self, event):
        """Paint the spinner."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw spinning arc
        pen = QPen(QColor(25, 118, 210), 3)  # Blue color
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        
        rect = self.rect().adjusted(10, 10, -10, -10)
        painter.drawArc(rect, self.angle * 16, 120 * 16)  # 120 degree arc


class LoadingOverlay(QWidget):
    """Overlay widget that shows loading indicator over content."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Setup UI
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        
        # Container for spinner and text
        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 240);
                border-radius: 10px;
                padding: 20px;
            }
        """)
        container_layout = QVBoxLayout(container)
        
        # Spinner
        self.spinner = SpinnerWidget()
        container_layout.addWidget(self.spinner, alignment=Qt.AlignCenter)
        
        # Loading text
        self.loading_label = QLabel("Loading...")
        self.loading_label.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setPointSize(11)
        self.loading_label.setFont(font)
        container_layout.addWidget(self.loading_label)
        
        # Progress bar (hidden by default)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        container_layout.addWidget(self.progress_bar)
        
        # Cancel button (hidden by default)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setVisible(False)
        self.cancel_btn.clicked.connect(self.cancel_clicked)
        container_layout.addWidget(self.cancel_btn, alignment=Qt.AlignCenter)
        
        layout.addWidget(container)
        
        # Opacity effect for fade in/out
        self.opacity_effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0)
        
        # Animation
        self.fade_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_animation.setDuration(200)
        
        self.hide()
        
    # Signals
    cancel_requested = Signal()
    
    def show_loading(self, text: str = "Loading...", can_cancel: bool = False):
        """Show the loading overlay."""
        self.loading_label.setText(text)
        self.cancel_btn.setVisible(can_cancel)
        self.progress_bar.setVisible(False)
        
        # Resize to parent
        if self.parent():
            self.resize(self.parent().size())
            
        self.show()
        self.raise_()
        
        # Fade in
        self.fade_animation.setStartValue(0)
        self.fade_animation.setEndValue(1)
        self.fade_animation.start()
        
        self.spinner.start()
        
    def show_progress(self, text: str = "Processing...", max_value: int = 100, can_cancel: bool = True):
        """Show loading with progress bar."""
        self.loading_label.setText(text)
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(max_value)
        self.progress_bar.setValue(0)
        self.cancel_btn.setVisible(can_cancel)
        
        # Resize to parent
        if self.parent():
            self.resize(self.parent().size())
            
        self.show()
        self.raise_()
        
        # Fade in
        self.fade_animation.setStartValue(0)
        self.fade_animation.setEndValue(1)
        self.fade_animation.start()
        
        self.spinner.start()
        
    def update_progress(self, value: int, text: Optional[str] = None):
        """Update progress bar value."""
        self.progress_bar.setValue(value)
        if text:
            self.loading_label.setText(text)
            
    def hide_loading(self):
        """Hide the loading overlay with fade out."""
        # Fade out
        self.fade_animation.setStartValue(1)
        self.fade_animation.setEndValue(0)
        self.fade_animation.finished.connect(self._on_fade_out_finished)
        self.fade_animation.start()
        
    def _on_fade_out_finished(self):
        """Handle fade out completion."""
        self.spinner.stop()
        self.hide()
        self.fade_animation.finished.disconnect(self._on_fade_out_finished)
        
    def cancel_clicked(self):
        """Handle cancel button click."""
        self.cancel_requested.emit()
        self.hide_loading()
        
    def resizeEvent(self, event):
        """Handle parent resize."""
        if self.parent():
            self.resize(self.parent().size())


class LoadingDialog(QDialog):
    """Modal loading dialog for blocking operations."""
    
    # Signals
    cancel_requested = Signal()
    
    def __init__(self, 
                 title: str = "Processing",
                 message: str = "Please wait...",
                 can_cancel: bool = True,
                 parent=None):
        super().__init__(parent)
        
        self.setWindowTitle(title)
        self.setModal(True)
        self.setFixedSize(300, 150)
        
        # Remove window buttons except close
        self.setWindowFlags(
            Qt.Dialog | 
            Qt.CustomizeWindowHint | 
            Qt.WindowTitleHint
        )
        
        # Setup UI
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Message
        self.message_label = QLabel(message)
        self.message_label.setWordWrap(True)
        self.message_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.message_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate
        layout.addWidget(self.progress_bar)
        
        # Time elapsed
        self.time_label = QLabel("Elapsed: 0:00")
        self.time_label.setAlignment(Qt.AlignCenter)
        self.time_label.setStyleSheet("color: gray; font-size: 9pt;")
        layout.addWidget(self.time_label)
        
        # Cancel button
        if can_cancel:
            self.cancel_btn = QPushButton("Cancel")
            self.cancel_btn.clicked.connect(self.cancel_clicked)
            layout.addWidget(self.cancel_btn, alignment=Qt.AlignCenter)
            
        # Timer for elapsed time
        self.start_time = None
        self.elapsed_timer = QTimer()
        self.elapsed_timer.timeout.connect(self.update_elapsed_time)
        
    def show_loading(self, message: Optional[str] = None):
        """Show the loading dialog."""
        if message:
            self.message_label.setText(message)
            
        self.start_time = datetime.now()
        self.elapsed_timer.start(1000)  # Update every second
        
        self.show()
        
    def set_progress(self, value: int, maximum: int = 100):
        """Set determinate progress."""
        self.progress_bar.setRange(0, maximum)
        self.progress_bar.setValue(value)
        
    def update_message(self, message: str):
        """Update the loading message."""
        self.message_label.setText(message)
        
    def update_elapsed_time(self):
        """Update elapsed time display."""
        if self.start_time:
            elapsed = datetime.now() - self.start_time
            minutes = int(elapsed.total_seconds() // 60)
            seconds = int(elapsed.total_seconds() % 60)
            self.time_label.setText(f"Elapsed: {minutes}:{seconds:02d}")
            
    def cancel_clicked(self):
        """Handle cancel button click."""
        self.cancel_requested.emit()
        self.close()
        
    def closeEvent(self, event):
        """Handle dialog close."""
        self.elapsed_timer.stop()
        event.accept()


class ProgressTracker:
    """Helper class to track progress across multiple operations."""
    
    def __init__(self, total_steps: int, callback: Optional[Callable[[int, str], None]] = None):
        """
        Initialize progress tracker.
        
        Args:
            total_steps: Total number of steps
            callback: Callback function(progress, message) to report progress
        """
        self.total_steps = total_steps
        self.current_step = 0
        self.callback = callback
        self.start_time = datetime.now()
        
    def update(self, message: str = ""):
        """Update progress by one step."""
        self.current_step += 1
        progress = int((self.current_step / self.total_steps) * 100)
        
        if self.callback:
            self.callback(progress, message)
            
        return progress
        
    def set_step(self, step: int, message: str = ""):
        """Set current step directly."""
        self.current_step = min(step, self.total_steps)
        progress = int((self.current_step / self.total_steps) * 100)
        
        if self.callback:
            self.callback(progress, message)
            
        return progress
        
    def get_elapsed_time(self) -> timedelta:
        """Get elapsed time since start."""
        return datetime.now() - self.start_time
        
    def get_estimated_remaining(self) -> Optional[timedelta]:
        """Get estimated remaining time."""
        if self.current_step == 0:
            return None
            
        elapsed = self.get_elapsed_time()
        rate = elapsed.total_seconds() / self.current_step
        remaining_steps = self.total_steps - self.current_step
        estimated_seconds = rate * remaining_steps
        
        return timedelta(seconds=estimated_seconds)
        
    def is_complete(self) -> bool:
        """Check if all steps are complete."""
        return self.current_step >= self.total_steps


def show_loading(parent: QWidget, message: str = "Loading...", can_cancel: bool = False) -> LoadingOverlay:
    """
    Convenience function to show loading overlay on a widget.
    
    Args:
        parent: Parent widget to overlay
        message: Loading message
        can_cancel: Whether to show cancel button
        
    Returns:
        LoadingOverlay instance
    """
    overlay = LoadingOverlay(parent)
    overlay.show_loading(message, can_cancel)
    return overlay


def show_loading_dialog(message: str = "Please wait...", 
                        title: str = "Processing",
                        can_cancel: bool = True,
                        parent=None) -> LoadingDialog:
    """
    Convenience function to show loading dialog.
    
    Args:
        message: Loading message
        title: Dialog title
        can_cancel: Whether to show cancel button
        parent: Parent widget
        
    Returns:
        LoadingDialog instance
    """
    dialog = LoadingDialog(title, message, can_cancel, parent)
    dialog.show_loading()
    return dialog