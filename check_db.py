import sqlite3

conn = sqlite3.connect('Vino.sqlite')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Check if Users table exists
print("Tables in database:")
tables = cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
for table in tables:
    print(f"- {table['name']}")

# Check if there are any users
try:
    users = cur.execute("SELECT * FROM Users").fetchall()
    print(f"\nNumber of users: {len(users)}")
    for user in users:
        print(f"User: {dict(user)}")
except Exception as e:
    print(f"Error accessing Users table: {e}")

conn.close()