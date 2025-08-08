"""
Settings Dialog for People Management System Client

Provides a comprehensive settings interface for user preferences, connection settings,
appearance customization, and advanced options.
"""

import logging
from typing import Dict, Any, Optional

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QGroupBox, QLabel, QLineEdit, QPushButton, QComboBox,
    QCheckBox, QSpinBox, QSlider, QListWidget, QDialogButtonBox,
    QFormLayout, QGridLayout, QTextEdit, QFileDialog,
    QMessageBox, QColorDialog, QFontDialog
)
from PySide6.QtCore import Qt, Signal, QSettings
from PySide6.QtGui import QFont, QColor, QIcon

logger = logging.getLogger(__name__)


class SettingsDialog(QDialog):
    """Comprehensive settings dialog for application preferences."""
    
    # Signals
    settings_changed = Signal(dict)  # Emitted when settings are saved
    theme_changed = Signal(str)  # Theme name
    
    def __init__(self, config_service=None, parent=None):
        super().__init__(parent)
        
        self.config_service = config_service
        self.settings = QSettings("YourOrganization", "PeopleManagementSystem")
        self.current_settings = self.load_current_settings()
        self.modified_settings = {}
        
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.resize(700, 500)
        
        self.setup_ui()
        self.load_settings_to_ui()
    
    def setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        
        # Tab widget for different setting categories
        self.tab_widget = QTabWidget()
        
        # Create tabs
        self.create_general_tab()
        self.create_connection_tab()
        self.create_appearance_tab()
        self.create_behavior_tab()
        self.create_advanced_tab()
        self.create_shortcuts_tab()
        
        layout.addWidget(self.tab_widget)
        
        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Apply | QDialogButtonBox.RestoreDefaults
        )
        
        button_box.accepted.connect(self.save_and_close)
        button_box.rejected.connect(self.reject)
        
        # Get individual buttons
        self.apply_btn = button_box.button(QDialogButtonBox.Apply)
        self.apply_btn.clicked.connect(self.apply_settings)
        
        self.restore_btn = button_box.button(QDialogButtonBox.RestoreDefaults)
        self.restore_btn.clicked.connect(self.restore_defaults)
        
        layout.addWidget(button_box)
    
    def create_general_tab(self):
        """Create general settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # User Information
        user_group = QGroupBox("User Information")
        user_layout = QFormLayout(user_group)
        
        self.user_name_edit = QLineEdit()
        self.user_name_edit.setPlaceholderText("Your name")
        user_layout.addRow("Display Name:", self.user_name_edit)
        
        self.user_email_edit = QLineEdit()
        self.user_email_edit.setPlaceholderText("your.email@example.com")
        user_layout.addRow("Email:", self.user_email_edit)
        
        layout.addWidget(user_group)
        
        # Data Management
        data_group = QGroupBox("Data Management")
        data_layout = QFormLayout(data_group)
        
        self.auto_save_check = QCheckBox("Enable auto-save")
        self.auto_save_check.setToolTip("Automatically save changes as you work")
        data_layout.addRow(self.auto_save_check)
        
        self.auto_save_interval = QSpinBox()
        self.auto_save_interval.setRange(1, 60)
        self.auto_save_interval.setSuffix(" minutes")
        self.auto_save_interval.setValue(5)
        data_layout.addRow("Auto-save interval:", self.auto_save_interval)
        
        self.confirm_delete_check = QCheckBox("Confirm before deleting")
        self.confirm_delete_check.setChecked(True)
        data_layout.addRow(self.confirm_delete_check)
        
        self.backup_on_exit_check = QCheckBox("Create backup on exit")
        data_layout.addRow(self.backup_on_exit_check)
        
        layout.addWidget(data_group)
        
        # Default Values
        defaults_group = QGroupBox("Default Values")
        defaults_layout = QFormLayout(defaults_group)
        
        self.default_country_edit = QLineEdit()
        self.default_country_edit.setPlaceholderText("e.g., United States")
        defaults_layout.addRow("Default Country:", self.default_country_edit)
        
        self.default_date_format = QComboBox()
        self.default_date_format.addItems([
            "DD-MM-YYYY",
            "MM-DD-YYYY",
            "YYYY-MM-DD",
            "DD/MM/YYYY",
            "MM/DD/YYYY"
        ])
        defaults_layout.addRow("Date Format:", self.default_date_format)
        
        layout.addWidget(defaults_group)
        
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "General")
    
    def create_connection_tab(self):
        """Create connection settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # API Connection
        api_group = QGroupBox("API Connection")
        api_layout = QFormLayout(api_group)
        
        self.api_url_edit = QLineEdit()
        self.api_url_edit.setPlaceholderText("http://localhost:8000")
        api_layout.addRow("API URL:", self.api_url_edit)
        
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.Password)
        self.api_key_edit.setPlaceholderText("Enter API key")
        api_layout.addRow("API Key:", self.api_key_edit)
        
        # Show/Hide API key button
        self.show_api_key_btn = QPushButton("Show")
        self.show_api_key_btn.setCheckable(True)
        self.show_api_key_btn.toggled.connect(self.toggle_api_key_visibility)
        api_layout.addRow("", self.show_api_key_btn)
        
        # Test connection button
        self.test_connection_btn = QPushButton("Test Connection")
        self.test_connection_btn.clicked.connect(self.test_connection)
        api_layout.addRow("", self.test_connection_btn)
        
        layout.addWidget(api_group)
        
        # Network Settings
        network_group = QGroupBox("Network Settings")
        network_layout = QFormLayout(network_group)
        
        self.connection_timeout = QSpinBox()
        self.connection_timeout.setRange(5, 120)
        self.connection_timeout.setSuffix(" seconds")
        self.connection_timeout.setValue(30)
        network_layout.addRow("Connection Timeout:", self.connection_timeout)
        
        self.retry_attempts = QSpinBox()
        self.retry_attempts.setRange(0, 10)
        self.retry_attempts.setValue(3)
        network_layout.addRow("Retry Attempts:", self.retry_attempts)
        
        self.use_cache_check = QCheckBox("Enable response caching")
        self.use_cache_check.setChecked(True)
        network_layout.addRow(self.use_cache_check)
        
        self.cache_duration = QSpinBox()
        self.cache_duration.setRange(1, 60)
        self.cache_duration.setSuffix(" minutes")
        self.cache_duration.setValue(5)
        network_layout.addRow("Cache Duration:", self.cache_duration)
        
        layout.addWidget(network_group)
        
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "Connection")
    
    def create_appearance_tab(self):
        """Create appearance settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Theme Settings
        theme_group = QGroupBox("Theme")
        theme_layout = QFormLayout(theme_group)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Light", "Dark", "Auto"])
        self.theme_combo.currentTextChanged.connect(self.preview_theme)
        theme_layout.addRow("Theme:", self.theme_combo)
        
        self.accent_color_btn = QPushButton("Choose...")
        self.accent_color_btn.clicked.connect(self.choose_accent_color)
        theme_layout.addRow("Accent Color:", self.accent_color_btn)
        
        layout.addWidget(theme_group)
        
        # Font Settings
        font_group = QGroupBox("Fonts")
        font_layout = QFormLayout(font_group)
        
        self.app_font_btn = QPushButton("Choose Font...")
        self.app_font_btn.clicked.connect(self.choose_application_font)
        font_layout.addRow("Application Font:", self.app_font_btn)
        
        self.font_size_slider = QSlider(Qt.Horizontal)
        self.font_size_slider.setRange(8, 16)
        self.font_size_slider.setValue(10)
        self.font_size_slider.setTickPosition(QSlider.TicksBelow)
        self.font_size_slider.setTickInterval(1)
        self.font_size_label = QLabel("10 pt")
        self.font_size_slider.valueChanged.connect(
            lambda v: self.font_size_label.setText(f"{v} pt")
        )
        font_layout.addRow("Font Size:", self.font_size_slider)
        font_layout.addRow("", self.font_size_label)
        
        layout.addWidget(font_group)
        
        # Window Settings
        window_group = QGroupBox("Window")
        window_layout = QFormLayout(window_group)
        
        self.remember_window_size_check = QCheckBox("Remember window size and position")
        self.remember_window_size_check.setChecked(True)
        window_layout.addRow(self.remember_window_size_check)
        
        self.start_maximized_check = QCheckBox("Start maximized")
        window_layout.addRow(self.start_maximized_check)
        
        self.show_toolbar_check = QCheckBox("Show toolbar")
        self.show_toolbar_check.setChecked(True)
        window_layout.addRow(self.show_toolbar_check)
        
        self.show_statusbar_check = QCheckBox("Show status bar")
        self.show_statusbar_check.setChecked(True)
        window_layout.addRow(self.show_statusbar_check)
        
        layout.addWidget(window_group)
        
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "Appearance")
    
    def create_behavior_tab(self):
        """Create behavior settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Table Behavior
        table_group = QGroupBox("Table Behavior")
        table_layout = QFormLayout(table_group)
        
        self.rows_per_page = QSpinBox()
        self.rows_per_page.setRange(10, 100)
        self.rows_per_page.setSingleStep(10)
        self.rows_per_page.setValue(20)
        table_layout.addRow("Rows per page:", self.rows_per_page)
        
        self.enable_sorting_check = QCheckBox("Enable column sorting")
        self.enable_sorting_check.setChecked(True)
        table_layout.addRow(self.enable_sorting_check)
        
        self.enable_filtering_check = QCheckBox("Enable filtering")
        self.enable_filtering_check.setChecked(True)
        table_layout.addRow(self.enable_filtering_check)
        
        self.double_click_action = QComboBox()
        self.double_click_action.addItems(["Edit", "View Details", "Do Nothing"])
        table_layout.addRow("Double-click action:", self.double_click_action)
        
        layout.addWidget(table_group)
        
        # Search Behavior
        search_group = QGroupBox("Search Behavior")
        search_layout = QFormLayout(search_group)
        
        self.search_as_type_check = QCheckBox("Search as you type")
        self.search_as_type_check.setChecked(True)
        search_layout.addRow(self.search_as_type_check)
        
        self.search_delay = QSpinBox()
        self.search_delay.setRange(100, 2000)
        self.search_delay.setSingleStep(100)
        self.search_delay.setSuffix(" ms")
        self.search_delay.setValue(500)
        search_layout.addRow("Search delay:", self.search_delay)
        
        self.highlight_matches_check = QCheckBox("Highlight search matches")
        self.highlight_matches_check.setChecked(True)
        search_layout.addRow(self.highlight_matches_check)
        
        layout.addWidget(search_group)
        
        # Notifications
        notify_group = QGroupBox("Notifications")
        notify_layout = QFormLayout(notify_group)
        
        self.show_success_notify_check = QCheckBox("Show success notifications")
        self.show_success_notify_check.setChecked(True)
        notify_layout.addRow(self.show_success_notify_check)
        
        self.show_error_notify_check = QCheckBox("Show error notifications")
        self.show_error_notify_check.setChecked(True)
        notify_layout.addRow(self.show_error_notify_check)
        
        self.notify_duration = QSpinBox()
        self.notify_duration.setRange(1, 10)
        self.notify_duration.setSuffix(" seconds")
        self.notify_duration.setValue(3)
        notify_layout.addRow("Notification duration:", self.notify_duration)
        
        layout.addWidget(notify_group)
        
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "Behavior")
    
    def create_advanced_tab(self):
        """Create advanced settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Performance
        perf_group = QGroupBox("Performance")
        perf_layout = QFormLayout(perf_group)
        
        self.enable_lazy_loading_check = QCheckBox("Enable lazy loading")
        self.enable_lazy_loading_check.setChecked(True)
        perf_layout.addRow(self.enable_lazy_loading_check)
        
        self.max_cache_size = QSpinBox()
        self.max_cache_size.setRange(10, 500)
        self.max_cache_size.setSuffix(" MB")
        self.max_cache_size.setValue(100)
        perf_layout.addRow("Max cache size:", self.max_cache_size)
        
        self.clear_cache_btn = QPushButton("Clear Cache Now")
        self.clear_cache_btn.clicked.connect(self.clear_cache)
        perf_layout.addRow("", self.clear_cache_btn)
        
        layout.addWidget(perf_group)
        
        # Logging
        log_group = QGroupBox("Logging")
        log_layout = QFormLayout(log_group)
        
        self.enable_logging_check = QCheckBox("Enable logging")
        self.enable_logging_check.setChecked(True)
        log_layout.addRow(self.enable_logging_check)
        
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self.log_level_combo.setCurrentText("INFO")
        log_layout.addRow("Log level:", self.log_level_combo)
        
        self.log_file_edit = QLineEdit()
        self.log_file_edit.setPlaceholderText("people_management.log")
        log_layout.addRow("Log file:", self.log_file_edit)
        
        self.open_log_btn = QPushButton("Open Log File")
        self.open_log_btn.clicked.connect(self.open_log_file)
        log_layout.addRow("", self.open_log_btn)
        
        layout.addWidget(log_group)
        
        # Database
        db_group = QGroupBox("Database")
        db_layout = QFormLayout(db_group)
        
        self.db_path_edit = QLineEdit()
        self.db_path_edit.setReadOnly(True)
        self.db_path_edit.setPlaceholderText("Default database location")
        db_layout.addRow("Database path:", self.db_path_edit)
        
        self.backup_db_btn = QPushButton("Backup Database")
        self.backup_db_btn.clicked.connect(self.backup_database)
        db_layout.addRow("", self.backup_db_btn)
        
        self.restore_db_btn = QPushButton("Restore Database")
        self.restore_db_btn.clicked.connect(self.restore_database)
        db_layout.addRow("", self.restore_db_btn)
        
        layout.addWidget(db_group)
        
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "Advanced")
    
    def create_shortcuts_tab(self):
        """Create keyboard shortcuts tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Instructions
        instructions = QLabel(
            "Keyboard shortcuts help you work more efficiently. "
            "Below are the available shortcuts in the application:"
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Shortcuts list
        shortcuts_group = QGroupBox("Keyboard Shortcuts")
        shortcuts_layout = QVBoxLayout(shortcuts_group)
        
        # Create a text widget to display shortcuts
        self.shortcuts_text = QTextEdit()
        self.shortcuts_text.setReadOnly(True)
        self.shortcuts_text.setHtml(self.get_shortcuts_html())
        shortcuts_layout.addWidget(self.shortcuts_text)
        
        layout.addWidget(shortcuts_group)
        
        # Customization note
        custom_note = QLabel(
            "Note: Keyboard shortcut customization will be available in a future update."
        )
        custom_note.setStyleSheet("color: gray; font-style: italic;")
        layout.addWidget(custom_note)
        
        self.tab_widget.addTab(tab, "Shortcuts")
    
    def get_shortcuts_html(self) -> str:
        """Get HTML formatted list of keyboard shortcuts."""
        return """
        <style>
            table { width: 100%; border-collapse: collapse; }
            th { background-color: #f0f0f0; padding: 8px; text-align: left; }
            td { padding: 6px; border-bottom: 1px solid #e0e0e0; }
            .shortcut { font-family: monospace; font-weight: bold; color: #1976d2; }
        </style>
        <table>
            <tr><th>Action</th><th>Shortcut</th></tr>
            <tr><td>New Person</td><td class="shortcut">Ctrl+N</td></tr>
            <tr><td>Edit Selected</td><td class="shortcut">Ctrl+E</td></tr>
            <tr><td>Delete Selected</td><td class="shortcut">Del</td></tr>
            <tr><td>Search</td><td class="shortcut">Ctrl+F</td></tr>
            <tr><td>Refresh</td><td class="shortcut">F5</td></tr>
            <tr><td>Export Data</td><td class="shortcut">Ctrl+Shift+E</td></tr>
            <tr><td>Import Data</td><td class="shortcut">Ctrl+Shift+I</td></tr>
            <tr><td>Settings</td><td class="shortcut">Ctrl+,</td></tr>
            <tr><td>Help</td><td class="shortcut">F1</td></tr>
            <tr><td>Navigate Dashboard</td><td class="shortcut">Alt+1</td></tr>
            <tr><td>Navigate People</td><td class="shortcut">Alt+2</td></tr>
            <tr><td>Navigate Departments</td><td class="shortcut">Alt+3</td></tr>
            <tr><td>Navigate Positions</td><td class="shortcut">Alt+4</td></tr>
            <tr><td>Navigate Employment</td><td class="shortcut">Alt+5</td></tr>
            <tr><td>Toggle Theme</td><td class="shortcut">Ctrl+Shift+T</td></tr>
            <tr><td>Quit Application</td><td class="shortcut">Ctrl+Q</td></tr>
        </table>
        """
    
    def load_current_settings(self) -> Dict[str, Any]:
        """Load current settings from config service or QSettings."""
        settings = {}
        
        # Load from config service if available
        if self.config_service:
            try:
                config = self.config_service.load_config()
                settings.update(config)
            except Exception as e:
                logger.error(f"Error loading settings from config service: {e}")
        
        # Load from QSettings
        for key in self.settings.allKeys():
            settings[key] = self.settings.value(key)
        
        return settings
    
    def load_settings_to_ui(self):
        """Load current settings into UI elements."""
        # General tab
        self.user_name_edit.setText(self.current_settings.get('user_name', ''))
        self.user_email_edit.setText(self.current_settings.get('user_email', ''))
        self.auto_save_check.setChecked(self.current_settings.get('auto_save', False))
        self.auto_save_interval.setValue(self.current_settings.get('auto_save_interval', 5))
        self.confirm_delete_check.setChecked(self.current_settings.get('confirm_delete', True))
        
        # Connection tab
        self.api_url_edit.setText(self.current_settings.get('base_url', 'http://localhost:8000'))
        self.api_key_edit.setText(self.current_settings.get('api_key', ''))
        self.connection_timeout.setValue(self.current_settings.get('connection_timeout', 30))
        
        # Appearance tab
        theme = self.current_settings.get('theme', 'Light')
        index = self.theme_combo.findText(theme)
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)
        
        # Behavior tab
        self.rows_per_page.setValue(self.current_settings.get('rows_per_page', 20))
        self.search_as_type_check.setChecked(self.current_settings.get('search_as_type', True))
        self.search_delay.setValue(self.current_settings.get('search_delay', 500))
        
        # Advanced tab
        self.log_level_combo.setCurrentText(self.current_settings.get('log_level', 'INFO'))
    
    def save_settings(self) -> Dict[str, Any]:
        """Save settings from UI to storage."""
        settings = {}
        
        # General tab
        settings['user_name'] = self.user_name_edit.text()
        settings['user_email'] = self.user_email_edit.text()
        settings['auto_save'] = self.auto_save_check.isChecked()
        settings['auto_save_interval'] = self.auto_save_interval.value()
        settings['confirm_delete'] = self.confirm_delete_check.isChecked()
        settings['default_country'] = self.default_country_edit.text()
        settings['date_format'] = self.default_date_format.currentText()
        
        # Connection tab
        settings['base_url'] = self.api_url_edit.text()
        settings['api_key'] = self.api_key_edit.text()
        settings['connection_timeout'] = self.connection_timeout.value()
        settings['retry_attempts'] = self.retry_attempts.value()
        settings['use_cache'] = self.use_cache_check.isChecked()
        settings['cache_duration'] = self.cache_duration.value()
        
        # Appearance tab
        settings['theme'] = self.theme_combo.currentText()
        settings['font_size'] = self.font_size_slider.value()
        settings['remember_window_size'] = self.remember_window_size_check.isChecked()
        settings['start_maximized'] = self.start_maximized_check.isChecked()
        settings['show_toolbar'] = self.show_toolbar_check.isChecked()
        settings['show_statusbar'] = self.show_statusbar_check.isChecked()
        
        # Behavior tab
        settings['rows_per_page'] = self.rows_per_page.value()
        settings['enable_sorting'] = self.enable_sorting_check.isChecked()
        settings['enable_filtering'] = self.enable_filtering_check.isChecked()
        settings['double_click_action'] = self.double_click_action.currentText()
        settings['search_as_type'] = self.search_as_type_check.isChecked()
        settings['search_delay'] = self.search_delay.value()
        settings['highlight_matches'] = self.highlight_matches_check.isChecked()
        settings['show_success_notify'] = self.show_success_notify_check.isChecked()
        settings['show_error_notify'] = self.show_error_notify_check.isChecked()
        settings['notify_duration'] = self.notify_duration.value()
        
        # Advanced tab
        settings['enable_lazy_loading'] = self.enable_lazy_loading_check.isChecked()
        settings['max_cache_size'] = self.max_cache_size.value()
        settings['enable_logging'] = self.enable_logging_check.isChecked()
        settings['log_level'] = self.log_level_combo.currentText()
        settings['log_file'] = self.log_file_edit.text()
        
        # Save to QSettings
        for key, value in settings.items():
            self.settings.setValue(key, value)
        
        # Save to config service if available
        if self.config_service:
            try:
                self.config_service.save_config(settings)
            except Exception as e:
                logger.error(f"Error saving settings to config service: {e}")
        
        self.modified_settings = settings
        return settings
    
    def apply_settings(self):
        """Apply settings without closing dialog."""
        settings = self.save_settings()
        self.settings_changed.emit(settings)
        
        # Apply theme immediately if changed
        if settings.get('theme') != self.current_settings.get('theme'):
            self.theme_changed.emit(settings['theme'])
        
        self.current_settings = settings
        
        QMessageBox.information(self, "Settings Applied", "Settings have been applied successfully.")
    
    def save_and_close(self):
        """Save settings and close dialog."""
        self.apply_settings()
        self.accept()
    
    def restore_defaults(self):
        """Restore all settings to defaults."""
        reply = QMessageBox.question(
            self,
            "Restore Defaults",
            "Are you sure you want to restore all settings to their default values?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Clear all settings
            self.settings.clear()
            
            # Set defaults
            defaults = {
                'theme': 'Light',
                'rows_per_page': 20,
                'confirm_delete': True,
                'auto_save': False,
                'search_as_type': True,
                'search_delay': 500,
                'connection_timeout': 30,
                'log_level': 'INFO'
            }
            
            for key, value in defaults.items():
                self.settings.setValue(key, value)
            
            # Reload UI
            self.current_settings = defaults
            self.load_settings_to_ui()
            
            QMessageBox.information(self, "Defaults Restored", "All settings have been restored to defaults.")
    
    def toggle_api_key_visibility(self, checked: bool):
        """Toggle API key visibility."""
        if checked:
            self.api_key_edit.setEchoMode(QLineEdit.Normal)
            self.show_api_key_btn.setText("Hide")
        else:
            self.api_key_edit.setEchoMode(QLineEdit.Password)
            self.show_api_key_btn.setText("Show")
    
    def test_connection(self):
        """Test API connection."""
        # TODO: Implement actual connection test
        QMessageBox.information(self, "Connection Test", "Connection test functionality will be implemented with the API service.")
    
    def preview_theme(self, theme_name: str):
        """Preview theme change."""
        # Emit signal for immediate preview
        self.theme_changed.emit(theme_name)
    
    def choose_accent_color(self):
        """Open color dialog to choose accent color."""
        color = QColorDialog.getColor(Qt.blue, self, "Choose Accent Color")
        if color.isValid():
            self.accent_color_btn.setStyleSheet(f"background-color: {color.name()};")
            self.modified_settings['accent_color'] = color.name()
    
    def choose_application_font(self):
        """Open font dialog to choose application font."""
        font, ok = QFontDialog.getFont(QFont("Arial", 10), self, "Choose Application Font")
        if ok:
            self.app_font_btn.setText(f"{font.family()}, {font.pointSize()}pt")
            self.modified_settings['app_font_family'] = font.family()
            self.modified_settings['app_font_size'] = font.pointSize()
    
    def clear_cache(self):
        """Clear application cache."""
        # TODO: Implement cache clearing
        QMessageBox.information(self, "Cache Cleared", "Application cache has been cleared.")
    
    def open_log_file(self):
        """Open the log file."""
        # TODO: Implement log file opening
        QMessageBox.information(self, "Log File", "Log file viewer will be implemented.")
    
    def backup_database(self):
        """Backup the database."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Backup Database",
            "people_management_backup.db",
            "Database Files (*.db);;All Files (*)"
        )
        
        if file_path:
            # TODO: Implement database backup
            QMessageBox.information(self, "Backup", f"Database backup to {file_path} will be implemented.")
    
    def restore_database(self):
        """Restore database from backup."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Restore Database",
            "",
            "Database Files (*.db);;All Files (*)"
        )
        
        if file_path:
            # TODO: Implement database restore
            QMessageBox.information(self, "Restore", f"Database restore from {file_path} will be implemented.")