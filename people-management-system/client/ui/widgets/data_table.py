"""
Reusable Data Table Widget for People Management System Client

Provides a feature-rich table widget with pagination, sorting, filtering, and export capabilities.
"""

import csv
import json
import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QComboBox, QSpinBox, QProgressBar, QHeaderView,
    QMenu, QMessageBox, QFileDialog, QCheckBox, QFrame, QSplitter,
    QAbstractItemView, QApplication
)
from PySide6.QtCore import Qt, Signal, QThread, QTimer, QMimeData
from PySide6.QtGui import QFont, QColor, QAction, QClipboard

logger = logging.getLogger(__name__)


class ExportWorker(QThread):
    """Worker thread for exporting data."""
    
    # Signals
    progress = Signal(int)  # Progress percentage
    finished = Signal(bool, str)  # Success, message
    
    def __init__(self, data: List[Dict[str, Any]], file_path: str, format_type: str):
        super().__init__()
        self.data = data
        self.file_path = file_path
        self.format_type = format_type
    
    def run(self):
        """Export the data."""
        try:
            if self.format_type.lower() == 'csv':
                self.export_csv()
            elif self.format_type.lower() == 'json':
                self.export_json()
            else:
                raise ValueError(f"Unsupported format: {self.format_type}")
            
            self.finished.emit(True, f"Data exported successfully to {self.file_path}")
            
        except Exception as e:
            self.finished.emit(False, f"Export failed: {str(e)}")
    
    def export_csv(self):
        """Export data as CSV."""
        if not self.data:
            raise ValueError("No data to export")
        
        with open(self.file_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = self.data[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            
            total_rows = len(self.data)
            for i, row in enumerate(self.data):
                writer.writerow(row)
                
                # Emit progress
                progress = int((i + 1) / total_rows * 100)
                self.progress.emit(progress)
    
    def export_json(self):
        """Export data as JSON."""
        with open(self.file_path, 'w', encoding='utf-8') as jsonfile:
            json.dump(self.data, jsonfile, indent=2, ensure_ascii=False, default=str)
        
        self.progress.emit(100)


class ColumnConfig:
    """Configuration for a table column."""
    
    def __init__(self, 
                 key: str, 
                 title: str, 
                 width: int = 100,
                 sortable: bool = True,
                 filterable: bool = True,
                 formatter: Optional[Callable] = None,
                 alignment: Qt.AlignmentFlag = Qt.AlignLeft):
        self.key = key
        self.title = title
        self.width = width
        self.sortable = sortable
        self.filterable = filterable
        self.formatter = formatter
        self.alignment = alignment


class DataTable(QWidget):
    """
    Feature-rich data table widget with pagination, sorting, filtering, and export.
    """
    
    # Signals
    item_selected = Signal(dict)  # Selected item data
    item_double_clicked = Signal(dict)  # Double-clicked item data
    selection_changed = Signal(list)  # List of selected items
    data_updated = Signal()  # Data was updated
    page_changed = Signal(int)  # Page number changed
    
    def __init__(self, columns: List[ColumnConfig], parent=None):
        super().__init__(parent)
        
        self.columns = columns
        self.data: List[Dict[str, Any]] = []
        self.filtered_data: List[Dict[str, Any]] = []
        self.current_page = 1
        self.page_size = 20
        self.total_items = 0
        self.total_pages = 0
        
        # Sorting
        self.sort_column = None
        self.sort_ascending = True
        
        # Export worker
        self.export_worker: Optional[ExportWorker] = None
        
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Toolbar
        self.create_toolbar(layout)
        
        # Table
        self.create_table(layout)
        
        # Pagination controls
        self.create_pagination(layout)
        
        # Status bar
        self.create_status_bar(layout)
    
    def create_toolbar(self, layout: QVBoxLayout):
        """Create the toolbar."""
        toolbar_frame = QFrame()
        toolbar_layout = QHBoxLayout(toolbar_frame)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        
        # Refresh button
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.clicked.connect(self.refresh_requested.emit)
        toolbar_layout.addWidget(self.refresh_btn)
        
        # Export button
        self.export_btn = QPushButton("📤 Export")
        self.export_btn.clicked.connect(self.show_export_menu)
        toolbar_layout.addWidget(self.export_btn)
        
        # Column visibility button
        self.columns_btn = QPushButton("⚙️ Columns")
        self.columns_btn.clicked.connect(self.show_column_menu)
        toolbar_layout.addWidget(self.columns_btn)
        
        # Spacer
        toolbar_layout.addStretch()
        
        # Page size selector
        toolbar_layout.addWidget(QLabel("Rows per page:"))
        self.page_size_combo = QComboBox()
        self.page_size_combo.addItems(["10", "20", "50", "100"])
        self.page_size_combo.setCurrentText(str(self.page_size))
        self.page_size_combo.currentTextChanged.connect(self.on_page_size_changed)
        toolbar_layout.addWidget(self.page_size_combo)
        
        layout.addWidget(toolbar_frame)
    
    def create_table(self, layout: QVBoxLayout):
        """Create the main table widget."""
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table.setSortingEnabled(True)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        
        # Set up columns
        self.table.setColumnCount(len(self.columns))
        headers = [col.title for col in self.columns]
        self.table.setHorizontalHeaderLabels(headers)
        
        # Configure columns
        header = self.table.horizontalHeader()
        for i, col in enumerate(self.columns):
            header.resizeSection(i, col.width)
        
        header.setStretchLastSection(True)
        
        # Configure rows
        self.table.verticalHeader().setVisible(False)
        
        layout.addWidget(self.table)
    
    def create_pagination(self, layout: QVBoxLayout):
        """Create pagination controls."""
        pagination_frame = QFrame()
        pagination_layout = QHBoxLayout(pagination_frame)
        pagination_layout.setContentsMargins(0, 0, 0, 0)
        
        # First page button
        self.first_btn = QPushButton("⏮️")
        self.first_btn.setToolTip("First page")
        self.first_btn.clicked.connect(lambda: self.go_to_page(1))
        pagination_layout.addWidget(self.first_btn)
        
        # Previous page button
        self.prev_btn = QPushButton("◀️")
        self.prev_btn.setToolTip("Previous page")
        self.prev_btn.clicked.connect(self.go_to_previous_page)
        pagination_layout.addWidget(self.prev_btn)
        
        # Page info
        self.page_info_label = QLabel("Page 1 of 1")
        pagination_layout.addWidget(self.page_info_label)
        
        # Next page button
        self.next_btn = QPushButton("▶️")
        self.next_btn.setToolTip("Next page")
        self.next_btn.clicked.connect(self.go_to_next_page)
        pagination_layout.addWidget(self.next_btn)
        
        # Last page button
        self.last_btn = QPushButton("⏭️")
        self.last_btn.setToolTip("Last page")
        self.last_btn.clicked.connect(lambda: self.go_to_page(self.total_pages))
        pagination_layout.addWidget(self.last_btn)
        
        # Spacer
        pagination_layout.addStretch()
        
        # Go to page
        pagination_layout.addWidget(QLabel("Go to page:"))
        self.page_spinbox = QSpinBox()
        self.page_spinbox.setMinimum(1)
        self.page_spinbox.setValue(1)
        self.page_spinbox.valueChanged.connect(self.go_to_page)
        pagination_layout.addWidget(self.page_spinbox)
        
        layout.addWidget(pagination_frame)
    
    def create_status_bar(self, layout: QVBoxLayout):
        """Create status bar."""
        status_frame = QFrame()
        status_layout = QHBoxLayout(status_frame)
        status_layout.setContentsMargins(5, 5, 5, 5)
        
        # Item count
        self.item_count_label = QLabel("0 items")
        status_layout.addWidget(self.item_count_label)
        
        # Selected count
        self.selected_count_label = QLabel("")
        status_layout.addWidget(self.selected_count_label)
        
        # Spacer
        status_layout.addStretch()
        
        # Progress bar (hidden by default)
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(200)
        self.progress_bar.setVisible(False)
        status_layout.addWidget(self.progress_bar)
        
        layout.addWidget(status_frame)
    
    # Signal to emit when refresh is requested
    refresh_requested = Signal()
    
    def setup_connections(self):
        """Set up signal connections."""
        # Table signals
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        self.table.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        self.table.horizontalHeader().sectionClicked.connect(self.on_header_clicked)
    
    def on_selection_changed(self):
        """Handle selection change."""
        selected_rows = set()
        for item in self.table.selectedItems():
            selected_rows.add(item.row())
        
        selected_data = []
        for row in selected_rows:
            if row < len(self.filtered_data):
                selected_data.append(self.filtered_data[row])
        
        # Update status
        if selected_data:
            self.selected_count_label.setText(f"{len(selected_data)} selected")
            self.item_selected.emit(selected_data[0])  # Emit first selected item
        else:
            self.selected_count_label.setText("")
        
        self.selection_changed.emit(selected_data)
    
    def on_item_double_clicked(self, item: QTableWidgetItem):
        """Handle item double click."""
        row = item.row()
        if row < len(self.filtered_data):
            self.item_double_clicked.emit(self.filtered_data[row])
    
    def on_header_clicked(self, logical_index: int):
        """Handle header click for sorting."""
        if logical_index < len(self.columns):
            column = self.columns[logical_index]
            if column.sortable:
                # Toggle sort order if same column
                if self.sort_column == column.key:
                    self.sort_ascending = not self.sort_ascending
                else:
                    self.sort_column = column.key
                    self.sort_ascending = True
                
                self.sort_data()
                self.update_display()
    
    def on_page_size_changed(self, new_size: str):
        """Handle page size change."""
        try:
            self.page_size = int(new_size)
            self.current_page = 1
            self.update_pagination()
            self.update_display()
        except ValueError:
            pass
    
    def show_context_menu(self, position):
        """Show context menu."""
        if not self.table.itemAt(position):
            return
        
        menu = QMenu(self)
        
        # Copy actions
        copy_cell_action = QAction("Copy Cell", self)
        copy_cell_action.triggered.connect(self.copy_cell)
        menu.addAction(copy_cell_action)
        
        copy_row_action = QAction("Copy Row", self)
        copy_row_action.triggered.connect(self.copy_row)
        menu.addAction(copy_row_action)
        
        menu.addSeparator()
        
        # Export selected
        export_selected_action = QAction("Export Selected", self)
        export_selected_action.triggered.connect(self.export_selected)
        menu.addAction(export_selected_action)
        
        menu.exec(self.table.mapToGlobal(position))
    
    def show_export_menu(self):
        """Show export options menu."""
        menu = QMenu(self)
        
        csv_action = QAction("Export as CSV", self)
        csv_action.triggered.connect(lambda: self.export_data('csv'))
        menu.addAction(csv_action)
        
        json_action = QAction("Export as JSON", self)
        json_action.triggered.connect(lambda: self.export_data('json'))
        menu.addAction(json_action)
        
        menu.exec(self.export_btn.mapToGlobal(self.export_btn.rect().bottomLeft()))
    
    def show_column_menu(self):
        """Show column visibility menu."""
        menu = QMenu(self)
        
        for i, column in enumerate(self.columns):
            action = QAction(column.title, self)
            action.setCheckable(True)
            action.setChecked(not self.table.isColumnHidden(i))
            action.triggered.connect(lambda checked, col=i: self.toggle_column(col, checked))
            menu.addAction(action)
        
        menu.exec(self.columns_btn.mapToGlobal(self.columns_btn.rect().bottomLeft()))
    
    def toggle_column(self, column_index: int, visible: bool):
        """Toggle column visibility."""
        self.table.setColumnHidden(column_index, not visible)
    
    def copy_cell(self):
        """Copy current cell to clipboard."""
        current_item = self.table.currentItem()
        if current_item:
            QApplication.clipboard().setText(current_item.text())
    
    def copy_row(self):
        """Copy current row to clipboard."""
        current_row = self.table.currentRow()
        if current_row >= 0 and current_row < len(self.filtered_data):
            row_data = self.filtered_data[current_row]
            # Format as tab-separated values
            text = '\t'.join(str(row_data.get(col.key, '')) for col in self.columns)
            QApplication.clipboard().setText(text)
    
    def export_selected(self):
        """Export selected rows."""
        selected_rows = set()
        for item in self.table.selectedItems():
            selected_rows.add(item.row())
        
        if not selected_rows:
            QMessageBox.information(self, "Export", "No rows selected for export.")
            return
        
        selected_data = [self.filtered_data[row] for row in sorted(selected_rows) 
                        if row < len(self.filtered_data)]
        
        self._export_data_to_file(selected_data, "selected_data")
    
    def export_data(self, format_type: str):
        """Export all data."""
        if not self.data:
            QMessageBox.information(self, "Export", "No data to export.")
            return
        
        self._export_data_to_file(self.data, f"data_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    
    def _export_data_to_file(self, data: List[Dict[str, Any]], filename_base: str):
        """Export data to file with file dialog."""
        file_filters = "CSV Files (*.csv);;JSON Files (*.json);;All Files (*)"
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self, "Export Data", f"{filename_base}.csv", file_filters
        )
        
        if not file_path:
            return
        
        # Determine format from file extension or filter
        if file_path.endswith('.json') or 'JSON' in selected_filter:
            format_type = 'json'
        else:
            format_type = 'csv'
        
        # Start export worker
        self.export_worker = ExportWorker(data, file_path, format_type)
        self.export_worker.progress.connect(self.progress_bar.setValue)
        self.export_worker.finished.connect(self.on_export_finished)
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.export_worker.start()
    
    def on_export_finished(self, success: bool, message: str):
        """Handle export completion."""
        self.progress_bar.setVisible(False)
        
        if self.export_worker:
            self.export_worker.deleteLater()
            self.export_worker = None
        
        if success:
            QMessageBox.information(self, "Export Successful", message)
        else:
            QMessageBox.critical(self, "Export Failed", message)
    
    def set_data(self, data: List[Dict[str, Any]]):
        """Set table data."""
        self.data = data
        self.filtered_data = data.copy()
        self.total_items = len(data)
        self.current_page = 1
        
        self.sort_data()
        self.update_pagination()
        self.update_display()
        self.data_updated.emit()
    
    def add_data(self, new_data: List[Dict[str, Any]]):
        """Add new data to the table."""
        self.data.extend(new_data)
        self.filtered_data = self.data.copy()
        self.total_items = len(self.data)
        
        self.sort_data()
        self.update_pagination()
        self.update_display()
        self.data_updated.emit()
    
    def clear_data(self):
        """Clear all table data."""
        self.data.clear()
        self.filtered_data.clear()
        self.total_items = 0
        self.current_page = 1
        
        self.update_pagination()
        self.update_display()
        self.data_updated.emit()
    
    def filter_data(self, filter_func: Callable[[Dict[str, Any]], bool]):
        """Filter data using a custom function."""
        self.filtered_data = [item for item in self.data if filter_func(item)]
        self.total_items = len(self.filtered_data)
        self.current_page = 1
        
        self.update_pagination()
        self.update_display()
    
    def sort_data(self):
        """Sort data by current sort column."""
        if not self.sort_column:
            return
        
        def sort_key(item):
            value = item.get(self.sort_column, '')
            # Handle None values
            if value is None:
                return ''
            # Convert to string for comparison
            return str(value).lower() if isinstance(value, str) else value
        
        self.filtered_data.sort(key=sort_key, reverse=not self.sort_ascending)
    
    def update_pagination(self):
        """Update pagination controls."""
        if self.total_items == 0:
            self.total_pages = 1
        else:
            self.total_pages = (self.total_items - 1) // self.page_size + 1
        
        # Ensure current page is valid
        if self.current_page > self.total_pages:
            self.current_page = max(1, self.total_pages)
        
        # Update controls
        self.page_info_label.setText(f"Page {self.current_page} of {self.total_pages}")
        self.page_spinbox.setMaximum(max(1, self.total_pages))
        self.page_spinbox.setValue(self.current_page)
        
        # Update button states
        self.first_btn.setEnabled(self.current_page > 1)
        self.prev_btn.setEnabled(self.current_page > 1)
        self.next_btn.setEnabled(self.current_page < self.total_pages)
        self.last_btn.setEnabled(self.current_page < self.total_pages)
        
        # Update item count
        start_item = (self.current_page - 1) * self.page_size + 1
        end_item = min(self.current_page * self.page_size, self.total_items)
        
        if self.total_items == 0:
            self.item_count_label.setText("0 items")
        else:
            self.item_count_label.setText(f"Showing {start_item}-{end_item} of {self.total_items} items")
    
    def update_display(self):
        """Update table display with current page data."""
        # Calculate page data
        start_index = (self.current_page - 1) * self.page_size
        end_index = start_index + self.page_size
        page_data = self.filtered_data[start_index:end_index]
        
        # Clear table
        self.table.setRowCount(0)
        
        # Add data
        for row_index, item in enumerate(page_data):
            self.table.insertRow(row_index)
            
            for col_index, column in enumerate(self.columns):
                value = item.get(column.key, '')
                
                # Apply formatter if available
                if column.formatter and value is not None:
                    try:
                        display_value = column.formatter(value)
                    except Exception as e:
                        logger.warning(f"Error formatting value {value}: {e}")
                        display_value = str(value)
                else:
                    display_value = str(value) if value is not None else ''
                
                # Create table item
                table_item = QTableWidgetItem(display_value)
                table_item.setTextAlignment(column.alignment)
                
                # Store original value for sorting
                table_item.setData(Qt.UserRole, value)
                
                self.table.setItem(row_index, col_index, table_item)
        
        # Clear selection
        self.table.clearSelection()
    
    def go_to_page(self, page: int):
        """Go to specific page."""
        if 1 <= page <= self.total_pages and page != self.current_page:
            self.current_page = page
            self.update_pagination()
            self.update_display()
            self.page_changed.emit(page)
    
    def go_to_next_page(self):
        """Go to next page."""
        if self.current_page < self.total_pages:
            self.go_to_page(self.current_page + 1)
    
    def go_to_previous_page(self):
        """Go to previous page."""
        if self.current_page > 1:
            self.go_to_page(self.current_page - 1)
    
    def get_selected_data(self) -> List[Dict[str, Any]]:
        """Get selected row data."""
        selected_rows = set()
        for item in self.table.selectedItems():
            selected_rows.add(item.row())
        
        return [self.filtered_data[row] for row in sorted(selected_rows)
                if row < len(self.filtered_data)]
    
    def refresh(self):
        """Refresh the table display."""
        self.update_display()