"""
Employment Records Management View for People Management System Client

Provides interface for managing employment records.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, date

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QPushButton,
    QMessageBox, QDialog, QDialogButtonBox, QLabel, QFrame,
    QToolButton, QMenu, QFormLayout, QLineEdit, QTextEdit,
    QComboBox, QGroupBox, QDateEdit, QDoubleSpinBox, QCheckBox
)
from PySide6.QtCore import Qt, Signal, QDate
from PySide6.QtGui import QAction

from client.services.api_service import APIService
from client.services.config_service import ConfigService
from client.ui.widgets.data_table import DataTable, ColumnConfig
from client.ui.widgets.search_widget import SearchWidget, SearchFilter

logger = logging.getLogger(__name__)


class EmploymentDialog(QDialog):
    """Dialog for adding/editing employment records."""
    
    def __init__(self, employment_data: Optional[Dict[str, Any]] = None, parent=None):
        super().__init__(parent)
        
        self.employment_data = employment_data
        self.is_editing = bool(employment_data)
        
        title = "Edit Employment Record" if self.is_editing else "Add New Employment Record"
        self.setWindowTitle(title)
        self.setModal(True)
        self.resize(600, 500)
        
        self.setup_ui()
        
        if employment_data:
            self.set_form_data(employment_data)
    
    def setup_ui(self):
        """Set up dialog UI."""
        layout = QVBoxLayout(self)
        
        # Basic information
        basic_group = QGroupBox("Basic Information")
        basic_layout = QFormLayout(basic_group)
        basic_layout.setVerticalSpacing(10)
        basic_layout.setContentsMargins(5, 10, 5, 5)
        
        # Person selection
        self.person_combo = QComboBox()
        self.person_combo.setPlaceholderText("Select person")
        basic_layout.addRow("Person *:", self.person_combo)
        
        # Position selection
        self.position_combo = QComboBox()
        self.position_combo.setPlaceholderText("Select position")
        basic_layout.addRow("Position *:", self.position_combo)
        
        layout.addWidget(basic_group)
        
        # Employment details
        details_group = QGroupBox("Employment Details")
        details_layout = QFormLayout(details_group)
        details_layout.setVerticalSpacing(10)
        details_layout.setContentsMargins(5, 10, 5, 5)
        
        # Start date
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setDate(QDate.currentDate())
        self.start_date_edit.setCalendarPopup(True)
        details_layout.addRow("Start Date *:", self.start_date_edit)
        
        # End date
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setDate(QDate.currentDate().addYears(1))
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setEnabled(False)
        details_layout.addRow("End Date:", self.end_date_edit)
        
        # Is active checkbox
        self.is_active_cb = QCheckBox("Currently Active")
        self.is_active_cb.setChecked(True)
        self.is_active_cb.toggled.connect(lambda checked: self.end_date_edit.setEnabled(not checked))
        details_layout.addRow("", self.is_active_cb)
        
        # Employment type
        self.employment_type_combo = QComboBox()
        self.employment_type_combo.addItems([
            "full_time", "part_time", "contract", "internship", "temporary"
        ])
        details_layout.addRow("Employment Type:", self.employment_type_combo)
        
        # Salary
        self.salary_spin = QDoubleSpinBox()
        self.salary_spin.setRange(0, 999999.99)
        self.salary_spin.setDecimals(2)
        self.salary_spin.setSuffix(" USD")
        details_layout.addRow("Salary:", self.salary_spin)
        
        layout.addWidget(details_group)
        
        # Additional information
        additional_group = QGroupBox("Additional Information")
        additional_layout = QFormLayout(additional_group)
        additional_layout.setVerticalSpacing(10)
        additional_layout.setContentsMargins(5, 10, 5, 5)
        
        # Notes
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Additional notes...")
        self.notes_edit.setMaximumHeight(80)
        additional_layout.addRow("Notes:", self.notes_edit)
        
        layout.addWidget(additional_group)
        
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
        self.person_combo.currentTextChanged.connect(self.validate_form)
        self.position_combo.currentTextChanged.connect(self.validate_form)
        self.validate_form()
    
    def validate_form(self):
        """Validate form data."""
        has_person = bool(self.person_combo.currentData())
        has_position = bool(self.position_combo.currentData())
        is_valid = has_person and has_position
        self.ok_button.setEnabled(is_valid)
    
    def accept_dialog(self):
        """Handle dialog acceptance."""
        if self.person_combo.currentData() and self.position_combo.currentData():
            self.accept()
        else:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Please select both a person and a position."
            )
    
    def get_form_data(self) -> Dict[str, Any]:
        """Get form data."""
        data = {
            'person_id': self.person_combo.currentData(),
            'position_id': self.position_combo.currentData(),
            'start_date': self.start_date_edit.date().toPython().isoformat(),
            'employment_type': self.employment_type_combo.currentText(),
            'is_active': self.is_active_cb.isChecked(),
            'notes': self.notes_edit.toPlainText().strip() or None
        }
        
        # End date only if not active
        if not self.is_active_cb.isChecked():
            data['end_date'] = self.end_date_edit.date().toPython().isoformat()
        
        # Salary only if > 0
        if self.salary_spin.value() > 0:
            data['salary'] = self.salary_spin.value()
        
        return data
    
    def set_form_data(self, data: Dict[str, Any]):
        """Set form data."""
        # Set person
        person_id = data.get('person_id')
        if person_id:
            for i in range(self.person_combo.count()):
                if self.person_combo.itemData(i) == person_id:
                    self.person_combo.setCurrentIndex(i)
                    break
        
        # Set position
        position_id = data.get('position_id')
        if position_id:
            for i in range(self.position_combo.count()):
                if self.position_combo.itemData(i) == position_id:
                    self.position_combo.setCurrentIndex(i)
                    break
        
        # Dates
        if data.get('start_date'):
            try:
                start_date = datetime.fromisoformat(data['start_date']).date()
                self.start_date_edit.setDate(QDate(start_date))
            except (ValueError, TypeError):
                pass
        
        if data.get('end_date'):
            try:
                end_date = datetime.fromisoformat(data['end_date']).date()
                self.end_date_edit.setDate(QDate(end_date))
            except (ValueError, TypeError):
                pass
        
        # Active status
        is_active = data.get('is_active', True)
        self.is_active_cb.setChecked(is_active)
        self.end_date_edit.setEnabled(not is_active)
        
        # Employment type
        employment_type = data.get('employment_type', 'full_time')
        self.employment_type_combo.setCurrentText(employment_type)
        
        # Salary
        if data.get('salary'):
            self.salary_spin.setValue(float(data['salary']))
        
        # Notes
        self.notes_edit.setText(data.get('notes', ''))


class EmploymentView(QWidget):
    """Employment records management view."""
    
    def __init__(self, api_service: APIService, config_service: ConfigService, parent=None):
        super().__init__(parent)
        
        self.api_service = api_service
        self.config_service = config_service
        
        # Current data and state
        self.current_employment: List[Dict[str, Any]] = []
        self.selected_employment: Optional[Dict[str, Any]] = None
        
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
        title_label = QLabel("Employment Records")
        title_font = title_label.font()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        toolbar_layout.addWidget(title_label)
        
        # Spacer
        toolbar_layout.addStretch()
        
        # Add employment button
        self.add_btn = QPushButton("➕ Add Employment")
        self.add_btn.clicked.connect(self.add_employment)
        toolbar_layout.addWidget(self.add_btn)
        
        # Edit employment button
        self.edit_btn = QPushButton("✏️ Edit")
        self.edit_btn.setEnabled(False)
        self.edit_btn.clicked.connect(self.edit_employment)
        toolbar_layout.addWidget(self.edit_btn)
        
        # End employment button
        self.end_btn = QPushButton("🔚 End Employment")
        self.end_btn.setEnabled(False)
        self.end_btn.clicked.connect(self.end_employment)
        toolbar_layout.addWidget(self.end_btn)
        
        # Delete employment button
        self.delete_btn = QPushButton("🗑️ Delete")
        self.delete_btn.setEnabled(False)
        self.delete_btn.clicked.connect(self.delete_employment)
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
        export_action = QAction("📤 Export Employment Records", self)
        export_action.triggered.connect(self.export_employment)
        menu.addAction(export_action)
        
        menu.addSeparator()
        
        # Filter actions
        active_only_action = QAction("👥 Show Active Only", self)
        active_only_action.triggered.connect(self.show_active_only)
        menu.addAction(active_only_action)
        
        inactive_only_action = QAction("📋 Show Inactive Only", self)
        inactive_only_action.triggered.connect(self.show_inactive_only)
        menu.addAction(inactive_only_action)
        
        menu.addSeparator()
        
        # Refresh action
        refresh_action = QAction("🔄 Refresh", self)
        refresh_action.triggered.connect(self.refresh_data)
        menu.addAction(refresh_action)
        
        self.more_btn.setMenu(menu)
    
    def create_search_section(self):
        """Create the search section."""
        field_definitions = {
            'person_name': {
                'label': 'Person Name',
                'type': 'text'
            },
            'position_title': {
                'label': 'Position Title',
                'type': 'text'
            },
            'department_name': {
                'label': 'Department',
                'type': 'text'
            },
            'employment_type': {
                'label': 'Employment Type',
                'type': 'choice',
                'choices': ['full_time', 'part_time', 'contract', 'internship', 'temporary']
            },
            'is_active': {
                'label': 'Status',
                'type': 'choice',
                'choices': [
                    {'label': 'Active', 'value': True},
                    {'label': 'Inactive', 'value': False}
                ]
            },
            'start_date': {
                'label': 'Start Date',
                'type': 'date'
            },
            'end_date': {
                'label': 'End Date',
                'type': 'date'
            },
            'salary': {
                'label': 'Salary',
                'type': 'number',
                'decimal': True
            }
        }
        
        self.search_widget = SearchWidget(field_definitions)
        self.splitter.addWidget(self.search_widget)
    
    def create_table_section(self):
        """Create the data table section."""
        columns = [
            ColumnConfig('person_name', 'Person', 150),
            ColumnConfig('position_title', 'Position', 150),
            ColumnConfig('department_name', 'Department', 120),
            ColumnConfig('employment_type', 'Type', 100),
            ColumnConfig('start_date', 'Start Date', 100, formatter=self.format_date),
            ColumnConfig('end_date', 'End Date', 100, formatter=self.format_date),
            ColumnConfig('is_active', 'Status', 80, formatter=lambda x: "Active" if x else "Inactive"),
            ColumnConfig('salary', 'Salary', 100, formatter=self.format_salary),
            ColumnConfig('duration', 'Duration', 100, formatter=self.format_duration),
            ColumnConfig('created_at', 'Created', 120, formatter=self.format_datetime),
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
        self.data_table.item_selected.connect(self.on_employment_selected)
        self.data_table.item_double_clicked.connect(self.on_employment_double_clicked)
        self.data_table.selection_changed.connect(self.on_selection_changed)
        self.data_table.page_changed.connect(self.on_page_changed)
        self.data_table.refresh_requested.connect(self.refresh_data)
    
    def format_date(self, value: Any) -> str:
        """Format date for display."""
        if not value:
            return ""
        
        try:
            if isinstance(value, str):
                dt = datetime.fromisoformat(value).date()
            else:
                dt = value
            
            return dt.strftime('%Y-%m-%d')
        except (ValueError, TypeError):
            return str(value)
    
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
    
    def format_salary(self, value: Any) -> str:
        """Format salary for display."""
        if not value:
            return ""
        
        try:
            return f"${float(value):,.2f}"
        except (ValueError, TypeError):
            return str(value)
    
    def format_duration(self, item: Dict[str, Any]) -> str:
        """Calculate and format employment duration."""
        start_date_str = item.get('start_date')
        end_date_str = item.get('end_date')
        is_active = item.get('is_active', True)
        
        if not start_date_str:
            return ""
        
        try:
            start_date = datetime.fromisoformat(start_date_str).date()
            
            if is_active or not end_date_str:
                end_date = date.today()
            else:
                end_date = datetime.fromisoformat(end_date_str).date()
            
            delta = end_date - start_date
            
            if delta.days < 30:
                return f"{delta.days} days"
            elif delta.days < 365:
                months = delta.days // 30
                return f"{months} month{'s' if months != 1 else ''}"
            else:
                years = delta.days // 365
                remaining_days = delta.days % 365
                months = remaining_days // 30
                
                if months > 0:
                    return f"{years} year{'s' if years != 1 else ''}, {months} month{'s' if months != 1 else ''}"
                else:
                    return f"{years} year{'s' if years != 1 else ''}"
        
        except (ValueError, TypeError):
            return ""
    
    def refresh_data(self):
        """Refresh employment data."""
        self.api_service.list_employment_async(
            page=self.current_page,
            page_size=self.page_size
        )
    
    def on_data_updated(self, data_type: str, data: Dict[str, Any]):
        """Handle data updates."""
        if data_type == "employment":
            self.update_employment_data(data)
    
    def update_employment_data(self, data: Dict[str, Any]):
        """Update the employment table."""
        try:
            items = data.get('items', [])
            self.current_employment = items
            
            # Apply filters
            filtered_items = self.apply_filters(items)
            self.data_table.set_data(filtered_items)
            
        except Exception as e:
            logger.error(f"Error updating employment data: {e}")
            QMessageBox.critical(self, "Error", f"Failed to update employment data: {e}")
    
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
            search_fields = ['person_name', 'position_title', 'department_name']
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
        
        elif search_filter.field_type == 'choice':
            if search_filter.operator == 'equals':
                return field_value == filter_value
        
        elif search_filter.field_type == 'date':
            try:
                field_date = datetime.fromisoformat(str(field_value)).date()
                filter_date = filter_value if isinstance(filter_value, date) else datetime.fromisoformat(str(filter_value)).date()
                
                if search_filter.operator == 'on':
                    return field_date == filter_date
                elif search_filter.operator == 'after':
                    return field_date > filter_date
                elif search_filter.operator == 'before':
                    return field_date < filter_date
            except (ValueError, TypeError):
                return False
        
        return True
    
    def on_search_requested(self, filters: List[SearchFilter]):
        """Handle search request."""
        self.current_filters = filters
        filtered_items = self.apply_filters(self.current_employment)
        self.data_table.set_data(filtered_items)
    
    def on_filters_changed(self, filters: List[SearchFilter]):
        """Handle filter changes."""
        self.current_filters = filters
        filtered_items = self.apply_filters(self.current_employment)
        self.data_table.set_data(filtered_items)
    
    def on_search_cleared(self):
        """Handle search cleared."""
        self.current_filters = []
        self.data_table.set_data(self.current_employment)
    
    def on_employment_selected(self, employment_data: Dict[str, Any]):
        """Handle employment selection."""
        self.selected_employment = employment_data
        is_active = employment_data.get('is_active', False)
        
        self.edit_btn.setEnabled(True)
        self.end_btn.setEnabled(is_active)
        self.delete_btn.setEnabled(True)
    
    def on_employment_double_clicked(self, employment_data: Dict[str, Any]):
        """Handle employment double-click."""
        self.selected_employment = employment_data
        self.edit_employment()
    
    def on_selection_changed(self, selected_items: List[Dict[str, Any]]):
        """Handle selection change."""
        has_selection = len(selected_items) > 0
        single_selection = len(selected_items) == 1
        
        self.edit_btn.setEnabled(single_selection)
        self.delete_btn.setEnabled(has_selection)
        
        # End employment button only for single active employment
        if single_selection:
            is_active = selected_items[0].get('is_active', False)
            self.end_btn.setEnabled(is_active)
        else:
            self.end_btn.setEnabled(False)
    
    def on_page_changed(self, page: int):
        """Handle page change."""
        self.current_page = page
        self.refresh_data()
    
    def on_operation_completed(self, operation: str, success: bool, message: str):
        """Handle operation completion."""
        if success and 'employment' in operation.lower():
            self.refresh_data()
            
            if 'delete' in operation.lower():
                self.selected_employment = None
                self.edit_btn.setEnabled(False)
                self.end_btn.setEnabled(False)
                self.delete_btn.setEnabled(False)
    
    def add_employment(self):
        """Add new employment record."""
        dialog = EmploymentDialog(parent=self)
        
        if dialog.exec() == QDialog.Accepted:
            employment_data = dialog.get_form_data()
            # Note: This would need to be implemented in API service
            QMessageBox.information(
                self,
                "Add Employment",
                "Employment creation functionality will be implemented soon."
            )
    
    def edit_employment(self):
        """Edit selected employment record."""
        if not self.selected_employment:
            return
        
        dialog = EmploymentDialog(self.selected_employment, parent=self)
        
        if dialog.exec() == QDialog.Accepted:
            employment_data = dialog.get_form_data()
            # Note: This would need to be implemented in API service
            QMessageBox.information(
                self,
                "Edit Employment",
                "Employment editing functionality will be implemented soon."
            )
    
    def end_employment(self):
        """End the selected employment record."""
        if not self.selected_employment:
            return
        
        person_name = self.selected_employment.get('person_name', 'Unknown')
        position_title = self.selected_employment.get('position_title', 'Unknown')
        
        reply = QMessageBox.question(
            self,
            "End Employment",
            f"Are you sure you want to end the employment for:\n\n"
            f"Person: {person_name}\n"
            f"Position: {position_title}\n\n"
            f"This will set the end date to today and mark the employment as inactive.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            employment_id = self.selected_employment.get('id')
            if employment_id:
                # Note: This would need to be implemented in API service
                QMessageBox.information(
                    self,
                    "End Employment",
                    "End employment functionality will be implemented soon."
                )
    
    def delete_employment(self):
        """Delete selected employment record(s)."""
        selected_items = self.data_table.get_selected_data()
        
        if not selected_items:
            return
        
        count = len(selected_items)
        record_text = "record" if count == 1 else "records"
        
        reply = QMessageBox.question(
            self,
            f"Delete Employment {record_text.title()}",
            f"Are you sure you want to delete {count} employment {record_text}?\n\n"
            "This action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Note: This would need to be implemented in API service
            QMessageBox.information(
                self,
                "Delete Employment",
                "Employment deletion functionality will be implemented soon."
            )
    
    def show_active_only(self):
        """Show only active employment records."""
        filters = [SearchFilter(field='is_active', operator='equals', value=True, field_type='choice')]
        self.search_widget.set_filters(filters)
        self.on_search_requested(filters)
    
    def show_inactive_only(self):
        """Show only inactive employment records."""
        filters = [SearchFilter(field='is_active', operator='equals', value=False, field_type='choice')]
        self.search_widget.set_filters(filters)
        self.on_search_requested(filters)
    
    def export_employment(self):
        """Export employment records to file."""
        self.data_table.export_data('csv')
    
    def refresh(self):
        """Refresh the view."""
        self.refresh_data()
    
    def showEvent(self, event):
        """Handle show event."""
        super().showEvent(event)
        if self.api_service.is_connected:
            self.refresh_data()