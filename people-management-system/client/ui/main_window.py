"""
Main Window for People Management System Client

Provides the main application interface with navigation sidebar and content area.
"""

import logging
from typing import Optional, Dict, Any

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QSplitter,
    QListWidget, QListWidgetItem, QStackedWidget, QLabel, QPushButton,
    QMenuBar, QMenu, QStatusBar, QToolBar, QFrame, QMessageBox,
    QProgressBar, QApplication, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QSize, QTimer, QSettings
from PySide6.QtGui import QIcon, QFont, QAction, QPalette, QPixmap

from client.services.api_service import APIService
from client.services.config_service import ConfigService
from client.utils.async_utils import QtSyncHelper
from client.ui.views.dashboard_view import DashboardView
from client.ui.views.people_view import PeopleView
from client.ui.views.departments_view import DepartmentsView
from client.ui.views.positions_view import PositionsView
from client.ui.views.employment_view import EmploymentView

logger = logging.getLogger(__name__)


class NavigationItem:
    """Navigation item data."""
    
    def __init__(self, name: str, icon: str, view_class, description: str = ""):
        self.name = name
        self.icon = icon
        self.view_class = view_class
        self.description = description


class MainWindow(QMainWindow):
    """Main application window."""
    
    # Signals
    closed = Signal()
    view_changed = Signal(str)  # View name
    
    def __init__(self, api_service: APIService, config_service: ConfigService, parent=None):
        super().__init__(parent)
        
        self.api_service = api_service
        self.config_service = config_service
        self.async_helper = QtSyncHelper(self)
        
        # Window state
        self.current_view_name = "dashboard"
        self.views: Dict[str, QWidget] = {}
        
        # Navigation items
        self.navigation_items = [
            NavigationItem("Dashboard", "📊", DashboardView, "System overview and statistics"),
            NavigationItem("People", "👥", PeopleView, "Manage people and personal information"),
            NavigationItem("Departments", "🏢", DepartmentsView, "Manage departments and organizational structure"),
            NavigationItem("Positions", "💼", PositionsView, "Manage job positions and requirements"),
            NavigationItem("Employment", "📝", EmploymentView, "Manage employment records and assignments"),
        ]
        
        self.setWindowTitle("People Management System")
        self.setMinimumSize(1000, 700)
        
        self.setup_ui()
        self.setup_connections()
        self.setup_status_bar()
        self.setup_menu_bar()
        self.setup_toolbar()
        
        self.load_window_settings()
        self.show_dashboard()
        
        # Start connection monitoring
        self.start_connection_monitoring()
    
    def setup_ui(self):
        """Set up the user interface."""
        # Central widget with splitter
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QHBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Main splitter
        self.splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(self.splitter)
        
        # Create sidebar
        self.create_sidebar()
        
        # Create content area
        self.create_content_area()
        
        # Set splitter sizes
        self.splitter.setSizes([250, 750])
        self.splitter.setCollapsible(0, False)  # Don't allow sidebar to collapse completely
    
    def create_sidebar(self):
        """Create the navigation sidebar."""
        sidebar_frame = QFrame()
        sidebar_frame.setFrameStyle(QFrame.StyledPanel)
        sidebar_frame.setMaximumWidth(300)
        sidebar_frame.setMinimumWidth(200)
        
        sidebar_layout = QVBoxLayout(sidebar_frame)
        sidebar_layout.setContentsMargins(5, 10, 5, 10)
        sidebar_layout.setSpacing(5)
        
        # Application title/logo area
        title_frame = QFrame()
        title_layout = QVBoxLayout(title_frame)
        title_layout.setContentsMargins(10, 5, 10, 15)
        
        app_title = QLabel("People Management")
        app_title_font = QFont()
        app_title_font.setPointSize(14)
        app_title_font.setBold(True)
        app_title.setFont(app_title_font)
        app_title.setAlignment(Qt.AlignCenter)
        title_layout.addWidget(app_title)
        
        subtitle = QLabel("System")
        subtitle_font = QFont()
        subtitle_font.setPointSize(10)
        subtitle.setFont(subtitle_font)
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: gray;")
        title_layout.addWidget(subtitle)
        
        sidebar_layout.addWidget(title_frame)
        
        # Navigation list
        self.nav_list = QListWidget()
        self.nav_list.setFrameStyle(QFrame.NoFrame)
        self.nav_list.itemClicked.connect(self.on_navigation_clicked)
        
        # Add navigation items
        for nav_item in self.navigation_items:
            item = QListWidgetItem(f"{nav_item.icon} {nav_item.name}")
            item.setData(Qt.UserRole, nav_item)
            item.setSizeHint(QSize(200, 40))
            item.setToolTip(nav_item.description)
            self.nav_list.addItem(item)
        
        sidebar_layout.addWidget(self.nav_list)
        
        # Connection status
        self.connection_status_frame = self.create_connection_status()
        sidebar_layout.addWidget(self.connection_status_frame)
        
        # Spacer
        sidebar_layout.addStretch()
        
        self.splitter.addWidget(sidebar_frame)
    
    def create_connection_status(self) -> QFrame:
        """Create connection status widget."""
        frame = QFrame()
        frame.setFrameStyle(QFrame.StyledPanel)
        frame.setMaximumHeight(80)
        
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 5, 10, 5)
        
        # Status indicator
        self.connection_status_label = QLabel("Connected")
        self.connection_status_label.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setPointSize(9)
        font.setBold(True)
        self.connection_status_label.setFont(font)
        layout.addWidget(self.connection_status_label)
        
        # Server info
        self.server_info_label = QLabel("")
        self.server_info_label.setAlignment(Qt.AlignCenter)
        self.server_info_label.setStyleSheet("color: gray; font-size: 8pt;")
        self.server_info_label.setWordWrap(True)
        layout.addWidget(self.server_info_label)
        
        # Update connection status
        self.update_connection_status(self.api_service.is_connected)
        
        return frame
    
    def create_content_area(self):
        """Create the main content area."""
        # Content frame
        content_frame = QFrame()
        content_frame.setFrameStyle(QFrame.StyledPanel)
        
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        # Header area with title and actions
        self.create_content_header(content_layout)
        
        # Main content stack
        self.content_stack = QStackedWidget()
        content_layout.addWidget(self.content_stack)
        
        self.splitter.addWidget(content_frame)
    
    def create_content_header(self, layout: QVBoxLayout):
        """Create the content header area."""
        header_frame = QFrame()
        header_frame.setMaximumHeight(60)
        header_frame.setFrameStyle(QFrame.NoFrame)
        
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(20, 10, 20, 10)
        
        # View title
        self.view_title = QLabel("Dashboard")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        self.view_title.setFont(title_font)
        header_layout.addWidget(self.view_title)
        
        # Spacer
        header_layout.addStretch()
        
        # Refresh button
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh_current_view)
        header_layout.addWidget(self.refresh_btn)
        
        layout.addWidget(header_frame)
    
    def setup_connections(self):
        """Set up signal connections."""
        # API service connections
        self.api_service.connection_status_changed.connect(self.update_connection_status)
        self.api_service.connection_error.connect(self.show_connection_error)
        self.api_service.operation_started.connect(self.show_operation_status)
        self.api_service.operation_completed.connect(self.on_operation_completed)
    
    def setup_status_bar(self):
        """Set up the status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Status message
        self.status_label = QLabel("Ready")
        self.status_bar.addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(200)
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
        # Connection indicator
        self.connection_indicator = QLabel("●")
        self.connection_indicator.setStyleSheet("color: green; font-size: 12pt; font-weight: bold;")
        self.connection_indicator.setToolTip("Connected to server")
        self.status_bar.addPermanentWidget(self.connection_indicator)
        
        # Update connection status now that the indicator is available
        self.update_connection_status(self.api_service.is_connected)
    
    def setup_menu_bar(self):
        """Set up the menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        export_action = QAction("Export Data...", self)
        export_action.setShortcut("Ctrl+E")
        export_action.triggered.connect(self.export_data)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu("View")
        
        refresh_action = QAction("Refresh", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self.refresh_current_view)
        view_menu.addAction(refresh_action)
        
        view_menu.addSeparator()
        
        # Theme submenu
        theme_menu = view_menu.addMenu("Theme")
        
        light_theme_action = QAction("Light", self)
        light_theme_action.triggered.connect(lambda: self.set_theme("light"))
        theme_menu.addAction(light_theme_action)
        
        dark_theme_action = QAction("Dark", self)
        dark_theme_action.triggered.connect(lambda: self.set_theme("dark"))
        theme_menu.addAction(dark_theme_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("Tools")
        
        settings_action = QAction("Settings...", self)
        settings_action.triggered.connect(self.show_settings)
        tools_menu.addAction(settings_action)
        
        clear_cache_action = QAction("Clear Cache", self)
        clear_cache_action.triggered.connect(self.clear_cache)
        tools_menu.addAction(clear_cache_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def setup_toolbar(self):
        """Set up the toolbar."""
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        
        # Quick actions
        refresh_action = QAction("🔄", self)
        refresh_action.setToolTip("Refresh current view")
        refresh_action.triggered.connect(self.refresh_current_view)
        toolbar.addAction(refresh_action)
        
        toolbar.addSeparator()
        
        # View navigation shortcuts
        for nav_item in self.navigation_items:
            action = QAction(nav_item.icon, self)
            action.setToolTip(f"Go to {nav_item.name}")
            action.triggered.connect(lambda checked, name=nav_item.name.lower(): self.show_view(name))
            toolbar.addAction(action)
    
    def start_connection_monitoring(self):
        """Start monitoring the API connection."""
        self.connection_timer = QTimer()
        self.connection_timer.timeout.connect(self.check_connection)
        self.connection_timer.start(30000)  # Check every 30 seconds
    
    def check_connection(self):
        """Check API connection status."""
        if self.api_service:
            self.api_service.test_connection_async()
    
    def on_navigation_clicked(self, item: QListWidgetItem):
        """Handle navigation item click."""
        nav_item: NavigationItem = item.data(Qt.UserRole)
        if nav_item:
            view_name = nav_item.name.lower()
            self.show_view(view_name)
    
    def show_view(self, view_name: str):
        """Show the specified view."""
        if view_name == self.current_view_name:
            return
        
        try:
            # Find navigation item
            nav_item = None
            for item in self.navigation_items:
                if item.name.lower() == view_name:
                    nav_item = item
                    break
            
            if not nav_item:
                logger.error(f"Unknown view: {view_name}")
                return
            
            # Create view if it doesn't exist
            if view_name not in self.views:
                self.create_view(view_name, nav_item)
            
            # Switch to view
            view = self.views[view_name]
            self.content_stack.setCurrentWidget(view)
            
            # Update UI
            self.current_view_name = view_name
            self.view_title.setText(nav_item.name)
            
            # Update navigation selection
            for i in range(self.nav_list.count()):
                item = self.nav_list.item(i)
                item_nav = item.data(Qt.UserRole)
                if item_nav and item_nav.name.lower() == view_name:
                    self.nav_list.setCurrentItem(item)
                    break
            
            # Emit signal
            self.view_changed.emit(view_name)
            
            # Update status
            self.status_label.setText(f"Viewing {nav_item.name}")
            
            logger.info(f"Switched to view: {view_name}")
            
        except Exception as e:
            logger.error(f"Error showing view {view_name}: {e}")
            self.show_error_message(f"Failed to load {view_name} view", str(e))
    
    def create_view(self, view_name: str, nav_item: NavigationItem):
        """Create a view instance."""
        try:
            view_class = nav_item.view_class
            view = view_class(self.api_service, self.config_service, self)
            
            self.views[view_name] = view
            self.content_stack.addWidget(view)
            
            logger.info(f"Created view: {view_name}")
            
        except Exception as e:
            logger.error(f"Error creating view {view_name}: {e}")
            # Create a simple error view
            error_view = QLabel(f"Error loading {nav_item.name} view:\n{str(e)}")
            error_view.setAlignment(Qt.AlignCenter)
            error_view.setStyleSheet("color: red; font-size: 14pt;")
            
            self.views[view_name] = error_view
            self.content_stack.addWidget(error_view)
    
    def show_dashboard(self):
        """Show the dashboard view."""
        self.show_view("dashboard")
    
    def refresh_current_view(self):
        """Refresh the current view."""
        if self.current_view_name in self.views:
            view = self.views[self.current_view_name]
            if hasattr(view, 'refresh'):
                view.refresh()
            else:
                # Clear cache and recreate view
                self.api_service.clear_cache()
                self.status_label.setText("Cache cleared - refresh completed")
    
    def update_connection_status(self, connected: bool):
        """Update connection status display."""
        if connected:
            self.connection_status_label.setText("✓ Connected")
            self.connection_status_label.setStyleSheet("color: green; font-weight: bold;")
            
            # Only update connection_indicator if it exists (status bar has been set up)
            if hasattr(self, 'connection_indicator'):
                self.connection_indicator.setStyleSheet("color: green; font-size: 12pt; font-weight: bold;")
                self.connection_indicator.setToolTip("Connected to server")
            
            # Update server info
            base_url = self.api_service.base_url
            self.server_info_label.setText(f"Server: {base_url}")
            
        else:
            self.connection_status_label.setText("✗ Disconnected")
            self.connection_status_label.setStyleSheet("color: red; font-weight: bold;")
            
            # Only update connection_indicator if it exists (status bar has been set up)
            if hasattr(self, 'connection_indicator'):
                self.connection_indicator.setStyleSheet("color: red; font-size: 12pt; font-weight: bold;")
                self.connection_indicator.setToolTip("Disconnected from server")
            
            self.server_info_label.setText("No connection")
    
    def show_connection_error(self, error_message: str):
        """Show connection error message."""
        if hasattr(self, 'status_label'):
            self.status_label.setText(f"Connection error: {error_message}")
        logger.error(f"Connection error: {error_message}")
    
    def show_operation_status(self, operation: str):
        """Show operation status."""
        if hasattr(self, 'status_label'):
            self.status_label.setText(operation)
        if hasattr(self, 'progress_bar'):
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # Indeterminate
    
    def on_operation_completed(self, operation: str, success: bool, message: str):
        """Handle operation completion."""
        if hasattr(self, 'progress_bar'):
            self.progress_bar.setVisible(False)
        
        if hasattr(self, 'status_label'):
            if success:
                self.status_label.setText(message)
            else:
                self.status_label.setText(f"Error: {message}")
        
        if not success:
            logger.error(f"Operation {operation} failed: {message}")
    
    def export_data(self):
        """Export data functionality."""
        # TODO: Implement data export
        QMessageBox.information(self, "Export Data", "Data export functionality will be implemented soon.")
    
    def set_theme(self, theme: str):
        """Set application theme."""
        # TODO: Implement theme switching
        QMessageBox.information(self, "Theme", f"Theme switching to {theme} will be implemented soon.")
    
    def show_settings(self):
        """Show settings dialog."""
        # TODO: Implement settings dialog
        QMessageBox.information(self, "Settings", "Settings dialog will be implemented soon.")
    
    def clear_cache(self):
        """Clear application cache."""
        self.api_service.clear_cache()
        self.status_label.setText("Cache cleared successfully")
    
    def show_about(self):
        """Show about dialog."""
        about_text = """
        <h3>People Management System</h3>
        <p>Version 1.0.0</p>
        <p>A modern GUI client for managing people, departments, and employment records.</p>
        <p>Built with PySide6 and Qt for Python.</p>
        """
        
        QMessageBox.about(self, "About People Management System", about_text)
    
    def show_error_message(self, title: str, message: str):
        """Show error message dialog."""
        QMessageBox.critical(self, title, message)
    
    def load_window_settings(self):
        """Load window settings from config."""
        try:
            if self.config_service:
                ui_config = self.config_service.get_ui_config()
                
                # Restore window geometry
                if ui_config.window_geometry:
                    geometry = ui_config.window_geometry
                    if all(key in geometry for key in ['x', 'y', 'width', 'height']):
                        self.setGeometry(
                            geometry['x'], geometry['y'],
                            geometry['width'], geometry['height']
                        )
                
                # Restore window state
                if ui_config.window_state == "maximized":
                    self.showMaximized()
                
                # Restore splitter sizes
                if ui_config.sidebar_width:
                    total_width = self.width()
                    content_width = total_width - ui_config.sidebar_width
                    self.splitter.setSizes([ui_config.sidebar_width, content_width])
                    
        except Exception as e:
            logger.error(f"Error loading window settings: {e}")
    
    def save_window_settings(self):
        """Save window settings to config."""
        try:
            if self.config_service:
                ui_config = self.config_service.get_ui_config()
                
                # Save window geometry
                geometry = self.geometry()
                ui_config.window_geometry = {
                    'x': geometry.x(),
                    'y': geometry.y(),
                    'width': geometry.width(),
                    'height': geometry.height()
                }
                
                # Save window state
                if self.isMaximized():
                    ui_config.window_state = "maximized"
                else:
                    ui_config.window_state = "normal"
                
                # Save splitter sizes  
                sizes = self.splitter.sizes()
                if sizes:
                    ui_config.sidebar_width = sizes[0]
                
                # Save config asynchronously
                def on_error(error):
                    logger.error(f"Error saving UI config: {error}")
                
                self.async_helper.call_sync(
                    lambda: self.config_service.update_ui_config(ui_config),
                    error_callback=on_error
                )
                
        except Exception as e:
            logger.error(f"Error saving window settings: {e}")
    
    def closeEvent(self, event):
        """Handle window close event."""
        try:
            # Save window settings
            self.save_window_settings()
            
            # Stop timers
            if hasattr(self, 'connection_timer'):
                self.connection_timer.stop()
            
            # Clean up async helper
            if self.async_helper:
                self.async_helper.cleanup()
            
            # Emit closed signal
            self.closed.emit()
            
            event.accept()
            
        except Exception as e:
            logger.error(f"Error during window close: {e}")
            event.accept()