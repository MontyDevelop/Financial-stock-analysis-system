"""
database.py - Realtional Presistence & Cryptographic Security Engine
Handles SQLite 3NF Database Initialization and Native PBKDF2 Password Security.
"""


import sqlite3
import hashlib
import os


DB_NAME = 'stock_system.db'


# ----- Connection to Database-----

def get_db_connection():
    """Establish connection to SQLite database and enforces 3NF relational integration."""
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Creates Third Normal Form (3NF) relatinal tables: 'users' and 'alerts'."""
    conn = get_db_connection()
    cursor = conn.cursor()


    # ----------User Table (Authentication & Brute force Rate Limiting)-------------
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users(
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        failed_attempts INTEGER Default 0,
        lockout_until TEXT,
        created at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS alerts(
        alert_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER FOREGIN KEY,
        stock_symbol TEXT NOT NULL,
        target_price TEXT NOT NULL,
        condition TEXT NOT NULL CHECK(condition IN ("ABOVE" , "BELOW")),
        is_active INTEGER Default 1,
        created at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE);
        """
    )

    conn.commit()
    conn.close()
    print("SQLite 3NF Database Schema Initialized.")



# get_db_connection()


# def hash_password():



# # Creation of database

# stock = sqlite3.connect("practice.db")
# cursor = stock.cursor()

# # Creating table
# cursor.execute(
# """
# CREATE TABLE IF NOT EXISTS students(
#     id INTEGER PRIMARY KEY AUTOINCREMENT,
#     name TEXT,
#     marks INTEGER
# )
# """
# )

# stock.commit()
# stock.close()

# print("Table created successfully...")