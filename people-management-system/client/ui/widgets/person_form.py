"""
Person Form Widget for People Management System Client

Provides a comprehensive form for creating and editing person records with validation.
"""

import re
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, date

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGridLayout,
    QLineEdit, QPushButton, QTextEdit, QDateEdit, QLabel, QFrame,
    QGroupBox, QScrollArea, QMessageBox, QCompleter, QComboBox,
    QCheckBox, QSpinBox, QTabWidget, QFileDialog, QProgressBar,
    QSizePolicy, QSpacerItem
)
from PySide6.QtCore import Qt, Signal, QDate, QRegularExpression, QTimer
from PySide6.QtGui import (
    QFont, QPixmap, QValidator, QRegularExpressionValidator,
    QPalette, QColor, QIcon
)

logger = logging.getLogger(__name__)


class EmailValidator(QValidator):
    """Email address validator that allows smooth typing of all valid email characters."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # Complete email regex for final validation - allows single char TLD for testing
        self.email_regex = QRegularExpression(r'^[a-zA-Z0-9.!#$%&\'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*\.[a-zA-Z]{1,}$')
        
        # Character set for valid email characters (permissive during typing)
        self.valid_chars_regex = QRegularExpression(r'^[a-zA-Z0-9.!#$%&\'*+/=?^_`{|}~@-]*$')
    
    def validate(self, input_text: str, pos: int):
        """
        Validate email input with permissive typing approach.
        
        Returns:
        - Acceptable: Complete valid email address
        - Intermediate: Partial input or valid characters being typed
        - Invalid: Only for truly invalid characters (should rarely happen)
        """
        if not input_text:
            return QValidator.Intermediate, input_text, pos
        
        # First check if input contains only valid email characters
        if not self.valid_chars_regex.match(input_text).hasMatch():
            return QValidator.Invalid, input_text, pos
        
        # Check if it's a complete, valid email
        if self.email_regex.match(input_text).hasMatch():
            return QValidator.Acceptable, input_text, pos
        
        # For partial input, be permissive to allow smooth typing
        # Allow any partial input with valid characters
        return QValidator.Intermediate, input_text, pos


class PhoneValidator(QValidator):
    """Phone number validator."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # Allow various phone number formats
        self.phone_regex = QRegularExpression(r'^[\+]?[1-9][\d\s\-\(\)]{7,15}$')
    
    def validate(self, input_text: str, pos: int):
        if not input_text:
            return QValidator.Intermediate, input_text, pos
        
        if self.phone_regex.match(input_text).hasMatch():
            return QValidator.Acceptable, input_text, pos
        else:
            return QValidator.Intermediate, input_text, pos


class PersonForm(QWidget):
    """
    Comprehensive form for creating and editing person records.
    
    Features:
    - Form validation with visual feedback
    - Auto-save functionality
    - Photo upload support
    - Address completion
    - Custom field support
    """
    
    # Signals
    data_changed = Signal(dict)  # Form data changed (for auto-save)
    validation_changed = Signal(bool)  # Form validation status changed
    save_requested = Signal(dict)  # Save button clicked with form data
    cancel_requested = Signal()  # Cancel button clicked
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.person_data: Optional[Dict[str, Any]] = None
        self.is_editing = False
        self.auto_save_enabled = True
        self.validation_errors: Dict[str, str] = {}
        
        # Auto-save timer
        self.auto_save_timer = QTimer()
        self.auto_save_timer.setSingleShot(True)
        self.auto_save_timer.timeout.connect(self.emit_data_changed)
        self.auto_save_delay = 1000  # 1 second
        
        self.setup_ui()
        self.setup_validation()
        self.setup_connections()
    
    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Create scroll area for the form
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Main form widget
        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)
        form_layout.setSpacing(15)
        
        # Create form sections
        self.create_basic_info_section(form_layout)
        self.create_contact_info_section(form_layout)
        self.create_personal_info_section(form_layout)
        self.create_additional_info_section(form_layout)
        
        # Add stretch to push everything up
        form_layout.addStretch()
        
        scroll_area.setWidget(form_widget)
        layout.addWidget(scroll_area)
        
        # Action buttons
        self.action_buttons_widget = self.create_action_buttons(layout)
        
        # Status bar
        self.create_status_bar(layout)
    
    def create_basic_info_section(self, layout: QVBoxLayout):
        """Create basic information section."""
        basic_group = QGroupBox("Basic Information")
        basic_layout = QFormLayout(basic_group)
        basic_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        
        # First name (required)
        self.first_name_edit = QLineEdit()
        self.first_name_edit.setPlaceholderText("Enter first name")
        basic_layout.addRow("First Name *:", self.first_name_edit)
        
        # Last name (required)
        self.last_name_edit = QLineEdit()
        self.last_name_edit.setPlaceholderText("Enter last name")
        basic_layout.addRow("Last Name *:", self.last_name_edit)
        
        # Full name (auto-generated, read-only)
        self.full_name_label = QLabel()
        self.full_name_label.setStyleSheet("font-weight: bold; color: #666;")
        basic_layout.addRow("Full Name:", self.full_name_label)
        
        # Title/Prefix
        self.title_combo = QComboBox()
        self.title_combo.setEditable(True)
        self.title_combo.addItems(["", "Mr.", "Ms.", "Mrs.", "Dr.", "Prof."])
        basic_layout.addRow("Title:", self.title_combo)
        
        # Suffix
        self.suffix_edit = QLineEdit()
        self.suffix_edit.setPlaceholderText("Jr., Sr., III, etc.")
        basic_layout.addRow("Suffix:", self.suffix_edit)
        
        layout.addWidget(basic_group)
    
    def create_contact_info_section(self, layout: QVBoxLayout):
        """Create contact information section."""
        contact_group = QGroupBox("Contact Information")
        contact_layout = QFormLayout(contact_group)
        contact_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        
        # Email (required)
        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("Enter email address")
        contact_layout.addRow("Email Address *:", self.email_edit)
        
        # Phone
        self.phone_edit = QLineEdit()
        self.phone_edit.setPlaceholderText("Enter phone number")
        contact_layout.addRow("Phone Number:", self.phone_edit)
        
        # Mobile
        self.mobile_edit = QLineEdit()
        self.mobile_edit.setPlaceholderText("Enter mobile number")
        contact_layout.addRow("Mobile Number:", self.mobile_edit)
        
        # Address
        self.address_edit = QTextEdit()
        self.address_edit.setPlaceholderText("Enter full address")
        self.address_edit.setMaximumHeight(100)
        contact_layout.addRow("Address:", self.address_edit)
        
        # City, State, Zip in a row
        location_layout = QHBoxLayout()
        
        self.city_edit = QLineEdit()
        self.city_edit.setPlaceholderText("City")
        location_layout.addWidget(self.city_edit)
        
        self.state_edit = QLineEdit()
        self.state_edit.setPlaceholderText("State/Province")
        location_layout.addWidget(self.state_edit)
        
        self.zip_edit = QLineEdit()
        self.zip_edit.setPlaceholderText("ZIP/Postal Code")
        location_layout.addWidget(self.zip_edit)
        
        contact_layout.addRow("City, State, ZIP:", location_layout)
        
        # Country
        self.country_combo = QComboBox()
        self.country_combo.setEditable(True)
        self.populate_countries()
        contact_layout.addRow("Country:", self.country_combo)
        
        layout.addWidget(contact_group)
    
    def create_personal_info_section(self, layout: QVBoxLayout):
        """Create personal information section."""
        personal_group = QGroupBox("Personal Information")
        personal_layout = QFormLayout(personal_group)
        personal_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        
        # Date of birth
        self.dob_edit = QDateEdit()
        self.dob_edit.setDate(QDate.currentDate().addYears(-25))
        self.dob_edit.setCalendarPopup(True)
        self.dob_edit.setMaximumDate(QDate.currentDate())
        # Set display format to dd-mm-yyyy
        self.dob_edit.setDisplayFormat("dd-MM-yyyy")
        personal_layout.addRow("Date of Birth:", self.dob_edit)
        
        # Age (auto-calculated)
        self.age_label = QLabel("0 years")
        self.age_label.setStyleSheet("color: #666;")
        personal_layout.addRow("Age:", self.age_label)
        
        # Gender
        self.gender_combo = QComboBox()
        self.gender_combo.addItems(["", "Male", "Female", "Other", "Prefer not to say"])
        personal_layout.addRow("Gender:", self.gender_combo)
        
        # Marital status
        self.marital_status_combo = QComboBox()
        self.marital_status_combo.addItems([
            "", "Single", "Married", "Divorced", "Widowed", "Separated"
        ])
        personal_layout.addRow("Marital Status:", self.marital_status_combo)
        
        # Emergency contact
        emergency_layout = QHBoxLayout()
        
        self.emergency_name_edit = QLineEdit()
        self.emergency_name_edit.setPlaceholderText("Emergency contact name")
        emergency_layout.addWidget(self.emergency_name_edit)
        
        self.emergency_phone_edit = QLineEdit()
        self.emergency_phone_edit.setPlaceholderText("Emergency contact phone")
        emergency_layout.addWidget(self.emergency_phone_edit)
        
        personal_layout.addRow("Emergency Contact:", emergency_layout)
        
        layout.addWidget(personal_group)
    
    def create_additional_info_section(self, layout: QVBoxLayout):
        """Create additional information section."""
        additional_group = QGroupBox("Additional Information")
        additional_layout = QFormLayout(additional_group)
        additional_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        
        # Notes
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Additional notes or comments...")
        self.notes_edit.setMaximumHeight(120)
        additional_layout.addRow("Notes:", self.notes_edit)
        
        # Tags/Categories
        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText("Tags separated by commas (e.g., VIP, Client, Vendor)")
        additional_layout.addRow("Tags:", self.tags_edit)
        
        # Status
        self.status_combo = QComboBox()
        self.status_combo.addItems(["Active", "Inactive", "Pending", "Archived"])
        additional_layout.addRow("Status:", self.status_combo)
        
        # Created/Modified info (read-only)
        self.created_label = QLabel("-")
        self.created_label.setStyleSheet("color: #666; font-size: 9pt;")
        additional_layout.addRow("Created:", self.created_label)
        
        self.modified_label = QLabel("-")
        self.modified_label.setStyleSheet("color: #666; font-size: 9pt;")
        additional_layout.addRow("Last Modified:", self.modified_label)
        
        layout.addWidget(additional_group)
    
    def create_action_buttons(self, layout: QVBoxLayout):
        """Create action buttons."""
        # Create a widget to hold the buttons so we can show/hide it
        button_widget = QWidget()
        button_layout = QHBoxLayout(button_widget)
        
        # Auto-save indicator
        self.auto_save_label = QLabel("")
        self.auto_save_label.setStyleSheet("color: #666; font-style: italic;")
        button_layout.addWidget(self.auto_save_label)
        
        # Spacer
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
        self.save_btn.clicked.connect(self.save_person)
        button_layout.addWidget(self.save_btn)
        
        layout.addWidget(button_widget)
        return button_widget
    
    def create_status_bar(self, layout: QVBoxLayout):
        """Create status bar with validation messages."""
        self.status_frame = QFrame()
        self.status_frame.setFrameStyle(QFrame.StyledPanel)
        self.status_frame.setVisible(False)
        
        status_layout = QHBoxLayout(self.status_frame)
        status_layout.setContentsMargins(10, 5, 10, 5)
        
        # Status icon
        self.status_icon = QLabel()
        status_layout.addWidget(self.status_icon)
        
        # Status message
        self.status_message = QLabel()
        self.status_message.setWordWrap(True)
        status_layout.addWidget(self.status_message)
        
        # Close button
        close_btn = QPushButton("✖")
        close_btn.setMaximumSize(20, 20)
        close_btn.clicked.connect(lambda: self.status_frame.setVisible(False))
        status_layout.addWidget(close_btn)
        
        layout.addWidget(self.status_frame)
    
    def populate_countries(self):
        """Populate country dropdown."""
        countries = [
            "", "United States", "Canada", "United Kingdom", "Australia",
            "Germany", "France", "Italy", "Spain", "Netherlands",
            "Sweden", "Norway", "Denmark", "Japan", "South Korea",
            "China", "India", "Brazil", "Mexico", "Argentina"
        ]
        self.country_combo.addItems(countries)
        self.country_combo.setCurrentText("United States")
    
    def setup_validation(self):
        """Set up form validation."""
        # Email validator
        self.email_edit.setValidator(EmailValidator())
        
        # Phone validators
        phone_validator = PhoneValidator()
        self.phone_edit.setValidator(phone_validator)
        self.mobile_edit.setValidator(phone_validator)
        self.emergency_phone_edit.setValidator(phone_validator)
    
    def setup_connections(self):
        """Set up signal connections."""
        # Auto-update full name
        self.first_name_edit.textChanged.connect(self.update_full_name)
        self.last_name_edit.textChanged.connect(self.update_full_name)
        self.title_combo.currentTextChanged.connect(self.update_full_name)
        self.suffix_edit.textChanged.connect(self.update_full_name)
        
        # Auto-calculate age
        self.dob_edit.dateChanged.connect(self.update_age)
        
        # Form change detection for auto-save
        form_widgets = [
            self.first_name_edit, self.last_name_edit, self.title_combo,
            self.suffix_edit, self.email_edit, self.phone_edit, self.mobile_edit,
            self.address_edit, self.city_edit, self.state_edit, self.zip_edit,
            self.country_combo, self.dob_edit, self.gender_combo,
            self.marital_status_combo, self.emergency_name_edit,
            self.emergency_phone_edit, self.notes_edit, self.tags_edit,
            self.status_combo
        ]
        
        for widget in form_widgets:
            if hasattr(widget, 'textChanged'):
                widget.textChanged.connect(self.on_form_changed)
            elif hasattr(widget, 'currentTextChanged'):
                widget.currentTextChanged.connect(self.on_form_changed)
            elif hasattr(widget, 'dateChanged'):
                widget.dateChanged.connect(self.on_form_changed)
        
        # Validation on text change
        self.first_name_edit.textChanged.connect(self.validate_form)
        self.last_name_edit.textChanged.connect(self.validate_form)
        self.email_edit.textChanged.connect(self.validate_form)
    
    def update_full_name(self):
        """Update the full name display."""
        parts = []
        
        title = self.title_combo.currentText().strip()
        if title:
            parts.append(title)
        
        first_name = self.first_name_edit.text().strip()
        if first_name:
            parts.append(first_name)
        
        last_name = self.last_name_edit.text().strip()
        if last_name:
            parts.append(last_name)
        
        suffix = self.suffix_edit.text().strip()
        if suffix:
            parts.append(suffix)
        
        full_name = " ".join(parts)
        self.full_name_label.setText(full_name or "—")
    
    def update_age(self):
        """Update the age display."""
        birth_date = self.dob_edit.date().toPython()
        today = date.today()
        
        age = today.year - birth_date.year
        if today.month < birth_date.month or (today.month == birth_date.month and today.day < birth_date.day):
            age -= 1
        
        self.age_label.setText(f"{age} years")
    
    def on_form_changed(self):
        """Handle form changes for auto-save."""
        if self.auto_save_enabled:
            self.auto_save_timer.stop()
            self.auto_save_timer.start(self.auto_save_delay)
            self.auto_save_label.setText("Auto-saving...")
    
    def emit_data_changed(self):
        """Emit data changed signal with current form data."""
        self.auto_save_label.setText("Auto-saved")
        QTimer.singleShot(2000, lambda: self.auto_save_label.setText(""))
        
        data = self.get_form_data()
        self.data_changed.emit(data)
    
    def validate_form(self) -> bool:
        """Validate the form and return True if valid."""
        self.validation_errors.clear()
        
        # Required fields
        if not self.first_name_edit.text().strip():
            self.validation_errors['first_name'] = "First name is required"
        
        if not self.last_name_edit.text().strip():
            self.validation_errors['last_name'] = "Last name is required"
        
        if not self.email_edit.text().strip():
            self.validation_errors['email'] = "Email address is required"
        elif not self.email_edit.hasAcceptableInput():
            self.validation_errors['email'] = "Please enter a valid email address"
        
        # Phone validation (if provided)
        if self.phone_edit.text().strip() and not self.phone_edit.hasAcceptableInput():
            self.validation_errors['phone'] = "Please enter a valid phone number"
        
        if self.mobile_edit.text().strip() and not self.mobile_edit.hasAcceptableInput():
            self.validation_errors['mobile'] = "Please enter a valid mobile number"
        
        # Visual feedback
        self.apply_validation_styling()
        
        is_valid = len(self.validation_errors) == 0
        self.save_btn.setEnabled(is_valid)
        
        # Show/hide status message
        if self.validation_errors:
            self.show_validation_errors()
        else:
            self.status_frame.setVisible(False)
        
        self.validation_changed.emit(is_valid)
        return is_valid
    
    def apply_validation_styling(self):
        """Apply visual styling based on validation results."""
        # Reset all styles first
        widgets_to_style = {
            'first_name': self.first_name_edit,
            'last_name': self.last_name_edit,
            'email': self.email_edit,
            'phone': self.phone_edit,
            'mobile': self.mobile_edit
        }
        
        for field, widget in widgets_to_style.items():
            if field in self.validation_errors:
                widget.setStyleSheet("border: 2px solid red;")
            else:
                widget.setStyleSheet("")
    
    def show_validation_errors(self):
        """Show validation errors in status bar."""
        error_messages = list(self.validation_errors.values())
        message = "; ".join(error_messages)
        
        self.status_icon.setText("⚠️")
        self.status_message.setText(message)
        self.status_message.setStyleSheet("color: red;")
        self.status_frame.setVisible(True)
    
    def get_form_data(self) -> Dict[str, Any]:
        """Get current form data as dictionary."""
        data = {
            'first_name': self.first_name_edit.text().strip(),
            'last_name': self.last_name_edit.text().strip(),
            'email': self.email_edit.text().strip(),
            'phone': self.phone_edit.text().strip() or None,
            'mobile': self.mobile_edit.text().strip() or None,
            'address': self.address_edit.toPlainText().strip() or None,
            'city': self.city_edit.text().strip() or None,
            'state': self.state_edit.text().strip() or None,
            'zip_code': self.zip_edit.text().strip() or None,
            'country': self.country_combo.currentText().strip() or None,
            'date_of_birth': self.dob_edit.date().toPython().strftime('%d-%m-%Y') if self.dob_edit.date().isValid() else None,
            'gender': self.gender_combo.currentText().strip() or None,
            'marital_status': self.marital_status_combo.currentText().strip() or None,
            'emergency_contact_name': self.emergency_name_edit.text().strip() or None,
            'emergency_contact_phone': self.emergency_phone_edit.text().strip() or None,
            'notes': self.notes_edit.toPlainText().strip() or None,
            'tags': [tag.strip() for tag in self.tags_edit.text().split(',') if tag.strip()],
            'status': self.status_combo.currentText().strip(),
            'title': self.title_combo.currentText().strip() or None,
            'suffix': self.suffix_edit.text().strip() or None
        }
        
        # Include ID if editing existing record
        if self.person_data and self.person_data.get('id'):
            data['id'] = self.person_data['id']
        
        # Debug logging
        logger.info('=== FORM DATA BEING SENT ===')
        logger.info(f'First Name: {data.get("first_name")}')
        logger.info(f'Last Name: {data.get("last_name")}')
        logger.info(f'Title: {data.get("title")}')
        logger.info(f'Suffix: {data.get("suffix")}')
        logger.info(f'Email: {data.get("email")}')
        logger.info('==========================')
        
        return data
    
    def set_form_data(self, data: Dict[str, Any]):
        """Set form data from dictionary."""
        self.person_data = data
        self.is_editing = bool(data.get('id'))
        
        # Block signals during data loading
        self.blockSignals(True)
        
        try:
            # Basic info
            self.first_name_edit.setText(data.get('first_name', ''))
            self.last_name_edit.setText(data.get('last_name', ''))
            self.title_combo.setCurrentText(data.get('title', ''))
            self.suffix_edit.setText(data.get('suffix', ''))
            
            # Contact info
            self.email_edit.setText(data.get('email', ''))
            self.phone_edit.setText(data.get('phone', ''))
            self.mobile_edit.setText(data.get('mobile', ''))
            self.address_edit.setText(data.get('address', ''))
            self.city_edit.setText(data.get('city', ''))
            self.state_edit.setText(data.get('state', ''))
            self.zip_edit.setText(data.get('zip_code', ''))
            self.country_combo.setCurrentText(data.get('country', ''))
            
            # Personal info
            if data.get('date_of_birth'):
                try:
                    # Try to parse as dd-mm-yyyy format first
                    birth_date = datetime.strptime(data['date_of_birth'], '%d-%m-%Y').date()
                    self.dob_edit.setDate(QDate(birth_date))
                except (ValueError, TypeError):
                    try:
                        # Fall back to ISO format for backward compatibility
                        birth_date = datetime.fromisoformat(data['date_of_birth']).date()
                        self.dob_edit.setDate(QDate(birth_date))
                    except (ValueError, TypeError):
                        pass
            
            self.gender_combo.setCurrentText(data.get('gender', ''))
            self.marital_status_combo.setCurrentText(data.get('marital_status', ''))
            self.emergency_name_edit.setText(data.get('emergency_contact_name', ''))
            self.emergency_phone_edit.setText(data.get('emergency_contact_phone', ''))
            
            # Additional info
            self.notes_edit.setText(data.get('notes', ''))
            tags = data.get('tags', [])
            if isinstance(tags, list):
                self.tags_edit.setText(', '.join(tags))
            else:
                self.tags_edit.setText(str(tags))
            
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
        
        finally:
            self.blockSignals(False)
            
            # Update calculated fields
            self.update_full_name()
            self.update_age()
            
            # Validate form
            self.validate_form()
    
    def clear_form(self):
        """Clear all form fields."""
        self.person_data = None
        self.is_editing = False
        
        # Clear all input fields
        # findChildren doesn't accept tuple of types in PySide6, so we need to call separately
        widgets = []
        widgets.extend(self.findChildren(QLineEdit))
        widgets.extend(self.findChildren(QTextEdit))  
        widgets.extend(self.findChildren(QComboBox))
        
        for widget in widgets:
            if isinstance(widget, (QLineEdit, QTextEdit)):
                widget.clear()
            elif isinstance(widget, QComboBox):
                widget.setCurrentIndex(0)
        
        # Reset date to default
        self.dob_edit.setDate(QDate.currentDate().addYears(-25))
        
        # Reset metadata labels
        self.created_label.setText("-")
        self.modified_label.setText("-")
        
        # Update calculated fields
        self.update_full_name()
        self.update_age()
        
        # Clear validation
        self.validation_errors.clear()
        self.apply_validation_styling()
        self.status_frame.setVisible(False)
    
    def reset_form(self):
        """Reset form to original data."""
        if self.person_data:
            self.set_form_data(self.person_data)
        else:
            self.clear_form()
    
    def save_person(self):
        """Save person data."""
        logger.debug("Save person requested")
        
        if self.validate_form():
            data = self.get_form_data()
            logger.debug(f"Form is valid, saving person data: {data.get('first_name')} {data.get('last_name')}")
            
            # Add ID if editing
            if self.is_editing and self.person_data:
                data['id'] = self.person_data.get('id')
                logger.debug(f"Editing existing person with ID: {data['id']}")
            else:
                logger.debug("Creating new person")
            
            self.save_requested.emit(data)
            logger.debug("save_requested signal emitted")
        else:
            logger.debug(f"Form validation failed with errors: {self.validation_errors}")
            # Show validation errors if not already shown
            if self.validation_errors:
                self.show_validation_errors()
    
    def set_auto_save_enabled(self, enabled: bool):
        """Enable/disable auto-save functionality."""
        self.auto_save_enabled = enabled
        if not enabled:
            self.auto_save_timer.stop()
            self.auto_save_label.setText("")
    
    def set_action_buttons_visible(self, visible: bool):
        """Show/hide the action buttons (Save, Cancel, Reset)."""
        if hasattr(self, 'action_buttons_widget'):
            self.action_buttons_widget.setVisible(visible)
    
    def get_validation_errors(self) -> Dict[str, str]:
        """Get current validation errors."""
        return self.validation_errors.copy()
    
    def is_form_valid(self) -> bool:
        """Check if form is currently valid."""
        return self.validate_form()
    
    def has_unsaved_changes(self) -> bool:
        """Check if form has unsaved changes."""
        if not self.person_data:
            # New person - check if any required fields are filled
            return bool(self.first_name_edit.text().strip() or 
                       self.last_name_edit.text().strip() or 
                       self.email_edit.text().strip())
        
        current_data = self.get_form_data()
        
        # Compare with original data (excluding metadata)
        compare_fields = [
            'first_name', 'last_name', 'email', 'phone', 'mobile',
            'address', 'city', 'state', 'zip_code', 'country',
            'date_of_birth', 'gender', 'marital_status',
            'emergency_contact_name', 'emergency_contact_phone',
            'notes', 'tags', 'status', 'title', 'suffix'
        ]
        
        for field in compare_fields:
            current_value = current_data.get(field)
            original_value = self.person_data.get(field)
            
            # Handle None vs empty string
            if current_value != original_value:
                if not (not current_value and not original_value):
                    return True
        
        return False