from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
import sqlite3
from contextlib import contextmanager
import logging
from typing import Optional, List, Dict, Any
from datetime import date
from functools import wraps
import os
import hashlib
import secrets

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(16))  # Use environment variable or generate random key
app.config['SESSION_COOKIE_SECURE'] = True  # For HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevents JavaScript access to session cookie
app.config['PERMANENT_SESSION_LIFETIME'] = 1800  # 30 minutes
logging.basicConfig(level=logging.INFO)

# Custom exception for database errors
class DatabaseError(Exception):
    pass

# Database connection context manager
@contextmanager
def get_db_connection():
    conn = None
    try:
        conn = sqlite3.connect('Vino.sqlite')
        conn.row_factory = sqlite3.Row
        yield conn
        conn.commit()
    except sqlite3.Error as e:
        if conn:
            conn.rollback()
        logging.error(f"Database error: {str(e)}")
        raise DatabaseError(f"Database operation failed: {str(e)}")
    finally:
        if conn:
            conn.close()

# Data validation functions
def validate_item(item_data: Dict[str, Any]) -> List[str]:
    errors = []
    if not item_data.get('item_name'):
        errors.append("Item name is required")
    if not item_data.get('quantity').isdigit():
        errors.append("Quantity must be a positive number")
    try:
        price = float(item_data.get('price', 0))
        if price < 0:
            errors.append("Price cannot be negative")
    except ValueError:
        errors.append("Price must be a valid number")
    return errors

# Initialize user table
def init_user_table():
    try:
        with get_db_connection() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS Users (
                    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    is_admin INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL
                )
            ''')
            
            # Check if admin user exists, if not create one
            admin = conn.execute('SELECT * FROM Users WHERE username = ?', ('admin',)).fetchone()
            if not admin:
                salt = secrets.token_hex(16)
                password = "admin123"  # Default password
                password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
                
                conn.execute('''
                    INSERT INTO Users (username, password_hash, salt, is_admin, created_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', ('admin', password_hash, salt, 1, date.today().isoformat()))
                
                logging.info("Created default admin user")
    except Exception as e:
        logging.error(f"Error initializing user table: {str(e)}")

# Initialize user table when app starts
with app.app_context():
    init_user_table()

# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in to access this page", "error")
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# Admin-only decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in to access this page", "error")
            return redirect(url_for('login', next=request.url))
        
        if not session.get('is_admin'):
            flash("You don't have permission to access this page", "error")
            return redirect(url_for('index'))
            
        return f(*args, **kwargs)
    return decorated_function

# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        try:
            with get_db_connection() as conn:
                user = conn.execute('SELECT * FROM Users WHERE username = ?', (username,)).fetchone()
                
                if user:
                    password_hash = hashlib.sha256((password + user['salt']).encode()).hexdigest()
                    
                    if password_hash == user['password_hash']:
                        session.clear()
                        session['user_id'] = user['user_id']
                        session['username'] = user['username']
                        session['is_admin'] = bool(user['is_admin'])
                        
                        next_page = request.args.get('next')
                        if next_page and next_page.startswith('/'):
                            return redirect(next_page)
                        return redirect(url_for('index'))
                
                flash("Invalid username or password", "error")
                
        except DatabaseError as e:
            flash(str(e), "error")
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out", "success")
    return redirect(url_for('login'))

# User management routes (admin only)
@app.route('/users')
@admin_required
def users():
    try:
        with get_db_connection() as conn:
            all_users = conn.execute('SELECT user_id, username, is_admin, created_at FROM Users').fetchall()
            return render_template('users.html', users=all_users)
    except DatabaseError as e:
        flash(str(e), "error")
        return redirect(url_for('index'))

@app.route('/users/add', methods=['GET', 'POST'])
@admin_required
def add_user():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        is_admin = request.form.get('is_admin') == 'on'
        
        if not username or not password:
            flash("Username and password are required", "error")
            return render_template('add_user.html')
            
        try:
            with get_db_connection() as conn:
                # Check if username exists
                existing = conn.execute('SELECT username FROM Users WHERE username = ?', (username,)).fetchone()
                if existing:
                    flash("Username already exists", "error")
                    return render_template('add_user.html')
                
                # Create new user
                salt = secrets.token_hex(16)
                password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
                
                conn.execute('''
                    INSERT INTO Users (username, password_hash, salt, is_admin, created_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (username, password_hash, salt, 1 if is_admin else 0, date.today().isoformat()))
                
                flash("User created successfully", "success")
                return redirect(url_for('users'))
                
        except DatabaseError as e:
            flash(str(e), "error")
            
    return render_template('add_user.html')

@app.route('/users/delete/<int:user_id>', methods=['POST'])
@admin_required
def delete_user(user_id):
    try:
        with get_db_connection() as conn:
            # Prevent deleting yourself
            if user_id == session.get('user_id'):
                flash("You cannot delete your own account", "error")
                return redirect(url_for('users'))
                
            conn.execute('DELETE FROM Users WHERE user_id = ?', (user_id,))
            flash("User deleted successfully", "success")
            
    except DatabaseError as e:
        flash(str(e), "error")
        
    return redirect(url_for('users'))

# Change password route
@app.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not current_password or not new_password or not confirm_password:
            flash("All fields are required", "error")
            return render_template('change_password.html')
            
        if new_password != confirm_password:
            flash("New passwords do not match", "error")
            return render_template('change_password.html')
            
        try:
            with get_db_connection() as conn:
                user = conn.execute('SELECT * FROM Users WHERE user_id = ?', (session['user_id'],)).fetchone()
                
                # Verify current password
                current_hash = hashlib.sha256((current_password + user['salt']).encode()).hexdigest()
                if current_hash != user['password_hash']:
                    flash("Current password is incorrect", "error")
                    return render_template('change_password.html')
                
                # Update password
                salt = secrets.token_hex(16)
                new_hash = hashlib.sha256((new_password + salt).encode()).hexdigest()
                
                conn.execute('''
                    UPDATE Users 
                    SET password_hash = ?, salt = ?
                    WHERE user_id = ?
                ''', (new_hash, salt, session['user_id']))
                
                flash("Password changed successfully", "success")
                return redirect(url_for('index'))
                
        except DatabaseError as e:
            flash(str(e), "error")
            
    return render_template('change_password.html')

# Home route - display inventory
@app.route('/')
@login_required
def index():
    try:
        with get_db_connection() as conn:
            inventory = conn.execute('''
                SELECT i.id, i.item_name, i.category, i.quantity, i.price, 
                       i.low_stock_threshold, i.last_updated, w.wine_id, w.name, w.type
                FROM Inventory i
                LEFT JOIN Wines w ON i.wine_id = w.wine_id
                ORDER BY i.category, i.item_name
            ''').fetchall()
        return render_template('index.html', 
                             items=inventory, 
                             success_message=request.args.get('success_message'))
    except DatabaseError as e:
        flash(str(e), 'error')
        return render_template('index.html', items=[])

# Add new wine to inventory
@app.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        item_data = {
            'item_name': request.form.get('item_name', '').strip(),
            'wine_name': request.form.get('wine_name', '').strip(),
            'wine_type': request.form.get('wine_type', '').strip(),
            'category': request.form.get('category', 'wine').strip(),
            'quantity': request.form.get('quantity', '0'),
            'price': request.form.get('price', '0'),
            'low_stock_threshold': request.form.get('low_stock_threshold', '5')
        }
        
        errors = validate_item(item_data)
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('add.html', item=item_data)
        
        try:
            with get_db_connection() as conn:
                # First, insert or get the wine
                wine_id = None
                if item_data['category'] == 'wine' and item_data['wine_name'] and item_data['wine_type']:
                    conn.execute('''
                        INSERT OR IGNORE INTO Wines (name, type, price) 
                        VALUES (?, ?, ?)
                    ''', (
                        item_data['wine_name'],
                        item_data['wine_type'],
                        float(item_data['price'])
                    ))
                    
                    wine_row = conn.execute('''
                        SELECT wine_id FROM Wines 
                        WHERE name = ? AND type = ?
                    ''', (item_data['wine_name'], item_data['wine_type'])).fetchone()
                    
                    if wine_row:
                        wine_id = wine_row['wine_id']
                
                # Then insert into inventory
                conn.execute('''
                    INSERT INTO Inventory 
                    (item_name, category, quantity, price, wine_id, low_stock_threshold, last_updated) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    item_data['item_name'],
                    item_data['category'],
                    int(item_data['quantity']),
                    float(item_data['price']),
                    wine_id,
                    int(item_data['low_stock_threshold']),
                    date.today().isoformat()
                ))
            flash("New item added successfully!", 'success')
            return redirect(url_for('index'))
        except DatabaseError as e:
            flash(str(e), 'error')
            return render_template('add.html', item=item_data)
            
    return render_template('add.html')

# Update existing inventory item
@app.route('/update/<int:item_id>', methods=['GET', 'POST'])
@login_required
def update(item_id: int):
    try:
        with get_db_connection() as conn:
            if request.method == 'POST':
                item_data = {
                    'item_name': request.form.get('item_name', '').strip(),
                    'category': request.form.get('category', '').strip(),
                    'quantity': request.form.get('quantity', '0'),
                    'price': request.form.get('price', '0'),
                    'low_stock_threshold': request.form.get('low_stock_threshold', '5')
                }
                
                errors = validate_item(item_data)
                if errors:
                    for error in errors:
                        flash(error, 'error')
                    return render_template('update.html', item=item_data)

                conn.execute('''
                    UPDATE Inventory 
                    SET item_name = ?, category = ?, quantity = ?, price = ?, 
                        low_stock_threshold = ?, last_updated = ?
                    WHERE id = ?
                ''', (
                    item_data['item_name'],
                    item_data['category'],
                    int(item_data['quantity']),
                    float(item_data['price']),
                    int(item_data['low_stock_threshold']),
                    date.today().isoformat(),
                    item_id
                ))
                
                # If wine, update wine information too
                wine_id = request.form.get('wine_id')
                if wine_id and item_data['category'] == 'wine':
                    conn.execute('''
                        UPDATE Wines
                        SET price = ?
                        WHERE wine_id = ?
                    ''', (float(item_data['price']), wine_id))
                
                flash("Item updated successfully!", 'success')
                return redirect(url_for('index'))
            
            item = conn.execute('''
                SELECT i.*, w.wine_id, w.name as wine_name, w.type as wine_type
                FROM Inventory i
                LEFT JOIN Wines w ON i.wine_id = w.wine_id
                WHERE i.id = ?
            ''', (item_id,)).fetchone()
            
            if not item:
                flash("Item not found", 'error')
                return redirect(url_for('index'))
            return render_template('update.html', item=item)
            
    except DatabaseError as e:
        flash(str(e), 'error')
        return redirect(url_for('index'))

# Delete an inventory item
@app.route('/delete/<int:item_id>', methods=['POST'])
@login_required
def delete(item_id: int):
    try:
        with get_db_connection() as conn:
            # Check if this is a wine inventory item
            item = conn.execute('SELECT wine_id FROM Inventory WHERE id = ?', (item_id,)).fetchone()
            
            result = conn.execute('DELETE FROM Inventory WHERE id = ?', (item_id,))
            if result.rowcount == 0:
                flash("Item not found", 'error')
            else:
                # Also remove from Wines table if no other inventory references it
                if item and item['wine_id']:
                    remaining = conn.execute('SELECT COUNT(*) as count FROM Inventory WHERE wine_id = ?', 
                                            (item['wine_id'],)).fetchone()
                    if remaining['count'] == 0:
                        conn.execute('DELETE FROM Wines WHERE wine_id = ?', (item['wine_id'],))
                
                flash("Item deleted successfully!", 'success')
    except DatabaseError as e:
        flash(str(e), 'error')
    return redirect(url_for('index'))

# Add restock record
@app.route('/restock/<int:wine_id>', methods=['GET', 'POST'])
@login_required
def restock(wine_id: int):
    try:
        with get_db_connection() as conn:
            if request.method == 'POST':
                quantity = request.form.get('quantity', '0')
                
                if not quantity.isdigit() or int(quantity) <= 0:
                    flash("Quantity must be a positive number", 'error')
                    return redirect(url_for('restock', wine_id=wine_id))
                
                # Add restock record
                conn.execute('''
                    INSERT INTO Restock (wine_id, quantity_restocked, restock_date)
                    VALUES (?, ?, ?)
                ''', (wine_id, int(quantity), date.today().isoformat()))
                
                # Update inventory
                conn.execute('''
                    UPDATE Inventory
                    SET quantity = quantity + ?,
                        last_updated = ?
                    WHERE wine_id = ?
                ''', (int(quantity), date.today().isoformat(), wine_id))
                
                flash("Restock recorded successfully!", 'success')
                return redirect(url_for('index'))
            
            wine = conn.execute('''
                SELECT w.*, i.quantity as current_stock
                FROM Wines w
                JOIN Inventory i ON w.wine_id = i.wine_id
                WHERE w.wine_id = ?
            ''', (wine_id,)).fetchone()
            
            if not wine:
                flash("Wine not found", 'error')
                return redirect(url_for('index'))
            
            return render_template('restock.html', wine=wine)
    except DatabaseError as e:
        flash(str(e), 'error')
        return redirect(url_for('index'))

# View restock history
@app.route('/history')
@login_required
def history():
    try:
        with get_db_connection() as conn:
            restock_history = conn.execute('''
                SELECT r.restock_id, r.quantity_restocked, r.restock_date,
                       w.name, w.type, w.wine_id
                FROM Restock r
                JOIN Wines w ON r.wine_id = w.wine_id
                ORDER BY r.restock_date DESC
            ''').fetchall()
            
            return render_template('history.html', history=restock_history)
    except DatabaseError as e:
        flash(str(e), 'error')
        return redirect(url_for('index'))

# Low stock alert dashboard
@app.route('/alerts')
@login_required
def alerts():
    try:
        with get_db_connection() as conn:
            low_stock_items = conn.execute('''
                SELECT i.id, i.item_name, i.quantity, i.low_stock_threshold,
                       w.name, w.type, w.wine_id
                FROM Inventory i
                LEFT JOIN Wines w ON i.wine_id = w.wine_id
                WHERE i.quantity <= i.low_stock_threshold
                ORDER BY (i.quantity * 1.0 / i.low_stock_threshold)
            ''').fetchall()
            
            return render_template('alerts.html', items=low_stock_items)
    except DatabaseError as e:
        flash(str(e), 'error')
        return redirect(url_for('index'))

# API endpoint for inventory data
@app.route('/api/inventory', methods=['GET'])
@login_required
def api_inventory():
    try:
        with get_db_connection() as conn:
            inventory = conn.execute('''
                SELECT i.id, i.item_name, i.category, i.quantity, i.price, 
                       i.low_stock_threshold, i.last_updated, w.name, w.type
                FROM Inventory i
                LEFT JOIN Wines w ON i.wine_id = w.wine_id
            ''').fetchall()
            
            # Convert to list of dicts for JSON serialization
            result = []
            for item in inventory:
                item_dict = dict(item)
                result.append(item_dict)
                
            return jsonify({"inventory": result})
    except DatabaseError as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)