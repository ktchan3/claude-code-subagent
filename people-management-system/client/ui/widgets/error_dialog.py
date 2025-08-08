"""
Enhanced Error Dialog for People Management System Client

Provides user-friendly error dialogs with detailed information, retry options,
and helpful suggestions for resolution.
"""

import logging
import traceback
from typing import Optional, Callable, Dict, Any
from datetime import datetime

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QGroupBox, QDialogButtonBox, QFrame,
    QApplication
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QIcon, QPixmap, QPainter

logger = logging.getLogger(__name__)


class ErrorDialog(QDialog):
    """Enhanced error dialog with retry and detailed information."""
    
    # Signals
    retry_requested = Signal()
    report_requested = Signal(dict)  # Error details for reporting
    
    def __init__(self, 
                 title: str = "Error",
                 message: str = "An error occurred",
                 details: Optional[str] = None,
                 error_type: str = "error",
                 retry_action: Optional[Callable] = None,
                 suggestions: Optional[list] = None,
                 parent=None):
        """
        Initialize the error dialog.
        
        Args:
            title: Dialog title
            message: Main error message
            details: Detailed error information
            error_type: Type of error ('error', 'warning', 'network', 'validation')
            retry_action: Callable to retry the failed operation
            suggestions: List of suggestions for resolving the error
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.error_title = title
        self.error_message = message
        self.error_details = details
        self.error_type = error_type
        self.retry_action = retry_action
        self.suggestions = suggestions or []
        
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(500)
        
        self.setup_ui()
        self.apply_error_type_styling()
    
    def setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Error icon and message section
        self.create_header_section(layout)
        
        # Suggestions section (if any)
        if self.suggestions:
            self.create_suggestions_section(layout)
        
        # Details section (collapsible)
        if self.error_details:
            self.create_details_section(layout)
        
        # Action buttons
        self.create_button_section(layout)
    
    def create_header_section(self, layout: QVBoxLayout):
        """Create the header section with icon and message."""
        header_frame = QFrame()
        header_layout = QHBoxLayout(header_frame)
        
        # Error icon
        icon_label = QLabel()
        icon_emoji = self.get_error_icon()
        icon_font = QFont()
        icon_font.setPointSize(32)
        icon_label.setFont(icon_font)
        icon_label.setText(icon_emoji)
        icon_label.setAlignment(Qt.AlignTop)
        header_layout.addWidget(icon_label)
        
        # Message section
        message_layout = QVBoxLayout()
        
        # Main message
        message_label = QLabel(self.error_message)
        message_label.setWordWrap(True)
        message_font = QFont()
        message_font.setPointSize(11)
        message_label.setFont(message_font)
        message_layout.addWidget(message_label)
        
        # Timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        time_label = QLabel(f"Occurred at: {timestamp}")
        time_label.setStyleSheet("color: gray; font-size: 9pt;")
        message_layout.addWidget(time_label)
        
        header_layout.addLayout(message_layout)
        header_layout.addStretch()
        
        layout.addWidget(header_frame)
    
    def create_suggestions_section(self, layout: QVBoxLayout):
        """Create suggestions section."""
        suggestions_group = QGroupBox("Suggestions")
        suggestions_layout = QVBoxLayout(suggestions_group)
        
        for i, suggestion in enumerate(self.suggestions, 1):
            suggestion_label = QLabel(f"{i}. {suggestion}")
            suggestion_label.setWordWrap(True)
            suggestion_label.setStyleSheet("padding: 5px;")
            suggestions_layout.addWidget(suggestion_label)
        
        layout.addWidget(suggestions_group)
    
    def create_details_section(self, layout: QVBoxLayout):
        """Create collapsible details section."""
        self.details_group = QGroupBox("Technical Details")
        self.details_group.setCheckable(True)
        self.details_group.setChecked(False)  # Collapsed by default
        
        details_layout = QVBoxLayout(self.details_group)
        
        # Details text area
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setPlainText(self.error_details)
        self.details_text.setMaximumHeight(150)
        self.details_text.setStyleSheet("font-family: monospace; font-size: 9pt;")
        details_layout.addWidget(self.details_text)
        
        # Copy button
        copy_btn = QPushButton("Copy to Clipboard")
        copy_btn.clicked.connect(self.copy_details_to_clipboard)
        details_layout.addWidget(copy_btn)
        
        layout.addWidget(self.details_group)
    
    def create_button_section(self, layout: QVBoxLayout):
        """Create action buttons section."""
        button_layout = QHBoxLayout()
        
        # Retry button (if retry action provided)
        if self.retry_action:
            self.retry_btn = QPushButton("🔄 Retry")
            self.retry_btn.clicked.connect(self.on_retry_clicked)
            button_layout.addWidget(self.retry_btn)
        
        # Report button
        self.report_btn = QPushButton("📧 Report Issue")
        self.report_btn.clicked.connect(self.on_report_clicked)
        button_layout.addWidget(self.report_btn)
        
        button_layout.addStretch()
        
        # OK button
        self.ok_btn = QPushButton("OK")
        self.ok_btn.setDefault(True)
        self.ok_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.ok_btn)
        
        layout.addLayout(button_layout)
    
    def get_error_icon(self) -> str:
        """Get appropriate icon based on error type."""
        icons = {
            'error': '❌',
            'warning': '⚠️',
            'network': '🌐',
            'validation': '📝',
            'authentication': '🔐',
            'permission': '🚫',
            'database': '🗄️',
            'timeout': '⏱️'
        }
        return icons.get(self.error_type, '❌')
    
    def apply_error_type_styling(self):
        """Apply styling based on error type."""
        styles = {
            'error': 'QDialog { background-color: #fff5f5; }',
            'warning': 'QDialog { background-color: #fffaf0; }',
            'network': 'QDialog { background-color: #f0f8ff; }',
            'validation': 'QDialog { background-color: #fafafa; }'
        }
        
        style = styles.get(self.error_type, '')
        if style:
            self.setStyleSheet(style)
    
    def on_retry_clicked(self):
        """Handle retry button click."""
        if self.retry_action:
            self.accept()  # Close dialog first
            try:
                self.retry_action()
                self.retry_requested.emit()
            except Exception as e:
                logger.error(f"Retry failed: {e}")
                # Show new error dialog for retry failure
                show_error(
                    "Retry Failed",
                    f"The retry attempt failed: {str(e)}",
                    parent=self.parent()
                )
    
    def on_report_clicked(self):
        """Handle report button click."""
        error_details = {
            'title': self.error_title,
            'message': self.error_message,
            'details': self.error_details,
            'type': self.error_type,
            'timestamp': datetime.now().isoformat()
        }
        
        self.report_requested.emit(error_details)
        
        # Show confirmation
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(
            self,
            "Issue Reported",
            "The error details have been prepared for reporting.\n"
            "They have been copied to your clipboard."
        )
        
        # Copy to clipboard
        self.copy_details_to_clipboard()
    
    def copy_details_to_clipboard(self):
        """Copy error details to clipboard."""
        clipboard = QApplication.clipboard()
        
        details_text = f"""
Error Report
============
Title: {self.error_title}
Type: {self.error_type}
Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

Message:
{self.error_message}

Technical Details:
{self.error_details or 'No additional details available'}
        """.strip()
        
        clipboard.setText(details_text)


class NetworkErrorDialog(ErrorDialog):
    """Specialized dialog for network errors."""
    
    def __init__(self, message: str, details: Optional[str] = None, 
                 retry_action: Optional[Callable] = None, parent=None):
        
        suggestions = [
            "Check your internet connection",
            "Verify the server is running and accessible",
            "Check if the API URL is correct in settings",
            "Try again in a few moments",
            "Contact system administrator if the problem persists"
        ]
        
        super().__init__(
            title="Network Error",
            message=message,
            details=details,
            error_type="network",
            retry_action=retry_action,
            suggestions=suggestions,
            parent=parent
        )


class ValidationErrorDialog(ErrorDialog):
    """Specialized dialog for validation errors."""
    
    def __init__(self, message: str, validation_errors: Optional[Dict[str, Any]] = None,
                 parent=None):
        
        # Format validation errors
        details = None
        suggestions = []
        
        if validation_errors:
            details = "Field Errors:\n"
            for field, errors in validation_errors.items():
                if isinstance(errors, list):
                    for error in errors:
                        details += f"  • {field}: {error}\n"
                        suggestions.append(f"Fix {field}: {error}")
                else:
                    details += f"  • {field}: {errors}\n"
                    suggestions.append(f"Fix {field}: {errors}")
        
        super().__init__(
            title="Validation Error",
            message=message,
            details=details,
            error_type="validation",
            suggestions=suggestions[:5],  # Limit to 5 suggestions
            parent=parent
        )


def show_error(title: str, message: str, details: Optional[str] = None,
               error_type: str = "error", retry_action: Optional[Callable] = None,
               parent=None) -> ErrorDialog:
    """
    Convenience function to show an error dialog.
    
    Args:
        title: Dialog title
        message: Error message
        details: Detailed error information
        error_type: Type of error
        retry_action: Callable to retry the operation
        parent: Parent widget
        
    Returns:
        ErrorDialog instance
    """
    dialog = ErrorDialog(
        title=title,
        message=message,
        details=details,
        error_type=error_type,
        retry_action=retry_action,
        parent=parent
    )
    dialog.exec()
    return dialog


def show_network_error(message: str, details: Optional[str] = None,
                      retry_action: Optional[Callable] = None, parent=None) -> NetworkErrorDialog:
    """Show a network error dialog."""
    dialog = NetworkErrorDialog(message, details, retry_action, parent)
    dialog.exec()
    return dialog


def show_validation_error(message: str, validation_errors: Optional[Dict[str, Any]] = None,
                         parent=None) -> ValidationErrorDialog:
    """Show a validation error dialog."""
    dialog = ValidationErrorDialog(message, validation_errors, parent)
    dialog.exec()
    return dialog


def handle_exception(exception: Exception, title: str = "Unexpected Error",
                    retry_action: Optional[Callable] = None, parent=None) -> ErrorDialog:
    """
    Handle an exception and show appropriate error dialog.
    
    Args:
        exception: The exception to handle
        title: Dialog title
        retry_action: Callable to retry the operation
        parent: Parent widget
        
    Returns:
        ErrorDialog instance
    """
    # Get exception details
    message = str(exception)
    details = traceback.format_exc()
    
    # Determine error type based on exception
    error_type = "error"
    suggestions = []
    
    if "network" in message.lower() or "connection" in message.lower():
        error_type = "network"
        suggestions = ["Check your network connection", "Verify server is accessible"]
    elif "validation" in message.lower():
        error_type = "validation"
        suggestions = ["Check the input data", "Ensure all required fields are filled"]
    elif "permission" in message.lower() or "forbidden" in message.lower():
        error_type = "permission"
        suggestions = ["Check your access permissions", "Contact administrator"]
    elif "timeout" in message.lower():
        error_type = "timeout"
        suggestions = ["Try again with a smaller dataset", "Check server performance"]
    
    dialog = ErrorDialog(
        title=title,
        message=message,
        details=details,
        error_type=error_type,
        retry_action=retry_action,
        suggestions=suggestions,
        parent=parent
    )
    dialog.exec()
    return dialog