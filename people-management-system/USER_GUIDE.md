# People Management System - User Guide

## Table of Contents
1. [Getting Started](#getting-started)
2. [Main Interface Overview](#main-interface-overview)
3. [Navigation](#navigation)
4. [Managing People](#managing-people)
5. [Managing Departments](#managing-departments)
6. [Managing Positions](#managing-positions)
7. [Managing Employment Records](#managing-employment-records)
8. [Search and Filtering](#search-and-filtering)
9. [Data Import/Export](#data-importexport)
10. [Settings and Preferences](#settings-and-preferences)
11. [Keyboard Shortcuts](#keyboard-shortcuts)
12. [Themes and Appearance](#themes-and-appearance)
13. [Troubleshooting](#troubleshooting)
14. [Tips and Best Practices](#tips-and-best-practices)

---

## Getting Started

### First Launch
When you first launch the People Management System, you'll be prompted to connect to the API server:

1. **API URL**: Enter the server address (default: `http://localhost:8000`)
2. **API Key**: Enter your API key for authentication
3. **Test Connection**: Click to verify the connection before proceeding
4. **Save Credentials**: Check this to remember your connection settings

### Main Window
After successful connection, you'll see the main application window with:
- **Navigation Sidebar** (left): Quick access to all main sections
- **Content Area** (center): Displays the selected view
- **Status Bar** (bottom): Shows connection status and operation feedback
- **Toolbar** (top): Quick action buttons

---

## Main Interface Overview

### Dashboard View
The Dashboard provides an at-a-glance overview of your system:

- **Statistics Cards**: 
  - Total People: Number of people in the system
  - Active Employees: Currently employed individuals
  - Departments: Number of departments
  - Open Positions: Available positions

- **Recent Activity**: Shows the latest changes and additions
- **Quick Actions**: One-click access to common tasks

### Navigation Sidebar
The sidebar provides access to five main sections:
- 📊 **Dashboard**: System overview and statistics
- 👥 **People**: Manage individual records
- 🏢 **Departments**: Organizational structure
- 💼 **Positions**: Job positions and roles
- 📝 **Employment**: Employment history and assignments

### Status Indicators
- 🟢 **Green Circle**: Connected to server
- 🔴 **Red Circle**: Disconnected from server
- ⏳ **Loading Spinner**: Operation in progress

---

## Navigation

### Using the Sidebar
Click any item in the sidebar to switch between views. The current view is highlighted.

### Keyboard Navigation
- **Alt+1**: Go to Dashboard
- **Alt+2**: Go to People
- **Alt+3**: Go to Departments
- **Alt+4**: Go to Positions
- **Alt+5**: Go to Employment

### Toolbar Quick Actions
The toolbar provides instant access to:
- 🔄 **Refresh**: Update current view data
- ➕ **Add**: Create new record (context-sensitive)
- 🔍 **Search**: Focus search field

---

## Managing People

### Viewing People Records
The People view displays all individuals in a sortable, filterable table:

**Table Columns**:
- Title, First Name, Last Name, Suffix
- Contact Information (Email, Phone, Mobile)
- Address Details (Address, City, State, ZIP, Country)
- Personal Information (Date of Birth, Gender, Marital Status)
- Emergency Contact Details
- Notes and Tags
- Status (Active/Inactive)
- Created/Modified dates

### Adding a New Person

1. Click **➕ Add Person** button or press **Ctrl+N**
2. Fill in the required fields:
   - First Name (required)
   - Last Name (required)
   - Email (required, must be unique)
3. Optional fields include:
   - Title (Mr., Ms., Mrs., Dr., Prof.)
   - Phone numbers
   - Address information
   - Personal details
   - Emergency contact
   - Notes and tags
4. Click **Save** to create the record

### Editing a Person

1. **Method 1**: Double-click on a person's row
2. **Method 2**: Select a person and click **✏️ Edit**
3. **Method 3**: Select a person and press **Enter**
4. Make your changes in the edit dialog
5. Click **Save** to update the record

### Deleting People

1. Select one or more people in the table
2. Click **🗑️ Delete** or press **Delete** key
3. Confirm the deletion in the confirmation dialog

⚠️ **Warning**: Deletion is permanent and cannot be undone!

### Bulk Operations

**Bulk Edit**:
1. Select multiple people using Ctrl+Click or Shift+Click
2. Click **⚙️ More** → **📝 Bulk Edit**
3. Choose fields to update for all selected records
4. Apply changes

**Bulk Delete**:
1. Select multiple people
2. Click **⚙️ More** → **🗑️ Bulk Delete**
3. Confirm deletion of all selected records

---

## Managing Departments

### Department Structure
Departments represent organizational units within your company.

### Creating a Department
1. Navigate to Departments view (Alt+3)
2. Click **➕ Add Department**
3. Enter:
   - Department Name (required)
   - Description
   - Manager (select from people)
   - Parent Department (for hierarchical structure)
4. Click **Save**

### Department Features
- View department hierarchy
- See employee count per department
- Assign/reassign department managers
- Track department statistics

---

## Managing Positions

### Position Management
Positions define job roles within departments.

### Creating a Position
1. Navigate to Positions view (Alt+4)
2. Click **➕ Add Position**
3. Enter:
   - Position Title (required)
   - Department (required)
   - Description
   - Requirements
   - Salary Range
4. Click **Save**

### Position Features
- Link positions to departments
- Track position requirements
- View employees in each position
- Manage position availability

---

## Managing Employment Records

### Employment History
Track the complete employment history of individuals.

### Creating Employment Record
1. Navigate to Employment view (Alt+5)
2. Click **➕ Add Employment**
3. Select:
   - Person (required)
   - Position (required)
   - Start Date (required)
   - End Date (optional, leave blank for current)
   - Employment Type (Full-time, Part-time, Contract)
   - Status (Active, Inactive, On Leave)
4. Click **Save**

### Employment Features
- Track employment timeline
- View current vs. past employees
- Generate employment reports
- Manage employment transitions

---

## Search and Filtering

### Quick Search
- Press **Ctrl+F** to focus the search field
- Type to search across all visible columns
- Results update in real-time as you type

### Advanced Filtering

1. Click **🔽 Advanced Filters** to expand filter options
2. Available filter types:
   - **Text Fields**: Contains, starts with, ends with, exact match
   - **Date Fields**: Before, after, between, exact date
   - **Choice Fields**: Select from dropdown options
   - **Number Fields**: Equal, greater than, less than, between

### Filter Examples
- Find all people in "New York": City = "New York"
- Find recent additions: Created > [Last Week]
- Find active employees: Status = "Active"

### Combining Filters
Multiple filters work with AND logic - all conditions must match.

### Clearing Filters
Click **Clear** button or press **Escape** to remove all filters.

---

## Data Import/Export

### Exporting Data

1. Navigate to the desired view
2. Apply any filters to limit export
3. Click **📤 Export** or press **Ctrl+Shift+E**
4. Choose format:
   - **CSV**: For spreadsheet applications
   - **JSON**: For data interchange
   - **PDF**: For reports (coming soon)
5. Select save location
6. Click **Save**

### Importing Data

1. Click **📥 Import** or press **Ctrl+Shift+I**
2. Select import file (CSV or JSON)
3. Map columns to fields:
   - Auto-mapping attempts to match column names
   - Manual mapping for unmatched columns
4. Preview import data
5. Choose import options:
   - **Skip duplicates**: Ignore existing records
   - **Update existing**: Update matching records
   - **Create all**: Create new records only
6. Click **Import**

### Import File Format

**CSV Requirements**:
```csv
first_name,last_name,email,phone,date_of_birth
John,Doe,john.doe@example.com,555-0100,1990-01-15
Jane,Smith,jane.smith@example.com,555-0101,1985-03-22
```

**JSON Format**:
```json
[
  {
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com",
    "phone": "555-0100",
    "date_of_birth": "1990-01-15"
  }
]
```

---

## Settings and Preferences

Access settings via **Tools → Settings** or press **Ctrl+,**

### General Settings
- **User Information**: Your name and email
- **Auto-save**: Enable/disable and set interval
- **Confirmations**: Toggle delete confirmations
- **Default Values**: Set default country, date format

### Connection Settings
- **API URL**: Server address
- **API Key**: Authentication key
- **Timeout**: Connection timeout in seconds
- **Retry Attempts**: Number of retry attempts
- **Caching**: Enable/disable response caching

### Appearance Settings
- **Theme**: Light, Dark, or Auto
- **Font**: Application font and size
- **Window**: Remember size/position, start maximized
- **UI Elements**: Show/hide toolbar, status bar

### Behavior Settings
- **Table**: Rows per page, sorting, filtering options
- **Search**: Search-as-you-type, delay, highlighting
- **Notifications**: Success/error notifications, duration

### Advanced Settings
- **Performance**: Lazy loading, cache size
- **Logging**: Enable logging, log level, log file
- **Database**: Backup/restore options

---

## Keyboard Shortcuts

### Navigation
| Shortcut | Action |
|----------|--------|
| Alt+1 | Go to Dashboard |
| Alt+2 | Go to People |
| Alt+3 | Go to Departments |
| Alt+4 | Go to Positions |
| Alt+5 | Go to Employment |

### Actions
| Shortcut | Action |
|----------|--------|
| Ctrl+N | Add new person |
| Ctrl+E | Edit selected |
| Delete | Delete selected |
| Ctrl+F | Focus search |
| F5 | Refresh view |
| Escape | Clear search/Cancel |

### File Operations
| Shortcut | Action |
|----------|--------|
| Ctrl+Shift+E | Export data |
| Ctrl+Shift+I | Import data |
| Ctrl+S | Save (in forms) |
| Ctrl+Q | Quit application |

### View Options
| Shortcut | Action |
|----------|--------|
| Ctrl+Shift+T | Toggle theme |
| Ctrl+, | Open settings |
| F1 | Open help |
| F11 | Toggle fullscreen |

### Table Navigation
| Shortcut | Action |
|----------|--------|
| ↑/↓ | Navigate rows |
| Page Up/Down | Navigate pages |
| Home/End | First/Last row |
| Space | Select row |
| Ctrl+A | Select all |

---

## Themes and Appearance

### Switching Themes
1. **Quick Toggle**: Press **Ctrl+Shift+T** to switch between light and dark
2. **Menu**: View → Theme → Select theme
3. **Settings**: Tools → Settings → Appearance → Theme

### Theme Options
- **Light Theme**: Bright, clean interface for well-lit environments
- **Dark Theme**: Reduced eye strain in low-light conditions
- **Auto**: Follows system theme (coming soon)

### Customization
- Adjust font size in Settings → Appearance
- Choose accent colors for better visibility
- Configure UI element visibility

---

## Troubleshooting

### Connection Issues

**Problem**: Cannot connect to server
- **Solution 1**: Verify server is running
- **Solution 2**: Check API URL is correct
- **Solution 3**: Confirm API key is valid
- **Solution 4**: Check firewall settings

**Problem**: Connection timeout
- **Solution**: Increase timeout in Settings → Connection

### Data Issues

**Problem**: Changes not saving
- **Solution 1**: Check connection status
- **Solution 2**: Verify you have edit permissions
- **Solution 3**: Check for validation errors

**Problem**: Data not refreshing
- **Solution 1**: Press F5 to manual refresh
- **Solution 2**: Clear cache in Tools → Clear Cache
- **Solution 3**: Check auto-refresh settings

### Performance Issues

**Problem**: Application running slowly
- **Solution 1**: Reduce rows per page in Settings
- **Solution 2**: Clear cache regularly
- **Solution 3**: Enable lazy loading in Advanced Settings

### Display Issues

**Problem**: Text too small/large
- **Solution**: Adjust font size in Settings → Appearance

**Problem**: Theme not applying
- **Solution**: Restart application after theme change

---

## Tips and Best Practices

### Data Entry
1. **Use Tab key** to move between fields quickly
2. **Set default values** in Settings to speed up data entry
3. **Use templates** for common entries (coming soon)
4. **Enable auto-save** to prevent data loss

### Organization
1. **Use tags** to categorize people
2. **Add notes** for important information
3. **Keep emergency contacts** updated
4. **Regular backups** via Advanced Settings

### Search Efficiency
1. **Use quick search** for simple lookups
2. **Save common filters** (coming soon)
3. **Learn keyboard shortcuts** for faster navigation
4. **Use wildcards** in search (* for any characters)

### Data Management
1. **Regular exports** for backup
2. **Validate before import** to prevent errors
3. **Use bulk operations** for multiple changes
4. **Archive old records** instead of deleting

### Security
1. **Keep API key secure** - never share it
2. **Use strong authentication**
3. **Regular password updates**
4. **Log out when finished**

### Performance
1. **Limit visible columns** to essential data
2. **Use pagination** for large datasets
3. **Clear cache periodically**
4. **Close unused views**

---

## Support and Feedback

### Getting Help
- Press **F1** for context-sensitive help
- Check this user guide for detailed instructions
- Review tooltips by hovering over UI elements

### Reporting Issues
When reporting issues, include:
1. Steps to reproduce the problem
2. Error messages (if any)
3. Screenshot of the issue
4. System information (from Help → About)

### Feature Requests
We welcome suggestions for improvements! Please provide:
1. Description of the feature
2. Use case and benefits
3. Priority level

---

## Appendix

### Date Format Examples
- **DD-MM-YYYY**: 25-12-2024
- **MM-DD-YYYY**: 12-25-2024
- **YYYY-MM-DD**: 2024-12-25

### Status Values
- **Active**: Currently employed/active
- **Inactive**: Not currently active
- **Pending**: Awaiting processing
- **Archived**: Historical record

### Field Validation Rules
- **Email**: Must be valid email format
- **Phone**: Accepts various formats
- **Date of Birth**: Must be in the past
- **ZIP Code**: 5 or 9 digit format

---

*Last Updated: November 2024*
*Version: 1.0.0*