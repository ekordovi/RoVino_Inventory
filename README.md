# RoVino - Wine Inventory Management System

RoVino is a web-based wine inventory management system built with Python Flask and SQLite. It helps you keep track of your wine collection, manage inventory levels, and record restocking activities.

## Features

- **User Authentication**: Secure login system with role-based access control
- **Inventory Management**: Track wine and other related items in your inventory
- **Stock Alerts**: Automatically identify when items are running low
- **Restock Tracking**: Record when you restock items and view history
- **Wine Details**: Store information about wines including name, type, and price
- **User Management**: Admin interface for managing system users

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/rovino.git
   cd rovino
   ```

2. Create a virtual environment (recommended):
   ```
   python -m venv venv
   ```

3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`

4. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

5. Initialize the database:
   ```
   python Vino.py
   ```

6. Run the application:
   ```
   python Vino_Flask.py
   ```

7. Access the application in your web browser at `http://localhost:5000`

## Directory Structure

```
RoVino/
│
├── Vino.py                # Database initialization script
├── Vino_Flask.py          # Flask application
├── Vino.sqlite            # SQLite database
├── requirements.txt       # Python dependencies
│
├── templates/             # Flask HTML templates
│   ├── layout.html        # Base template
│   ├── login.html         # Login page
│   ├── index.html         # Inventory list
│   ├── add.html           # Add new item
│   ├── update.html        # Update existing item
│   ├── restock.html       # Restock wine
│   ├── history.html       # Restock history
│   ├── alerts.html        # Low stock alerts
│   ├── users.html         # User management
│   ├── add_user.html      # Add new user
│   └── change_password.html # Change password page
│
└── static/                # Static assets
    ├── css/
    │   └── custom.css     # Custom styles
    ├── js/
    │   └── app.js         # JavaScript functionality
    └── img/
        └── logo.png       # Application logo
```

## Database Schema

RoVino uses an SQLite database with the following tables:

1. **Wines**: Stores information about wine varieties
   - wine_id: Unique identifier
   - name: Wine name (e.g., "Daou")
   - type: Wine type (e.g., "Cabernet Sauvignon")
   - price: Price per bottle
   - category: Default "wine"

2. **Inventory**: Tracks current inventory items
   - id: Unique identifier
   - wine_id: Foreign key to Wines table (for wine items)
   - item_name: Name of the item
   - category: Type of item (wine, accessory, equipment, etc.)
   - quantity: Current quantity in stock
   - price: Current price
   - low_stock_threshold: Level at which to alert low stock
   - last_updated: Date of last inventory update

3. **Restock**: Records history of restocking activities
   - restock_id: Unique identifier
   - wine_id: Foreign key to Wines table
   - quantity_restocked: Amount added to inventory
   - restock_date: Date of restock

4. **Users**: Stores user authentication information
   - user_id: Unique identifier
   - username: User login name
   - password_hash: Securely stored password
   - salt: Random value for password security
   - is_admin: Boolean indicating admin privileges
   - created_at: Account creation date

5. **WineNotes**: Stores tasting notes and ratings
   - note_id: Unique identifier
   - wine_id: Foreign key to Wines table
   - user_id: Foreign key to Users table
   - rating: Numerical rating
   - tasting_notes: Text notes about the wine
   - date_added: Date the note was created

## Usage

### Default Login

- Username: `admin`
- Password: `admin123`

**Important**: Change the default password after first login.

### Adding Items

1. Log in to the system
2. Click "Add Item" on the main inventory page
3. Fill in the item details
4. For wines, provide both the wine name and type
5. Set a low stock threshold for notifications
6. Click "Add Item" to save

### Restocking

1. Navigate to the inventory page
2. Find the wine you want to restock
3. Click the "+" button in the Actions column
4. Enter the quantity you're adding
5. Click "Restock Wine" to save

### Managing Users (Admin only)

1. Log in as an admin user
2. Navigate to the user management page
3. To add a user, click "Add New User"
4. To delete a user, click the "Delete" button next to their entry

## Security Features

- Password hashing with salt
- Session management
- CSRF protection through Flask
- Role-based access control
- Secure cookie settings
- Input validation and sanitization

## Future Enhancements

- Wine tasting notes and ratings system
- QR code scanning for inventory management
- Export data to CSV/Excel
- Advanced reporting and analytics
- Mobile app integration

## License

[MIT License](LICENSE)

## Acknowledgements

- Flask web framework
- Bootstrap for responsive design
- SQLite for database storage
- Font Awesome for icons

## Support

For issues, questions, or feature requests, please [open an issue](https://github.com/yourusername/rovino/issues) on GitHub.