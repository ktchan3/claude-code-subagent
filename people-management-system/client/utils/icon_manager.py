"""
Icon Manager for People Management System Client

Provides centralized icon management with fallback to emoji when icon files are not available.
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any

from PySide6.QtGui import QIcon, QPixmap, QPainter, QFont, QColor
from PySide6.QtCore import Qt, QSize

logger = logging.getLogger(__name__)


class IconManager:
    """Manages application icons with emoji fallback support."""
    
    # Icon mappings with emoji fallbacks
    ICON_MAP = {
        # Application icons
        'app': '👥',
        'app_icon': '👥',
        
        # Navigation icons
        'dashboard': '📊',
        'people': '👥',
        'departments': '🏢',
        'positions': '💼',
        'employment': '📝',
        
        # Action icons
        'add': '➕',
        'edit': '✏️',
        'delete': '🗑️',
        'save': '💾',
        'cancel': '❌',
        'refresh': '🔄',
        'search': '🔍',
        'filter': '🔽',
        'export': '📤',
        'import': '📥',
        'settings': '⚙️',
        'help': '❓',
        'info': 'ℹ️',
        'warning': '⚠️',
        'error': '❌',
        'success': '✅',
        
        # Status icons
        'connected': '🟢',
        'disconnected': '🔴',
        'pending': '🟡',
        'loading': '⏳',
        
        # Navigation arrows
        'arrow_left': '◀️',
        'arrow_right': '▶️',
        'arrow_up': '🔼',
        'arrow_down': '🔽',
        'first_page': '⏮️',
        'last_page': '⏭️',
        
        # File operations
        'file': '📄',
        'folder': '📁',
        'csv': '📊',
        'json': '📋',
        'pdf': '📑',
        
        # User actions
        'user': '👤',
        'users': '👥',
        'profile': '👤',
        'logout': '🚪',
        'login': '🔑',
        
        # Miscellaneous
        'calendar': '📅',
        'clock': '🕐',
        'email': '📧',
        'phone': '📞',
        'location': '📍',
        'notes': '📝',
        'tags': '🏷️',
        'star': '⭐',
        'heart': '❤️',
        'flag': '🚩',
        'bookmark': '🔖',
    }
    
    def __init__(self, icon_dir: Optional[Path] = None):
        """
        Initialize the icon manager.
        
        Args:
            icon_dir: Directory containing icon files (optional)
        """
        self.icon_dir = icon_dir
        self.icon_cache: Dict[str, QIcon] = {}
        
        if icon_dir and icon_dir.exists():
            logger.info(f"Icon directory found: {icon_dir}")
        else:
            logger.info("No icon directory found, using emoji fallbacks")
    
    def get_icon(self, name: str, size: QSize = QSize(24, 24)) -> QIcon:
        """
        Get an icon by name, with emoji fallback.
        
        Args:
            name: Icon name
            size: Desired icon size
            
        Returns:
            QIcon object
        """
        # Check cache first
        cache_key = f"{name}_{size.width()}x{size.height()}"
        if cache_key in self.icon_cache:
            return self.icon_cache[cache_key]
        
        icon = None
        
        # Try to load from file first
        if self.icon_dir:
            icon = self._load_icon_from_file(name)
        
        # Fall back to emoji if no file found
        if not icon or icon.isNull():
            icon = self._create_emoji_icon(name, size)
        
        # Cache the icon
        self.icon_cache[cache_key] = icon
        return icon
    
    def _load_icon_from_file(self, name: str) -> Optional[QIcon]:
        """
        Try to load an icon from file.
        
        Args:
            name: Icon name
            
        Returns:
            QIcon if found, None otherwise
        """
        if not self.icon_dir:
            return None
        
        # Try different file extensions
        extensions = ['.png', '.svg', '.ico', '.jpg']
        for ext in extensions:
            icon_path = self.icon_dir / f"{name}{ext}"
            if icon_path.exists():
                return QIcon(str(icon_path))
        
        return None
    
    def _create_emoji_icon(self, name: str, size: QSize) -> QIcon:
        """
        Create an icon from an emoji.
        
        Args:
            name: Icon name
            size: Icon size
            
        Returns:
            QIcon with emoji
        """
        emoji = self.ICON_MAP.get(name, '❓')  # Default to question mark
        
        # Create a pixmap with the emoji
        pixmap = QPixmap(size)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Set font for emoji
        font = QFont()
        font.setPointSize(int(size.height() * 0.7))  # Adjust size to fit
        painter.setFont(font)
        
        # Draw emoji centered
        painter.drawText(pixmap.rect(), Qt.AlignCenter, emoji)
        painter.end()
        
        return QIcon(pixmap)
    
    def get_emoji(self, name: str) -> str:
        """
        Get emoji string for a given icon name.
        
        Args:
            name: Icon name
            
        Returns:
            Emoji string
        """
        return self.ICON_MAP.get(name, '❓')
    
    def create_colored_icon(self, name: str, color: QColor, size: QSize = QSize(24, 24)) -> QIcon:
        """
        Create a colored version of an icon.
        
        Args:
            name: Icon name
            color: Color for the icon
            size: Icon size
            
        Returns:
            Colored QIcon
        """
        base_icon = self.get_icon(name, size)
        
        # Create colored pixmap
        pixmap = base_icon.pixmap(size)
        colored_pixmap = QPixmap(size)
        colored_pixmap.fill(Qt.transparent)
        
        painter = QPainter(colored_pixmap)
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
        painter.drawPixmap(0, 0, pixmap)
        painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
        painter.fillRect(colored_pixmap.rect(), color)
        painter.end()
        
        return QIcon(colored_pixmap)
    
    def clear_cache(self):
        """Clear the icon cache."""
        self.icon_cache.clear()
        logger.debug("Icon cache cleared")


# Global icon manager instance
_icon_manager = None


def get_icon_manager() -> IconManager:
    """Get the global icon manager instance."""
    global _icon_manager
    if _icon_manager is None:
        # Try to find icon directory
        icon_dir = Path(__file__).parent.parent / "resources" / "icons"
        _icon_manager = IconManager(icon_dir)
    return _icon_manager


def get_icon(name: str, size: QSize = QSize(24, 24)) -> QIcon:
    """
    Convenience function to get an icon.
    
    Args:
        name: Icon name
        size: Icon size
        
    Returns:
        QIcon object
    """
    return get_icon_manager().get_icon(name, size)


def get_emoji(name: str) -> str:
    """
    Convenience function to get an emoji.
    
    Args:
        name: Icon name
        
    Returns:
        Emoji string
    """
    return get_icon_manager().get_emoji(name)