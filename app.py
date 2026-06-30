import os
import re
from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3

app = Flask(__name__)
CORS(app)

DB_FILE = "penny_platform.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            username TEXT NOT NULL,
            total_balance REAL DEFAULT 0,
            emergency_fund REAL DEFAULT 0,
            spent_month REAL DEFAULT 0,
            emergency_goal REAL DEFAULT 10000,
            chart_data TEXT DEFAULT '0,0,0,0,0,0',
            newsletter INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

def validate_email(email):
    email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return re.match(email_regex, email) is not None

def validate_password(password):
    if len(password) < 6:
        return False
    if not re.search(r"[A-Z]", password): return False
    if not re.search(r"[a-z]", password): return False
    if not re.search(r"[0-9]", password): return False
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>_\-_]", password): return False
    return True

@app.route('/api/check-email', methods=['POST'])
def api_check_email():
    """Checks if an email profile exists in the database table."""
    data = request.get_json() or {}
    email = data.get('email', '').strip()
    
    if not email or not validate_email(email):
        return jsonify({"success": False, "exists": False, "message": "Please provide a valid email format."}), 400

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT email FROM users WHERE email = ?", (email,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return jsonify({"success": True, "exists": True})
    return jsonify({"success": True, "exists": False})

@app.route('/api/signup', methods=['POST'])
def api_signup():
    data = request.get_json() or {}
    email = data.get('email', '').strip()
    password = data.get('password', '')
    confirm_password = data.get('confirm_password', '')
    agree_tos = data.get('agree_tos', False)
    newsletter = data.get('newsletter', False)

    if not email or not password:
        return jsonify({"success": False, "message": "Missing email or password."}), 400
    
    if not validate_email(email):
         return jsonify({"success": False, "message": "The provided email format is structurally invalid."}), 400

    if password != confirm_password:
        return jsonify({"success": False, "message": "Passwords do not match."}), 400

    if not agree_tos:
        return jsonify({"success": False, "message": "You must agree to the Terms of Service."}), 400

    if not validate_password(password):
        return jsonify({"success": False, "message": "Password criteria not met."}), 400

    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute("SELECT email FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            conn.close()
            return jsonify({"success": False, "message": "An account with this email already exists."}), 400

        username = email.split('@')[0]
        cursor.execute('''
            INSERT INTO users (email, password, username, newsletter) 
            VALUES (?, ?, ?, ?)
        ''', (email, password, username, 1 if newsletter else 0))
        
        conn.commit()
        conn.close()
        # FIXED: Returns username directly to support immediate front-end session auto-login
        return jsonify({"success": True, "message": "Registration successful!", "username": username})
    except Exception as e:
        return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500

@app.route('/api/signin', methods=['POST'])
def api_signin():
    data = request.get_json() or {}
    email = data.get('email', '').strip()
    password = data.get('password', '')

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT password, username FROM users WHERE email = ?", (email,))
    row = cursor.fetchone()
    conn.close()

    if row and row[0] == password:
        return jsonify({"success": True, "username": row[1]})
    return jsonify({"success": False, "message": "Incorrect password."}), 401

if __name__ == '__main__':
    init_db()
    app.run(debug=True)