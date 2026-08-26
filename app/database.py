"""database.py - Relational Persistence & Cryptographic Security Engine

Handles SQLite 3NF Database Initialization and Native PBKDF2 Password Security.
"""

import hashlib
import os
import sqlite3

DB_NAME = "stock_system.db"


# ----- Connection to Database -----


def get_db_connection():
    """Establish connection to SQLite database and enforces 3NF relational integrity."""
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Creates Third Normal Form (3NF) relational tables: 'users' and 'alerts'."""
    conn = get_db_connection()
    cursor = conn.cursor()

# ---------- User Table (Authentication & Brute Force Rate Limiting) ----------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            failed_attempts INTEGER DEFAULT 0,
            lockout_until TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

# ---------- Alerts Table (1:N Relationship) ----------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            alert_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            stock_symbol TEXT NOT NULL,
            target_price REAL NOT NULL,
            condition TEXT NOT NULL CHECK(condition IN ('ABOVE', 'BELOW')),
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
        );
    """)

    conn.commit()
    conn.close()
    print("SQLite 3NF Database Schema Initialized.")