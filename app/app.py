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



app = Flask(__name__, template_folder="../templates", static_folder="../static")


app.secret_key = os.environ.get("FLASK_SECRET_KEY", os.urandom(24).hex())

init_db()




def verify_login_security(username_input, password_input):
    """Check credentials and apply a 15-minute lockout after three failed attempts."""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
       
        cursor.execute(
            "SELECT * FROM users WHERE username = ?",
            (username_input,),
        )
        user = cursor.fetchone()

      
        if user is None:
            return "INVALID_CREDENTIALS"

    
        if user["lockout_until"] is not None:
            current_time = datetime.now()
            lockout_until = datetime.fromisoformat(user["lockout_until"])

            if current_time < lockout_until:
                return "ACCOUNT_LOCKED_OUT"

        
            cursor.execute(
                """
                UPDATE users
                SET failed_attempts = 0, lockout_until = NULL
                WHERE user_id = ?
                """,
                (user["user_id"],),
            )
            conn.commit()
            failed_attempts = 0
        else:
            failed_attempts = user["failed_attempts"]

        is_valid = verify_password(user["password_hash"], password_input)


        if is_valid:
            cursor.execute(
                "UPDATE users SET failed_attempts = 0 WHERE user_id = ?",
                (user["user_id"],),
            )
            conn.commit()
            return "LOGIN_SUCCESS"

        new_attempts = failed_attempts + 1

        if new_attempts >= 3:
            lockout_time = (datetime.now() + timedelta(minutes=15)).isoformat()
            cursor.execute(
                """
                UPDATE users
                SET failed_attempts = ?, lockout_until = ?
                WHERE user_id = ?
                """,
                (new_attempts, lockout_time, user["user_id"]),
            )
            conn.commit()
            return "ACCOUNT_LOCKED_OUT"

        cursor.execute(
            "UPDATE users SET failed_attempts = ? WHERE user_id = ?",
            (new_attempts, user["user_id"]),
        )
        conn.commit()
        return "INVALID_CREDENTIALS"

    finally:
        conn.close()


# ROUTE 1: Root & Index Redirection

@app.route("/")
def index():
    """Redirect authenticated users to the dashboard, others to login."""
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


# ROUTE 2: User Registration (Signup)

@app.route("/register", methods=["GET", "POST"])
def register():
    """Create a new user account after validating input and hashing the password."""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        # Check the username length
        if len(username) < 3:
            flash(
                "Validation Error: Username must be at least 3 characters long.",
                "danger",
            )
            return render_template("login.html", is_register=True)

        # Check the password length
        if len(password) < 6:
            flash(
                "Validation Error: Password must be at least 6 characters long.",
                "danger",
            )
            return render_template("login.html", is_register=True)

        # Hash the password before storing it
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

    return render_template("login.html", is_register=True)


# ROUTE 3: User Login

@app.route("/login", methods=["GET", "POST"])
def login():
    """Use Algorithm 3 to check credentials and create the user session."""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        # Run the login security algorithm
        result = verify_login_security(username, password)

        if result == "LOGIN_SUCCESS":
            # Retrieve the user ID for the Flask session
            conn = get_db_connection()
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "SELECT user_id FROM users WHERE username = ?",
                    (username,),
                )
                user = cursor.fetchone()
            finally:
                conn.close()

            if user is None:
                flash("Invalid credentials. Please try again.", "danger")
                return render_template("login.html", is_register=False)

            session["user_id"] = user["user_id"]
            session["username"] = username
            flash(f"Welcome back, {username}! Session active.", "success")
            return redirect(url_for("dashboard"))

        if result == "ACCOUNT_LOCKED_OUT":
            flash(
                "Security Alert: Your account is locked. Please try again after 15 minutes.",
                "danger",
            )
        else:
            flash("Invalid username or password.", "danger")

    return render_template("login.html", is_register=False)


# ROUTE 4: Protected Dashboard

MARKET_BASKET = ["AAPL", "MFST", "NVDA", "TSLA", "AMZN", "GOOGL", "META"]


@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    """Fetch stock data, calculate indicators, and display the ranked stocks."""
    if "user_id" not in session:
        flash("Unauthorized access: Please log in first.", "danger")
        return redirect(url_for("login"))

    if request.method == "GET":
        ticker = request.args.get("ticker", "AAPL").strip().upper()
    else:
        ticker = request.form.get("ticker", "AAPL").strip().upper()

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
            pct_change = round(
                ((p_today - p_yesterday) / p_yesterday) * 100,
                2,
            )
            leaderboard_candidates.append(
                {
                    "symbol": sym,
                    "daily_return_pct": pct_change,
                    "price": p_today,
                }
            )

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
    """End the current user session and redirect to login."""
    session.clear()
    flash("You have been signed out successfully.", "info")
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True, port=5000)
