import urllib.request, urllib.parse, urllib.error
import sqlite3
import json
import ssl
import sys

conn = sqlite3.connect('Vino.sqlite')
cur = conn.cursor()

cur.execute('PRAGMA foreign_keys = ON;')

cur.execute('''
        CREATE TABLE IF NOT EXISTS Wines (
            wine_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
            name VARCHAR(100) NOT NULL,
            type VARCHAR(50) NOT NULL,
            UNIQUE(name, type)
);
''')

cur.execute('INSERT OR IGNORE INTO Wines (name, type) VALUES (?, ?)', ('Yealands', 'Sauvignon Blanc'))
cur.execute('INSERT OR IGNORE INTO Wines (name, type) VALUES (?, ?)', ('Daou', 'Chardonnay'))
cur.execute('INSERT OR IGNORE INTO Wines (name, type) VALUES (?, ?)', ('Daou', 'Cabernet Sauvignon'))
cur.execute('INSERT OR IGNORE INTO Wines (name, type) VALUES (?, ?)', ('Daou - Pessimist', 'Red Blend'))
cur.execute('INSERT OR IGNORE INTO Wines (name, type) VALUES (?, ?)', ('Ruffino', 'Chianti Classico'))
cur.execute('INSERT OR IGNORE INTO Wines (name, type) VALUES (?, ?)', ('Ruffino', 'Chianti Reserva'))



cur.execute('''
    CREATE TABLE IF NOT EXISTS Inventory (
        inventory_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
        wine_id INTEGER NOT NULL UNIQUE,
        current_stock INTEGER NOT NULL,
        low_stock_threshold INTEGER,
        last_updated DATE,
        FOREIGN KEY (wine_id) REFERENCES Wines(wine_id)
        );
''')

cur.execute('INSERT INTO Inventory (wine_id, current_stock, low_stock_threshold, last_updated) VALUES (?, ?, ?, ?)', 
            (1, 10, 5, "2024-11-30"))
cur.execute('INSERT INTO Inventory (wine_id, current_stock, low_stock_threshold, last_updated) VALUES (?, ?, ?, ?)', 
            (2, 8, 3, "2024-11-30"))
cur.execute('INSERT INTO Inventory (wine_id, current_stock, low_stock_threshold, last_updated) VALUES (?, ?, ?, ?)', 
            (3, 15, 7, "2024-11-30"))



cur.execute('''
    CREATE TABLE IF NOT EXISTS Restock (
        restock_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
        wine_id INTEGER NOT NULL,
        quantity_restocked INTEGER NOT NULL,
        restock_date DATE NOT NULL,
        FOREIGN KEY (wine_id) REFERENCES Wines(wine_id)
    );
''')





conn.commit()
conn.close()



