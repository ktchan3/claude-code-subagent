"""
People Management System - PySide6 GUI Client Application

This is the main entry point for the People Management System GUI client.
It provides a modern, user-friendly interface for managing people, departments,
positions, and employment records through the People Management System API.
"""

import sys
import logging
import asyncio
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import QApplication, QMessageBox, QSplashScreen
from PySide6.QtCore import Qt, QThread, QTimer, QCoreApplication
from PySide6.QtGui import QPixmap, QPainter, QFont, QIcon

from client.services.config_service import ConfigService
from client.services.api_service import APIService
from client.ui.login_dialog import LoginDialog
from client.ui.main_window import MainWindow


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('people_management_client.log')
    ]
)
logger = logging.getLogger(__name__)


class PeopleManagementApp(QApplication):
    """Main application class for the People Management System client."""
    
    def __init__(self, argv):
        super().__init__(argv)
        
        # Set application properties
        self.setApplicationName("People Management System")
        self.setApplicationVersion("1.0.0")
        self.setOrganizationName("Your Organization")
        self.setOrganizationDomain("example.com")
        
        # Application state
        self.config_service: Optional[ConfigService] = None
        self.api_service: Optional[APIService] = None
        self.main_window: Optional[MainWindow] = None
        self.splash: Optional[QSplashScreen] = None
        
        # Set up event loop for async operations
        self.event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.event_loop)
        
        # Dark/Light theme handling
        self.setStyle("Fusion")
        self.setup_theme()
        
    def setup_theme(self):
        """Set up the application theme."""
        # You can implement dark/light theme switching here
        # For now, we'll use a modern flat design with Fusion style
        
        # Set window icon if available
        icon_path = Path(__file__).parent / "resources" / "icons" / "app_icon.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
    
    def create_splash_screen(self) -> QSplashScreen:
        """Create and show splash screen during startup."""
        # Create a simple splash screen
        pixmap = QPixmap(400, 300)
        pixmap.fill(Qt.white)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw application title
        font = QFont("Arial", 24, QFont.Bold)
        painter.setFont(font)
        painter.setPen(Qt.black)
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "People Management\nSystem")
        
        # Draw version
        font = QFont("Arial", 12)
        painter.setFont(font)
        painter.setPen(Qt.gray)
        painter.drawText(pixmap.rect().adjusted(0, 80, 0, 0), Qt.AlignCenter, "Version 1.0.0")
        
        painter.end()
        
        splash = QSplashScreen(pixmap)
        splash.show()
        
        return splash
    
    def show_splash_message(self, message: str):
        """Show a message on the splash screen."""
        if self.splash:
            self.splash.showMessage(
                message,
                Qt.AlignBottom | Qt.AlignCenter,
                Qt.black
            )
            self.processEvents()
    
    async def initialize_services(self):
        """Initialize application services."""
        try:
            self.show_splash_message("Initializing configuration...")
            
            # Initialize configuration service
            self.config_service = ConfigService()
            await self.config_service.initialize()
            
            self.show_splash_message("Loading settings...")
            
            # Load saved configuration
            config = await self.config_service.load_config()
            
            if config and config.get('api_key') and config.get('base_url'):
                self.show_splash_message("Connecting to API...")
                
                # Initialize API service with saved config
                self.api_service = APIService(
                    base_url=config['base_url'],
                    api_key=config['api_key']
                )
                
                # Test connection
                if await self.api_service.test_connection():
                    logger.info("Successfully connected to API")
                    return True
                else:
                    logger.warning("Failed to connect to API with saved credentials")
                    self.api_service = None
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to initialize services: {e}")
            return False
    
    def show_login_dialog(self) -> bool:
        """Show login dialog and handle authentication."""
        dialog = LoginDialog(self.config_service)
        
        if dialog.exec() == LoginDialog.Accepted:
            # Get connection details from dialog
            config = dialog.get_connection_config()
            
            # Initialize API service
            self.api_service = APIService(
                base_url=config['base_url'],
                api_key=config['api_key']
            )
            
            return True
        
        return False
    
    def show_main_window(self):
        """Create and show the main application window."""
        self.main_window = MainWindow(
            self.api_service,
            self.config_service
        )
        
        # Connect window closed signal to app quit
        self.main_window.closed.connect(self.quit_application)
        
        self.main_window.show()
        
        if self.splash:
            self.splash.finish(self.main_window)
            self.splash = None
    
    def quit_application(self):
        """Clean up and quit the application."""
        logger.info("Shutting down application...")
        
        try:
            # Save configuration
            if self.config_service:
                asyncio.run(self.config_service.save_config())
            
            # Close API service
            if self.api_service:
                asyncio.run(self.api_service.close())
                
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
        
        # Close event loop
        if self.event_loop and not self.event_loop.is_closed():
            self.event_loop.close()
        
        self.quit()
    
    def handle_exception(self, exc_type, exc_value, exc_traceback):
        """Handle uncaught exceptions."""
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        logger.error(
            "Uncaught exception",
            exc_info=(exc_type, exc_value, exc_traceback)
        )
        
        # Show error dialog to user
        QMessageBox.critical(
            None,
            "Unexpected Error",
            f"An unexpected error occurred:\n\n{exc_value}\n\n"
            "Please check the log file for more details."
        )


async def run_app():
    """Run the application with async support."""
    app = PeopleManagementApp(sys.argv)
    
    # Set up exception handling
    sys.excepthook = app.handle_exception
    
    # Create splash screen
    app.splash = app.create_splash_screen()
    
    try:
        # Initialize services
        services_initialized = await app.initialize_services()
        
        if not services_initialized:
            # Show login dialog if services couldn't be initialized
            app.show_splash_message("Authentication required...")
            
            # Close splash temporarily for login dialog
            if app.splash:
                app.splash.hide()
            
            if not app.show_login_dialog():
                logger.info("User cancelled login, exiting...")
                return 1
            
            # Show splash again
            if app.splash:
                app.splash.show()
                app.show_splash_message("Starting application...")
        
        # Show main window
        app.show_main_window()
        
        # Run the application
        return app.exec()
        
    except Exception as e:
        logger.error(f"Application startup failed: {e}")
        
        QMessageBox.critical(
            None,
            "Startup Error",
            f"Failed to start the application:\n\n{e}"
        )
        
        return 1
    
    finally:
        # Clean up
        if app.splash:
            app.splash.close()


def main():
    """Main entry point for the application."""
    # Set up Qt application attributes before creating QApplication
    QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QCoreApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    try:
        # Run the async application
        exit_code = asyncio.run(run_app())
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        sys.exit(0)
    
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()