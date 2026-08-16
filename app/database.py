import sqlite3

# Creation of database

stock = sqlite3.connect("practice.db")
cursor = stock.cursor()

# Creating table
cursor.execute(
"""
CREATE TABLE IF NOT EXISTS students(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    marks INTEGER
)
"""
)

stock.commit()
stock.close()

print("Table created successfully...")