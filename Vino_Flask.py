from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

# Database connection helper
def get_db_connection():
    conn = sqlite3.connect('Vino.sqlite')
    conn.row_factory = sqlite3.Row  # Allows access by column names
    return conn

# Route: Show Inventory
@app.route('/')
def index():
    conn = get_db_connection()
    items = conn.execute('SELECT * FROM inventory').fetchall()
    conn.close()
    return render_template('index.html', items=items, success_message=request.args.get('success_message'))

# Route: Add New Inventory Item
@app.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        item_name = request.form['item_name']
        category = request.form['category']
        quantity = request.form['quantity']
        price = request.form['price']

        conn = get_db_connection()
        conn.execute(
            'INSERT INTO inventory (item_name, category, quantity, price) VALUES (?, ?, ?, ?)',
            (item_name, category, quantity, price)
        )
        conn.commit()
        conn.close()
        return redirect(url_for('index', success_message="New item added successfully!"))

    return render_template('add.html')

# Route: Update Existing Inventory Item
@app.route('/update/<int:item_id>', methods=['GET', 'POST'])
def update(item_id):
    conn = get_db_connection()
    item = conn.execute('SELECT * FROM inventory WHERE id = ?', (item_id,)).fetchone()

    if request.method == 'POST':
        item_name = request.form['item_name']
        category = request.form['category']
        quantity = request.form['quantity']
        price = request.form['price']

        conn.execute(
            'UPDATE inventory SET item_name = ?, category = ?, quantity = ?, price = ?, last_updated = CURRENT_TIMESTAMP WHERE id = ?',
            (item_name, category, quantity, price, item_id)
        )
        conn.commit()
        conn.close()
        return redirect(url_for('index', success_message="Item updated successfully!"))

    return render_template('update.html', item=item)

# Route: Delete an Inventory Item
@app.route('/delete/<int:item_id>', methods=['POST'])
def delete(item_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM inventory WHERE id = ?', (item_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index', success_message="Item deleted successfully!"))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

