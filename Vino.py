import urllib.request, urllib.parse, urllib.error
import sqlite3
import json
import ssl
import sys
from datetime import date

conn = sqlite3.connect('Vino.sqlite')
cur = conn.cursor()

cur.execute('PRAGMA foreign_keys = ON;')

# Main Wines table
cur.execute('''
        CREATE TABLE IF NOT EXISTS Wines (
            wine_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
            name VARCHAR(100) NOT NULL,
            type VARCHAR(50) NOT NULL,
            price REAL,
            category VARCHAR(50) DEFAULT 'wine',
            UNIQUE(name, type)
);
''')

# Sample wine data
wines = [
    ('Yealands', 'Sauvignon Blanc', 19.99),
    ('Daou', 'Chardonnay', 24.99),
    ('Daou', 'Cabernet Sauvignon', 29.99),
    ('Daou - Pessimist', 'Red Blend', 27.99),
    ('Ruffino', 'Chianti Classico', 21.99),
    ('Ruffino', 'Chianti Reserva', 25.99)
]

for wine in wines:
    cur.execute('INSERT OR IGNORE INTO Wines (name, type, price) VALUES (?, ?, ?)', 
                (wine[0], wine[1], wine[2]))

# Inventory table with additional fields to match Flask app
cur.execute('''
    CREATE TABLE IF NOT EXISTS Inventory (
        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
        wine_id INTEGER NOT NULL UNIQUE,
        item_name VARCHAR(150),
        category VARCHAR(50) DEFAULT 'wine',
        quantity INTEGER NOT NULL,
        price REAL,
        low_stock_threshold INTEGER,
        last_updated DATE,
        FOREIGN KEY (wine_id) REFERENCES Wines(wine_id)
        );
''')

# Get today's date for the records
today = date.today().isoformat()

# Add inventory records that match with the Flask app requirements
cur.execute('''INSERT OR REPLACE INTO Inventory 
               (wine_id, item_name, quantity, price, low_stock_threshold, last_updated, category) 
               SELECT w.wine_id, w.name || ' - ' || w.type, ?, w.price, ?, ?, 'wine'
               FROM Wines w
               WHERE w.wine_id = ?''', 
            (10, 5, today, 1))

cur.execute('''INSERT OR REPLACE INTO Inventory 
               (wine_id, item_name, quantity, price, low_stock_threshold, last_updated, category) 
               SELECT w.wine_id, w.name || ' - ' || w.type, ?, w.price, ?, ?, 'wine'
               FROM Wines w
               WHERE w.wine_id = ?''', 
            (8, 3, today, 2))

cur.execute('''INSERT OR REPLACE INTO Inventory 
               (wine_id, item_name, quantity, price, low_stock_threshold, last_updated, category) 
               SELECT w.wine_id, w.name || ' - ' || w.type, ?, w.price, ?, ?, 'wine'
               FROM Wines w
               WHERE w.wine_id = ?''', 
            (15, 7, today, 3))

# Restock table
cur.execute('''
    CREATE TABLE IF NOT EXISTS Restock (
        restock_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
        wine_id INTEGER NOT NULL,
        quantity_restocked INTEGER NOT NULL,
        restock_date DATE NOT NULL,
        FOREIGN KEY (wine_id) REFERENCES Wines(wine_id)
    );
''')

# Add sample restock history
cur.execute('INSERT OR IGNORE INTO Restock (wine_id, quantity_restocked, restock_date) VALUES (?, ?, ?)', 
            (1, 5, '2024-11-15'))
cur.execute('INSERT OR IGNORE INTO Restock (wine_id, quantity_restocked, restock_date) VALUES (?, ?, ?)', 
            (2, 4, '2024-11-20'))
cur.execute('INSERT OR IGNORE INTO Restock (wine_id, quantity_restocked, restock_date) VALUES (?, ?, ?)', 
            (3, 7, '2024-11-25'))

print("Database initialized successfully.")
conn.commit()
conn.close()
