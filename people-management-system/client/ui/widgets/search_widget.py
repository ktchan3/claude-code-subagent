"""
Advanced Search Widget for People Management System Client

Provides a comprehensive search interface with filters, saved searches, and real-time search.
"""

import json
import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, date
from dataclasses import dataclass, asdict

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGridLayout,
    QLineEdit, QPushButton, QComboBox, QDateEdit, QCheckBox, QLabel,
    QFrame, QGroupBox, QSplitter, QListWidget, QListWidgetItem,
    QMessageBox, QMenu, QToolButton, QSpacerItem, QSizePolicy,
    QButtonGroup, QRadioButton, QSpinBox, QDoubleSpinBox, QTextEdit,
    QTabWidget, QScrollArea
)
from PySide6.QtCore import Qt, Signal, QDate, QTimer, QSettings
from PySide6.QtGui import QFont, QIcon, QAction

logger = logging.getLogger(__name__)


@dataclass
class SearchFilter:
    """Individual search filter definition."""
    field: str
    operator: str
    value: Any
    field_type: str = "text"  # text, number, date, boolean, choice


@dataclass
class SavedSearch:
    """Saved search configuration."""
    name: str
    filters: List[SearchFilter]
    created_at: datetime
    last_used: Optional[datetime] = None
    use_count: int = 0


class SearchWidget(QWidget):
    """Advanced search widget with filters and saved searches."""
    
    # Signals
    search_requested = Signal(list)  # List of SearchFilter objects
    filters_changed = Signal(list)  # Filters changed (for real-time search)
    search_cleared = Signal()  # Search was cleared
    
    def __init__(self, field_definitions: Dict[str, Dict[str, Any]], parent=None):
        """
        Initialize search widget.
        
        Args:
            field_definitions: Dict mapping field names to their definitions
            Format: {
                'field_name': {
                    'label': 'Display Name',
                    'type': 'text|number|date|boolean|choice',
                    'choices': [...] (for choice type),
                    'operators': [...] (optional, defaults based on type)
                }
            }
        """
        super().__init__(parent)
        
        self.field_definitions = field_definitions
        self.current_filters: List[SearchFilter] = []
        self.saved_searches: List[SavedSearch] = []
        self.real_time_search = True
        
        # Search delay timer for real-time search
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self._emit_search)
        self.search_delay = 500  # ms
        
        self.setup_ui()
        self.load_saved_searches()
    
    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Create main splitter
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)
        
        # Left side - Search form
        self.create_search_form(splitter)
        
        # Right side - Saved searches
        self.create_saved_searches_panel(splitter)
        
        # Set splitter sizes
        splitter.setSizes([400, 200])
        
        # Action buttons
        self.create_action_buttons(layout)
    
    def create_search_form(self, parent):
        """Create the main search form."""
        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)
        
        # Quick search
        self.create_quick_search(form_layout)
        
        # Advanced filters
        self.create_advanced_filters(form_layout)
        
        parent.addWidget(form_widget)
    
    def create_quick_search(self, layout: QVBoxLayout):
        """Create quick search section."""
        quick_group = QGroupBox("Quick Search")
        quick_layout = QHBoxLayout(quick_group)
        quick_layout.setContentsMargins(10, 15, 10, 10)  # Add proper margins
        quick_layout.setSpacing(8)  # Add spacing between elements
        
        # Search input
        self.quick_search_input = QLineEdit()
        self.quick_search_input.setPlaceholderText("Search across all fields...")
        self.quick_search_input.textChanged.connect(self.on_quick_search_changed)
        quick_layout.addWidget(self.quick_search_input)
        
        # Search button
        self.quick_search_btn = QPushButton("🔍")
        self.quick_search_btn.setToolTip("Search")
        self.quick_search_btn.clicked.connect(self.perform_quick_search)
        quick_layout.addWidget(self.quick_search_btn)
        
        # Clear button
        clear_btn = QPushButton("✖")
        clear_btn.setToolTip("Clear search")
        clear_btn.clicked.connect(self.clear_search)
        quick_layout.addWidget(clear_btn)
        
        layout.addWidget(quick_group)
    
    def create_advanced_filters(self, layout: QVBoxLayout):
        """Create advanced filters section."""
        filters_group = QGroupBox("Advanced Filters")
        filters_layout = QVBoxLayout(filters_group)
        filters_layout.setContentsMargins(10, 15, 10, 10)  # Add proper margins
        filters_layout.setSpacing(10)  # Add spacing between elements
        
        # Filter list container
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMaximumHeight(300)
        
        self.filters_container = QWidget()
        self.filters_layout = QVBoxLayout(self.filters_container)
        self.filters_layout.addStretch()
        
        scroll_area.setWidget(self.filters_container)
        filters_layout.addWidget(scroll_area)
        
        # Add filter button
        add_filter_layout = QHBoxLayout()
        self.add_filter_btn = QPushButton("+ Add Filter")
        self.add_filter_btn.clicked.connect(self.add_filter)
        add_filter_layout.addWidget(self.add_filter_btn)
        
        add_filter_layout.addStretch()
        filters_layout.addLayout(add_filter_layout)
        
        layout.addWidget(filters_group)
    
    def create_saved_searches_panel(self, parent):
        """Create saved searches panel."""
        saved_widget = QWidget()
        saved_layout = QVBoxLayout(saved_widget)
        
        # Header
        header_layout = QHBoxLayout()
        saved_label = QLabel("Saved Searches")
        font = QFont()
        font.setBold(True)
        saved_label.setFont(font)
        header_layout.addWidget(saved_label)
        
        header_layout.addStretch()
        
        # Save current search button
        self.save_search_btn = QPushButton("💾")
        self.save_search_btn.setToolTip("Save current search")
        self.save_search_btn.clicked.connect(self.save_current_search)
        header_layout.addWidget(self.save_search_btn)
        
        saved_layout.addLayout(header_layout)
        
        # Saved searches list
        self.saved_searches_list = QListWidget()
        self.saved_searches_list.itemDoubleClicked.connect(self.load_saved_search)
        self.saved_searches_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.saved_searches_list.customContextMenuRequested.connect(self.show_saved_search_context_menu)
        saved_layout.addWidget(self.saved_searches_list)
        
        parent.addWidget(saved_widget)
    
    def create_action_buttons(self, layout: QVBoxLayout):
        """Create action buttons."""
        button_layout = QHBoxLayout()
        
        # Real-time search toggle
        self.realtime_cb = QCheckBox("Real-time search")
        self.realtime_cb.setChecked(self.real_time_search)
        self.realtime_cb.toggled.connect(self.set_real_time_search)
        button_layout.addWidget(self.realtime_cb)
        
        button_layout.addStretch()
        
        # Clear all button
        self.clear_all_btn = QPushButton("Clear All")
        self.clear_all_btn.clicked.connect(self.clear_all_filters)
        button_layout.addWidget(self.clear_all_btn)
        
        # Search button
        self.search_btn = QPushButton("Search")
        self.search_btn.setDefault(True)
        self.search_btn.clicked.connect(self.perform_search)
        button_layout.addWidget(self.search_btn)
        
        layout.addLayout(button_layout)
    
    def add_filter(self, filter_data: Optional[SearchFilter] = None):
        """Add a new filter row."""
        filter_widget = self.create_filter_widget(filter_data)
        
        # Insert before the stretch
        insert_index = self.filters_layout.count() - 1
        self.filters_layout.insertWidget(insert_index, filter_widget)
        
        # Update filter count
        self.update_filter_visibility()
    
    def create_filter_widget(self, filter_data: Optional[SearchFilter] = None) -> QWidget:
        """Create a single filter widget."""
        filter_frame = QFrame()
        filter_frame.setFrameStyle(QFrame.StyledPanel)
        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.setContentsMargins(5, 5, 5, 5)
        
        # Field selector
        field_combo = QComboBox()
        field_combo.addItem("Select field...", "")
        for field_name, field_def in self.field_definitions.items():
            field_combo.addItem(field_def['label'], field_name)
        filter_layout.addWidget(field_combo)
        
        # Operator selector
        operator_combo = QComboBox()
        filter_layout.addWidget(operator_combo)
        
        # Value input (will be replaced based on field type)
        value_widget = QLineEdit()
        filter_layout.addWidget(value_widget)
        
        # Remove button
        remove_btn = QPushButton("✖")
        remove_btn.setToolTip("Remove filter")
        remove_btn.clicked.connect(lambda: self.remove_filter(filter_frame))
        filter_layout.addWidget(remove_btn)
        
        # Connect field change to update operators and value widget
        field_combo.currentTextChanged.connect(
            lambda: self.update_filter_widgets(field_combo, operator_combo, value_widget, filter_layout)
        )
        
        # Store references
        filter_frame.field_combo = field_combo
        filter_frame.operator_combo = operator_combo
        filter_frame.value_widget = value_widget
        
        # Set initial values if provided
        if filter_data:
            # Find and set field
            for i in range(field_combo.count()):
                if field_combo.itemData(i) == filter_data.field:
                    field_combo.setCurrentIndex(i)
                    break
            
            # Update widgets based on field
            self.update_filter_widgets(field_combo, operator_combo, value_widget, filter_layout)
            
            # Set operator
            for i in range(operator_combo.count()):
                if operator_combo.itemData(i) == filter_data.operator:
                    operator_combo.setCurrentIndex(i)
                    break
            
            # Set value
            self.set_filter_value(value_widget, filter_data.value, filter_data.field_type)
        
        # Connect change events for real-time search
        field_combo.currentTextChanged.connect(self.on_filter_changed)
        operator_combo.currentTextChanged.connect(self.on_filter_changed)
        
        return filter_frame
    
    def update_filter_widgets(self, field_combo: QComboBox, operator_combo: QComboBox, 
                            old_value_widget: QWidget, layout: QHBoxLayout):
        """Update operator and value widgets based on selected field."""
        field_name = field_combo.currentData()
        if not field_name:
            return
        
        field_def = self.field_definitions.get(field_name, {})
        field_type = field_def.get('type', 'text')
        
        # Update operators
        operator_combo.clear()
        operators = field_def.get('operators', self.get_default_operators(field_type))
        
        for op_key, op_label in operators.items():
            operator_combo.addItem(op_label, op_key)
        
        # Replace value widget
        new_value_widget = self.create_value_widget(field_type, field_def)
        
        # Replace in layout
        layout.replaceWidget(old_value_widget, new_value_widget)
        old_value_widget.deleteLater()
        
        # Update reference
        filter_frame = field_combo.parent()
        filter_frame.value_widget = new_value_widget
        
        # Connect change event
        self.connect_value_widget_signals(new_value_widget)
    
    def get_default_operators(self, field_type: str) -> Dict[str, str]:
        """Get default operators for a field type."""
        if field_type == 'text':
            return {
                'contains': 'Contains',
                'equals': 'Equals',
                'starts_with': 'Starts with',
                'ends_with': 'Ends with',
                'not_contains': 'Does not contain',
                'not_equals': 'Does not equal'
            }
        elif field_type == 'number':
            return {
                'equals': 'Equals',
                'not_equals': 'Does not equal',
                'greater_than': 'Greater than',
                'less_than': 'Less than',
                'greater_equal': 'Greater than or equal',
                'less_equal': 'Less than or equal',
                'between': 'Between'
            }
        elif field_type == 'date':
            return {
                'on': 'On date',
                'before': 'Before',
                'after': 'After',
                'between': 'Between dates'
            }
        elif field_type == 'boolean':
            return {
                'is_true': 'Is true',
                'is_false': 'Is false'
            }
        elif field_type == 'choice':
            return {
                'equals': 'Is',
                'not_equals': 'Is not',
                'in': 'Is one of'
            }
        else:
            return {'equals': 'Equals'}
    
    def create_value_widget(self, field_type: str, field_def: Dict[str, Any]) -> QWidget:
        """Create appropriate value input widget for field type."""
        if field_type == 'text':
            widget = QLineEdit()
            widget.setPlaceholderText("Enter text...")
            
        elif field_type == 'number':
            if field_def.get('decimal', False):
                widget = QDoubleSpinBox()
                widget.setRange(-999999.99, 999999.99)
                widget.setDecimals(2)
            else:
                widget = QSpinBox()
                widget.setRange(-999999, 999999)
            
        elif field_type == 'date':
            widget = QDateEdit()
            widget.setDate(QDate.currentDate())
            widget.setCalendarPopup(True)
            
        elif field_type == 'boolean':
            widget = QComboBox()
            widget.addItem("True", True)
            widget.addItem("False", False)
            
        elif field_type == 'choice':
            widget = QComboBox()
            choices = field_def.get('choices', [])
            for choice in choices:
                if isinstance(choice, dict):
                    widget.addItem(choice['label'], choice['value'])
                else:
                    widget.addItem(str(choice), choice)
                    
        else:
            widget = QLineEdit()
        
        return widget
    
    def connect_value_widget_signals(self, widget: QWidget):
        """Connect appropriate signals for value widget changes."""
        if isinstance(widget, QLineEdit):
            widget.textChanged.connect(self.on_filter_changed)
        elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
            widget.valueChanged.connect(self.on_filter_changed)
        elif isinstance(widget, QDateEdit):
            widget.dateChanged.connect(self.on_filter_changed)
        elif isinstance(widget, QComboBox):
            widget.currentTextChanged.connect(self.on_filter_changed)
    
    def set_filter_value(self, widget: QWidget, value: Any, field_type: str):
        """Set value in the appropriate widget."""
        if isinstance(widget, QLineEdit):
            widget.setText(str(value) if value is not None else '')
        elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
            if value is not None:
                widget.setValue(float(value))
        elif isinstance(widget, QDateEdit):
            if value:
                if isinstance(value, str):
                    date_obj = datetime.fromisoformat(value).date()
                else:
                    date_obj = value
                widget.setDate(QDate(date_obj))
        elif isinstance(widget, QComboBox):
            for i in range(widget.count()):
                if widget.itemData(i) == value:
                    widget.setCurrentIndex(i)
                    break
    
    def remove_filter(self, filter_widget: QWidget):
        """Remove a filter widget."""
        filter_widget.deleteLater()
        self.update_filter_visibility()
        self.on_filter_changed()
    
    def update_filter_visibility(self):
        """Update visibility of filter-related elements."""
        filter_count = self.get_filter_count()
        self.clear_all_btn.setEnabled(filter_count > 0)
    
    def get_filter_count(self) -> int:
        """Get number of active filters."""
        count = 0
        for i in range(self.filters_layout.count()):
            widget = self.filters_layout.itemAt(i).widget()
            if widget and hasattr(widget, 'field_combo'):
                count += 1
        return count
    
    def on_quick_search_changed(self):
        """Handle quick search text change."""
        if self.real_time_search:
            self.search_timer.stop()
            self.search_timer.start(self.search_delay)
    
    def on_filter_changed(self):
        """Handle filter change."""
        if self.real_time_search:
            self.search_timer.stop()
            self.search_timer.start(self.search_delay)
    
    def perform_quick_search(self):
        """Perform quick search."""
        query = self.quick_search_input.text().strip()
        if query:
            # Create a general search filter
            filters = [SearchFilter(
                field='_quick_search',
                operator='contains',
                value=query,
                field_type='text'
            )]
            self.search_requested.emit(filters)
        else:
            self.clear_search()
    
    def perform_search(self):
        """Perform advanced search."""
        filters = self.collect_filters()
        if filters:
            self.search_requested.emit(filters)
        else:
            self.search_cleared.emit()
    
    def _emit_search(self):
        """Emit search with current filters (for real-time search)."""
        filters = self.collect_filters()
        self.filters_changed.emit(filters)
    
    def collect_filters(self) -> List[SearchFilter]:
        """Collect all current filters."""
        filters = []
        
        # Quick search
        quick_query = self.quick_search_input.text().strip()
        if quick_query:
            filters.append(SearchFilter(
                field='_quick_search',
                operator='contains',
                value=quick_query,
                field_type='text'
            ))
        
        # Advanced filters
        for i in range(self.filters_layout.count()):
            widget = self.filters_layout.itemAt(i).widget()
            if widget and hasattr(widget, 'field_combo'):
                field_name = widget.field_combo.currentData()
                operator = widget.operator_combo.currentData()
                
                if field_name and operator:
                    value = self.get_widget_value(widget.value_widget)
                    field_def = self.field_definitions.get(field_name, {})
                    field_type = field_def.get('type', 'text')
                    
                    if value is not None and value != '':
                        filters.append(SearchFilter(
                            field=field_name,
                            operator=operator,
                            value=value,
                            field_type=field_type
                        ))
        
        return filters
    
    def get_widget_value(self, widget: QWidget) -> Any:
        """Get value from widget."""
        if isinstance(widget, QLineEdit):
            return widget.text().strip()
        elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
            return widget.value()
        elif isinstance(widget, QDateEdit):
            return widget.date().toPython()
        elif isinstance(widget, QComboBox):
            return widget.currentData()
        else:
            return None
    
    def clear_search(self):
        """Clear quick search."""
        self.quick_search_input.clear()
        self.search_cleared.emit()
    
    def clear_all_filters(self):
        """Clear all filters."""
        # Clear quick search
        self.quick_search_input.clear()
        
        # Remove all filter widgets
        for i in reversed(range(self.filters_layout.count())):
            item = self.filters_layout.itemAt(i)
            if item.widget() and hasattr(item.widget(), 'field_combo'):
                item.widget().deleteLater()
        
        self.update_filter_visibility()
        self.search_cleared.emit()
    
    def set_real_time_search(self, enabled: bool):
        """Enable/disable real-time search."""
        self.real_time_search = enabled
        self.search_btn.setEnabled(not enabled)
    
    def save_current_search(self):
        """Save current search configuration."""
        filters = self.collect_filters()
        if not filters:
            QMessageBox.information(self, "Save Search", "No filters to save.")
            return
        
        # Get search name from user
        from PySide6.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(self, "Save Search", "Enter search name:")
        
        if ok and name.strip():
            saved_search = SavedSearch(
                name=name.strip(),
                filters=filters,
                created_at=datetime.now()
            )
            
            self.saved_searches.append(saved_search)
            self.update_saved_searches_list()
            self.save_searches_to_settings()
    
    def load_saved_search(self, item: QListWidgetItem):
        """Load a saved search."""
        search_name = item.text()
        saved_search = next((s for s in self.saved_searches if s.name == search_name), None)
        
        if saved_search:
            # Clear current filters
            self.clear_all_filters()
            
            # Load filters
            for filter_data in saved_search.filters:
                if filter_data.field == '_quick_search':
                    self.quick_search_input.setText(str(filter_data.value))
                else:
                    self.add_filter(filter_data)
            
            # Update usage statistics
            saved_search.last_used = datetime.now()
            saved_search.use_count += 1
            
            # Perform search
            self.perform_search()
            
            self.save_searches_to_settings()
    
    def show_saved_search_context_menu(self, position):
        """Show context menu for saved searches."""
        item = self.saved_searches_list.itemAt(position)
        if not item:
            return
        
        menu = QMenu(self)
        
        load_action = QAction("Load Search", self)
        load_action.triggered.connect(lambda: self.load_saved_search(item))
        menu.addAction(load_action)
        
        menu.addSeparator()
        
        rename_action = QAction("Rename", self)
        rename_action.triggered.connect(lambda: self.rename_saved_search(item))
        menu.addAction(rename_action)
        
        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(lambda: self.delete_saved_search(item))
        menu.addAction(delete_action)
        
        menu.exec(self.saved_searches_list.mapToGlobal(position))
    
    def rename_saved_search(self, item: QListWidgetItem):
        """Rename a saved search."""
        old_name = item.text()
        saved_search = next((s for s in self.saved_searches if s.name == old_name), None)
        
        if saved_search:
            from PySide6.QtWidgets import QInputDialog
            new_name, ok = QInputDialog.getText(
                self, "Rename Search", "Enter new name:", text=old_name
            )
            
            if ok and new_name.strip() and new_name.strip() != old_name:
                saved_search.name = new_name.strip()
                self.update_saved_searches_list()
                self.save_searches_to_settings()
    
    def delete_saved_search(self, item: QListWidgetItem):
        """Delete a saved search."""
        search_name = item.text()
        
        reply = QMessageBox.question(
            self, "Delete Search",
            f"Are you sure you want to delete the search '{search_name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.saved_searches = [s for s in self.saved_searches if s.name != search_name]
            self.update_saved_searches_list()
            self.save_searches_to_settings()
    
    def update_saved_searches_list(self):
        """Update the saved searches list widget."""
        self.saved_searches_list.clear()
        
        # Sort by last used, then by name
        sorted_searches = sorted(
            self.saved_searches,
            key=lambda s: (s.last_used or datetime.min, s.name),
            reverse=True
        )
        
        for search in sorted_searches:
            item_text = search.name
            if search.use_count > 0:
                item_text += f" ({search.use_count})"
            
            item = QListWidgetItem(item_text)
            item.setToolTip(f"Created: {search.created_at.strftime('%Y-%m-%d %H:%M')}")
            self.saved_searches_list.addItem(item)
    
    def save_searches_to_settings(self):
        """Save searches to QSettings."""
        settings = QSettings()
        searches_data = []
        
        for search in self.saved_searches:
            search_dict = asdict(search)
            # Convert datetime objects to strings
            search_dict['created_at'] = search.created_at.isoformat()
            if search.last_used:
                search_dict['last_used'] = search.last_used.isoformat()
            searches_data.append(search_dict)
        
        settings.setValue("saved_searches", json.dumps(searches_data))
    
    def load_saved_searches(self):
        """Load saved searches from QSettings."""
        settings = QSettings()
        searches_json = settings.value("saved_searches", "[]")
        
        try:
            searches_data = json.loads(searches_json)
            self.saved_searches = []
            
            for search_dict in searches_data:
                # Convert strings back to datetime objects
                search_dict['created_at'] = datetime.fromisoformat(search_dict['created_at'])
                if search_dict.get('last_used'):
                    search_dict['last_used'] = datetime.fromisoformat(search_dict['last_used'])
                
                # Convert filter dictionaries to SearchFilter objects
                filters = []
                for filter_dict in search_dict['filters']:
                    filters.append(SearchFilter(**filter_dict))
                search_dict['filters'] = filters
                
                self.saved_searches.append(SavedSearch(**search_dict))
            
            self.update_saved_searches_list()
            
        except Exception as e:
            logger.error(f"Error loading saved searches: {e}")
    
    def set_filters(self, filters: List[SearchFilter]):
        """Set filters programmatically."""
        self.clear_all_filters()
        
        for filter_data in filters:
            if filter_data.field == '_quick_search':
                self.quick_search_input.setText(str(filter_data.value))
            else:
                self.add_filter(filter_data)
    
    def get_filters(self) -> List[SearchFilter]:
        """Get current filters."""
        return self.collect_filters()