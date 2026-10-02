from datetime import datetime, timedelta
import os
import sqlite3
from database import get_db_connection, hash_password, init_db, verify_password
from flask import Flask, flash, redirect, render_template, request, session, url_for

from algorithms import (
    calculate_linear_regression,
    calculate_rsi,
    calculate_sma,
    merge_sort_stocks,
)

from data_parser import fetch_stock_data

# Initialize Flask Central Application
app = Flask(__name__, template_folder="../templates", static_folder="../static")

# Cryptographically secure signed session key
app.secret_key = os.environ.get("FLASK_SECRET_KEY", os.urandom(24).hex())

# Ensure database tables exist upon server startup
init_db()

# ROUTE 1: Root & Index Redirection

@app.route("/")
def index():
    """Redirects authenticated users to the dashboard, others to login."""
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


# ROUTE 2: User Registration (Signup)

@app.route("/register", methods=["GET", "POST"])
def register():
    """Handles new user signup with input boundary validation and salted PBKDF2 hashing."""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        # Input Boundary Validation (Success Criteria SC1 / Test T2)
        if len(username) < 3:
            flash(
                "Validation Error: Username must be at least 3 characters long.",
                "danger",
            )
            return render_template("login.html", is_register=True)

        if len(password) < 6:
            flash(
                "Validation Error: Password must be at least 6 characters long.",
                "danger",
            )
            return render_template("login.html", is_register=True)

        # Generate native salted PBKDF2 digest
        hashed_password = hash_password(password)

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO users (username, password_hash)
                VALUES (?, ?)
            """,
                (username, hashed_password),
            )
            conn.commit()
            flash("Account created successfully! Please sign in.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash(
                f"Error: Username '{username}' is already taken. Please choose another.",
                "danger",
            )
            return render_template("login.html", is_register=True)
        finally:
            conn.close()

    # GET request displays registration form
    return render_template("login.html", is_register=True)



# ROUTE 3: User Authentication & 15-Minute Lockout Guard (Login)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Authenticates credentials against native PBKDF2 hashes and enforces 15-min lockout."""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()

        if not user:
            conn.close()
            flash("Invalid credentials: Username not recognized.", "danger")
            return render_template("login.html", is_register=False)

        current_time = datetime.now()

        # Check Active Lockout State (Defensive Security Guard)
        lockout_until_str = user["lockout_until"]
        if lockout_until_str:
            lockout_until = datetime.fromisoformat(lockout_until_str)
            if current_time < lockout_until:
                remaining_mins = (
                    int((lockout_until - current_time).total_seconds() // 60)
                    + 1
                )
                conn.close()
                flash(
                    f"Security Alert: Account locked due to 3 failed attempts. Try again in {remaining_mins} minute(s).",
                    "danger",
                )
                return render_template("login.html", is_register=False)
            else:
                # Lockout period expired; reset attempt counter
                cursor.execute(
                    """
                    UPDATE users SET failed_attempts = 0, lockout_until = NULL
                    WHERE user_id = ?
                """,
                    (user["user_id"],),
                )
                conn.commit()
                failed_attempts = 0
        else:
            failed_attempts = user["failed_attempts"]

        # Constant-Time PBKDF2 Password Verification
        if verify_password(user["password_hash"], password):
            # Reset failed attempts upon successful login
            cursor.execute(
                "UPDATE users SET failed_attempts = 0, lockout_until = NULL WHERE user_id = ?",
                (user["user_id"],),
            )
            conn.commit()
            conn.close()

            # Establish session state
            session["user_id"] = user["user_id"]
            session["username"] = user["username"]
            flash(
                f"Welcome back, {user['username']}! Session active.", "success"
            )
            return redirect(url_for("dashboard"))
        else:
            # Handle Failed Authentication Attempt
            new_attempts = failed_attempts + 1
            if new_attempts >= 3:
                lockout_deadline = (
                    current_time + timedelta(minutes=15)
                ).isoformat()
                cursor.execute(
                    """
                    UPDATE users SET failed_attempts = ?, lockout_until = ?
                    WHERE user_id = ?
                """,
                    (new_attempts, lockout_deadline, user["user_id"]),
                )
                conn.commit()
                conn.close()
                flash(
                    "Security Alert: 3 failed attempts detected! Account locked for 15 minutes.",
                    "danger",
                )
            else:
                cursor.execute(
                    "UPDATE users SET failed_attempts = ? WHERE user_id = ?",
                    (new_attempts, user["user_id"]),
                )
                conn.commit()
                conn.close()
                remaining_tries = 3 - new_attempts
                flash(
                    f"Invalid password! Attempts remaining before lockout: {remaining_tries}",
                    "danger",
                )

            return render_template("login.html", is_register=False)

    return render_template("login.html", is_register=False)



# ROUTE 4: Protected Dashboard Placeholder

MARKET_BASKET = ['AAPL','MFST','NVDA','TSLA','AMZN','GOOGL','META']

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
  """Main Analytics Dashboard.

  Fetches live data, computes technical indicators, and renders Chart.js
  visuals alongside the Top 5 Merge-Sorted leaderboard.
  """
  if "user_id" not in session:
    flash("Unauthorized access: Please log in first.", "danger")
    return redirect(url_for("login"))

  
  ticker = (
      request.args.get("ticker", "AAPL").strip().upper()
      if request.method == "GET"
      else request.form.get("ticker", "AAPL").strip().upper()
  )

  
  market_payload = fetch_stock_data(ticker)

  if not market_payload["success"]:
    flash(market_payload.get("error", "Failed to retrieve data."), "danger")
    
    target_data = {
        "symbol": ticker,
        "current_price": 0.0,
        "currency": "USD",
        "close_prices": [],
        "timestamps": [],
        "sma_10": None,
        "rsi_14": 50.0,
        "regression": None,
    }
  else:
    prices = market_payload["close_prices"]
    
    sma_val = calculate_sma(prices, time_window=10)
    rsi_val = calculate_rsi(prices, period=14)
    reg_val = calculate_linear_regression(prices, forecast_days=7)

    target_data = {
        "symbol": market_payload["symbol"],
        "current_price": market_payload["current_price"],
        "currency": market_payload["currency"],
        "close_prices": prices,
        
        "labels": [
            datetime.fromtimestamp(ts).strftime("%b %d")
            for ts in market_payload["timestamps"]
        ],
        "sma_10": sma_val,
        "rsi_14": rsi_val,
        "regression": reg_val,
    }

  
  leaderboard_candidates = []
  for sym in MARKET_BASKET:
    quote = fetch_stock_data(sym)
    if quote["success"] and len(quote["close_prices"]) >= 2:
      p_today = quote["close_prices"][-1]
      p_yesterday = quote["close_prices"][-2]
      pct_change = round(((p_today - p_yesterday) / p_yesterday) * 100, 2)
      leaderboard_candidates.append({
          "symbol": sym,
          "daily_return_pct": pct_change,
          "price": p_today,
      })

  
  sorted_basket = merge_sort_stocks(leaderboard_candidates)
  top_5_stocks = sorted_basket[:5]

  return render_template(
      "dashboard.html",
      stock=target_data,
      top_5=top_5_stocks,
      active_user=session.get("username"),
  )



# ROUTE 5: Logout & Session Termination

@app.route("/logout")
def logout():
    """Terminates active session and redirects to login interface."""
    session.clear()
    flash("You have been signed out successfully.", "info")
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True, port=5000)