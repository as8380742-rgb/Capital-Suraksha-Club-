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

# --- UI TEMPLATE (Sab Kuch Shamil Hai) ---
HTML_PRO = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CSC Professional</title>
    <style>
        body { font-family: sans-serif; background: #0f172a; color: white; margin: 0; padding: 15px; }
        .box { background: #1e293b; padding: 20px; border-radius: 15px; margin-bottom: 20px; border: 1px solid #334155; }
        .btn { background: #3b82f6; color: white; border: none; width: 100%; padding: 15px; border-radius: 10px; font-weight: bold; cursor: pointer; margin-top: 10px; }
        .status-unpaid { color: #ef4444; font-size: 14px; font-weight: bold; }
        input { width: 100%; padding: 12px; margin: 10px 0; background: #334155; border: none; border-radius: 8px; color: white; box-sizing: border-box;}
        label { font-size: 12px; color: #94a3b8; margin-top: 5px; display: block; }
        h3 { margin-top: 0; color: #f8fafc; }
    </style>
</head>
<body>
    <h2 style="display: flex; align-items: center;">🛡️ CSC Professional</h2>
    
    <div class="box">
        <h3>Account Status</h3>
        <span class="status-unpaid">PAYMENT PENDING ❌</span>
        <button class="btn" style="background:#f59e0b;">Pay Now to Activate</button>
    </div>

    <div class="box">
        <h3>Step 1: Broker Login (2FA)</h3>
        <label>Angel One Client ID</label>
        <input type="text" placeholder="Enter ID">
        <label>API Key</label>
        <input type="password" placeholder="Enter API Key">
        <label>TOTP Token</label>
        <input type="text" placeholder="6-digit OTP">
        <button class="btn">Connect Real-Time</button>
    </div>

    <div class="box" style="border-left: 5px solid #ef4444;">
        <h3>Step 2: Risk Engine (Kill-Switch)</h3>
        <label>Daily Max Loss (M2M)</label>
        <input type="number" placeholder="e.g. 5000">
        <label>Max Trades Per Day</label>
        <input type="number" placeholder="e.g. 10">
        <button class="btn" style="background:#ef4444;">ACTIVATE PROTECTION</button>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    # 'is_paid' ko 0 rakha hai taaki payment wall dikhe
    return render_template_string(HTML_PRO, is_paid=0)

if __name__ == "__main__":
    # Railway ke dynamic port ke liye
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
