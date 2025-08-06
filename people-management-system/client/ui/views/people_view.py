"""
People Management View for People Management System Client

Provides comprehensive interface for managing people records.
"""

import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QPushButton,
    QMessageBox, QDialog, QDialogButtonBox, QLabel, QFrame,
    QToolButton, QMenu, QFileDialog, QProgressDialog
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QAction, QIcon

from client.services.api_service import APIService
from client.services.config_service import ConfigService
from client.ui.widgets.data_table import DataTable, ColumnConfig
from client.ui.widgets.search_widget import SearchWidget, SearchFilter
from client.ui.widgets.person_form import PersonForm

logger = logging.getLogger(__name__)


class PersonDialog(QDialog):
    """Dialog for adding/editing person records."""
    
    def __init__(self, person_data: Optional[Dict[str, Any]] = None, parent=None):
        super().__init__(parent)
        
        self.person_data = person_data
        self.is_editing = bool(person_data)
        
        title = "Edit Person" if self.is_editing else "Add New Person"
        self.setWindowTitle(title)
        self.setModal(True)
        self.resize(600, 700)
        
        self.setup_ui()
        
        if person_data:
            self.person_form.set_form_data(person_data)
    
    def setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        
        # Person form
        self.person_form = PersonForm()
        self.person_form.set_auto_save_enabled(False)  # Disable auto-save in dialog
        self.person_form.set_action_buttons_visible(False)  # Hide form's own buttons
        layout.addWidget(self.person_form)
        
        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal
        )
        button_box.accepted.connect(self.accept_dialog)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # Update OK button state based on form validation
        self.ok_button = button_box.button(QDialogButtonBox.Ok)
        self.person_form.validation_changed.connect(self.ok_button.setEnabled)
        
        # Connect form's save_requested signal (in case form is used directly)
        self.person_form.save_requested.connect(self.on_form_save_requested)
        
        # Initial validation
        self.ok_button.setEnabled(self.person_form.is_form_valid())
        
        # Also trigger validation when dialog is shown
        self.person_form.validate_form()
    
    def accept_dialog(self):
        """Handle dialog acceptance."""
        logger.debug("Dialog OK button clicked")
        
        if self.person_form.is_form_valid():
            logger.debug("Form is valid, accepting dialog")
            self.accept()
        else:
            logger.debug(f"Form validation failed: {self.person_form.get_validation_errors()}")
            QMessageBox.warning(
                self,
                "Validation Error",
                "Please correct the validation errors before saving."
            )
    
    def on_form_save_requested(self, data):
        """Handle save request from form."""
        logger.debug("Form save requested with data")
        # Form is requesting save, accept the dialog if valid
        if self.person_form.is_form_valid():
            logger.debug("Form is valid, accepting dialog from form save request")
            self.accept()
        else:
            logger.debug(f"Form validation failed in save request: {self.person_form.get_validation_errors()}")
            QMessageBox.warning(
                self,
                "Validation Error", 
                "Please correct the validation errors before saving."
            )
    
    def get_form_data(self) -> Dict[str, Any]:
        """Get form data."""
        return self.person_form.get_form_data()


class PeopleView(QWidget):
    """People management view with table, search, and form."""
    
    def __init__(self, api_service: APIService, config_service: ConfigService, parent=None):
        super().__init__(parent)
        
        self.api_service = api_service
        self.config_service = config_service
        
        # Current data and state
        self.current_people: List[Dict[str, Any]] = []
        self.selected_person: Optional[Dict[str, Any]] = None
        
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
        
        # Set splitter sizes (search smaller, table larger)
        self.splitter.setSizes([200, 600])
    
    def create_toolbar(self, layout: QVBoxLayout):
        """Create the toolbar."""
        toolbar_frame = QFrame()
        toolbar_layout = QHBoxLayout(toolbar_frame)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        
        # Title
        title_label = QLabel("People Management")
        title_font = title_label.font()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        toolbar_layout.addWidget(title_label)
        
        # Spacer
        toolbar_layout.addStretch()
        
        # Add person button
        self.add_btn = QPushButton("➕ Add Person")
        self.add_btn.clicked.connect(self.add_person)
        toolbar_layout.addWidget(self.add_btn)
        
        # Edit person button
        self.edit_btn = QPushButton("✏️ Edit")
        self.edit_btn.setEnabled(False)
        self.edit_btn.clicked.connect(self.edit_person)
        toolbar_layout.addWidget(self.edit_btn)
        
        # Delete person button
        self.delete_btn = QPushButton("🗑️ Delete")
        self.delete_btn.setEnabled(False)
        self.delete_btn.clicked.connect(self.delete_person)
        toolbar_layout.addWidget(self.delete_btn)
        
        # More actions menu
        self.more_btn = QToolButton()
        self.more_btn.setText("⚙️ More")
        self.more_btn.setPopupMode(QToolButton.InstantPopup)
        self.create_more_menu()
        toolbar_layout.addWidget(self.more_btn)
        
        layout.addWidget(toolbar_frame)
    
    def create_more_menu(self):
        """Create the more actions menu."""
        menu = QMenu(self)
        
        # Import/Export actions
        import_action = QAction("📥 Import People", self)
        import_action.triggered.connect(self.import_people)
        menu.addAction(import_action)
        
        export_action = QAction("📤 Export People", self)
        export_action.triggered.connect(self.export_people)
        menu.addAction(export_action)
        
        menu.addSeparator()
        
        # Bulk actions
        bulk_edit_action = QAction("📝 Bulk Edit", self)
        bulk_edit_action.triggered.connect(self.bulk_edit)
        menu.addAction(bulk_edit_action)
        
        bulk_delete_action = QAction("🗑️ Bulk Delete", self)
        bulk_delete_action.triggered.connect(self.bulk_delete)
        menu.addAction(bulk_delete_action)
        
        menu.addSeparator()
        
        # View options
        refresh_action = QAction("🔄 Refresh", self)
        refresh_action.triggered.connect(self.refresh_data)
        menu.addAction(refresh_action)
        
        self.more_btn.setMenu(menu)
    
    def create_search_section(self):
        """Create the search section."""
        # Define searchable fields - expanded to include all relevant fields
        field_definitions = {
            # Basic Information
            'first_name': {
                'label': 'First Name',
                'type': 'text'
            },
            'last_name': {
                'label': 'Last Name',
                'type': 'text'
            },
            'title': {
                'label': 'Title',
                'type': 'choice',
                'choices': ['Mr.', 'Ms.', 'Mrs.', 'Dr.', 'Prof.']
            },
            'suffix': {
                'label': 'Suffix',
                'type': 'text'
            },
            
            # Contact Information
            'email': {
                'label': 'Email',
                'type': 'text'
            },
            'phone': {
                'label': 'Phone',
                'type': 'text'
            },
            'mobile': {
                'label': 'Mobile',
                'type': 'text'
            },
            'address': {
                'label': 'Address',
                'type': 'text'
            },
            'city': {
                'label': 'City',
                'type': 'text'
            },
            'state': {
                'label': 'State',
                'type': 'text'
            },
            'zip_code': {
                'label': 'ZIP Code',
                'type': 'text'
            },
            'country': {
                'label': 'Country',
                'type': 'text'
            },
            
            # Personal Information
            'date_of_birth': {
                'label': 'Date of Birth',
                'type': 'date'
            },
            'gender': {
                'label': 'Gender',
                'type': 'choice',
                'choices': ['Male', 'Female', 'Other', 'Prefer not to say']
            },
            'marital_status': {
                'label': 'Marital Status',
                'type': 'choice',
                'choices': ['Single', 'Married', 'Divorced', 'Widowed', 'Separated']
            },
            
            # Emergency Contact
            'emergency_contact_name': {
                'label': 'Emergency Contact Name',
                'type': 'text'
            },
            'emergency_contact_phone': {
                'label': 'Emergency Contact Phone',
                'type': 'text'
            },
            
            # Additional Information
            'notes': {
                'label': 'Notes',
                'type': 'text'
            },
            'tags': {
                'label': 'Tags',
                'type': 'text'
            },
            'status': {
                'label': 'Status',
                'type': 'choice',
                'choices': ['Active', 'Inactive', 'Pending', 'Archived']
            }
        }
        
        self.search_widget = SearchWidget(field_definitions)
        self.splitter.addWidget(self.search_widget)
    
    def create_table_section(self):
        """Create the data table section."""
        # Define table columns - displaying ALL database fields
        columns = [
            # Basic Information
            ColumnConfig('id', 'ID', 100),
            ColumnConfig('title', 'Title', 60),
            ColumnConfig('first_name', 'First Name', 120),
            ColumnConfig('last_name', 'Last Name', 120),
            ColumnConfig('suffix', 'Suffix', 60),
            
            # Contact Information
            ColumnConfig('email', 'Email', 200),
            ColumnConfig('phone', 'Phone', 120),
            ColumnConfig('mobile', 'Mobile', 120),
            ColumnConfig('address', 'Address', 150),
            ColumnConfig('city', 'City', 100),
            ColumnConfig('state', 'State', 80),
            ColumnConfig('zip_code', 'ZIP Code', 80),
            ColumnConfig('country', 'Country', 100),
            
            # Personal Information
            ColumnConfig('date_of_birth', 'Date of Birth', 120, formatter=self.format_date),
            ColumnConfig('gender', 'Gender', 80),
            ColumnConfig('marital_status', 'Marital Status', 120),
            
            # Emergency Contact
            ColumnConfig('emergency_contact_name', 'Emergency Contact', 150),
            ColumnConfig('emergency_contact_phone', 'Emergency Phone', 120),
            
            # Additional Information
            ColumnConfig('notes', 'Notes', 200, formatter=self.format_notes),
            ColumnConfig('tags', 'Tags', 150, formatter=self.format_tags),
            ColumnConfig('status', 'Status', 80),
            
            # System Information
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
        self.data_table.item_selected.connect(self.on_person_selected)
        self.data_table.item_double_clicked.connect(self.on_person_double_clicked)
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
    
    def format_date(self, value: Any) -> str:
        """Format date for display."""
        if not value:
            return ""
        
        try:
            if isinstance(value, str):
                # Handle different date formats
                if '-' in value and len(value.split('-')[0]) == 4:  # ISO format
                    dt = datetime.fromisoformat(value).date()
                else:  # dd-mm-yyyy format
                    dt = datetime.strptime(value, '%d-%m-%Y').date()
                return dt.strftime('%d-%m-%Y')
            else:
                return value.strftime('%d-%m-%Y')
        except (ValueError, TypeError):
            return str(value)
    
    def format_notes(self, value: Any) -> str:
        """Format notes for display (truncate if too long)."""
        if not value:
            return ""
        
        text = str(value).strip()
        if len(text) > 100:
            return text[:97] + "..."
        return text
    
    def format_tags(self, value: Any) -> str:
        """Format tags for display."""
        if not value:
            return ""
        
        try:
            if isinstance(value, str):
                import json
                tags = json.loads(value)
                if isinstance(tags, list):
                    return ", ".join(tags)
                else:
                    return str(value)
            elif isinstance(value, list):
                return ", ".join(str(tag) for tag in value)
            else:
                return str(value)
        except (json.JSONDecodeError, TypeError):
            return str(value)
    
    def refresh_data(self):
        """Refresh people data."""
        self.api_service.list_people_async(
            page=self.current_page,
            page_size=self.page_size
        )
    
    def on_data_updated(self, data_type: str, data: Dict[str, Any]):
        """Handle data updates from API service."""
        if data_type == "people":
            self.update_people_data(data)
    
    def update_people_data(self, data: Dict[str, Any]):
        """Update the people table with new data."""
        try:
            items = data.get('items', [])
            self.current_people = items
            
            # Apply any current filters
            filtered_items = self.apply_filters(items)
            
            self.data_table.set_data(filtered_items)
            
        except Exception as e:
            logger.error(f"Error updating people data: {e}")
            QMessageBox.critical(self, "Error", f"Failed to update people data: {e}")
    
    def apply_filters(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply current search filters to items."""
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
        """Check if an item matches a search filter."""
        field_value = item.get(search_filter.field, '')
        filter_value = search_filter.value
        
        if field_value is None:
            field_value = ''
        
        # Handle quick search
        if search_filter.field == '_quick_search':
            # Search across multiple key fields
            search_fields = [
                'first_name', 'last_name', 'title', 'suffix', 'email', 
                'phone', 'mobile', 'city', 'state', 'country',
                'emergency_contact_name', 'notes', 'tags'
            ]
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
            elif search_filter.operator == 'starts_with':
                return field_str.startswith(filter_str)
            elif search_filter.operator == 'ends_with':
                return field_str.endswith(filter_str)
            elif search_filter.operator == 'not_contains':
                return filter_str not in field_str
            elif search_filter.operator == 'not_equals':
                return field_str != filter_str
        
        elif search_filter.field_type == 'choice':
            if search_filter.operator == 'equals':
                return field_value == filter_value
            elif search_filter.operator == 'not_equals':
                return field_value != filter_value
        
        # Add more filter type handling as needed
        
        return True
    
    def on_search_requested(self, filters: List[SearchFilter]):
        """Handle search request."""
        self.current_filters = filters
        self.current_page = 1
        
        # Apply filters to current data
        filtered_items = self.apply_filters(self.current_people)
        self.data_table.set_data(filtered_items)
    
    def on_filters_changed(self, filters: List[SearchFilter]):
        """Handle real-time filter changes."""
        self.current_filters = filters
        
        # Apply filters to current data
        filtered_items = self.apply_filters(self.current_people)
        self.data_table.set_data(filtered_items)
    
    def on_search_cleared(self):
        """Handle search cleared."""
        self.current_filters = []
        self.data_table.set_data(self.current_people)
    
    def on_person_selected(self, person_data: Dict[str, Any]):
        """Handle person selection."""
        self.selected_person = person_data
        self.edit_btn.setEnabled(True)
        self.delete_btn.setEnabled(True)
    
    def on_person_double_clicked(self, person_data: Dict[str, Any]):
        """Handle person double-click."""
        self.selected_person = person_data
        self.edit_person()
    
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
        if success:
            if operation in ['create_person', 'update_person', 'delete_person']:
                # Refresh data after person operations
                self.refresh_data()
                
                # Clear selection after delete
                if operation == 'delete_person':
                    self.selected_person = None
                    self.edit_btn.setEnabled(False)
                    self.delete_btn.setEnabled(False)
    
    def add_person(self):
        """Add a new person."""
        logger.debug("Opening add person dialog")
        dialog = PersonDialog(parent=self)
        
        if dialog.exec() == QDialog.Accepted:
            person_data = dialog.get_form_data()
            logger.debug(f"Creating new person: {person_data.get('first_name')} {person_data.get('last_name')}")
            self.api_service.create_person_async(person_data)
        else:
            logger.debug("Add person dialog cancelled")
    
    def edit_person(self):
        """Edit the selected person."""
        if not self.selected_person:
            return
        
        dialog = PersonDialog(self.selected_person, parent=self)
        
        if dialog.exec() == QDialog.Accepted:
            person_data = dialog.get_form_data()
            person_id = self.selected_person.get('id')
            
            if person_id:
                self.api_service.update_person_async(person_id, person_data)
    
    def delete_person(self):
        """Delete the selected person(s)."""
        selected_items = self.data_table.get_selected_data()
        
        if not selected_items:
            return
        
        count = len(selected_items)
        person_text = "person" if count == 1 else "people"
        
        reply = QMessageBox.question(
            self,
            f"Delete {person_text.title()}",
            f"Are you sure you want to delete {count} {person_text}?\n\n"
            "This action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            for person in selected_items:
                person_id = person.get('id')
                if person_id:
                    self.api_service.delete_person_async(person_id)
    
    def import_people(self):
        """Import people from file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import People",
            "",
            "CSV Files (*.csv);;JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            # TODO: Implement import functionality
            QMessageBox.information(
                self,
                "Import People",
                f"Import from {file_path} will be implemented soon."
            )
    
    def export_people(self):
        """Export people to file."""
        # Use the table's export functionality
        self.data_table.export_data('csv')
    
    def bulk_edit(self):
        """Bulk edit selected people."""
        selected_items = self.data_table.get_selected_data()
        
        if not selected_items:
            QMessageBox.information(
                self,
                "Bulk Edit",
                "Please select people to edit."
            )
            return
        
        # TODO: Implement bulk edit dialog
        QMessageBox.information(
            self,
            "Bulk Edit",
            f"Bulk edit for {len(selected_items)} people will be implemented soon."
        )
    
    def bulk_delete(self):
        """Bulk delete selected people."""
        self.delete_person()  # Same as regular delete, handles multiple selection
    
    def refresh(self):
        """Refresh the view."""
        self.refresh_data()
    
    def showEvent(self, event):
        """Handle show event."""
        super().showEvent(event)
        # Refresh data when view becomes visible
        if self.api_service.is_connected:
            self.refresh_data()