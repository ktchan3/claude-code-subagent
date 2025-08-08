"""
Departments Management View for People Management System Client

Provides interface for managing department records.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QPushButton,
    QMessageBox, QDialog, QDialogButtonBox, QLabel, QFrame,
    QToolButton, QMenu, QFormLayout, QLineEdit, QTextEdit,
    QComboBox, QGroupBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction

from client.services.api_service import APIService
from client.services.config_service import ConfigService
from client.ui.widgets.data_table import DataTable, ColumnConfig
from client.ui.widgets.search_widget import SearchWidget, SearchFilter

logger = logging.getLogger(__name__)


class DepartmentForm(QWidget):
    """Form for creating/editing departments."""
    
    # Signals
    data_changed = Signal(dict)
    save_requested = Signal(dict)
    cancel_requested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.department_data: Optional[Dict[str, Any]] = None
        self.is_editing = False
        
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """Set up the form UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Department details group
        details_group = QGroupBox("Department Details")
        details_layout = QFormLayout(details_group)
        details_layout.setVerticalSpacing(10)
        details_layout.setContentsMargins(5, 10, 5, 5)
        
        # Name (required)
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter department name")
        details_layout.addRow("Name *:", self.name_edit)
        
        # Description
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Enter department description")
        self.description_edit.setMaximumHeight(100)
        details_layout.addRow("Description:", self.description_edit)
        
        # Manager
        self.manager_combo = QComboBox()
        self.manager_combo.setEditable(True)
        self.manager_combo.setPlaceholderText("Select or enter manager email")
        details_layout.addRow("Manager:", self.manager_combo)
        
        layout.addWidget(details_group)
        
        # Status and metadata
        meta_group = QGroupBox("Status & Information")
        meta_layout = QFormLayout(meta_group)
        meta_layout.setVerticalSpacing(10)
        meta_layout.setContentsMargins(5, 10, 5, 5)
        
        # Status
        self.status_combo = QComboBox()
        self.status_combo.addItems(["Active", "Inactive", "Pending"])
        meta_layout.addRow("Status:", self.status_combo)
        
        # Created info
        self.created_label = QLabel("-")
        self.created_label.setStyleSheet("color: #666; font-size: 9pt;")
        meta_layout.addRow("Created:", self.created_label)
        
        # Modified info
        self.modified_label = QLabel("-")
        self.modified_label.setStyleSheet("color: #666; font-size: 9pt;")
        meta_layout.addRow("Last Modified:", self.modified_label)
        
        layout.addWidget(meta_group)
        
        # Spacer
        layout.addStretch()
        
        # Action buttons
        self.create_buttons(layout)
    
    def create_buttons(self, layout: QVBoxLayout):
        """Create action buttons."""
        button_layout = QHBoxLayout()
        
        button_layout.addStretch()
        
        # Reset button
        self.reset_btn = QPushButton("Reset")
        self.reset_btn.clicked.connect(self.reset_form)
        button_layout.addWidget(self.reset_btn)
        
        # Cancel button
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.cancel_requested.emit)
        button_layout.addWidget(self.cancel_btn)
        
        # Save button
        self.save_btn = QPushButton("Save")
        self.save_btn.setDefault(True)
        self.save_btn.clicked.connect(self.save_department)
        button_layout.addWidget(self.save_btn)
        
        layout.addLayout(button_layout)
    
    def setup_connections(self):
        """Set up signal connections."""
        # Form change detection
        self.name_edit.textChanged.connect(self.on_form_changed)
        self.description_edit.textChanged.connect(self.on_form_changed)
        self.manager_combo.currentTextChanged.connect(self.on_form_changed)
        self.status_combo.currentTextChanged.connect(self.on_form_changed)
        
        # Validation
        self.name_edit.textChanged.connect(self.validate_form)
    
    def on_form_changed(self):
        """Handle form changes."""
        data = self.get_form_data()
        self.data_changed.emit(data)
    
    def validate_form(self) -> bool:
        """Validate form data."""
        is_valid = bool(self.name_edit.text().strip())
        self.save_btn.setEnabled(is_valid)
        
        # Visual feedback
        if not is_valid and self.name_edit.text():
            self.name_edit.setStyleSheet("border: 2px solid red;")
        else:
            self.name_edit.setStyleSheet("")
        
        return is_valid
    
    def get_form_data(self) -> Dict[str, Any]:
        """Get form data."""
        return {
            'name': self.name_edit.text().strip(),
            'description': self.description_edit.toPlainText().strip() or None,
            'manager_email': self.manager_combo.currentText().strip() or None,
            'status': self.status_combo.currentText()
        }
    
    def set_form_data(self, data: Dict[str, Any]):
        """Set form data."""
        self.department_data = data
        self.is_editing = bool(data.get('id'))
        
        self.name_edit.setText(data.get('name', ''))
        self.description_edit.setText(data.get('description', ''))
        self.manager_combo.setCurrentText(data.get('manager_email', ''))
        self.status_combo.setCurrentText(data.get('status', 'Active'))
        
        # Metadata
        if data.get('created_at'):
            try:
                created_dt = datetime.fromisoformat(data['created_at'])
                self.created_label.setText(created_dt.strftime('%Y-%m-%d %H:%M:%S'))
            except (ValueError, TypeError):
                self.created_label.setText(str(data['created_at']))
        
        if data.get('updated_at'):
            try:
                updated_dt = datetime.fromisoformat(data['updated_at'])
                self.modified_label.setText(updated_dt.strftime('%Y-%m-%d %H:%M:%S'))
            except (ValueError, TypeError):
                self.modified_label.setText(str(data['updated_at']))
        
        self.validate_form()
    
    def clear_form(self):
        """Clear form data."""
        self.department_data = None
        self.is_editing = False
        
        self.name_edit.clear()
        self.description_edit.clear()
        self.manager_combo.setCurrentText("")
        self.status_combo.setCurrentText("Active")
        
        self.created_label.setText("-")
        self.modified_label.setText("-")
        
        self.validate_form()
    
    def reset_form(self):
        """Reset form to original data."""
        if self.department_data:
            self.set_form_data(self.department_data)
        else:
            self.clear_form()
    
    def save_department(self):
        """Save department data."""
        if self.validate_form():
            data = self.get_form_data()
            
            if self.is_editing and self.department_data:
                data['id'] = self.department_data.get('id')
            
            self.save_requested.emit(data)


class DepartmentDialog(QDialog):
    """Dialog for adding/editing departments."""
    
    def __init__(self, department_data: Optional[Dict[str, Any]] = None, parent=None):
        super().__init__(parent)
        
        self.department_data = department_data
        self.is_editing = bool(department_data)
        
        title = "Edit Department" if self.is_editing else "Add New Department"
        self.setWindowTitle(title)
        self.setModal(True)
        self.resize(500, 400)
        
        self.setup_ui()
        
        if department_data:
            self.department_form.set_form_data(department_data)
    
    def setup_ui(self):
        """Set up dialog UI."""
        layout = QVBoxLayout(self)
        
        # Department form
        self.department_form = DepartmentForm()
        layout.addWidget(self.department_form)
        
        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal
        )
        button_box.accepted.connect(self.accept_dialog)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # Update OK button state
        self.ok_button = button_box.button(QDialogButtonBox.Ok)
        self.department_form.name_edit.textChanged.connect(
            lambda: self.ok_button.setEnabled(bool(self.department_form.name_edit.text().strip()))
        )
        
        # Initial validation
        self.ok_button.setEnabled(bool(self.department_form.name_edit.text().strip()))
    
    def accept_dialog(self):
        """Handle dialog acceptance."""
        if self.department_form.validate_form():
            self.accept()
        else:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Please enter a department name."
            )
    
    def get_form_data(self) -> Dict[str, Any]:
        """Get form data."""
        return self.department_form.get_form_data()


class DepartmentsView(QWidget):
    """Departments management view."""
    
    def __init__(self, api_service: APIService, config_service: ConfigService, parent=None):
        super().__init__(parent)
        
        self.api_service = api_service
        self.config_service = config_service
        
        # Current data and state
        self.current_departments: List[Dict[str, Any]] = []
        self.selected_department: Optional[Dict[str, Any]] = None
        
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
        title_label = QLabel("Department Management")
        title_font = title_label.font()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        toolbar_layout.addWidget(title_label)
        
        # Spacer
        toolbar_layout.addStretch()
        
        # Add department button
        self.add_btn = QPushButton("➕ Add Department")
        self.add_btn.clicked.connect(self.add_department)
        toolbar_layout.addWidget(self.add_btn)
        
        # Edit department button
        self.edit_btn = QPushButton("✏️ Edit")
        self.edit_btn.setEnabled(False)
        self.edit_btn.clicked.connect(self.edit_department)
        toolbar_layout.addWidget(self.edit_btn)
        
        # Delete department button
        self.delete_btn = QPushButton("🗑️ Delete")
        self.delete_btn.setEnabled(False)
        self.delete_btn.clicked.connect(self.delete_department)
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
        export_action = QAction("📤 Export Departments", self)
        export_action.triggered.connect(self.export_departments)
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
            'name': {
                'label': 'Department Name',
                'type': 'text'
            },
            'description': {
                'label': 'Description',
                'type': 'text'
            },
            'manager_email': {
                'label': 'Manager Email',
                'type': 'text'
            },
            'status': {
                'label': 'Status',
                'type': 'choice',
                'choices': ['Active', 'Inactive', 'Pending']
            }
        }
        
        self.search_widget = SearchWidget(field_definitions)
        self.splitter.addWidget(self.search_widget)
    
    def create_table_section(self):
        """Create the data table section."""
        columns = [
            ColumnConfig('name', 'Name', 200),
            ColumnConfig('description', 'Description', 300),
            ColumnConfig('manager_email', 'Manager', 200),
            ColumnConfig('status', 'Status', 100),
            ColumnConfig('employee_count', 'Employees', 100),
            ColumnConfig('created_at', 'Created', 150, formatter=self.format_datetime),
            ColumnConfig('updated_at', 'Modified', 150, formatter=self.format_datetime),
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
        self.data_table.item_selected.connect(self.on_department_selected)
        self.data_table.item_double_clicked.connect(self.on_department_double_clicked)
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
    
    def refresh_data(self):
        """Refresh departments data."""
        self.api_service.list_departments_async(
            page=self.current_page,
            page_size=self.page_size
        )
    
    def on_data_updated(self, data_type: str, data: Dict[str, Any]):
        """Handle data updates."""
        if data_type == "departments":
            self.update_departments_data(data)
    
    def update_departments_data(self, data: Dict[str, Any]):
        """Update the departments table."""
        try:
            items = data.get('items', [])
            self.current_departments = items
            
            # Apply filters
            filtered_items = self.apply_filters(items)
            self.data_table.set_data(filtered_items)
            
        except Exception as e:
            logger.error(f"Error updating departments data: {e}")
            QMessageBox.critical(self, "Error", f"Failed to update departments data: {e}")
    
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
            search_fields = ['name', 'description', 'manager_email']
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
            # Add more operators as needed
        
        elif search_filter.field_type == 'choice':
            if search_filter.operator == 'equals':
                return field_value == filter_value
        
        return True
    
    def on_search_requested(self, filters: List[SearchFilter]):
        """Handle search request."""
        self.current_filters = filters
        filtered_items = self.apply_filters(self.current_departments)
        self.data_table.set_data(filtered_items)
    
    def on_filters_changed(self, filters: List[SearchFilter]):
        """Handle filter changes."""
        self.current_filters = filters
        filtered_items = self.apply_filters(self.current_departments)
        self.data_table.set_data(filtered_items)
    
    def on_search_cleared(self):
        """Handle search cleared."""
        self.current_filters = []
        self.data_table.set_data(self.current_departments)
    
    def on_department_selected(self, department_data: Dict[str, Any]):
        """Handle department selection."""
        self.selected_department = department_data
        self.edit_btn.setEnabled(True)
        self.delete_btn.setEnabled(True)
    
    def on_department_double_clicked(self, department_data: Dict[str, Any]):
        """Handle department double-click."""
        self.selected_department = department_data
        self.edit_department()
    
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
        if success and operation in ['create_department', 'update_department', 'delete_department']:
            self.refresh_data()
            
            if operation == 'delete_department':
                self.selected_department = None
                self.edit_btn.setEnabled(False)
                self.delete_btn.setEnabled(False)
    
    def add_department(self):
        """Add new department."""
        dialog = DepartmentDialog(parent=self)
        
        if dialog.exec() == QDialog.Accepted:
            department_data = dialog.get_form_data()
            self.api_service.create_department_async(department_data)
    
    def edit_department(self):
        """Edit selected department."""
        if not self.selected_department:
            return
        
        dialog = DepartmentDialog(self.selected_department, parent=self)
        
        if dialog.exec() == QDialog.Accepted:
            department_data = dialog.get_form_data()
            department_id = self.selected_department.get('id')
            
            if department_id:
                # Note: API service doesn't have update_department_async yet
                # This would need to be implemented in the API service
                QMessageBox.information(
                    self,
                    "Update Department", 
                    "Department update functionality will be implemented soon."
                )
    
    def delete_department(self):
        """Delete selected department(s)."""
        selected_items = self.data_table.get_selected_data()
        
        if not selected_items:
            return
        
        count = len(selected_items)
        dept_text = "department" if count == 1 else "departments"
        
        reply = QMessageBox.question(
            self,
            f"Delete {dept_text.title()}",
            f"Are you sure you want to delete {count} {dept_text}?\n\n"
            "This action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            for department in selected_items:
                department_id = department.get('id')
                if department_id:
                    # Note: API service doesn't have delete_department_async yet
                    QMessageBox.information(
                        self,
                        "Delete Department",
                        "Department deletion functionality will be implemented soon."
                    )
    
    def export_departments(self):
        """Export departments to file."""
        self.data_table.export_data('csv')
    
    def refresh(self):
        """Refresh the view."""
        self.refresh_data()
    
    def showEvent(self, event):
        """Handle show event."""
        super().showEvent(event)
        if self.api_service.is_connected:
            self.refresh_data()