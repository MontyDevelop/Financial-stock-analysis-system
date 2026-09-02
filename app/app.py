from datetime import datetime, timedelta

import os
import sqlite3
from database import get_db_connection, init_db, hash_password, verify_password
from flask import Flask, flash,redirect,render_template, request,session, url_for


app = Flask(__name__, template_folder='../templates',static_Folder ='../static' )

app.secret_key = os.environ.get("", os.urandom(24).hex())


# home
@ app.route("/")
def index():
    if 'user_id' in session:
        return redirect(url_for('Dashboard'))
    return redirect(url_for('login'))


@app.route("/register", methods=['GET',"POST"])
def register():
    if request.method == 'POST':
        username = request.form.get('username',"")
        password = request.form.get('password',"")

        if len(username) < 3:
            flash(
                "Validation Error:  Username must be at least 3 characters."
            )
        
            return render_template("login.html",isregister=True)
        
        if len(password) < 6:
            flash(
            "Validation Error:  Password must be at least 6 characters."
            )

            return render_template("login.html",isregister=True)

        hashed_password = hash_password(password)
        conn = get_db_connection()
        cur = conn.cursor()

        try:
            cur.execute(
                """
                INSERT INTO users (username, password_hash)
                VALUES (?, ?)
            """,
                (username, hashed_password),
            )
            conn.commit()
            flash(
                "Account created Successfully"
            )
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash(f"Error: Username {username} is already taken.")
            return render_template('login.html', is_register = True)
        finally:
            conn.close()

    return render_template('login.html', is_register = True)



@app.route('/login',methods=['GET','POST'])
def login():
    if request.method() == 'POST':
        username = request.form.get('username',"").strip()
        password = request.form.get('password',"")

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(f"SELECT * From users WHERE username = ?, {username}")
        user = cur.fetchone()

        if not user:
            conn.close()
            flash("Invalid credentials  ")
            return render_template('login.html', is_register = False)

        curret_time  = datetime.now()

        # check the active lockout state
        
        lockout_until_str = user['lockout_until']
        if lockout_until_str:
            lockout_until = datetime.fromisoformat(lockout_until_str)
            if curret_time < lockout_until:
                remaining_mins = (int((lockout_until-curret_time).total_seconds() // 60) + 1)
                


init_db()