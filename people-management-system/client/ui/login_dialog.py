"""
Login Dialog for People Management System Client

Provides authentication and server configuration interface.
"""

import asyncio
import logging
from typing import Optional, Dict, Any

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QCheckBox, QProgressBar,
    QTabWidget, QWidget, QTextEdit, QGroupBox, QSpacerItem, QSizePolicy,
    QMessageBox, QFrame
)
from PySide6.QtCore import Qt, Signal, QThread, QTimer
from PySide6.QtGui import QFont, QPixmap, QPalette, QIcon

from client.services.config_service import ConfigService, ConnectionConfig, RecentConnection
from client.services.api_service import APIService

logger = logging.getLogger(__name__)


class ConnectionTestWorker(QThread):
    """Worker thread for testing API connection."""
    
    # Signals
    finished = Signal(bool, str)  # success, message
    
    def __init__(self, base_url: str, api_key: str):
        super().__init__()
        self.base_url = base_url
        self.api_key = api_key
    
    def run(self):
        """Test the connection."""
        try:
            # Create temporary API service
            api_service = APIService(self.base_url, self.api_key)
            
            # Test connection
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            success = loop.run_until_complete(api_service.test_connection())
            
            # Clean up
            loop.run_until_complete(api_service.close())
            loop.close()
            
            if success:
                self.finished.emit(True, "Connection successful!")
            else:
                self.finished.emit(False, "Connection failed - unable to reach server")
                
        except Exception as e:
            self.finished.emit(False, f"Connection failed: {str(e)}")


class LoginDialog(QDialog):
    """Login and server configuration dialog."""
    
    def __init__(self, config_service: Optional[ConfigService] = None, parent=None):
        super().__init__(parent)
        
        self.config_service = config_service
        self.connection_config: Optional[Dict[str, Any]] = None
        self.test_worker: Optional[ConnectionTestWorker] = None
        
        self.setWindowTitle("People Management System - Login")
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setModal(True)
        self.resize(500, 600)
        
        self.setup_ui()
        self.setup_connections()
        self.load_saved_connections()
    
    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        self.create_header(layout)
        
        # Main content with tabs
        self.create_tabs(layout)
        
        # Progress bar (hidden by default)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: gray; font-style: italic;")
        layout.addWidget(self.status_label)
        
        # Buttons
        self.create_buttons(layout)
    
    def create_header(self, layout: QVBoxLayout):
        """Create the dialog header."""
        header_frame = QFrame()
        header_frame.setFrameStyle(QFrame.NoFrame)
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 10)
        
        # Title
        title_label = QLabel("People Management System")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(title_label)
        
        # Subtitle
        subtitle_label = QLabel("Connect to your People Management Server")
        subtitle_font = QFont()
        subtitle_font.setPointSize(11)
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet("color: gray;")
        header_layout.addWidget(subtitle_label)
        
        layout.addWidget(header_frame)
    
    def create_tabs(self, layout: QVBoxLayout):
        """Create the tab widget with connection options."""
        self.tab_widget = QTabWidget()
        
        # Quick Connect tab
        self.create_quick_connect_tab()
        
        # Advanced Settings tab
        self.create_advanced_settings_tab()
        
        # Recent Connections tab
        self.create_recent_connections_tab()
        
        layout.addWidget(self.tab_widget)
    
    def create_quick_connect_tab(self):
        """Create the quick connect tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        
        # Connection form
        form_group = QGroupBox("Server Connection")
        form_layout = QFormLayout(form_group)
        form_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        
        # Server URL
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("http://localhost:8000")
        self.url_edit.setText("http://localhost:8000")
        form_layout.addRow("Server URL:", self.url_edit)
        
        # API Key
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setPlaceholderText("Enter your API key")
        self.api_key_edit.setEchoMode(QLineEdit.Password)
        form_layout.addRow("API Key:", self.api_key_edit)
        
        # Show API key checkbox
        self.show_api_key_cb = QCheckBox("Show API key")
        self.show_api_key_cb.toggled.connect(
            lambda checked: self.api_key_edit.setEchoMode(
                QLineEdit.Normal if checked else QLineEdit.Password
            )
        )
        form_layout.addRow("", self.show_api_key_cb)
        
        layout.addWidget(form_group)
        
        # Remember connection
        self.remember_cb = QCheckBox("Remember this connection")
        self.remember_cb.setChecked(True)
        layout.addWidget(self.remember_cb)
        
        # Test connection button
        self.test_btn = QPushButton("Test Connection")
        self.test_btn.clicked.connect(self.test_connection)
        layout.addWidget(self.test_btn)
        
        # Spacer
        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        self.tab_widget.addTab(tab, "Quick Connect")
    
    def create_advanced_settings_tab(self):
        """Create the advanced settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Connection settings
        conn_group = QGroupBox("Connection Settings")
        conn_layout = QFormLayout(conn_group)
        
        self.timeout_edit = QLineEdit("30")
        conn_layout.addRow("Timeout (seconds):", self.timeout_edit)
        
        self.verify_ssl_cb = QCheckBox("Verify SSL certificates")
        self.verify_ssl_cb.setChecked(True)
        conn_layout.addRow("", self.verify_ssl_cb)
        
        layout.addWidget(conn_group)
        
        # Proxy settings (for future use)
        proxy_group = QGroupBox("Proxy Settings (Optional)")
        proxy_layout = QFormLayout(proxy_group)
        
        self.proxy_host_edit = QLineEdit()
        self.proxy_host_edit.setPlaceholderText("proxy.company.com")
        proxy_layout.addRow("Proxy Host:", self.proxy_host_edit)
        
        self.proxy_port_edit = QLineEdit()
        self.proxy_port_edit.setPlaceholderText("8080")
        proxy_layout.addRow("Proxy Port:", self.proxy_port_edit)
        
        layout.addWidget(proxy_group)
        
        # Spacer
        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        self.tab_widget.addTab(tab, "Advanced")
    
    def create_recent_connections_tab(self):
        """Create the recent connections tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Recent connections list
        connections_group = QGroupBox("Recent Connections")
        connections_layout = QVBoxLayout(connections_group)
        
        self.connections_combo = QComboBox()
        self.connections_combo.currentTextChanged.connect(self.on_recent_connection_selected)
        connections_layout.addWidget(self.connections_combo)
        
        # Connection details (read-only)
        details_layout = QFormLayout()
        
        self.recent_url_label = QLabel("-")
        details_layout.addRow("Server URL:", self.recent_url_label)
        
        self.recent_last_used_label = QLabel("-")
        details_layout.addRow("Last Used:", self.recent_last_used_label)
        
        self.recent_status_label = QLabel("-")
        details_layout.addRow("Status:", self.recent_status_label)
        
        connections_layout.addLayout(details_layout)
        
        # Use selected connection button
        self.use_recent_btn = QPushButton("Use Selected Connection")
        self.use_recent_btn.setEnabled(False)
        self.use_recent_btn.clicked.connect(self.use_recent_connection)
        connections_layout.addWidget(self.use_recent_btn)
        
        layout.addWidget(connections_group)
        
        # Clear recent connections
        clear_btn = QPushButton("Clear Recent Connections")
        clear_btn.clicked.connect(self.clear_recent_connections)
        layout.addWidget(clear_btn)
        
        # Spacer
        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        self.tab_widget.addTab(tab, "Recent")
    
    def create_buttons(self, layout: QVBoxLayout):
        """Create dialog buttons."""
        button_layout = QHBoxLayout()
        
        # Help button
        help_btn = QPushButton("Help")
        help_btn.clicked.connect(self.show_help)
        button_layout.addWidget(help_btn)
        
        # Spacer
        button_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        
        # Cancel button
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        # Connect button
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.setDefault(True)
        self.connect_btn.clicked.connect(self.connect_to_server)
        button_layout.addWidget(self.connect_btn)
        
        layout.addLayout(button_layout)
    
    def setup_connections(self):
        """Set up signal connections."""
        # Enable/disable connect button based on input
        self.url_edit.textChanged.connect(self.validate_input)
        self.api_key_edit.textChanged.connect(self.validate_input)
        
        # Initial validation
        self.validate_input()
    
    def validate_input(self):
        """Validate input and enable/disable connect button."""
        url = self.url_edit.text().strip()
        api_key = self.api_key_edit.text().strip()
        
        valid = bool(url and api_key)
        self.connect_btn.setEnabled(valid)
        self.test_btn.setEnabled(valid)
    
    def load_saved_connections(self):
        """Load saved connections from config service."""
        if not self.config_service:
            return
        
        try:
            # Load current config
            config = self.config_service.get_config()
            if config and config.connection:
                self.url_edit.setText(config.connection.base_url)
                # API key will be loaded from keyring when needed
            
            # Load recent connections
            recent_connections = self.config_service.get_recent_connections()
            self.connections_combo.clear()
            
            if recent_connections:
                for conn in recent_connections:
                    display_name = f"{conn.name} - {conn.base_url}"
                    self.connections_combo.addItem(display_name, conn)
                
                self.use_recent_btn.setEnabled(True)
            else:
                self.connections_combo.addItem("No recent connections")
                self.use_recent_btn.setEnabled(False)
                
        except Exception as e:
            logger.error(f"Error loading saved connections: {e}")
    
    def on_recent_connection_selected(self):
        """Handle recent connection selection."""
        current_data = self.connections_combo.currentData()
        if isinstance(current_data, RecentConnection):
            self.recent_url_label.setText(current_data.base_url)
            self.recent_last_used_label.setText(current_data.last_used.strftime("%Y-%m-%d %H:%M"))
            self.recent_status_label.setText("Success" if current_data.successful else "Failed")
            self.use_recent_btn.setEnabled(True)
        else:
            self.recent_url_label.setText("-")
            self.recent_last_used_label.setText("-")
            self.recent_status_label.setText("-")
            self.use_recent_btn.setEnabled(False)
    
    def use_recent_connection(self):
        """Use the selected recent connection."""
        current_data = self.connections_combo.currentData()
        if isinstance(current_data, RecentConnection):
            self.url_edit.setText(current_data.base_url)
            
            # Try to get API key from keyring
            if self.config_service:
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    api_key = loop.run_until_complete(
                        self.config_service.get_api_key(current_data.base_url)
                    )
                    loop.close()
                    
                    if api_key:
                        self.api_key_edit.setText(api_key)
                        
                except Exception as e:
                    logger.error(f"Error loading API key: {e}")
            
            # Switch to quick connect tab
            self.tab_widget.setCurrentIndex(0)
    
    def clear_recent_connections(self):
        """Clear recent connections."""
        reply = QMessageBox.question(
            self,
            "Clear Recent Connections",
            "Are you sure you want to clear all recent connections?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes and self.config_service:
            try:
                self.config_service._recent_connections.clear()
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.config_service.save_recent_connections())
                loop.close()
                
                # Reload the combo box
                self.load_saved_connections()
                
            except Exception as e:
                logger.error(f"Error clearing recent connections: {e}")
                QMessageBox.warning(self, "Error", f"Failed to clear recent connections: {e}")
    
    def test_connection(self):
        """Test the API connection."""
        url = self.url_edit.text().strip()
        api_key = self.api_key_edit.text().strip()
        
        if not url or not api_key:
            self.status_label.setText("Please enter both server URL and API key")
            return
        
        # Disable UI during test
        self.set_ui_enabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.status_label.setText("Testing connection...")
        
        # Start test worker
        self.test_worker = ConnectionTestWorker(url, api_key)
        self.test_worker.finished.connect(self.on_connection_test_finished)
        self.test_worker.start()
    
    def on_connection_test_finished(self, success: bool, message: str):
        """Handle connection test completion."""
        # Clean up worker
        if self.test_worker:
            self.test_worker.deleteLater()
            self.test_worker = None
        
        # Update UI
        self.set_ui_enabled(True)
        self.progress_bar.setVisible(False)
        
        if success:
            self.status_label.setText(f"✓ {message}")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.status_label.setText(f"✗ {message}")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
    
    def connect_to_server(self):
        """Connect to the server."""
        url = self.url_edit.text().strip()
        api_key = self.api_key_edit.text().strip()
        
        if not url or not api_key:
            QMessageBox.warning(self, "Invalid Input", "Please enter both server URL and API key")
            return
        
        # Create connection config
        timeout = float(self.timeout_edit.text() or "30")
        verify_ssl = self.verify_ssl_cb.isChecked()
        
        self.connection_config = {
            'base_url': url,
            'api_key': api_key,
            'timeout': timeout,
            'verify_ssl': verify_ssl
        }
        
        # Save connection if requested
        if self.remember_cb.isChecked() and self.config_service:
            try:
                connection_config = ConnectionConfig(**self.connection_config)
                
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.config_service.update_connection_config(connection_config))
                loop.run_until_complete(self.config_service.add_recent_connection("Server", url, True))
                loop.close()
                
            except Exception as e:
                logger.error(f"Error saving connection config: {e}")
        
        # Accept the dialog
        self.accept()
    
    def get_connection_config(self) -> Optional[Dict[str, Any]]:
        """Get the connection configuration."""
        return self.connection_config
    
    def set_ui_enabled(self, enabled: bool):
        """Enable/disable UI elements."""
        self.tab_widget.setEnabled(enabled)
        self.connect_btn.setEnabled(enabled)
        self.test_btn.setEnabled(enabled)
        self.cancel_btn.setEnabled(enabled)
    
    def show_help(self):
        """Show help dialog."""
        help_text = """
<h3>People Management System - Connection Help</h3>

<p><b>Server URL:</b> The base URL of your People Management System server.<br>
Examples:<br>
• http://localhost:8000 (local development)<br>
• https://people.company.com (production server)</p>

<p><b>API Key:</b> Your authentication key for accessing the API.<br>
Contact your system administrator to obtain an API key.</p>

<p><b>SSL Verification:</b> Enable this for production servers with valid SSL certificates.<br>
Disable only for development servers with self-signed certificates.</p>

<p><b>Recent Connections:</b> Previously used server connections are saved for convenience.<br>
API keys are stored securely in your system's credential store.</p>

<p>If you're having connection issues, try the "Test Connection" button to diagnose problems.</p>
        """
        
        msg = QMessageBox(self)
        msg.setWindowTitle("Connection Help")
        msg.setTextFormat(Qt.RichText)
        msg.setText(help_text)
        msg.setIcon(QMessageBox.Information)
        msg.exec()
    
    def closeEvent(self, event):
        """Handle dialog close event."""
        # Clean up any running workers
        if self.test_worker and self.test_worker.isRunning():
            self.test_worker.quit()
            self.test_worker.wait(3000)
        
        event.accept()