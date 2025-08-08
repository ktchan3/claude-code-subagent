"""
Theme management for People Management System Client

Provides light and dark theme support for the application.
"""

from typing import Dict, Any, List
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor


class ThemeManager(QObject):
    """Manages application themes."""
    
    # Signals
    theme_changed = Signal(str)  # Theme name
    
    def __init__(self):
        super().__init__()
        self.current_theme = "light"
        self.themes = {
            "light": self._create_light_theme(),
            "dark": self._create_dark_theme()
        }
    
    def _create_light_theme(self) -> Dict[str, Any]:
        """Create light theme configuration."""
        return {
            "name": "Light",
            "colors": {
                "primary": "#1976d2",
                "primary_dark": "#1565c0",
                "primary_light": "#e3f2fd",
                "secondary": "#424242",
                "background": "#ffffff",
                "surface": "#f5f5f5",
                "error": "#d32f2f",
                "warning": "#f57c00",
                "success": "#388e3c",
                "info": "#1976d2",
                "text_primary": "#212121",
                "text_secondary": "#757575",
                "border": "#e0e0e0",
                "disabled": "#bdbdbd"
            },
            "palette": self._create_light_palette(),
            "stylesheet": self._get_light_stylesheet()
        }
    
    def _create_dark_theme(self) -> Dict[str, Any]:
        """Create dark theme configuration."""
        return {
            "name": "Dark",
            "colors": {
                "primary": "#90caf9",
                "primary_dark": "#42a5f5",
                "primary_light": "#1e3a8a",
                "secondary": "#b0bec5",
                "background": "#121212",
                "surface": "#1e1e1e",
                "error": "#cf6679",
                "warning": "#ffb74d",
                "success": "#81c784",
                "info": "#64b5f6",
                "text_primary": "#ffffff",
                "text_secondary": "#b0b0b0",
                "border": "#404040",
                "disabled": "#606060"
            },
            "palette": self._create_dark_palette(),
            "stylesheet": self._get_dark_stylesheet()
        }
    
    def _create_light_palette(self) -> QPalette:
        """Create light theme palette."""
        palette = QPalette()
        
        # Window colors
        palette.setColor(QPalette.Window, QColor("#f5f5f5"))
        palette.setColor(QPalette.WindowText, QColor("#212121"))
        
        # Base colors (input backgrounds)
        palette.setColor(QPalette.Base, QColor("#ffffff"))
        palette.setColor(QPalette.AlternateBase, QColor("#f9f9f9"))
        
        # Text colors
        palette.setColor(QPalette.Text, QColor("#212121"))
        palette.setColor(QPalette.BrightText, QColor("#ffffff"))
        
        # Button colors
        palette.setColor(QPalette.Button, QColor("#ffffff"))
        palette.setColor(QPalette.ButtonText, QColor("#212121"))
        
        # Highlight colors
        palette.setColor(QPalette.Highlight, QColor("#1976d2"))
        palette.setColor(QPalette.HighlightedText, QColor("#ffffff"))
        
        # Disabled colors
        palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor("#bdbdbd"))
        palette.setColor(QPalette.Disabled, QPalette.Text, QColor("#bdbdbd"))
        palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor("#bdbdbd"))
        
        return palette
    
    def _create_dark_palette(self) -> QPalette:
        """Create dark theme palette."""
        palette = QPalette()
        
        # Window colors
        palette.setColor(QPalette.Window, QColor("#2b2b2b"))
        palette.setColor(QPalette.WindowText, QColor("#ffffff"))
        
        # Base colors (input backgrounds)
        palette.setColor(QPalette.Base, QColor("#3c3c3c"))
        palette.setColor(QPalette.AlternateBase, QColor("#404040"))
        
        # Text colors
        palette.setColor(QPalette.Text, QColor("#ffffff"))
        palette.setColor(QPalette.BrightText, QColor("#ffffff"))
        
        # Button colors
        palette.setColor(QPalette.Button, QColor("#404040"))
        palette.setColor(QPalette.ButtonText, QColor("#ffffff"))
        
        # Highlight colors
        palette.setColor(QPalette.Highlight, QColor("#90caf9"))
        palette.setColor(QPalette.HighlightedText, QColor("#000000"))
        
        # Disabled colors
        palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor("#606060"))
        palette.setColor(QPalette.Disabled, QPalette.Text, QColor("#606060"))
        palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor("#606060"))
        
        return palette
    
    def _get_light_stylesheet(self) -> str:
        """Get light theme stylesheet."""
        return """
        /* Light Theme Overrides */
        QMainWindow {
            background-color: #f5f5f5;
        }
        
        /* Remove global QWidget styling that was hiding dashboard content
        QWidget {
            background-color: #f5f5f5;
            color: #212121;
        }
        */
        
        QPushButton {
            background-color: #1976d2;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
        }
        
        QPushButton:hover {
            background-color: #1565c0;
        }
        
        QLineEdit, QTextEdit, QComboBox {
            background-color: #ffffff;
            border: 2px solid #e0e0e0;
            color: #212121;
        }
        
        QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
            border-color: #1976d2;
        }
        
        QTableWidget {
            background-color: #ffffff;
            alternate-background-color: #f9f9f9;
            gridline-color: #e0e0e0;
        }
        """
    
    def _get_dark_stylesheet(self) -> str:
        """Get dark theme stylesheet."""
        return """
        /* Dark Theme Overrides */
        QMainWindow {
            background-color: #121212;
        }
        
        /* Remove global QWidget styling that was hiding dashboard content
        QWidget {
            background-color: #121212;
            color: #ffffff;
        }
        */
        
        QPushButton {
            background-color: #90caf9;
            color: #000000;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
        }
        
        QPushButton:hover {
            background-color: #42a5f5;
        }
        
        QLineEdit, QTextEdit, QComboBox {
            background-color: #3c3c3c;
            border: 2px solid #555555;
            color: #ffffff;
        }
        
        QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
            border-color: #90caf9;
        }
        
        QTableWidget {
            background-color: #1e1e1e;
            alternate-background-color: #2a2a2a;
            gridline-color: #404040;
            color: #ffffff;
        }
        
        QHeaderView::section {
            background-color: #2a2a2a;
            color: #ffffff;
            border-bottom: 2px solid #404040;
        }
        
        QListWidget {
            background-color: #1e1e1e;
            color: #ffffff;
            selection-background-color: #1e3a8a;
        }
        
        QGroupBox {
            color: #ffffff;
            border: 2px solid #404040;
        }
        
        QMenu {
            background-color: #2a2a2a;
            color: #ffffff;
            border: 1px solid #404040;
        }
        
        QMenuBar {
            background-color: #1e1e1e;
            color: #ffffff;
        }
        
        QStatusBar {
            background-color: #1e1e1e;
            color: #ffffff;
            border-top: 1px solid #404040;
        }
        """
    
    def get_current_theme(self) -> str:
        """Get current theme name."""
        return self.current_theme
    
    def get_theme_config(self, theme_name: str = None) -> Dict[str, Any]:
        """Get theme configuration."""
        theme_name = theme_name or self.current_theme
        return self.themes.get(theme_name, self.themes["light"])
    
    def get_color(self, color_name: str, theme_name: str = None) -> str:
        """Get color value from current theme."""
        theme = self.get_theme_config(theme_name)
        return theme["colors"].get(color_name, "#000000")
    
    def apply_theme(self, theme_name: str):
        """Apply theme to application."""
        if theme_name not in self.themes:
            theme_name = "light"
        
        self.current_theme = theme_name
        theme_config = self.themes[theme_name]
        
        app = QApplication.instance()
        if app:
            # Apply palette
            app.setPalette(theme_config["palette"])
            
            # Apply stylesheet
            stylesheet = theme_config["stylesheet"]
            app.setStyleSheet(stylesheet)
        
        self.theme_changed.emit(theme_name)
    
    def toggle_theme(self):
        """Toggle between light and dark themes."""
        new_theme = "dark" if self.current_theme == "light" else "light"
        self.apply_theme(new_theme)
    
    def get_available_themes(self) -> List[str]:
        """Get list of available theme names."""
        return list(self.themes.keys())


# Global theme manager instance
theme_manager = ThemeManager()