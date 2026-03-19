import os
from flask import Flask, render_template_string, request, jsonify, session
import sqlite3
import pyotp 

app = Flask(__name__)
app.secret_key = "CSC_SUPER_SECRET"

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                      (id INTEGER PRIMARY KEY, username TEXT, is_paid INTEGER DEFAULT 0, totp_key TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS risk_rules 
                      (user_id INTEGER, max_loss REAL, max_trades INTEGER)''')
    conn.commit()
    conn.close()

init_db()

# --- UI TEMPLATE ---
HTML_PRO = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CSC - Professional Dashboard</title>
    <style>
        body { font-family: sans-serif; background: #0f172a; color: white; margin: 0; padding: 15px; }
        .box { background: #1e293b; padding: 20px; border-radius: 15px; margin-bottom: 20px; border: 1px solid #334155; }
        .btn { background: #3b82f6; color: white; border: none; width: 100%; padding: 15px; border-radius: 10px; font-weight: bold; cursor: pointer; }
        .status-paid { color: #22c55e; font-size: 14px; font-weight: bold; }
        .status-unpaid { color: #ef4444; font-size: 14px; }
        input { width: 100%; padding: 12px; margin: 10px 0; background: #334155; border: none; border-radius: 8px; color: white; box-sizing: border-box;}
    </style>
</head>
<body>
    <h2>🛡️ CSC Professional</h2>
    <div class="box">
        <h3>Account Status</h3>
        {% if is_paid %}
            <span class="status-paid">PREMIUM ACTIVE ✅</span>
        {% else %}
            <span class="status-unpaid">PAYMENT PENDING ❌</span>
            <button class="btn" style="background:#f59e0b; margin-top:10px;">Pay Now to Activate</button>
        {% endif %}
    </div>
    <div class="box">
        <h3>Step 1: Broker Login (2FA)</h3>
        <input type="text" placeholder="Angel One Client ID">
        <input type="password" placeholder="API Key">
        <input type="text" placeholder="TOTP Token">
        <button class="btn">Connect Real-Time</button>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_PRO, is_paid=0)


    if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

