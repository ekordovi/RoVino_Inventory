import sqlite3
from datetime import date

# Initialize database connection
conn = sqlite3.connect('Vino.sqlite')
cur = conn.cursor()

# First, modify the Inventory table to make wine_id nullable
print("Modifying database schema...")
try:
    # Create a new Inventory table with modified constraints
    cur.execute('''
        CREATE TABLE IF NOT EXISTS InventoryNew (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
            wine_id INTEGER,  -- Now it's nullable
            item_name VARCHAR(150),
            category VARCHAR(50) DEFAULT 'wine',
            quantity INTEGER NOT NULL,
            price REAL,
            low_stock_threshold INTEGER,
            last_updated DATE,
            FOREIGN KEY (wine_id) REFERENCES Wines(wine_id)
        );
    ''')
    
    # Copy data from old table to new table
    cur.execute('''
        INSERT INTO InventoryNew 
        SELECT * FROM Inventory;
    ''')
    
    # Drop old table
    cur.execute('''
        DROP TABLE Inventory;
    ''')
    
    # Rename new table to original name
    cur.execute('''
        ALTER TABLE InventoryNew RENAME TO Inventory;
    ''')
    
    conn.commit()
    print("Database schema modified successfully.")
except Exception as e:
    print(f"Error modifying database schema: {e}")
    conn.rollback()

# Make sure we have the necessary tables and columns
try:
    # Create a spirits category in Wines table if it doesn't exist yet
    cur.execute('''
        CREATE TABLE IF NOT EXISTS SpiritTypes (
            type_id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            name TEXT NOT NULL,
            UNIQUE(category, name)
        )
    ''')
    
    # Add spirits to SpiritTypes table
    spirit_types = [
        ('Tequila', 'Blanco'),
        ('Tequila', 'Reposado'),
        ('Tequila', 'Anejo'),
        ('Mezcal', 'Mezcal'),
        ('Vodka', 'Vodka'),
        ('Whiskey', 'Bourbon'),
        ('Whiskey', 'Rye'),
        ('Scotch', 'Blended'),
        ('Scotch', 'Single Malt'),
        ('Gin', 'Gin'),
        ('Beer', 'Beer')
    ]
    
    for category, name in spirit_types:
        cur.execute('''
            INSERT OR IGNORE INTO SpiritTypes (category, name)
            VALUES (?, ?)
        ''', (category, name))
        
except Exception as e:
    print(f"Error setting up spirit tables: {e}")
    conn.rollback()

# Wine data structure: (name, type, price, low_stock_threshold, initial_quantity)
wines = [
    # White wines
    ('Yealands', 'Sauvignon Blanc', 56, 5, 10),
    ('Tenuta Polvara', 'Pinot Grigio', 60, 5, 10),
    ('Daou', 'Chardonnay', 60, 5, 10),
    ('Daou', 'Rose', 68, 5, 10),
    
    # Red wines
    ('Sartori Love Story', 'Pinot Noir', 56, 5, 10),
    ('Carletto', 'Montepulciano', 60, 5, 10),
    ('Monrosso', 'Chianti', 60, 5, 10),
    ('Santa Cristina', 'Super Tuscan Blend', 60, 5, 10),
    ('Casadei', 'Super Tuscan Blend', 68, 5, 10),
    ('La Posta Pizzella', 'Malbec', 56, 5, 10),
    ('Mon Frere', 'Pinot Noir', 56, 5, 10),
    ('Daou Pessimist', 'Red Blend', 68, 5, 10),
    ('Bread & Butter', 'Merlot', 56, 5, 10),
    ('Daou', 'Cabernet Sauvignon', 72, 5, 10),
    
    # Sparkling wines
    ('La Marca', 'Prosecco', 56, 5, 10),
    ('La Marca', 'Moscato', 60, 5, 10),
    ('Riondo', 'Sparkling', 60, 5, 10),
    
    # Bottle only - Domestic reds
    ('Austin Hope', 'Cabernet Sauvignon', 120, 2, 5),
    ('Chappellet', 'Cabernet Sauvignon', 150, 2, 5),
    ('Caymus', 'Petite Syrah', 99, 2, 5),
    
    # Bottle only - International reds
    ('Feudo Maccari', 'Nero d\'Avola', 60, 2, 5),
    ('Rubiolo', 'Chianti Classico', 65, 2, 5),
    ('Ruffino Ducale Gold', 'Chianti Riserva', 105, 2, 5),
    ('Produttori del Barbaresco', 'Barbaresco', 105, 2, 5),
    ('Giovanni Rosso', 'Barolo', 160, 2, 5),
    ('Ridolfi', 'Brunello', 180, 2, 5),
    ('Pertinance', 'Nebbiolo', 70, 2, 5),
    ('Sartori Corte Bra', 'Amarone', 200, 2, 5),
    ('Ornello', 'Super Tuscan', 120, 2, 5),
    ('Antinori Tignanello', 'Super Tuscan', 420, 2, 3)
]

# Liquor data structure: (name, category, type, price, low_stock_threshold, initial_quantity)
liquors = [
    # Tequila
    ('Casamigos Blanco', 'Tequila', 'Blanco', 15, 3, 5),
    ('Casamigos Reposado', 'Tequila', 'Reposado', 16, 3, 5),
    ('Casamigos Anejo', 'Tequila', 'Anejo', 18, 3, 5),
    ('Don Julio Blanco', 'Tequila', 'Blanco', 16, 3, 5),
    ('Don Julio Reposado', 'Tequila', 'Reposado', 17, 3, 5),
    ('Don Julio Anejo', 'Tequila', 'Anejo', 19, 3, 5),
    ('Clase Azul', 'Tequila', 'Reposado', 30, 2, 3),
    ('El Espadin', 'Mezcal', 'Mezcal', 15, 2, 3),
    
    # Vodka
    ('Belvedere', 'Vodka', 'Vodka', 15, 3, 5),
    ('Grey Goose', 'Vodka', 'Vodka', 15, 3, 5),
    ('Titos', 'Vodka', 'Vodka', 12, 3, 5),
    
    # Whiskey, Scotch, Bourbon
    ('Jack Daniels', 'Whiskey', 'Bourbon', 12, 3, 5),
    ('Makers Mark', 'Whiskey', 'Bourbon', 14, 3, 5),
    ('Bulleit Bourbon', 'Whiskey', 'Bourbon', 14, 3, 5),
    ('Johnnie Walker Red', 'Scotch', 'Blended', 14, 3, 5),
    ('Johnnie Walker Black', 'Scotch', 'Blended', 16, 3, 5),
    ('Basil Hayden', 'Whiskey', 'Rye', 15, 3, 5),
    ('Glenlivet 12', 'Scotch', 'Single Malt', 16, 3, 5),
    ('Glenlivet 14', 'Scotch', 'Single Malt', 18, 3, 5),
    ('Woodford Reserve', 'Whiskey', 'Bourbon', 15, 3, 5),
    
    # Gin
    ('Bombay', 'Gin', 'Gin', 12, 3, 5),
    ('Hendricks', 'Gin', 'Gin', 14, 3, 5),
    ('Malfy', 'Gin', 'Gin', 14, 3, 5),
    
    # Beer
    ('Peroni', 'Beer', 'Beer', 7, 5, 12),
    ('Hazy IPA', 'Beer', 'Beer', 8, 5, 12),
    ('IPA', 'Beer', 'Beer', 8, 5, 12),
    ('Blonde', 'Beer', 'Beer', 7, 5, 12)
]

# Add each wine to the database
wines_added = 0
liquors_added = 0
inventory_added = 0

# Process wines
print("Adding wines to inventory...")
for wine_data in wines:
    try:
        name, wine_type, price, threshold, quantity = wine_data
        
        # Insert or ignore into Wines table
        cur.execute('''
            INSERT OR IGNORE INTO Wines (name, type, price, category) 
            VALUES (?, ?, ?, 'wine')
        ''', (name, wine_type, price))
        
        # Get the wine_id
        cur.execute('''
            SELECT wine_id FROM Wines WHERE name = ? AND type = ?
        ''', (name, wine_type))
        wine_id = cur.fetchone()[0]
        
        # Check if the wine already has an inventory entry
        cur.execute('''
            SELECT id FROM Inventory WHERE wine_id = ?
        ''', (wine_id,))
        existing = cur.fetchone()
        
        if not existing:
            # Create an item name that describes the wine
            item_name = f"{name} - {wine_type}"
            
            # Add to inventory
            cur.execute('''
                INSERT INTO Inventory 
                (item_name, category, quantity, price, wine_id, low_stock_threshold, last_updated) 
                VALUES (?, 'wine', ?, ?, ?, ?, ?)
            ''', (
                item_name,
                quantity,
                price,
                wine_id,
                threshold,
                date.today().isoformat()
            ))
            inventory_added += 1
        
        wines_added += 1
    except Exception as e:
        print(f"Error adding wine {wine_data[0]} - {wine_data[1]}: {str(e)}")

# Process liquors
print("Adding liquors to inventory...")
for liquor_data in liquors:
    try:
        name, category, spirit_type, price, threshold, quantity = liquor_data
        
        # Add directly to Inventory since we don't need the wine_id foreign key
        item_name = f"{name} ({category})"
        
        # Check if this liquor already exists in inventory
        cur.execute('''
            SELECT id FROM Inventory WHERE item_name = ? AND category = ?
        ''', (item_name, category.lower()))
        existing = cur.fetchone()
        
        if not existing:
            # Add to inventory with NULL wine_id
            cur.execute('''
                INSERT INTO Inventory 
                (item_name, category, quantity, price, low_stock_threshold, last_updated) 
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                item_name,
                category.lower(),
                quantity,
                price,
                threshold,
                date.today().isoformat()
            ))
            inventory_added += 1
            liquors_added += 1
    except Exception as e:
        print(f"Error adding liquor {liquor_data[0]}: {str(e)}")

# Commit changes and close connection
conn.commit()
conn.close()

print(f"Import complete! Added {wines_added} wines and {liquors_added} liquors to the database.")
print(f"Created {inventory_added} new inventory entries.")
print("You can now log in to the RoVino system to see your complete inventory.")