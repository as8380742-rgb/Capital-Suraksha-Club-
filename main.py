import os
from flask import Flask, render_template_string, request, jsonify
import sqlite3

app = Flask(__name__)

# --- DATABASE SETUP (Settings Save Karne ke Liye) ---
def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS settings 
                      (id INTEGER PRIMARY KEY, user_id TEXT, max_loss REAL, max_trades INTEGER)''')
    conn.commit()
    conn.close()

init_db()

# --- DASHBOARD UI (Professional Design) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Capital Suraksha Club - Pro</title>
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <style>
        body { font-family: 'Poppins', sans-serif; background-color: #f4f7f9; margin: 0; padding: 15px; }
        .app-container { max-width: 450px; margin: auto; background: white; border-radius: 20px; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.1); }
        .header { background: #1a73e8; color: white; padding: 25px; text-align: center; }
        .card { margin: 15px; padding: 20px; border-radius: 12px; border: 1px solid #eee; background: #fff; }
        .login-card { border-left: 5px solid #1a73e8; }
        .api-card { border-left: 5px solid #fbbc04; }
        .risk-card { border-left: 5px solid #ea4335; background: #fff8f7; }
        h3 { margin-top: 0; font-size: 18px; color: #333; }
        input, select { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ddd; border-radius: 8px; box-sizing: border-box; }
        .btn { width: 100%; padding: 12px; border: none; border-radius: 8px; color: white; font-weight: bold; cursor: pointer; transition: 0.3s; }
        .btn-blue { background: #1a73e8; }
        .btn-red { background: #ea4335; }
        .status-bar { padding: 10px; font-size: 14px; background: #e6fffa; color: #2d6a4f; text-align: center; font-weight: bold; }
    </style>
</head>
<body>
    <div class="app-container">
        <div class="header">
            <h2>🛡️ Capital Suraksha Club</h2>
            <p>Your Personal Trading Guard</p>
        </div>
        
        <div class="status-bar">SYSTEM ACTIVE: MONITORING TRADES ✅</div>

        <div class="card login-card">
            <h3>👤 Step 1: User Login</h3>
            <input type="text" id="username" placeholder="Username" value="Trader_01">
            <button class="btn btn-blue">Login</button>
        </div>

        <div class="card api-card">
            <h3>🔌 Step 2: Broker API</h3>
            <select id="broker">
                <option value="angel">Angel One</option>
                <option value="dhan">Dhan</option>
            </select>
            <input type="password" id="api_key" placeholder="Enter API Key">
            <button class="btn btn-blue" style="background: #fbbc04; color: #333;">Connect Broker</button>
        </div>

        <div class="card risk-card">
            <h3>⚠️ Step 3: Set Kill-Switch</h3>
            <label>Daily Max Loss (M2M):</label>
            <input type="number" id="max_loss" placeholder="e.g. 2000" value="{{ max_loss }}">
            <label>Max Trades Per Day:</label>
            <input type="number" id="max_trades" placeholder="e.g. 5" value="{{ max_trades }}">
            <button class="btn btn-red" id="save_btn">Activate Protection</button>
        </div>
    </div>

    <script>
        $('#save_btn').click(function(){
            const data = {
                max_loss: $('#max_loss').val(),
                max_trades: $('#max_trades').val()
            };
            $.post('/save_settings', data, function(res){
                alert('Success: Kill-Switch Activated at ₹' + data.max_loss);
            });
        });
    </script>
</body>
</html>
"""

# --- ROUTES ---
@app.route('/')
def index():
    # Database se purani settings uthao
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT max_loss, max_trades FROM settings WHERE id=1")
    row = cursor.fetchone()
    conn.close()
    
    ml = row[0] if row else 0
    mt = row[1] if row else 0
    return render_template_string(HTML_TEMPLATE, max_loss=ml, max_trades=mt)

@app.route('/save_settings', methods=['POST'])
def save_settings():
    ml = request.form.get('max_loss')
    mt = request.form.get('max_trades')
    
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO settings (id, user_id, max_loss, max_trades) VALUES (1, 'default', ?, ?)", (ml, mt))
    conn.commit()
    conn.close()
    return jsonify({"status": "success"})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
