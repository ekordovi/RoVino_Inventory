from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from contextlib import contextmanager
import logging
from typing import Optional, List, Dict, Any

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

@app.route('/')
def index():
    try:
        with get_db_connection() as conn:
            items = conn.execute('SELECT * FROM inventory').fetchall()
        return render_template('index.html', 
                             items=items, 
                             success_message=request.args.get('success_message'))
    except DatabaseError as e:
        flash(str(e), 'error')
        return render_template('index.html', items=[])

@app.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        item_data = {
            'item_name': request.form.get('item_name', '').strip(),
            'category': request.form.get('category', '').strip(),
            'quantity': request.form.get('quantity', '0'),
            'price': request.form.get('price', '0')
        }
        
        errors = validate_item(item_data)
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('add.html', item=item_data)
        
        try:
            with get_db_connection() as conn:
                conn.execute('''
                    INSERT INTO inventory (item_name, category, quantity, price) 
                    VALUES (?, ?, ?, ?)
                ''', (
                    item_data['item_name'],
                    item_data['category'],
                    int(item_data['quantity']),
                    float(item_data['price'])
                ))
            flash("New item added successfully!", 'success')
            return redirect(url_for('index'))
        except DatabaseError as e:
            flash(str(e), 'error')
            return render_template('add.html', item=item_data)
            
    return render_template('add.html')

@app.route('/update/<int:item_id>', methods=['GET', 'POST'])
def update(item_id: int):
    try:
        with get_db_connection() as conn:
            if request.method == 'POST':
                item_data = {
                    'item_name': request.form.get('item_name', '').strip(),
                    'category': request.form.get('category', '').strip(),
                    'quantity': request.form.get('quantity', '0'),
                    'price': request.form.get('price', '0')
                }
                
                errors = validate_item(item_data)
                if errors:
                    for error in errors:
                        flash(error, 'error')
                    return render_template('update.html', item=item_data)

                conn.execute('''
                    UPDATE inventory 
                    SET item_name = ?, category = ?, quantity = ?, price = ?
                    WHERE id = ?
                ''', (
                    item_data['item_name'],
                    item_data['category'],
                    int(item_data['quantity']),
                    float(item_data['price']),
                    item_id
                ))
                flash("Item updated successfully!", 'success')
                return redirect(url_for('index'))
            
            item = conn.execute('SELECT * FROM inventory WHERE id = ?', (item_id,)).fetchone()
            if not item:
                flash("Item not found", 'error')
                return redirect(url_for('index'))
            return render_template('update.html', item=item)
            
    except DatabaseError as e:
        flash(str(e), 'error')
        return redirect(url_for('index'))

@app.route('/delete/<int:item_id>', methods=['POST'])
def delete(item_id: int):
    try:
        with get_db_connection() as conn:
            result = conn.execute('DELETE FROM inventory WHERE id = ?', (item_id,))
            if result.rowcount == 0:
                flash("Item not found", 'error')
            else:
                flash("Item deleted successfully!", 'success')
    except DatabaseError as e:
        flash(str(e), 'error')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)