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
from PySide6.QtGui import QIcon, QFont, QAction, QPalette, QPixmap, QKeySequence, QShortcut

from client.services.api_service import APIService
from client.services.config_service import ConfigService
from client.utils.async_utils import QtSyncHelper
from client.ui.views.dashboard_view import DashboardView
from client.ui.views.people_view import PeopleView
from client.ui.views.departments_view import DepartmentsView
from client.ui.views.positions_view import PositionsView
from client.ui.views.employment_view import EmploymentView
from client.ui.dialogs.settings_dialog import SettingsDialog
from client.ui.widgets.error_dialog import show_error, show_network_error
from client.utils.icon_manager import get_icon_manager, get_icon, get_emoji
from client.resources.themes import theme_manager

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
        
        # Icon manager
        self.icon_manager = get_icon_manager()
        
        # Navigation items with proper icons
        self.navigation_items = [
            NavigationItem("Dashboard", get_emoji('dashboard'), DashboardView, "System overview and statistics (Alt+1)"),
            NavigationItem("People", get_emoji('people'), PeopleView, "Manage people and personal information (Alt+2)"),
            NavigationItem("Departments", get_emoji('departments'), DepartmentsView, "Manage departments and organizational structure (Alt+3)"),
            NavigationItem("Positions", get_emoji('positions'), PositionsView, "Manage job positions and requirements (Alt+4)"),
            NavigationItem("Employment", get_emoji('employment'), EmploymentView, "Manage employment records and assignments (Alt+5)"),
        ]
        
        self.setWindowTitle("People Management System")
        self.setMinimumSize(1000, 700)
        
        self.setup_ui()
        self.setup_connections()
        self.setup_status_bar()
        self.setup_menu_bar()
        self.setup_toolbar()
        self.setup_keyboard_shortcuts()
        
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
        
        # Refresh button with icon and tooltip
        self.refresh_btn = QPushButton(f"{get_emoji('refresh')} Refresh")
        self.refresh_btn.setToolTip("Refresh current view (F5)")
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
        
        # Connection indicator with proper icon
        self.connection_indicator = QLabel(get_emoji('connected'))
        self.connection_indicator.setStyleSheet("font-size: 12pt; font-weight: bold;")
        self.connection_indicator.setToolTip("Connected to server")
        self.status_bar.addPermanentWidget(self.connection_indicator)
        
        # Update connection status now that the indicator is available
        self.update_connection_status(self.api_service.is_connected)
    
    def setup_menu_bar(self):
        """Set up the menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        export_action = QAction(f"{get_emoji('export')} Export Data...", self)
        export_action.setShortcut("Ctrl+Shift+E")
        export_action.setToolTip("Export data to file")
        export_action.triggered.connect(self.export_data)
        file_menu.addAction(export_action)
        
        import_action = QAction(f"{get_emoji('import')} Import Data...", self)
        import_action.setShortcut("Ctrl+Shift+I")
        import_action.setToolTip("Import data from file")
        import_action.triggered.connect(self.import_data)
        file_menu.addAction(import_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction(f"{get_emoji('logout')} Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.setToolTip("Exit the application")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu("View")
        
        refresh_action = QAction(f"{get_emoji('refresh')} Refresh", self)
        refresh_action.setShortcut("F5")
        refresh_action.setToolTip("Refresh current view")
        refresh_action.triggered.connect(self.refresh_current_view)
        view_menu.addAction(refresh_action)
        
        view_menu.addSeparator()
        
        # Theme submenu
        theme_menu = view_menu.addMenu("Theme")
        
        light_theme_action = QAction("☀️ Light", self)
        light_theme_action.setCheckable(True)
        light_theme_action.triggered.connect(lambda: self.set_theme("light"))
        theme_menu.addAction(light_theme_action)
        
        dark_theme_action = QAction("🌙 Dark", self)
        dark_theme_action.setCheckable(True)
        dark_theme_action.triggered.connect(lambda: self.set_theme("dark"))
        theme_menu.addAction(dark_theme_action)
        
        # Theme action group for radio button behavior
        self.theme_actions = [light_theme_action, dark_theme_action]
        light_theme_action.setChecked(True)  # Default to light theme
        
        # Tools menu
        tools_menu = menubar.addMenu("Tools")
        
        settings_action = QAction(f"{get_emoji('settings')} Settings...", self)
        settings_action.setShortcut("Ctrl+,")
        settings_action.setToolTip("Open application settings")
        settings_action.triggered.connect(self.show_settings)
        tools_menu.addAction(settings_action)
        
        clear_cache_action = QAction("Clear Cache", self)
        clear_cache_action.triggered.connect(self.clear_cache)
        tools_menu.addAction(clear_cache_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        user_guide_action = QAction(f"{get_emoji('help')} User Guide", self)
        user_guide_action.setShortcut("F1")
        user_guide_action.setToolTip("Open user guide")
        user_guide_action.triggered.connect(self.show_user_guide)
        help_menu.addAction(user_guide_action)
        
        help_menu.addSeparator()
        
        about_action = QAction(f"{get_emoji('info')} About", self)
        about_action.setToolTip("About this application")
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def setup_toolbar(self):
        """Set up the toolbar."""
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        
        # Quick actions with proper icons
        refresh_action = QAction(get_emoji('refresh'), self)
        refresh_action.setToolTip("Refresh current view (F5)")
        refresh_action.triggered.connect(self.refresh_current_view)
        toolbar.addAction(refresh_action)
        
        # Add person action
        add_person_action = QAction(get_emoji('add'), self)
        add_person_action.setToolTip("Add new person (Ctrl+N)")
        add_person_action.triggered.connect(self.quick_add_person)
        toolbar.addAction(add_person_action)
        
        # Search action
        search_action = QAction(get_emoji('search'), self)
        search_action.setToolTip("Search (Ctrl+F)")
        search_action.triggered.connect(self.focus_search)
        toolbar.addAction(search_action)
        
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
        logger.info(f"show_view called with: {view_name}")
        
        if view_name == self.current_view_name and view_name in self.views:
            logger.info(f"View {view_name} already current")
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
                logger.info(f"Creating new view: {view_name}")
                self.create_view(view_name, nav_item)
            else:
                logger.info(f"Using existing view: {view_name}")
            
            # Switch to view
            view = self.views[view_name]
            self.content_stack.setCurrentWidget(view)
            logger.info(f"Set current widget to: {view_name}")
            
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
            logger.info(f"Creating view instance for: {view_name}")
            view_class = nav_item.view_class
            view = view_class(self.api_service, self.config_service, self)
            
            self.views[view_name] = view
            self.content_stack.addWidget(view)
            
            # Force view to be visible
            view.show()
            
            logger.info(f"Successfully created and added view: {view_name}")
            
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
        logger.info("show_dashboard() called - switching to dashboard view")
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
            self.connection_status_label.setText(f"{get_emoji('success')} Connected")
            self.connection_status_label.setStyleSheet("color: green; font-weight: bold;")
            
            # Only update connection_indicator if it exists (status bar has been set up)
            if hasattr(self, 'connection_indicator'):
                self.connection_indicator.setText(get_emoji('connected'))
                self.connection_indicator.setToolTip("Connected to server")
            
            # Update server info
            base_url = self.api_service.base_url
            self.server_info_label.setText(f"Server: {base_url}")
            
        else:
            self.connection_status_label.setText(f"{get_emoji('error')} Disconnected")
            self.connection_status_label.setStyleSheet("color: red; font-weight: bold;")
            
            # Only update connection_indicator if it exists (status bar has been set up)
            if hasattr(self, 'connection_indicator'):
                self.connection_indicator.setText(get_emoji('disconnected'))
                self.connection_indicator.setToolTip("Disconnected from server")
            
            self.server_info_label.setText("No connection")
    
    def show_connection_error(self, error_message: str):
        """Show connection error message."""
        if hasattr(self, 'status_label'):
            self.status_label.setText(f"Connection error: {error_message}")
        logger.error(f"Connection error: {error_message}")
        
        # Show network error dialog with retry option
        show_network_error(
            message="Failed to connect to the server",
            details=error_message,
            retry_action=lambda: self.api_service.test_connection_async(),
            parent=self
        )
    
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
        if self.current_view_name in self.views:
            view = self.views[self.current_view_name]
            if hasattr(view, 'export_data'):
                view.export_data()
            else:
                QMessageBox.information(
                    self,
                    "Export Not Available",
                    f"Export is not available for the {self.current_view_name} view."
                )
        else:
            QMessageBox.warning(self, "No View", "Please select a view to export data from.")
    
    def set_theme(self, theme: str):
        """Set application theme."""
        # Apply theme using theme manager
        theme_manager.apply_theme(theme)
        
        # Update theme action checkmarks
        for action in self.theme_actions:
            action.setChecked(theme.lower() in action.text().lower())
        
        # Save theme preference
        if self.config_service:
            self.config_service.set_setting('theme', theme)
        
        self.status_label.setText(f"Theme changed to {theme}")
    
    def show_settings(self):
        """Show settings dialog."""
        dialog = SettingsDialog(self.config_service, self)
        dialog.settings_changed.connect(self.on_settings_changed)
        dialog.theme_changed.connect(self.set_theme)
        dialog.exec()
    
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
    
    def show_error_message(self, title: str, message: str, details: str = None):
        """Show enhanced error message dialog."""
        show_error(
            title=title,
            message=message,
            details=details,
            parent=self
        )
    
    def setup_keyboard_shortcuts(self):
        """Set up keyboard shortcuts for the application."""
        # Navigation shortcuts
        QShortcut(QKeySequence("Alt+1"), self, lambda: self.show_view("dashboard"))
        QShortcut(QKeySequence("Alt+2"), self, lambda: self.show_view("people"))
        QShortcut(QKeySequence("Alt+3"), self, lambda: self.show_view("departments"))
        QShortcut(QKeySequence("Alt+4"), self, lambda: self.show_view("positions"))
        QShortcut(QKeySequence("Alt+5"), self, lambda: self.show_view("employment"))
        
        # Action shortcuts
        QShortcut(QKeySequence("Ctrl+N"), self, self.quick_add_person)
        QShortcut(QKeySequence("Ctrl+F"), self, self.focus_search)
        QShortcut(QKeySequence("Ctrl+Shift+T"), self, self.toggle_theme)
        QShortcut(QKeySequence("Escape"), self, self.escape_pressed)
        
        logger.info("Keyboard shortcuts initialized")
    
    def quick_add_person(self):
        """Quick action to add a new person."""
        # Navigate to people view and trigger add
        self.show_view("people")
        if "people" in self.views:
            view = self.views["people"]
            if hasattr(view, 'add_person'):
                view.add_person()
    
    def focus_search(self):
        """Focus on search in current view."""
        if self.current_view_name in self.views:
            view = self.views[self.current_view_name]
            if hasattr(view, 'focus_search'):
                view.focus_search()
            elif hasattr(view, 'search_widget'):
                view.search_widget.setFocus()
    
    def toggle_theme(self):
        """Toggle between light and dark themes."""
        current_theme = theme_manager.get_current_theme()
        new_theme = "dark" if current_theme == "light" else "light"
        self.set_theme(new_theme)
    
    def escape_pressed(self):
        """Handle escape key press."""
        # Clear search or close dialogs
        if self.current_view_name in self.views:
            view = self.views[self.current_view_name]
            if hasattr(view, 'clear_search'):
                view.clear_search()
    
    def import_data(self):
        """Import data functionality."""
        if self.current_view_name in self.views:
            view = self.views[self.current_view_name]
            if hasattr(view, 'import_data'):
                view.import_data()
            else:
                QMessageBox.information(
                    self,
                    "Import Not Available",
                    f"Import is not available for the {self.current_view_name} view."
                )
        else:
            QMessageBox.warning(self, "No View", "Please select a view to import data into.")
    
    def show_user_guide(self):
        """Show user guide."""
        # Try to open USER_GUIDE.md if it exists
        import os
        import webbrowser
        from pathlib import Path
        
        guide_path = Path(__file__).parent.parent.parent / "USER_GUIDE.md"
        if guide_path.exists():
            webbrowser.open(f"file://{guide_path}")
        else:
            QMessageBox.information(
                self,
                "User Guide",
                "User Guide is being prepared.\n\n"
                "Key Shortcuts:\n"
                "• Alt+1-5: Navigate views\n"
                "• Ctrl+N: Add new person\n"
                "• Ctrl+F: Search\n"
                "• F5: Refresh\n"
                "• Ctrl+Shift+T: Toggle theme\n"
                "• Ctrl+,: Settings\n"
                "• F1: This help"
            )
    
    def on_settings_changed(self, settings: Dict[str, Any]):
        """Handle settings changes."""
        # Apply relevant settings
        if 'rows_per_page' in settings:
            # Update all views with new page size
            for view in self.views.values():
                if hasattr(view, 'page_size'):
                    view.page_size = settings['rows_per_page']
        
        # Refresh current view to apply changes
        self.refresh_current_view()
        
        self.status_label.setText("Settings applied successfully")
    
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