"""
Positions Management View for People Management System Client

Provides interface for managing position records.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QPushButton,
    QMessageBox, QDialog, QDialogButtonBox, QLabel, QFrame,
    QToolButton, QMenu, QFormLayout, QLineEdit, QTextEdit,
    QComboBox, QGroupBox, QSpinBox, QDoubleSpinBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction

from client.services.api_service import APIService
from client.services.config_service import ConfigService
from client.ui.widgets.data_table import DataTable, ColumnConfig
from client.ui.widgets.search_widget import SearchWidget, SearchFilter

logger = logging.getLogger(__name__)


class PositionDialog(QDialog):
    """Dialog for adding/editing positions."""
    
    def __init__(self, position_data: Optional[Dict[str, Any]] = None, api_service: Optional[APIService] = None, parent=None):
        super().__init__(parent)
        
        self.position_data = position_data
        self.is_editing = bool(position_data)
        self.api_service = api_service
        
        title = "Edit Position" if self.is_editing else "Add New Position"
        self.setWindowTitle(title)
        self.setModal(True)
        self.resize(600, 500)
        
        self.setup_ui()
        self.load_departments()
        
        if position_data:
            self.set_form_data(position_data)
    
    def setup_ui(self):
        """Set up dialog UI."""
        layout = QVBoxLayout(self)
        
        # Position details
        details_group = QGroupBox("Position Details")
        details_layout = QFormLayout(details_group)
        details_layout.setVerticalSpacing(10)
        details_layout.setContentsMargins(5, 10, 5, 5)
        
        # Title (required)
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Enter position title")
        details_layout.addRow("Title *:", self.title_edit)
        
        # Description
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Enter position description")
        self.description_edit.setMaximumHeight(100)
        details_layout.addRow("Description:", self.description_edit)
        
        # Department
        self.department_combo = QComboBox()
        self.department_combo.setPlaceholderText("Select department")
        details_layout.addRow("Department *:", self.department_combo)
        
        # Requirements
        self.requirements_edit = QTextEdit()
        self.requirements_edit.setPlaceholderText("Enter position requirements")
        self.requirements_edit.setMaximumHeight(80)
        details_layout.addRow("Requirements:", self.requirements_edit)
        
        layout.addWidget(details_group)
        
        # Salary information
        salary_group = QGroupBox("Salary Information")
        salary_layout = QFormLayout(salary_group)
        salary_layout.setVerticalSpacing(10)
        salary_layout.setContentsMargins(5, 10, 5, 5)
        
        # Salary range
        salary_range_layout = QHBoxLayout()
        
        self.salary_min_spin = QDoubleSpinBox()
        self.salary_min_spin.setRange(0, 999999.99)
        self.salary_min_spin.setDecimals(2)
        self.salary_min_spin.setSuffix(" USD")
        salary_range_layout.addWidget(self.salary_min_spin)
        
        salary_range_layout.addWidget(QLabel(" to "))
        
        self.salary_max_spin = QDoubleSpinBox()
        self.salary_max_spin.setRange(0, 999999.99)
        self.salary_max_spin.setDecimals(2)
        self.salary_max_spin.setSuffix(" USD")
        salary_range_layout.addWidget(self.salary_max_spin)
        
        salary_layout.addRow("Salary Range:", salary_range_layout)
        
        layout.addWidget(salary_group)
        
        # Status
        status_group = QGroupBox("Status")
        status_layout = QFormLayout(status_group)
        status_layout.setVerticalSpacing(10)
        status_layout.setContentsMargins(5, 10, 5, 5)
        
        self.status_combo = QComboBox()
        self.status_combo.addItems(["Active", "Inactive", "Draft", "Filled"])
        status_layout.addRow("Status:", self.status_combo)
        
        layout.addWidget(status_group)
        
        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal
        )
        button_box.accepted.connect(self.accept_dialog)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # Validation
        self.ok_button = button_box.button(QDialogButtonBox.Ok)
        self.title_edit.textChanged.connect(self.validate_form)
        self.validate_form()
    
    def load_departments(self):
        """Load departments for the dropdown."""
        if self.api_service:
            # Load departments synchronously for simplicity
            try:
                result = self.api_service.list_departments(page=1, page_size=100)
                departments = result.get('items', [])
                
                self.department_combo.clear()
                self.department_combo.addItem("", None)  # Empty option
                
                for dept in departments:
                    self.department_combo.addItem(dept.get('name', ''), dept.get('id'))
                    
            except Exception as e:
                logger.error(f"Failed to load departments: {e}")
    
    def validate_form(self):
        """Validate form data."""
        is_valid = bool(self.title_edit.text().strip())
        self.ok_button.setEnabled(is_valid)
    
    def accept_dialog(self):
        """Handle dialog acceptance."""
        if self.title_edit.text().strip():
            self.accept()
        else:
            QMessageBox.warning(self, "Validation Error", "Please enter a position title.")
    
    def get_form_data(self) -> Dict[str, Any]:
        """Get form data."""
        return {
            'title': self.title_edit.text().strip(),
            'description': self.description_edit.toPlainText().strip() or None,
            'department_id': self.department_combo.currentData(),
            'requirements': self.requirements_edit.toPlainText().strip().split('\n') if self.requirements_edit.toPlainText().strip() else None,
            'salary_min': self.salary_min_spin.value() if self.salary_min_spin.value() > 0 else None,
            'salary_max': self.salary_max_spin.value() if self.salary_max_spin.value() > 0 else None,
            'status': self.status_combo.currentText()
        }
    
    def set_form_data(self, data: Dict[str, Any]):
        """Set form data."""
        self.title_edit.setText(data.get('title', ''))
        self.description_edit.setText(data.get('description', ''))
        
        # Handle department selection
        department_id = data.get('department_id')
        if department_id:
            for i in range(self.department_combo.count()):
                if self.department_combo.itemData(i) == department_id:
                    self.department_combo.setCurrentIndex(i)
                    break
        
        # Handle requirements
        requirements = data.get('requirements', [])
        if isinstance(requirements, list):
            self.requirements_edit.setText('\n'.join(requirements))
        else:
            self.requirements_edit.setText(str(requirements) if requirements else '')
        
        # Salary
        if data.get('salary_min'):
            self.salary_min_spin.setValue(float(data['salary_min']))
        if data.get('salary_max'):
            self.salary_max_spin.setValue(float(data['salary_max']))
        
        self.status_combo.setCurrentText(data.get('status', 'Active'))


class PositionsView(QWidget):
    """Positions management view."""
    
    def __init__(self, api_service: APIService, config_service: ConfigService, parent=None):
        super().__init__(parent)
        
        self.api_service = api_service
        self.config_service = config_service
        
        # Current data and state
        self.current_positions: List[Dict[str, Any]] = []
        self.selected_position: Optional[Dict[str, Any]] = None
        
        # Search state
        self.current_filters: List[SearchFilter] = []
        self.current_page = 1
        self.page_size = 20
        
        self.setup_ui()
        self.setup_connections()
        
        # Load initial data
        self.refresh_data()
    
    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Toolbar
        self.create_toolbar(layout)
        
        # Main content splitter
        self.splitter = QSplitter(Qt.Vertical)
        layout.addWidget(self.splitter)
        
        # Search widget
        self.create_search_section()
        
        # Data table
        self.create_table_section()
        
        # Set splitter sizes
        self.splitter.setSizes([150, 450])
    
    def create_toolbar(self, layout: QVBoxLayout):
        """Create the toolbar."""
        toolbar_frame = QFrame()
        toolbar_layout = QHBoxLayout(toolbar_frame)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        
        # Title
        title_label = QLabel("Position Management")
        title_font = title_label.font()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        toolbar_layout.addWidget(title_label)
        
        # Spacer
        toolbar_layout.addStretch()
        
        # Add position button
        self.add_btn = QPushButton("➕ Add Position")
        self.add_btn.clicked.connect(self.add_position)
        toolbar_layout.addWidget(self.add_btn)
        
        # Edit position button
        self.edit_btn = QPushButton("✏️ Edit")
        self.edit_btn.setEnabled(False)
        self.edit_btn.clicked.connect(self.edit_position)
        toolbar_layout.addWidget(self.edit_btn)
        
        # Delete position button
        self.delete_btn = QPushButton("🗑️ Delete")
        self.delete_btn.setEnabled(False)
        self.delete_btn.clicked.connect(self.delete_position)
        toolbar_layout.addWidget(self.delete_btn)
        
        # More actions menu
        self.more_btn = QToolButton()
        self.more_btn.setText("⚙️ More")
        self.more_btn.setPopupMode(QToolButton.InstantPopup)
        self.create_more_menu()
        toolbar_layout.addWidget(self.more_btn)
        
        layout.addWidget(toolbar_frame)
    
    def create_more_menu(self):
        """Create more actions menu."""
        menu = QMenu(self)
        
        # Export action
        export_action = QAction("📤 Export Positions", self)
        export_action.triggered.connect(self.export_positions)
        menu.addAction(export_action)
        
        menu.addSeparator()
        
        # Refresh action
        refresh_action = QAction("🔄 Refresh", self)
        refresh_action.triggered.connect(self.refresh_data)
        menu.addAction(refresh_action)
        
        self.more_btn.setMenu(menu)
    
    def create_search_section(self):
        """Create the search section."""
        field_definitions = {
            'title': {
                'label': 'Position Title',
                'type': 'text'
            },
            'description': {
                'label': 'Description',
                'type': 'text'
            },
            'department_name': {
                'label': 'Department',
                'type': 'text'
            },
            'status': {
                'label': 'Status',
                'type': 'choice',
                'choices': ['Active', 'Inactive', 'Draft', 'Filled']
            },
            'salary_min': {
                'label': 'Minimum Salary',
                'type': 'number',
                'decimal': True
            },
            'salary_max': {
                'label': 'Maximum Salary',
                'type': 'number',
                'decimal': True
            }
        }
        
        self.search_widget = SearchWidget(field_definitions)
        self.splitter.addWidget(self.search_widget)
    
    def create_table_section(self):
        """Create the data table section."""
        columns = [
            ColumnConfig('title', 'Title', 200),
            ColumnConfig('description', 'Description', 250),
            ColumnConfig('department_name', 'Department', 150),
            ColumnConfig('salary_range', 'Salary Range', 150, formatter=self.format_salary_range),
            ColumnConfig('status', 'Status', 100),
            ColumnConfig('employee_count', 'Employees', 100),
            ColumnConfig('created_at', 'Created', 120, formatter=self.format_datetime),
            ColumnConfig('updated_at', 'Modified', 120, formatter=self.format_datetime),
        ]
        
        self.data_table = DataTable(columns)
        self.splitter.addWidget(self.data_table)
    
    def setup_connections(self):
        """Set up signal connections."""
        # API service connections
        self.api_service.data_updated.connect(self.on_data_updated)
        self.api_service.operation_completed.connect(self.on_operation_completed)
        
        # Search widget connections
        self.search_widget.search_requested.connect(self.on_search_requested)
        self.search_widget.filters_changed.connect(self.on_filters_changed)
        self.search_widget.search_cleared.connect(self.on_search_cleared)
        
        # Table connections
        self.data_table.item_selected.connect(self.on_position_selected)
        self.data_table.item_double_clicked.connect(self.on_position_double_clicked)
        self.data_table.selection_changed.connect(self.on_selection_changed)
        self.data_table.page_changed.connect(self.on_page_changed)
        self.data_table.refresh_requested.connect(self.refresh_data)
    
    def format_datetime(self, value: Any) -> str:
        """Format datetime for display."""
        if not value:
            return ""
        
        try:
            if isinstance(value, str):
                dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
            else:
                dt = value
            
            return dt.strftime('%Y-%m-%d %H:%M')
        except (ValueError, TypeError):
            return str(value)
    
    def format_salary_range(self, item: Dict[str, Any]) -> str:
        """Format salary range for display."""
        salary_min = item.get('salary_min')
        salary_max = item.get('salary_max')
        
        if salary_min and salary_max:
            return f"${salary_min:,.0f} - ${salary_max:,.0f}"
        elif salary_min:
            return f"${salary_min:,.0f}+"
        elif salary_max:
            return f"Up to ${salary_max:,.0f}"
        else:
            return "Not specified"
    
    def refresh_data(self):
        """Refresh positions data."""
        self.api_service.list_positions_async(
            page=self.current_page,
            page_size=self.page_size
        )
    
    def on_data_updated(self, data_type: str, data: Dict[str, Any]):
        """Handle data updates."""
        if data_type == "positions":
            self.update_positions_data(data)
    
    def update_positions_data(self, data: Dict[str, Any]):
        """Update the positions table."""
        try:
            items = data.get('items', [])
            self.current_positions = items
            
            # Apply filters
            filtered_items = self.apply_filters(items)
            self.data_table.set_data(filtered_items)
            
        except Exception as e:
            logger.error(f"Error updating positions data: {e}")
            QMessageBox.critical(self, "Error", f"Failed to update positions data: {e}")
    
    def apply_filters(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply search filters."""
        if not self.current_filters:
            return items
        
        filtered_items = []
        
        for item in items:
            matches = True
            
            for search_filter in self.current_filters:
                if not self.item_matches_filter(item, search_filter):
                    matches = False
                    break
            
            if matches:
                filtered_items.append(item)
        
        return filtered_items
    
    def item_matches_filter(self, item: Dict[str, Any], search_filter: SearchFilter) -> bool:
        """Check if item matches filter."""
        field_value = item.get(search_filter.field, '')
        filter_value = search_filter.value
        
        if field_value is None:
            field_value = ''
        
        # Handle quick search
        if search_filter.field == '_quick_search':
            search_fields = ['title', 'description', 'department_name']
            query = str(filter_value).lower()
            
            return any(
                query in str(item.get(field, '')).lower()
                for field in search_fields
            )
        
        # Handle specific field filters
        if search_filter.field_type == 'text':
            field_str = str(field_value).lower()
            filter_str = str(filter_value).lower()
            
            if search_filter.operator == 'contains':
                return filter_str in field_str
            elif search_filter.operator == 'equals':
                return field_str == filter_str
        
        elif search_filter.field_type == 'choice':
            if search_filter.operator == 'equals':
                return field_value == filter_value
        
        elif search_filter.field_type == 'number':
            try:
                field_num = float(field_value) if field_value else 0
                filter_num = float(filter_value)
                
                if search_filter.operator == 'greater_than':
                    return field_num > filter_num
                elif search_filter.operator == 'less_than':
                    return field_num < filter_num
                elif search_filter.operator == 'equals':
                    return field_num == filter_num
            except (ValueError, TypeError):
                return False
        
        return True
    
    def on_search_requested(self, filters: List[SearchFilter]):
        """Handle search request."""
        self.current_filters = filters
        filtered_items = self.apply_filters(self.current_positions)
        self.data_table.set_data(filtered_items)
    
    def on_filters_changed(self, filters: List[SearchFilter]):
        """Handle filter changes."""
        self.current_filters = filters
        filtered_items = self.apply_filters(self.current_positions)
        self.data_table.set_data(filtered_items)
    
    def on_search_cleared(self):
        """Handle search cleared."""
        self.current_filters = []
        self.data_table.set_data(self.current_positions)
    
    def on_position_selected(self, position_data: Dict[str, Any]):
        """Handle position selection."""
        self.selected_position = position_data
        self.edit_btn.setEnabled(True)
        self.delete_btn.setEnabled(True)
    
    def on_position_double_clicked(self, position_data: Dict[str, Any]):
        """Handle position double-click."""
        self.selected_position = position_data
        self.edit_position()
    
    def on_selection_changed(self, selected_items: List[Dict[str, Any]]):
        """Handle selection change."""
        has_selection = len(selected_items) > 0
        self.edit_btn.setEnabled(len(selected_items) == 1)
        self.delete_btn.setEnabled(has_selection)
    
    def on_page_changed(self, page: int):
        """Handle page change."""
        self.current_page = page
        self.refresh_data()
    
    def on_operation_completed(self, operation: str, success: bool, message: str):
        """Handle operation completion."""
        if success and 'position' in operation.lower():
            self.refresh_data()
            
            if 'delete' in operation.lower():
                self.selected_position = None
                self.edit_btn.setEnabled(False)
                self.delete_btn.setEnabled(False)
    
    def add_position(self):
        """Add new position."""
        dialog = PositionDialog(api_service=self.api_service, parent=self)
        
        if dialog.exec() == QDialog.Accepted:
            position_data = dialog.get_form_data()
            self.api_service.create_position_async(position_data)
    
    def edit_position(self):
        """Edit selected position."""
        if not self.selected_position:
            return
        
        dialog = PositionDialog(self.selected_position, api_service=self.api_service, parent=self)
        
        if dialog.exec() == QDialog.Accepted:
            position_data = dialog.get_form_data()
            position_id = self.selected_position.get('id')
            
            if position_id:
                self.api_service.update_position_async(position_id, position_data)
    
    def delete_position(self):
        """Delete selected position(s)."""
        selected_items = self.data_table.get_selected_data()
        
        if not selected_items:
            return
        
        count = len(selected_items)
        pos_text = "position" if count == 1 else "positions"
        
        reply = QMessageBox.question(
            self,
            f"Delete {pos_text.title()}",
            f"Are you sure you want to delete {count} {pos_text}?\n\n"
            "This action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            for position in selected_items:
                position_id = position.get('id')
                if position_id:
                    self.api_service.delete_position_async(position_id)
    
    def export_positions(self):
        """Export positions to file."""
        self.data_table.export_data('csv')
    
    def refresh(self):
        """Refresh the view."""
        self.refresh_data()
    
    def showEvent(self, event):
        """Handle show event."""
        super().showEvent(event)
        if self.api_service.is_connected:
            self.refresh_data()