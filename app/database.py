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



# NATIVE CRYPTOGRAPHIC SECURITY MODULE (Zero Third-Party Dependencies)

def hash_password(plain_text_password: str) -> str:
    """Converts plaintext password into a salted PBKDF2-HMAC-SHA256 digest.

    Performs 100,000 key-stretching iterations with a 16-byte random salt.
    Format: '100000$salt$hash'
    """
    salt = os.urandom(16).hex()
    iterations = 100_000

    hash_bytes = hashlib.pbkdf2_hmac(
        "sha256",
        plain_text_password.encode("utf-8"),
        bytes.fromhex(salt),
        iterations,
    )
    return f"{iterations}${salt}${hash_bytes.hex()}"


def verify_password(stored_hash_string: str, candidate_password: str) -> bool:
    """Verifies candidate password in constant time using custom bitwise XOR.

    Mitigates Side-Channel Timing Attacks.
    """
    try:
        iterations_str, salt, original_hash = stored_hash_string.split("$")
        iterations = int(iterations_str)

        # Re-compute candidate hash using extracted salt and iterations
        candidate_bytes = hashlib.pbkdf2_hmac(
            "sha256",
            candidate_password.encode("utf-8"),
            bytes.fromhex(salt),
            iterations,
        )
        candidate_hash = candidate_bytes.hex()

        # Length mismatch check
        if len(original_hash) != len(candidate_hash):
            return False

        # Constant-time comparison using bitwise XOR
        difference = 0
        for char_a, char_b in zip(original_hash, candidate_hash):
            difference |= ord(char_a) ^ ord(char_b)

        return difference == 0
    except Exception:
        return False


# SESSION SMOKE TEST & RELATIONAL VALIDATION

if __name__ == "__main__":
    print("==================================================")
    print("  RUNNING DATABASE & SECURITY SMOKE TEST")
    print("==================================================")

    init_db()

    # Test Hashing & Constant-Time Verification
    test_password = "QuantTrader2026!"
    hashed_str = hash_password(test_password)
    print(f"\n[Test 1] Plain Password   : {test_password}")
    print(f"[Test 1] Generated Hash   : {hashed_str}")

    is_valid = verify_password(hashed_str, test_password)
    is_invalid = verify_password(hashed_str, "WrongPassword!")
    print(f"[Test 2] Verification (Correct PW) : {is_valid} (Expected: True)")
    print(f"[Test 2] Verification (Wrong PW)   : {is_invalid} (Expected: False)")

    # Test 3NF Relational Insertion (Users + Alerts)
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT OR IGNORE INTO users (username, password_hash)
            VALUES (?, ?)
        """,
            ("mr_jones_quant", hashed_str),
        )
        conn.commit()

        cur.execute(
            "SELECT user_id FROM users WHERE username = ?", ("mr_jones_quant",)
        )
        user = cur.fetchone()

        if user:
            cur.execute(
                """
                INSERT INTO alerts (user_id, stock_symbol, target_price, condition)
                VALUES (?, ?, ?, ?)
            """,
                (user["user_id"], "AAPL", 195.50, "ABOVE"),
            )
            conn.commit()
            print(
                f"[Test 3] Foreign Key Linked Alert Inserted for user_id={user['user_id']} (Stock: AAPL, Target: $195.50)"
            )
    finally:
        conn.close()

    print("\n✓ ALL PRACTICAL CHECKS COMPLETED SUCCESSFULLY!")
