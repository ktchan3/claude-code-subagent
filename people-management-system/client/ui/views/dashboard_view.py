"""
Dashboard View for People Management System Client

Provides system overview with statistics, charts, and quick actions.
"""

import logging
from typing import Dict, Any, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QFrame, QGroupBox, QScrollArea, QProgressBar, QSizePolicy,
    QSpacerItem, QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QPalette, QColor

from client.services.api_service import APIService
from client.services.config_service import ConfigService

logger = logging.getLogger(__name__)


class StatCard(QFrame):
    """Statistical information card widget."""
    
    def __init__(self, title: str, value: str = "0", icon: str = "📊", parent=None):
        super().__init__(parent)
        
        self.setFrameStyle(QFrame.StyledPanel)
        self.setMinimumSize(150, 100)
        self.setMaximumHeight(120)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Header with icon and title
        header_layout = QHBoxLayout()
        
        # Icon
        icon_label = QLabel(icon)
        icon_font = QFont()
        icon_font.setPointSize(16)
        icon_label.setFont(icon_font)
        header_layout.addWidget(icon_label)
        
        # Title
        title_label = QLabel(title)
        title_font = QFont()
        title_font.setPointSize(10)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #666;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Value
        self.value_label = QLabel(value)
        value_font = QFont()
        value_font.setPointSize(24)
        value_font.setBold(True)
        self.value_label.setFont(value_font)
        self.value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.value_label)
        
        layout.addStretch()
    
    def set_value(self, value: str):
        """Update the card value."""
        self.value_label.setText(value)


class DashboardView(QWidget):
    """Dashboard view showing system statistics and overview."""
    
    # Signals
    navigation_requested = Signal(str)  # View name to navigate to
    
    def __init__(self, api_service: APIService, config_service: ConfigService, parent=None):
        super().__init__(parent)
        
        self.api_service = api_service
        self.config_service = config_service
        
        # Statistics data
        self.stats_data: Optional[Dict[str, Any]] = None
        
        # Auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_data)
        
        self.setup_ui()
        self.setup_connections()
        self.start_auto_refresh()
        
        # Delay initial data loading to allow connection to be established
        self.initial_load_timer = QTimer()
        self.initial_load_timer.setSingleShot(True)
        self.initial_load_timer.timeout.connect(self.initial_data_load)
        self.initial_load_timer.start(500)  # Wait 500ms for connection to be established
    
    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Welcome section
        self.create_welcome_section(layout)
        
        # Statistics cards
        self.create_statistics_section(layout)
        
        # Main content area
        content_layout = QHBoxLayout()
        
        # Left column - Recent activity
        self.create_activity_section(content_layout)
        
        # Right column - Quick actions
        self.create_quick_actions_section(content_layout)
        
        layout.addLayout(content_layout)
        
        # Add stretch to push content up
        layout.addStretch()
    
    def create_welcome_section(self, layout: QVBoxLayout):
        """Create welcome section."""
        welcome_frame = QFrame()
        welcome_layout = QVBoxLayout(welcome_frame)
        welcome_layout.setContentsMargins(0, 0, 0, 10)
        
        # Welcome message
        welcome_label = QLabel("Welcome to People Management System")
        welcome_font = QFont()
        welcome_font.setPointSize(18)
        welcome_font.setBold(True)
        welcome_label.setFont(welcome_font)
        welcome_layout.addWidget(welcome_label)
        
        # Subtitle
        subtitle_label = QLabel("Manage your people, departments, and employment records")
        subtitle_font = QFont()
        subtitle_font.setPointSize(12)
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setStyleSheet("color: #666;")
        welcome_layout.addWidget(subtitle_label)
        
        layout.addWidget(welcome_frame)
    
    def create_statistics_section(self, layout: QVBoxLayout):
        """Create statistics cards section."""
        stats_group = QGroupBox("System Overview")
        stats_layout = QVBoxLayout(stats_group)
        
        # Loading indicator
        self.stats_loading = QProgressBar()
        self.stats_loading.setRange(0, 0)  # Indeterminate
        self.stats_loading.setVisible(False)
        stats_layout.addWidget(self.stats_loading)
        
        # Statistics cards grid
        cards_widget = QWidget()
        self.cards_layout = QGridLayout(cards_widget)
        self.cards_layout.setSpacing(15)
        
        # Create stat cards
        self.people_card = StatCard("Total People", "0", "👥")
        self.departments_card = StatCard("Departments", "0", "🏢")
        self.positions_card = StatCard("Positions", "0", "💼")
        self.active_employment_card = StatCard("Active Employment", "0", "📝")
        
        # Add cards to grid
        self.cards_layout.addWidget(self.people_card, 0, 0)
        self.cards_layout.addWidget(self.departments_card, 0, 1)
        self.cards_layout.addWidget(self.positions_card, 0, 2)
        self.cards_layout.addWidget(self.active_employment_card, 0, 3)
        
        # Add second row of cards
        self.recent_hires_card = StatCard("Recent Hires", "0", "🆕")
        self.pending_reviews_card = StatCard("Pending Reviews", "0", "⏳")
        self.upcoming_birthdays_card = StatCard("Upcoming Birthdays", "0", "🎂")
        self.system_alerts_card = StatCard("System Alerts", "0", "⚠️")
        
        self.cards_layout.addWidget(self.recent_hires_card, 1, 0)
        self.cards_layout.addWidget(self.pending_reviews_card, 1, 1)
        self.cards_layout.addWidget(self.upcoming_birthdays_card, 1, 2)
        self.cards_layout.addWidget(self.system_alerts_card, 1, 3)
        
        stats_layout.addWidget(cards_widget)
        layout.addWidget(stats_group)
    
    def create_activity_section(self, layout: QHBoxLayout):
        """Create recent activity section."""
        activity_group = QGroupBox("Recent Activity")
        activity_group.setMinimumWidth(400)
        activity_layout = QVBoxLayout(activity_group)
        
        # Activity list
        self.activity_list = QListWidget()
        self.activity_list.setMaximumHeight(300)
        activity_layout.addWidget(self.activity_list)
        
        # Refresh button
        refresh_activity_btn = QPushButton("Refresh Activity")
        refresh_activity_btn.clicked.connect(self.refresh_activity)
        activity_layout.addWidget(refresh_activity_btn)
        
        layout.addWidget(activity_group)
    
    def create_quick_actions_section(self, layout: QHBoxLayout):
        """Create quick actions section."""
        actions_group = QGroupBox("Quick Actions")
        actions_group.setMaximumWidth(300)
        actions_layout = QVBoxLayout(actions_group)
        
        # Action buttons
        actions = [
            ("👤 Add New Person", "people"),
            ("🏢 Add Department", "departments"),
            ("💼 Add Position", "positions"),
            ("📝 Create Employment Record", "employment"),
            ("👥 View All People", "people"),
            ("📊 Generate Reports", "reports"),
        ]
        
        for text, action in actions:
            btn = QPushButton(text)
            btn.clicked.connect(lambda checked, a=action: self.handle_quick_action(a))
            btn.setMinimumHeight(40)
            btn.setStyleSheet("""
                QPushButton {
                    text-align: left;
                    padding: 10px;
                    border: 1px solid #ccc;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #f0f0f0;
                }
            """)
            actions_layout.addWidget(btn)
        
        # Spacer
        actions_layout.addStretch()
        
        # System info
        self.create_system_info(actions_layout)
        
        layout.addWidget(actions_group)
    
    def create_system_info(self, layout: QVBoxLayout):
        """Create system information section."""
        info_frame = QFrame()
        info_frame.setFrameStyle(QFrame.StyledPanel)
        info_layout = QVBoxLayout(info_frame)
        info_layout.setContentsMargins(10, 10, 10, 10)
        
        # System status
        status_label = QLabel("System Status")
        status_font = QFont()
        status_font.setBold(True)
        status_label.setFont(status_font)
        info_layout.addWidget(status_label)
        
        self.connection_status_label = QLabel("🔴 Disconnected")
        info_layout.addWidget(self.connection_status_label)
        
        self.server_info_label = QLabel("Server: Not connected")
        self.server_info_label.setStyleSheet("color: #666; font-size: 9pt;")
        info_layout.addWidget(self.server_info_label)
        
        # Last update
        self.last_update_label = QLabel("Last updated: Never")
        self.last_update_label.setStyleSheet("color: #666; font-size: 9pt;")
        info_layout.addWidget(self.last_update_label)
        
        layout.addWidget(info_frame)
    
    def setup_connections(self):
        """Set up signal connections."""
        # API service connections
        self.api_service.connection_status_changed.connect(self.update_connection_status)
        self.api_service.data_updated.connect(self.on_data_updated)
        self.api_service.operation_started.connect(self.on_operation_started)
        self.api_service.operation_completed.connect(self.on_operation_completed)
    
    def start_auto_refresh(self):
        """Start auto-refresh timer."""
        # Refresh every 2 minutes
        self.refresh_timer.start(120000)
    
    def initial_data_load(self):
        """Load initial data with connection retry logic."""
        # Test connection first if needed
        if not self.api_service.is_connected:
            self.api_service.test_connection_async()
        
        # Load data regardless of connection status - let the API service handle it
        self.refresh_data()
        
        # If still not connected, try again in 2 seconds
        if not self.api_service.is_connected:
            retry_timer = QTimer()
            retry_timer.setSingleShot(True)
            retry_timer.timeout.connect(self.refresh_data)
            retry_timer.start(2000)
    
    def refresh_data(self):
        """Refresh dashboard data."""
        # Always try to load data - the API service will handle connection errors gracefully
        self.stats_loading.setVisible(True)
        
        try:
            self.api_service.get_statistics_async()
        except Exception as e:
            logger.warning(f"Failed to load statistics: {e}")
            # If loading fails, show disconnected state after a brief delay
            disconnect_timer = QTimer()
            disconnect_timer.setSingleShot(True)
            disconnect_timer.timeout.connect(self.show_disconnected_state)
            disconnect_timer.start(1000)
    
    def refresh_activity(self):
        """Refresh recent activity."""
        # This would typically load recent activity from the API
        # For now, we'll show some placeholder data
        self.activity_list.clear()
        
        sample_activities = [
            "👤 John Doe added to Engineering department",
            "🏢 New department 'Research' created",
            "💼 Software Engineer position posted",
            "📝 Employment record updated for Jane Smith",
            "👥 5 new people imported from CSV",
            "📊 Monthly report generated",
        ]
        
        for activity in sample_activities:
            item = QListWidgetItem(activity)
            self.activity_list.addItem(item)
    
    def handle_quick_action(self, action: str):
        """Handle quick action button clicks."""
        if action == "reports":
            # For now, just show a message
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(
                self, 
                "Reports", 
                "Report generation feature will be implemented soon."
            )
        else:
            self.navigation_requested.emit(action)
    
    def update_connection_status(self, connected: bool):
        """Update connection status display."""
        if connected:
            self.connection_status_label.setText("🟢 Connected")
            self.server_info_label.setText(f"Server: {self.api_service.base_url}")
        else:
            self.connection_status_label.setText("🔴 Disconnected")
            self.server_info_label.setText("Server: Not connected")
            self.show_disconnected_state()
    
    def show_disconnected_state(self):
        """Show disconnected state."""
        self.stats_loading.setVisible(False)
        
        # Reset all cards to show disconnected state
        cards = [
            self.people_card, self.departments_card, self.positions_card,
            self.active_employment_card, self.recent_hires_card,
            self.pending_reviews_card, self.upcoming_birthdays_card,
            self.system_alerts_card
        ]
        
        for card in cards:
            card.set_value("—")
    
    def on_data_updated(self, data_type: str, data: Dict[str, Any]):
        """Handle data updates from API service."""
        if data_type == "statistics":
            self.update_statistics(data)
    
    def on_operation_started(self, operation: str):
        """Handle operation started."""
        if "statistics" in operation.lower():
            self.stats_loading.setVisible(True)
    
    def on_operation_completed(self, operation: str, success: bool, message: str):
        """Handle operation completed."""
        self.stats_loading.setVisible(False)
        
        if success and "statistics" in operation.lower():
            from datetime import datetime
            self.last_update_label.setText(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    def update_statistics(self, stats: Dict[str, Any]):
        """Update statistics cards with new data."""
        self.stats_data = stats
        
        try:
            # Update basic counts
            self.people_card.set_value(str(stats.get('total_people', 0)))
            self.departments_card.set_value(str(stats.get('total_departments', 0)))
            self.positions_card.set_value(str(stats.get('total_positions', 0)))
            self.active_employment_card.set_value(str(stats.get('active_employment', 0)))
            
            # Update secondary stats
            self.recent_hires_card.set_value(str(stats.get('recent_hires', 0)))
            self.pending_reviews_card.set_value(str(stats.get('pending_reviews', 0)))
            self.upcoming_birthdays_card.set_value(str(stats.get('upcoming_birthdays', 0)))
            self.system_alerts_card.set_value(str(stats.get('system_alerts', 0)))
            
            self.stats_loading.setVisible(False)
            
        except Exception as e:
            logger.error(f"Error updating statistics: {e}")
            self.stats_loading.setVisible(False)
    
    def refresh(self):
        """Refresh the dashboard view."""
        self.refresh_data()
        self.refresh_activity()
    
    def showEvent(self, event):
        """Handle show event."""
        super().showEvent(event)
        # Refresh data when view becomes visible, but only if we don't have any data yet
        # or if we're showing disconnected state
        if (self.stats_data is None or 
            self.people_card.value_label.text() in ["0", "—"]):
            self.refresh_data()
    
    def hideEvent(self, event):
        """Handle hide event."""
        super().hideEvent(event)
        # Stop loading indicators when view is hidden
        self.stats_loading.setVisible(False)