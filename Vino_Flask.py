from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import sqlite3
from contextlib import contextmanager
import logging
from typing import Optional, List, Dict, Any
from datetime import date

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Required for flash messages
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

# Home route - display inventory
@app.route('/')
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
    app.run(debug=True, host='0.0.0.0', port=5000)