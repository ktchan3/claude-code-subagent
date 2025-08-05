# People Management System - PySide6 Client

A modern, feature-rich GUI client for the People Management System built with PySide6 (Qt for Python).

## Features

### Core Functionality
- **People Management**: Create, edit, delete, and search people records
- **Department Management**: Organize people into departments
- **Position Management**: Define job positions and requirements
- **Employment Records**: Track employment history and assignments
- **Dashboard**: System overview with statistics and quick actions

### User Interface
- **Modern Design**: Clean, intuitive interface with flat design principles
- **Dark/Light Themes**: Switch between light and dark themes
- **Responsive Layout**: Adapts to different screen sizes
- **Advanced Search**: Powerful filtering and search capabilities
- **Data Export**: Export data to CSV and JSON formats
- **Real-time Updates**: Live data updates and notifications

### Technical Features
- **Async Operations**: Non-blocking API calls with progress indicators
- **Caching**: Intelligent data caching for better performance
- **Configuration Management**: Secure credential storage and settings
- **Error Handling**: Comprehensive error handling with user-friendly messages
- **Validation**: Form validation with visual feedback
- **Auto-save**: Automatic saving of form data

## Installation

### Prerequisites
- Python 3.9 or higher
- PySide6 6.6.0 or higher
- Running People Management System server

### Install Dependencies
```bash
cd client
pip install -e .
```

### Development Dependencies
```bash
pip install -e .[dev]
```

## Usage

### Starting the Application
```bash
# Using the installed script
people-management

# Or directly with Python
python -m client.main
```

### First Time Setup
1. Launch the application
2. In the login dialog, enter:
   - Server URL (e.g., `http://localhost:8000`)
   - API Key (obtain from system administrator)
3. Test the connection
4. Click "Connect" to start using the application

### Navigation
- Use the sidebar to switch between different views
- **Dashboard**: System overview and statistics
- **People**: Manage people records
- **Departments**: Manage organizational departments
- **Positions**: Manage job positions
- **Employment**: Manage employment records

## Application Structure

```
client/
├── main.py                     # Application entry point
├── services/                   # Business logic layer
│   ├── api_service.py         # API communication service
│   └── config_service.py      # Configuration management
├── ui/                        # User interface components
│   ├── main_window.py         # Main application window
│   ├── login_dialog.py        # Login and setup dialog
│   ├── views/                 # Main application views
│   │   ├── dashboard_view.py  # Dashboard with statistics
│   │   ├── people_view.py     # People management
│   │   ├── departments_view.py # Department management
│   │   ├── positions_view.py  # Position management
│   │   └── employment_view.py # Employment records
│   └── widgets/               # Reusable UI components
│       ├── data_table.py      # Advanced data table
│       ├── search_widget.py   # Search and filtering
│       └── person_form.py     # Person form widget
├── resources/                 # Application resources
│   ├── styles.qss            # Qt stylesheets
│   ├── themes.py             # Theme management
│   └── icons/                # Application icons
└── README.md                 # This file
```

## Key Components

### API Service
- Wraps the shared API client for Qt integration
- Provides async operations with Qt signals
- Implements caching and connection management
- Handles errors and retries

### Data Table Widget
- Sortable, filterable data display
- Pagination support
- Export functionality (CSV, JSON)
- Context menus and bulk operations
- Column visibility controls

### Search Widget
- Advanced filtering with multiple criteria
- Saved search functionality
- Real-time search as you type
- Support for different field types (text, number, date, choice)

### Form Widgets
- Comprehensive validation
- Auto-save functionality
- Rich input controls
- Visual feedback for errors

## Configuration

### Application Settings
Configuration is stored in platform-specific locations:
- **Windows**: `%APPDATA%/PeopleManagementSystem/config.json`
- **macOS**: `~/Library/Application Support/PeopleManagementSystem/config.json`
- **Linux**: `~/.config/PeopleManagementSystem/config.json`

### Secure Credential Storage
API keys are stored securely using the system keyring:
- **Windows**: Windows Credential Store
- **macOS**: Keychain
- **Linux**: Secret Service (GNOME Keyring, KWallet)

## Development

### Running in Development Mode
```bash
cd client
python main.py
```

### Code Style
The project follows PEP 8 style guidelines with:
- Line length: 100 characters
- Imports organized with isort
- Code formatted with black
- Type hints for better code documentation

### Testing
```bash
# Run tests
pytest

# Run with coverage
pytest --cov=client --cov-report=html
```

### Building
```bash
# Build wheel
python -m build

# Install from wheel
pip install dist/people_management_client-*.whl
```

## Troubleshooting

### Connection Issues
- Verify the server URL is correct and accessible
- Check that the API key is valid
- Ensure the server is running and responding
- Check firewall and network settings

### Performance Issues
- Clear the application cache (⚙️ More → Clear Cache)
- Reduce the number of items displayed per page
- Check system resources and close unnecessary applications

### UI Issues
- Try switching themes (View → Theme)
- Reset window layout by deleting configuration files
- Update graphics drivers for better rendering

## Support

For issues and questions:
1. Check the server logs for API-related issues
2. Check the client log file: `~/.local/share/PeopleManagementSystem/logs/`
3. Report bugs with detailed steps to reproduce

## License

This project is licensed under the MIT License - see the main project LICENSE file for details.