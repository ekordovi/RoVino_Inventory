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
    wines = conn.execute('''
        SELECT DISTINCT Wines.wine_id, Wines.name, Wines.type, Inventory.current_stock
        FROM Wines 
        JOIN Inventory ON Wines.wine_id = Inventory.wine_id
    ''').fetchall()
    conn.close()
    return render_template('index.html', wines=wines, success_message=request.args.get('success_message'))

# Route: Update Inventory
@app.route('/update', methods=['POST'])
def update():
    updates = request.form
    conn = get_db_connection()
    for wine_id, new_stock in updates.items():
        conn.execute('UPDATE Inventory SET current_stock = ? WHERE wine_id = ?', (new_stock, wine_id))
    conn.commit()
    conn.close()
    return redirect(url_for('index', success_message="Inventory updated successfully!"))

# Route: Add New Wine (GET and POST)
@app.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        name = request.form['name']
        wine_type = request.form['type']
        stock = request.form['current_stock']

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Insert wine into Wines table
            cursor.execute('INSERT INTO Wines (name, type) VALUES (?, ?)', (name, wine_type))
            wine_id = cursor.lastrowid  # Get the wine ID of the newly inserted wine

            # Insert inventory into Inventory table
            cursor.execute('INSERT INTO Inventory (wine_id, current_stock) VALUES (?, ?)', (wine_id, stock))

            # Commit changes and close connection
            conn.commit()

        except Exception as e:
            print(f"Error: {e}")
            conn.rollback()  # Rollback in case of an error

        finally:
            conn.close()  # Ensure the connection is always closed, even if there's an error

        return redirect(url_for('index', success_message="New wine added successfully!"))

    return render_template('add.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

