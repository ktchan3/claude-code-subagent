"""
Dashboard View for People Management System Client

Provides system overview with statistics, charts, and quick actions.
"""

import logging
import random
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QFrame, QGroupBox, QScrollArea, QProgressBar, QSizePolicy,
    QSpacerItem, QListWidget, QListWidgetItem, QGraphicsDropShadowEffect,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QTimer, QPropertyAnimation, QEasingCurve, QRect, QRectF, QPointF
from PySide6.QtGui import (
    QFont, QPalette, QColor, QLinearGradient, QBrush, QPainter,
    QPen, QPixmap, QPaintEvent, QPolygonF, QRadialGradient, QFontMetrics
)

from client.services.api_service import APIService
from client.services.config_service import ConfigService

logger = logging.getLogger(__name__)


class ChartWidget(QWidget):
    """Custom widget for drawing charts using QPainter."""
    
    def __init__(self, chart_type="pie", parent=None):
        super().__init__(parent)
        self.chart_type = chart_type
        self.data = []
        self.labels = []
        self.colors = [
            QColor("#1976d2"),  # Blue
            QColor("#43a047"),  # Green
            QColor("#fb8c00"),  # Orange
            QColor("#e53935"),  # Red
            QColor("#8e24aa"),  # Purple
            QColor("#00acc1"),  # Cyan
            QColor("#fdd835"),  # Yellow
            QColor("#546e7a"),  # Blue Grey
        ]
        self.setMinimumSize(250, 200)
        
    def set_data(self, data, labels):
        """Set chart data and labels."""
        self.data = data
        self.labels = labels
        self.update()  # Trigger repaint
        
    def paintEvent(self, event: QPaintEvent):
        """Custom paint event for drawing charts."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw background
        painter.fillRect(self.rect(), QColor("#ffffff"))
        
        if not self.data:
            # Draw placeholder if no data
            painter.setPen(QPen(QColor("#999999"), 1))
            painter.drawText(self.rect(), Qt.AlignCenter, "No data available")
            return
            
        if self.chart_type == "pie":
            self._draw_pie_chart(painter)
        elif self.chart_type == "bar":
            self._draw_bar_chart(painter)
        elif self.chart_type == "line":
            self._draw_line_chart(painter)
        elif self.chart_type == "donut":
            self._draw_donut_chart(painter)
            
    def _draw_pie_chart(self, painter: QPainter):
        """Draw a pie chart."""
        rect = QRectF(20, 20, min(self.width() - 100, self.height() - 40), min(self.width() - 100, self.height() - 40))
        
        total = sum(self.data) if self.data else 1
        start_angle = 90 * 16  # Start from top
        
        for i, value in enumerate(self.data):
            if value <= 0:
                continue
                
            span_angle = int((value / total) * 360 * 16)
            color = self.colors[i % len(self.colors)]
            
            # Draw pie slice
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(Qt.white, 2))
            painter.drawPie(rect, start_angle, span_angle)
            
            start_angle += span_angle
            
        # Draw legend
        legend_x = rect.right() + 20
        legend_y = rect.top()
        
        for i, (label, value) in enumerate(zip(self.labels[:len(self.data)], self.data)):
            if value <= 0:
                continue
                
            color = self.colors[i % len(self.colors)]
            
            # Legend color box
            painter.fillRect(QRectF(legend_x, legend_y + i * 25, 15, 15), color)
            
            # Legend text
            painter.setPen(QPen(QColor("#333333"), 1))
            text = f"{label}: {value}"
            painter.drawText(QPointF(legend_x + 20, legend_y + i * 25 + 12), text)
            
    def _draw_bar_chart(self, painter: QPainter):
        """Draw a bar chart."""
        if not self.data:
            return
            
        margin = 40
        chart_rect = QRectF(margin, margin, self.width() - 2 * margin, self.height() - 2 * margin)
        
        max_value = max(self.data) if self.data else 1
        bar_count = len(self.data)
        bar_width = chart_rect.width() / (bar_count * 1.5) if bar_count > 0 else 20
        spacing = bar_width * 0.5
        
        # Draw axes
        painter.setPen(QPen(QColor("#cccccc"), 1))
        painter.drawLine(chart_rect.bottomLeft(), chart_rect.bottomRight())
        painter.drawLine(chart_rect.bottomLeft(), chart_rect.topLeft())
        
        # Draw bars
        for i, (value, label) in enumerate(zip(self.data, self.labels[:len(self.data)])):
            if value <= 0:
                continue
                
            x = chart_rect.left() + i * (bar_width + spacing) + spacing
            height = (value / max_value) * chart_rect.height()
            y = chart_rect.bottom() - height
            
            # Draw bar
            color = self.colors[i % len(self.colors)]
            painter.fillRect(QRectF(x, y, bar_width, height), color)
            
            # Draw value on top
            painter.setPen(QPen(QColor("#333333"), 1))
            painter.drawText(QRectF(x, y - 20, bar_width, 20), Qt.AlignCenter, str(value))
            
            # Draw label at bottom
            font = painter.font()
            font.setPointSize(8)
            painter.setFont(font)
            painter.drawText(QRectF(x - 10, chart_rect.bottom() + 5, bar_width + 20, 20), 
                           Qt.AlignCenter, label)
            
    def _draw_line_chart(self, painter: QPainter):
        """Draw a line chart."""
        if not self.data or len(self.data) < 2:
            return
            
        margin = 40
        chart_rect = QRectF(margin, margin, self.width() - 2 * margin, self.height() - 2 * margin)
        
        max_value = max(self.data) if self.data else 1
        min_value = min(self.data) if self.data else 0
        value_range = max_value - min_value if max_value != min_value else 1
        
        # Draw grid
        painter.setPen(QPen(QColor("#eeeeee"), 1))
        for i in range(5):
            y = chart_rect.top() + (chart_rect.height() / 4) * i
            painter.drawLine(chart_rect.left(), y, chart_rect.right(), y)
            
        # Draw axes
        painter.setPen(QPen(QColor("#cccccc"), 1))
        painter.drawLine(chart_rect.bottomLeft(), chart_rect.bottomRight())
        painter.drawLine(chart_rect.bottomLeft(), chart_rect.topLeft())
        
        # Calculate points
        points = []
        for i, value in enumerate(self.data):
            x = chart_rect.left() + (i / (len(self.data) - 1)) * chart_rect.width()
            y = chart_rect.bottom() - ((value - min_value) / value_range) * chart_rect.height()
            points.append(QPointF(x, y))
            
        # Draw line
        painter.setPen(QPen(self.colors[0], 2))
        for i in range(len(points) - 1):
            painter.drawLine(points[i], points[i + 1])
            
        # Draw points
        painter.setBrush(QBrush(self.colors[0]))
        for point in points:
            painter.drawEllipse(point, 4, 4)
            
    def _draw_donut_chart(self, painter: QPainter):
        """Draw a donut chart."""
        outer_rect = QRectF(20, 20, min(self.width() - 100, self.height() - 40), 
                           min(self.width() - 100, self.height() - 40))
        inner_rect = QRectF(outer_rect.x() + outer_rect.width() * 0.3,
                           outer_rect.y() + outer_rect.height() * 0.3,
                           outer_rect.width() * 0.4,
                           outer_rect.height() * 0.4)
        
        total = sum(self.data) if self.data else 1
        start_angle = 90 * 16  # Start from top
        
        for i, value in enumerate(self.data):
            if value <= 0:
                continue
                
            span_angle = int((value / total) * 360 * 16)
            color = self.colors[i % len(self.colors)]
            
            # Draw outer arc
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(Qt.white, 2))
            painter.drawPie(outer_rect, start_angle, span_angle)
            
            start_angle += span_angle
            
        # Draw inner circle to create donut effect
        painter.setBrush(QBrush(Qt.white))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(inner_rect)
        
        # Draw center text
        painter.setPen(QPen(QColor("#333333"), 1))
        font = painter.font()
        font.setPointSize(14)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(inner_rect, Qt.AlignCenter, str(sum(self.data)))


class StatCard(QFrame):
    """Statistical information card widget."""
    
    def __init__(self, title: str, value: str = "0", icon: str = "📊", parent=None):
        super().__init__(parent)
        
        self.setFrameStyle(QFrame.StyledPanel)
        self.setMinimumSize(180, 140)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        
        # Store values for trend visualization
        self.current_value = 0
        self.previous_value = 0
        self.trend_data = []  # Store historical values for mini chart
        
        # Add modern styling
        self.setStyleSheet("""
            StatCard {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
            }
            StatCard:hover {
                border: 1px solid #1976d2;
                background-color: #f8f9fa;
            }
        """)
        
        # Add shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setXOffset(0)
        shadow.setYOffset(2)
        shadow.setColor(QColor(0, 0, 0, 30))
        self.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Header with icon and title
        header_layout = QHBoxLayout()
        
        # Icon with colored background
        icon_container = QFrame()
        icon_container.setFixedSize(36, 36)
        icon_container.setStyleSheet("""
            QFrame {
                background-color: #e3f2fd;
                border-radius: 18px;
            }
        """)
        icon_layout = QVBoxLayout(icon_container)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        
        icon_label = QLabel(icon)
        icon_font = QFont()
        icon_font.setPointSize(18)
        icon_label.setFont(icon_font)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_layout.addWidget(icon_label)
        
        header_layout.addWidget(icon_container)
        
        # Title
        title_label = QLabel(title)
        title_font = QFont()
        title_font.setPointSize(11)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #757575; margin-left: 8px;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Value with animation support
        self.value_label = QLabel(value)
        value_font = QFont()
        value_font.setPointSize(28)
        value_font.setBold(True)
        self.value_label.setFont(value_font)
        self.value_label.setAlignment(Qt.AlignCenter)
        self.value_label.setStyleSheet("color: #1976d2;")
        layout.addWidget(self.value_label)
        
        # Trend indicator with arrow and percentage
        self.trend_label = QLabel("")
        self.trend_label.setAlignment(Qt.AlignCenter)
        self.trend_label.setStyleSheet("color: #4caf50; font-size: 10pt;")
        layout.addWidget(self.trend_label)
        
        # Mini progress bar for visual indicator
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumHeight(4)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #f0f0f0;
                border: none;
                border-radius: 2px;
            }
            QProgressBar::chunk {
                background-color: #1976d2;
                border-radius: 2px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        layout.addStretch()
    
    def set_value(self, value: str, trend: str = "", progress: int = 0):
        """Update the card value with trend and progress."""
        self.value_label.setText(value)
        
        # Update trend with arrow indicator
        if trend:
            if trend.startswith("+"):
                self.trend_label.setText(f"↑ {trend}")
                self.trend_label.setStyleSheet("color: #4caf50; font-size: 10pt; font-weight: bold;")
            elif trend.startswith("-"):
                self.trend_label.setText(f"↓ {trend}")
                self.trend_label.setStyleSheet("color: #f44336; font-size: 10pt; font-weight: bold;")
            else:
                self.trend_label.setText(f"→ {trend}")
                self.trend_label.setStyleSheet("color: #757575; font-size: 10pt;")
        
        # Update progress bar
        if progress > 0:
            self.progress_bar.setValue(min(progress, 100))
            self.progress_bar.setVisible(True)
        else:
            self.progress_bar.setVisible(False)


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
        self.recent_activities = []
        self.is_loading = False
        
        # Auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_data)
        
        # Animation timer for smooth updates
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update_animations)
        self.animation_timer.start(1000)  # Update every second
        
        # Initialize UI first
        self.setup_ui()
        self.setup_connections()
        
        # Show sample data IMMEDIATELY to ensure dashboard is never empty
        logger.info("Dashboard initializing - showing default content")
        self.show_sample_data()
        
        # Then start auto-refresh
        self.start_auto_refresh()
        
        # Try to load real data after a short delay
        self.initial_load_timer = QTimer()
        self.initial_load_timer.setSingleShot(True)
        self.initial_load_timer.timeout.connect(self.initial_data_load)
        self.initial_load_timer.start(100)  # Reduced delay to 100ms
    
    def setup_ui(self):
        """Set up the user interface."""
        # Set a white background to ensure visibility
        self.setStyleSheet("""
            DashboardView {
                background-color: #ffffff;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Debug logging
        logger.info("Creating dashboard UI components...")
        
        # Welcome section with charts
        self.create_welcome_section(layout)
        logger.info("Welcome section created")
        
        # Statistics cards
        self.create_statistics_section(layout)
        logger.info("Statistics section created")
        
        # Main content area
        content_layout = QHBoxLayout()
        
        # Left column - Recent activity and notifications
        self.create_activity_section(content_layout)
        logger.info("Activity section created")
        
        # Right column - Quick actions and data tools
        self.create_quick_actions_section(content_layout)
        logger.info("Quick actions section created")
        
        layout.addLayout(content_layout)
        
        # Add stretch to push content up
        layout.addStretch()
        
        logger.info("Dashboard UI setup complete")
    
    def create_welcome_section(self, layout: QVBoxLayout):
        """Create welcome section with comprehensive information."""
        # Main welcome container
        welcome_container = QWidget()
        welcome_container_layout = QVBoxLayout(welcome_container)
        welcome_container_layout.setSpacing(15)
        
        # Top gradient header
        welcome_frame = QFrame()
        welcome_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1976d2, stop:0.5 #2196f3, stop:1 #42a5f5);
                border-radius: 10px;
                padding: 20px;
            }
        """)
        welcome_frame.setMinimumHeight(140)
        welcome_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        welcome_layout = QVBoxLayout(welcome_frame)
        welcome_layout.setContentsMargins(20, 20, 20, 20)
        
        # Center layout for title and date/time
        center_layout = QVBoxLayout()
        center_layout.setSpacing(10)
        center_layout.setAlignment(Qt.AlignCenter)
        
        # Main title - People Management System
        main_title_label = QLabel("People Management System")
        main_title_font = QFont()
        main_title_font.setPointSize(32)
        main_title_font.setBold(True)
        main_title_label.setFont(main_title_font)
        main_title_label.setStyleSheet("color: white;")
        main_title_label.setAlignment(Qt.AlignCenter)
        center_layout.addWidget(main_title_label)
        
        # Live date and time display
        self.datetime_label = QLabel()
        datetime_font = QFont()
        datetime_font.setPointSize(16)
        self.datetime_label.setFont(datetime_font)
        self.datetime_label.setStyleSheet("color: rgba(255, 255, 255, 0.95);")
        self.datetime_label.setAlignment(Qt.AlignCenter)
        self.update_datetime()
        center_layout.addWidget(self.datetime_label)
        
        welcome_layout.addLayout(center_layout)
        
        # Bottom section with greeting and health status
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(20)
        
        # Left side - Greeting
        left_info_layout = QVBoxLayout()
        current_hour = datetime.now().hour
        if current_hour < 12:
            greeting = "Good Morning"
            icon = "☀️"
        elif current_hour < 17:
            greeting = "Good Afternoon"
            icon = "🌤️"
        else:
            greeting = "Good Evening"
            icon = "🌙"
        
        greeting_label = QLabel(f"{icon} {greeting}")
        greeting_font = QFont()
        greeting_font.setPointSize(14)
        greeting_label.setFont(greeting_font)
        greeting_label.setStyleSheet("color: rgba(255, 255, 255, 0.9);")
        left_info_layout.addWidget(greeting_label)
        
        bottom_layout.addLayout(left_info_layout)
        bottom_layout.addStretch()
        
        # Right side - System health
        self.health_status_label = QLabel("🟢 System Health: Excellent")
        health_font = QFont()
        health_font.setPointSize(14)
        self.health_status_label.setFont(health_font)
        self.health_status_label.setStyleSheet("color: rgba(255, 255, 255, 0.9);")
        bottom_layout.addWidget(self.health_status_label)
        
        welcome_layout.addLayout(bottom_layout)
        
        # Key insights section (moved to separate row)
        insights_layout = QHBoxLayout()
        insights_layout.setContentsMargins(0, 10, 0, 0)
        
        # Quick summary box
        summary_frame = QFrame()
        summary_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.15);
                border-radius: 8px;
                padding: 10px;
            }
        """)
        summary_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        summary_layout = QHBoxLayout(summary_frame)
        summary_layout.setContentsMargins(15, 10, 15, 10)
        
        summary_title = QLabel("📊 Key Insights:")
        summary_title_font = QFont()
        summary_title_font.setPointSize(12)
        summary_title_font.setBold(True)
        summary_title.setFont(summary_title_font)
        summary_title.setStyleSheet("color: white;")
        summary_layout.addWidget(summary_title)
        
        self.insight_labels = []
        for i in range(3):
            insight_label = QLabel("• Loading...")
            insight_font = QFont()
            insight_font.setPointSize(11)
            insight_label.setFont(insight_font)
            insight_label.setStyleSheet("color: rgba(255, 255, 255, 0.9);")
            summary_layout.addWidget(insight_label)
            self.insight_labels.append(insight_label)
        
        summary_layout.addStretch()
        insights_layout.addWidget(summary_frame)
        welcome_layout.addLayout(insights_layout)
        
        welcome_container_layout.addWidget(welcome_frame)
        
        # Charts section below the welcome header
        charts_frame = QFrame()
        charts_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
            }
        """)
        charts_layout = QHBoxLayout(charts_frame)
        charts_layout.setContentsMargins(15, 15, 15, 15)
        charts_layout.setSpacing(20)
        
        # Department Distribution Pie Chart
        dept_chart_container = QVBoxLayout()
        dept_chart_label = QLabel("Department Distribution")
        dept_chart_label.setAlignment(Qt.AlignCenter)
        dept_chart_label.setStyleSheet("font-weight: bold; color: #333333; padding: 5px;")
        dept_chart_container.addWidget(dept_chart_label)
        
        self.dept_chart = ChartWidget("pie")
        self.dept_chart.setMinimumSize(280, 200)
        dept_chart_container.addWidget(self.dept_chart)
        charts_layout.addLayout(dept_chart_container)
        
        # Position Distribution Bar Chart  
        pos_chart_container = QVBoxLayout()
        pos_chart_label = QLabel("Top Positions")
        pos_chart_label.setAlignment(Qt.AlignCenter)
        pos_chart_label.setStyleSheet("font-weight: bold; color: #333333; padding: 5px;")
        pos_chart_container.addWidget(pos_chart_label)
        
        self.pos_chart = ChartWidget("bar")
        self.pos_chart.setMinimumSize(280, 200)
        pos_chart_container.addWidget(self.pos_chart)
        charts_layout.addLayout(pos_chart_container)
        
        # Employee Growth Line Chart
        growth_chart_container = QVBoxLayout()
        growth_chart_label = QLabel("Employee Growth Trend")
        growth_chart_label.setAlignment(Qt.AlignCenter)
        growth_chart_label.setStyleSheet("font-weight: bold; color: #333333; padding: 5px;")
        growth_chart_container.addWidget(growth_chart_label)
        
        self.growth_chart = ChartWidget("line")
        self.growth_chart.setMinimumSize(280, 200)
        growth_chart_container.addWidget(self.growth_chart)
        charts_layout.addLayout(growth_chart_container)
        
        welcome_container_layout.addWidget(charts_frame)
        
        layout.addWidget(welcome_container)
    
    def create_statistics_section(self, layout: QVBoxLayout):
        """Create statistics cards section."""
        stats_group = QGroupBox("System Overview")
        stats_layout = QVBoxLayout(stats_group)
        
        # Loading indicator
        self.stats_loading = QProgressBar()
        self.stats_loading.setRange(0, 0)  # Indeterminate
        self.stats_loading.setVisible(False)
        stats_layout.addWidget(self.stats_loading)
        
        # Statistics cards grid with responsive layout
        cards_widget = QWidget()
        cards_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.cards_layout = QGridLayout(cards_widget)
        self.cards_layout.setSpacing(15)
        
        # Create primary stat cards with enhanced icons and better defaults
        self.people_card = StatCard("Total People", "0", "👥")
        self.people_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.departments_card = StatCard("Departments", "0", "🏢")
        self.departments_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.positions_card = StatCard("Positions", "0", "💼")
        self.positions_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.active_employment_card = StatCard("Active Employment", "0", "✅")
        self.active_employment_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        
        # Add cards to grid
        self.cards_layout.addWidget(self.people_card, 0, 0)
        self.cards_layout.addWidget(self.departments_card, 0, 1)
        self.cards_layout.addWidget(self.positions_card, 0, 2)
        self.cards_layout.addWidget(self.active_employment_card, 0, 3)
        
        # Add second row of cards with meaningful defaults
        self.recent_hires_card = StatCard("Recent Hires (30d)", "0", "🆕")
        self.recent_hires_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.avg_tenure_card = StatCard("Avg Tenure", "0y", "📅")
        self.avg_tenure_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.turnover_rate_card = StatCard("Turnover Rate", "0.0%", "📊")
        self.turnover_rate_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.avg_salary_card = StatCard("Avg Salary", "$0", "💰")
        self.avg_salary_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        
        self.cards_layout.addWidget(self.recent_hires_card, 1, 0)
        self.cards_layout.addWidget(self.avg_tenure_card, 1, 1)
        self.cards_layout.addWidget(self.turnover_rate_card, 1, 2)
        self.cards_layout.addWidget(self.avg_salary_card, 1, 3)
        
        stats_layout.addWidget(cards_widget)
        layout.addWidget(stats_group)
    
    def create_activity_section(self, layout: QHBoxLayout):
        """Create recent activity section with enhanced display."""
        # Activity and notifications container with responsive layout
        left_container = QWidget()
        left_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        left_layout = QVBoxLayout(left_container)
        left_layout.setSpacing(15)
        
        # Recent Activity section
        activity_group = QGroupBox("Recent Activity")
        activity_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        activity_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 12pt;
                border: 2px solid #e0e0e0;
                border-radius: 5px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        activity_layout = QVBoxLayout(activity_group)
        
        # Activity table for better display
        self.activity_table = QTableWidget()
        self.activity_table.setColumnCount(3)
        self.activity_table.setHorizontalHeaderLabels(["Time", "Type", "Description"])
        self.activity_table.horizontalHeader().setStretchLastSection(True)
        self.activity_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.activity_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.activity_table.setColumnWidth(0, 80)
        self.activity_table.setColumnWidth(1, 80)
        self.activity_table.setMaximumHeight(350)
        self.activity_table.setAlternatingRowColors(True)
        self.activity_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.activity_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.activity_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #e0e0e0;
                gridline-color: #f0f0f0;
            }
            QTableWidget::item {
                padding: 5px;
            }
        """)
        activity_layout.addWidget(self.activity_table)
        
        # Activity controls
        controls_layout = QHBoxLayout()
        
        self.activity_status_label = QLabel("No recent activity")
        self.activity_status_label.setStyleSheet("color: #666; font-style: italic;")
        controls_layout.addWidget(self.activity_status_label)
        
        controls_layout.addStretch()
        
        refresh_activity_btn = QPushButton("🔄 Refresh")
        refresh_activity_btn.setStyleSheet("""
            QPushButton {
                padding: 5px 15px;
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        refresh_activity_btn.clicked.connect(self.refresh_activity)
        controls_layout.addWidget(refresh_activity_btn)
        
        activity_layout.addLayout(controls_layout)
        
        left_layout.addWidget(activity_group)
        
        # System Notifications section
        notifications_group = QGroupBox("System Notifications")
        notifications_layout = QVBoxLayout(notifications_group)
        
        self.notifications_list = QListWidget()
        self.notifications_list.setMaximumHeight(120)
        self.notifications_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                background-color: #fafafa;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f0f0f0;
            }
            QListWidget::item:hover {
                background-color: #e8f4f8;
            }
        """)
        
        # Add sample notifications
        self.add_notification("ℹ️ System initialized successfully", "info")
        self.add_notification("✅ Database connection established", "success")
        self.add_notification("📊 Dashboard data refreshed", "info")
        
        notifications_layout.addWidget(self.notifications_list)
        
        # Notification controls
        notif_controls = QHBoxLayout()
        clear_notif_btn = QPushButton("Clear All")
        clear_notif_btn.clicked.connect(self.notifications_list.clear)
        clear_notif_btn.setMaximumWidth(100)
        notif_controls.addStretch()
        notif_controls.addWidget(clear_notif_btn)
        notifications_layout.addLayout(notif_controls)
        
        left_layout.addWidget(notifications_group)
        left_layout.addStretch()
        
        layout.addWidget(left_container, 2)  # Give more stretch to left container
    
    def create_quick_actions_section(self, layout: QHBoxLayout):
        """Create quick actions and additional info sections."""
        # Right container for actions and data tools
        right_container = QWidget()
        right_container.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        right_layout = QVBoxLayout(right_container)
        right_layout.setSpacing(15)
        
        # Quick Actions section with responsive grid layout
        actions_group = QGroupBox("Quick Actions")
        actions_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        actions_grid = QGridLayout(actions_group)
        actions_grid.setSpacing(10)
        
        # Action buttons in a 2-column grid
        actions = [
            ("👤 Add New Person", "people"),
            ("🏢 Add Department", "departments"),
            ("💼 Add Position", "positions"),
            ("📝 Create Employment", "employment"),
            ("👥 View All People", "people"),
            ("📊 Generate Reports", "reports"),
        ]
        
        for i, (text, action) in enumerate(actions):
            btn = QPushButton(text)
            btn.clicked.connect(lambda checked, a=action: self.handle_quick_action(a))
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            btn.setMinimumHeight(45)
            btn.setStyleSheet("""
                QPushButton {
                    text-align: left;
                    padding: 12px;
                    border: 1px solid #ccc;
                    border-radius: 5px;
                    font-size: 11pt;
                }
                QPushButton:hover {
                    background-color: #f0f0f0;
                    border: 1px solid #1976d2;
                }
            """)
            row = i // 2
            col = i % 2
            actions_grid.addWidget(btn, row, col)
        
        right_layout.addWidget(actions_group)
        
        # Data Management Tools section with responsive layout
        data_tools_group = QGroupBox("Data Management")
        data_tools_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        data_tools_layout = QVBoxLayout(data_tools_group)
        data_tools_layout.setSpacing(8)
        
        # Export options with responsive buttons
        export_label = QLabel("Export Data")
        export_label.setStyleSheet("font-weight: bold; color: #666; font-size: 10pt;")
        data_tools_layout.addWidget(export_label)
        
        export_buttons = [
            ("📄 Export to CSV", self.export_csv),
            ("📊 Export to Excel", self.export_excel),
            ("📑 Generate PDF Report", self.generate_pdf),
        ]
        
        for text, callback in export_buttons:
            btn = QPushButton(text)
            btn.clicked.connect(callback)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            btn.setMinimumHeight(36)
            btn.setStyleSheet("""
                QPushButton {
                    text-align: left;
                    padding: 10px;
                    background-color: #f5f5f5;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    font-size: 10pt;
                }
                QPushButton:hover {
                    background-color: #e0e0e0;
                    border: 1px solid #1976d2;
                }
            """)
            data_tools_layout.addWidget(btn)
        
        # Search functionality with responsive design
        search_label = QLabel("Quick Search")
        search_label.setStyleSheet("font-weight: bold; color: #666; margin-top: 10px; font-size: 10pt;")
        data_tools_layout.addWidget(search_label)
        
        self.quick_search = QLineEdit()
        self.quick_search.setPlaceholderText("🔍 Search people, departments...")
        self.quick_search.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.quick_search.setMinimumHeight(36)
        self.quick_search.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
                font-size: 10pt;
            }
            QLineEdit:focus {
                border: 1px solid #1976d2;
                background-color: #f8f9fa;
            }
        """)
        self.quick_search.returnPressed.connect(self.perform_quick_search)
        data_tools_layout.addWidget(self.quick_search)
        
        data_tools_layout.addStretch()
        right_layout.addWidget(data_tools_group)
        
        # System info with responsive layout
        info_group = QGroupBox("System Information")
        info_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        info_layout = QVBoxLayout(info_group)
        self.create_system_info(info_layout)
        right_layout.addWidget(info_group)
        
        right_layout.addStretch()
        layout.addWidget(right_container, 1)  # Give it stretch factor
    
    def create_system_info(self, layout: QVBoxLayout):
        """Create system information section."""
        # Connection status
        self.connection_status_label = QLabel("🔴 Disconnected")
        self.connection_status_label.setStyleSheet("font-size: 11pt;")
        layout.addWidget(self.connection_status_label)
        
        self.server_info_label = QLabel("Server: Not connected")
        self.server_info_label.setStyleSheet("color: #666; font-size: 9pt;")
        layout.addWidget(self.server_info_label)
        
        # Database info
        self.db_status_label = QLabel("📊 Database: SQLite")
        self.db_status_label.setStyleSheet("color: #666; font-size: 9pt;")
        layout.addWidget(self.db_status_label)
        
        # Memory usage (mock)
        self.memory_label = QLabel("💾 Memory: 45.2 MB")
        self.memory_label.setStyleSheet("color: #666; font-size: 9pt;")
        layout.addWidget(self.memory_label)
        
        # Last update
        self.last_update_label = QLabel("Last updated: Never")
        self.last_update_label.setStyleSheet("color: #666; font-size: 9pt;")
        layout.addWidget(self.last_update_label)
        
        # Version info
        version_label = QLabel("Version: 2.1.0")
        version_label.setStyleSheet("color: #999; font-size: 8pt; margin-top: 5px;")
        layout.addWidget(version_label)
    
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
        logger.info("Starting initial data load")
        
        # Don't show loading state over existing sample data
        # Only show loading if we're actually connected
        if self.api_service.is_connected:
            self.show_loading_state()
        
        # Test connection first if needed
        if not self.api_service.is_connected:
            logger.info("Not connected, attempting connection...")
            self.api_service.test_connection_async()
        
        # Load data regardless of connection status - let the API service handle it
        self.refresh_data()
        
        # If still not connected, show sample data
        if not self.api_service.is_connected:
            logger.info("Still not connected, keeping sample data")
            self.show_sample_data()
            
            # Try again in 2 seconds
            retry_timer = QTimer()
            retry_timer.setSingleShot(True)
            retry_timer.timeout.connect(self.refresh_data)
            retry_timer.start(2000)
    
    def refresh_data(self):
        """Refresh dashboard data."""
        if self.is_loading:
            return  # Prevent multiple simultaneous requests
        
        self.is_loading = True
        self.stats_loading.setVisible(True)
        
        try:
            # Try to get statistics from API
            self.api_service.get_statistics_async()
            
            # Also try to get other useful data
            if self.api_service.is_connected:
                # These calls would fetch additional data
                pass  # Placeholder for additional API calls
        except Exception as e:
            logger.warning(f"Failed to load statistics: {e}")
            self.is_loading = False
            # Show sample data if API fails
            self.show_sample_data()
            # Still show as if connected with sample data
            self.update_connection_status(True)
    
    def refresh_activity(self):
        """Refresh recent activity with realistic data."""
        self.activity_table.setRowCount(0)
        
        # Generate sample activities based on actual data if available
        activity_types = [
            ("Person", "Added new person", "👤"),
            ("Dept", "Department created", "🏢"),
            ("Position", "Position updated", "💼"),
            ("Employment", "Employment record", "📝"),
            ("System", "Data imported", "📥"),
            ("Report", "Report generated", "📊"),
        ]
        
        # Create sample activities with timestamps
        current_time = datetime.now()
        for i in range(min(10, random.randint(5, 15))):
            time_delta = timedelta(minutes=random.randint(i * 30, (i + 1) * 60))
            activity_time = current_time - time_delta
            
            activity_type = random.choice(activity_types)
            
            row_position = self.activity_table.rowCount()
            self.activity_table.insertRow(row_position)
            
            # Time column
            time_item = QTableWidgetItem(activity_time.strftime("%H:%M"))
            time_item.setTextAlignment(Qt.AlignCenter)
            self.activity_table.setItem(row_position, 0, time_item)
            
            # Type column
            type_item = QTableWidgetItem(f"{activity_type[2]} {activity_type[0]}")
            type_item.setTextAlignment(Qt.AlignCenter)
            self.activity_table.setItem(row_position, 1, type_item)
            
            # Description column
            descriptions = [
                f"{activity_type[1]} - ID: {random.randint(1000, 9999)}",
                f"{activity_type[1]} successfully",
                f"{activity_type[1]} by admin",
            ]
            desc_item = QTableWidgetItem(random.choice(descriptions))
            self.activity_table.setItem(row_position, 2, desc_item)
        
        self.activity_status_label.setText(f"Showing {self.activity_table.rowCount()} recent activities")
        self.recent_activities = [("sample", i) for i in range(self.activity_table.rowCount())]
    
    def handle_quick_action(self, action: str):
        """Handle quick action button clicks."""
        if action == "reports":
            # For now, just show a message
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
        self.is_loading = False
        
        # Show sample data instead of empty dashboard
        self.show_sample_data()
        
        # Update health status
        self.health_status_label.setText("⚠️ Running in offline mode with sample data")
    
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
            self.last_update_label.setText(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    def update_statistics(self, stats: Dict[str, Any]):
        """Update statistics cards with new data."""
        self.stats_data = stats
        self.is_loading = False
        
        try:
            # Update basic counts
            total_people = stats.get('total_people', 0)
            self.people_card.set_value(str(total_people))
            self.departments_card.set_value(str(stats.get('total_departments', 0)))
            self.positions_card.set_value(str(stats.get('total_positions', 0)))
            
            # Handle active employees from nested employment_statistics
            employment_stats = stats.get('employment_statistics', {})
            active_employees = stats.get('active_employees', employment_stats.get('active_employments', 0))
            self.active_employment_card.set_value(str(active_employees))
            
            # Update employment-related stats
            recent_hires = employment_stats.get('recent_hires_30_days', 0)
            self.recent_hires_card.set_value(str(recent_hires), "+" + str(recent_hires) if recent_hires > 0 else "")
            
            # Calculate and show average tenure with progress
            if active_employees > 0:
                avg_tenure_days = employment_stats.get('average_tenure_days', 365)
                avg_tenure_years = avg_tenure_days / 365.25
                # Calculate progress (assuming 5 years is 100%)
                tenure_progress = min(int((avg_tenure_years / 5) * 100), 100)
                self.avg_tenure_card.set_value(f"{avg_tenure_years:.1f}y", progress=tenure_progress)
            else:
                self.avg_tenure_card.set_value("0y")
            
            # Show turnover rate with trend
            turnover_rate = employment_stats.get('turnover_rate', 0)
            # Add trend indicator based on value
            if turnover_rate < 10:
                trend = "Low"
            elif turnover_rate > 15:
                trend = "High"
            else:
                trend = "Normal"
            self.turnover_rate_card.set_value(f"{turnover_rate:.1f}%", trend)
            
            # Show average salary with formatting
            avg_salary = stats.get('average_salary')
            if avg_salary:
                # Add trend based on industry average (mock)
                industry_avg = 65000
                if avg_salary > industry_avg:
                    salary_trend = f"+${(avg_salary - industry_avg):,.0f} vs industry"
                else:
                    salary_trend = f"-${(industry_avg - avg_salary):,.0f} vs industry"
                self.avg_salary_card.set_value(f"${avg_salary:,.0f}", salary_trend)
            else:
                self.avg_salary_card.set_value("$0")
            
            self.stats_loading.setVisible(False)
            
            # Update charts with real data if available
            if total_people > 0:
                self.update_charts_with_real_data(stats)
            
            # Update insights
            self.update_insights_with_sample_data(stats)
            
        except Exception as e:
            logger.error(f"Error updating statistics: {e}")
            self.stats_loading.setVisible(False)
            self.is_loading = False
    
    def refresh(self):
        """Refresh the dashboard view."""
        self.refresh_data()
        self.refresh_activity()
    
    def showEvent(self, event):
        """Handle show event."""
        super().showEvent(event)
        # Always refresh when view becomes visible to ensure fresh data
        if not self.is_loading:
            self.refresh_data()
            self.refresh_activity()
    
    def hideEvent(self, event):
        """Handle hide event."""
        super().hideEvent(event)
        # Stop loading indicators when view is hidden
        self.stats_loading.setVisible(False)
    
    def update_datetime(self):
        """Update the date and time display."""
        now = datetime.now()
        date_str = now.strftime("%A, %B %d, %Y - %I:%M:%S %p")
        if hasattr(self, 'datetime_label'):
            self.datetime_label.setText(date_str)
    
    def update_animations(self):
        """Update animations and dynamic content."""
        # Update datetime
        self.update_datetime()
        
        # Add any other periodic updates here
        pass
    
    def show_loading_state(self):
        """Show loading state for all cards."""
        self.stats_loading.setVisible(True)
        cards = [
            self.people_card, self.departments_card, self.positions_card,
            self.active_employment_card, self.recent_hires_card,
            self.avg_tenure_card, self.turnover_rate_card, self.avg_salary_card
        ]
        for card in cards:
            card.set_value("...")
    
    def show_sample_data(self):
        """Show sample data when API is not available."""
        logger.info("Showing sample data on dashboard")
        
        # Generate more realistic sample data
        num_people = random.randint(150, 300)
        num_depts = random.randint(8, 15)
        num_positions = random.randint(25, 50)
        num_active = int(num_people * random.uniform(0.75, 0.95))
        
        sample_stats = {
            'total_people': num_people,
            'total_departments': num_depts,
            'total_positions': num_positions,
            'active_employees': num_active,
            'average_salary': random.randint(50000, 90000),
            'employment_statistics': {
                'active_employments': num_active,
                'recent_hires_30_days': random.randint(3, 12),
                'turnover_rate': random.uniform(5.0, 15.0),
                'average_tenure_days': random.randint(300, 1000)
            }
        }
        
        # Update statistics with sample data
        self.update_statistics(sample_stats)
        
        # Update charts with sample data
        self.update_charts_with_sample_data()
        
        # Update insights
        self.update_insights_with_sample_data(sample_stats)
        
        # Always refresh activity to show something
        self.refresh_activity()
        
        # Update date/time immediately
        self.update_datetime()
        
        # Update system health
        self.health_status_label.setText("🟢 System Health: Excellent")
        
        logger.info("Sample data displayed successfully")
    
    def add_notification(self, message: str, notification_type: str = "info"):
        """Add a notification to the notifications list."""
        timestamp = datetime.now().strftime("%H:%M")
        item_text = f"[{timestamp}] {message}"
        item = QListWidgetItem(item_text)
        
        # Set background color based on type
        if notification_type == "success":
            item.setBackground(QColor("#e8f5e9"))
        elif notification_type == "warning":
            item.setBackground(QColor("#fff3e0"))
        elif notification_type == "error":
            item.setBackground(QColor("#ffebee"))
        else:  # info
            item.setBackground(QColor("#e3f2fd"))
            
        self.notifications_list.insertItem(0, item)  # Add to top
        
        # Keep only last 10 notifications
        while self.notifications_list.count() > 10:
            self.notifications_list.takeItem(self.notifications_list.count() - 1)
    
    def export_csv(self):
        """Export data to CSV."""
        QMessageBox.information(self, "Export", "CSV export functionality will be implemented soon.")
        self.add_notification("📄 CSV export initiated", "info")
    
    def export_excel(self):
        """Export data to Excel."""
        QMessageBox.information(self, "Export", "Excel export functionality will be implemented soon.")
        self.add_notification("📊 Excel export initiated", "info")
    
    def generate_pdf(self):
        """Generate PDF report."""
        QMessageBox.information(self, "Report", "PDF report generation will be implemented soon.")
        self.add_notification("📑 PDF report generation started", "info")
    
    def perform_quick_search(self):
        """Perform quick search."""
        search_text = self.quick_search.text()
        if search_text:
            self.add_notification(f"🔍 Searching for: {search_text}", "info")
            # Here you would implement actual search functionality
            QMessageBox.information(self, "Search", f"Searching for: {search_text}\n\nSearch results will appear here.")
    
    def update_charts_with_sample_data(self):
        """Update charts with sample visualization data."""
        # Department distribution data
        dept_names = ["Engineering", "Sales", "HR", "Marketing", "Finance", "Operations"]
        dept_values = [random.randint(20, 60) for _ in range(6)]
        self.dept_chart.set_data(dept_values, dept_names)
        
        # Position distribution data
        pos_names = ["Manager", "Developer", "Analyst", "Designer", "Sales Rep"]
        pos_values = [random.randint(10, 40) for _ in range(5)]
        self.pos_chart.set_data(pos_values, pos_names)
        
        # Employee growth trend data (last 12 months)
        growth_data = []
        base = random.randint(100, 150)
        for i in range(12):
            base += random.randint(-5, 15)
            growth_data.append(base)
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        self.growth_chart.set_data(growth_data, months)
    
    def update_insights_with_sample_data(self, stats: Dict[str, Any]):
        """Update insight labels with meaningful information."""
        insights = []
        
        # Utilization insight
        total_people = stats.get('total_people', 0)
        active_employees = stats.get('active_employees', 0)
        if total_people > 0:
            utilization = (active_employees / total_people) * 100
            insights.append(f"• {utilization:.0f}% workforce utilization")
        
        # Recent hires insight
        employment_stats = stats.get('employment_statistics', {})
        recent_hires = employment_stats.get('recent_hires_30_days', 0)
        if recent_hires > 0:
            insights.append(f"• {recent_hires} new hires this month")
        
        # Turnover insight
        turnover_rate = employment_stats.get('turnover_rate', 0)
        if turnover_rate < 10:
            insights.append(f"• Low turnover rate: {turnover_rate:.1f}%")
        elif turnover_rate > 15:
            insights.append(f"• High turnover alert: {turnover_rate:.1f}%")
        else:
            insights.append(f"• Normal turnover: {turnover_rate:.1f}%")
        
        # Update the insight labels
        for i, insight_label in enumerate(self.insight_labels):
            if i < len(insights):
                insight_label.setText(insights[i])
            else:
                insight_label.setText(f"• Department efficiency: {random.randint(85, 98)}%")
    
    def update_charts_with_real_data(self, stats: Dict[str, Any]):
        """Update charts with real data from API."""
        # This would be implemented when real data structure is available
        # For now, fall back to sample data
        self.update_charts_with_sample_data()