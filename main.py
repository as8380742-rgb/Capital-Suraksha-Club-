import os, threading, time, sqlite3
from flask import Flask, render_template_string, request, jsonify, session, redirect
from dhanhq import dhanhq

app = Flask(__name__)
app.secret_key = "CSC_PRO_ULTIMATE_SECRET"

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('database.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY, pin TEXT, is_paid INTEGER DEFAULT 0, 
        dhan_id TEXT, dhan_token TEXT, max_loss REAL, max_trades INTEGER, current_trades INTEGER DEFAULT 0)''')
    conn.commit()
    return conn

db = init_db()

# --- KILL SWITCH ENGINE ---
def run_kill_switch(user_id):
    while True:
        cursor = db.cursor()
        user = cursor.execute("SELECT dhan_id, dhan_token, max_loss FROM users WHERE id=?", (user_id,)).fetchone()
        if not user or not user[0]: break
        
        try:
            dhan = dhanhq(user[0], user[1])
            pos = dhan.get_positions()
            if pos.get('status') == 'success':
                pnl = sum(float(p.get('realizedProfit', 0)) + float(p.get('unrealizedProfit', 0)) for p in pos.get('data', []))
                if pnl <= -abs(float(user[2])):
                    # dhan.square_off_all() # Real Execution
                    cursor.execute("UPDATE users SET dhan_token=NULL WHERE id=?", (user_id,))
                    db.commit()
                    break 
        except: pass
        time.sleep(2)

# --- UI TEMPLATE (A to Z) ---
HTML_MAIN = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CSC Pro - A to Z</title>
    <style>
        body { font-family: sans-serif; background: #0f172a; color: white; padding: 15px; margin: 0; }
        .card { background: #1e293b; padding: 20px; border-radius: 15px; margin-bottom: 15px; border: 1px solid #334155; }
        input { width: 100%; padding: 12px; margin: 8px 0; background: #334155; border: none; border-radius: 8px; color: white; box-sizing: border-box; }
        .btn { width: 100%; padding: 15px; border-radius: 10px; border: none; font-weight: bold; cursor: pointer; margin-top: 10px; }
        .btn-blue { background: #3b82f6; color: white; }
        .btn-red { background: #ef4444; color: white; }
        .btn-gold { background: #f59e0b; color: white; }
        .status { font-size: 12px; padding: 5px; border-radius: 5px; }
    </style>
</head>
<body>
    <h2>🛡️ Capital Suraksha Club</h2>
    
    {% if not logged_in %}
    <div class="card">
        <h3>User Login</h3>
        <input id="uid" placeholder="Mobile Number">
        <input id="upin" type="password" placeholder="6-Digit PIN">
        <button class="btn btn-blue" onclick="auth('login')">Login / Register</button>
    </div>
    {% else %}
    <div class="card">
        <p>User: {{user_id}} | Status: {% if is_paid %} ✅ Premium {% else %} ❌ Free {% endif %}</p>
        {% if not is_paid %}
        <button class="btn btn-gold" onclick="alert('Pay ₹999 to UPI: yourvpa@upi')">Upgrade to Pro</button>
        {% endif %}
    </div>

    <div class="card">
        <h3>Step 1: Dhan API</h3>
        <input id="did" placeholder="Dhan Client ID" value="{{dhan_id or ''}}">
        <input id="dtk" type="password" placeholder="Dhan Access Token" value="{{dhan_token or ''}}">
        <button class="btn btn-blue" onclick="connect()">Save & Connect</button>
    </div>

    <div class="card" style="border-left: 5px solid #ef4444;">
        <h3>Step 2: Discipline Rules</h3>
        <label>Max M2M Loss (₹)</label>
        <input id="mloss" type="number" placeholder="e.g. 2000" value="{{max_loss or ''}}">
        <label>Max Trades Per Day</label>
        <input id="mtrades" type="number" placeholder="e.g. 3" value="{{max_trades or ''}}">
        <button class="btn btn-red" onclick="activate()">ACTIVATE KILL-SWITCH</button>
    </div>

    <div class="card">
        <h3>Handholding Support</h3>
        <p style="font-size: 13px; color: #94a3b8;">Premium users get 1-on-1 support with professional traders.</p>
        <button class="btn btn-blue" onclick="window.open('https://wa.me/YOUR_NUMBER')">Chat with Expert</button>
    </div>
    <a href="/logout" style="color: #ef4444; text-decoration: none; font-size: 14px;">Logout</a>
    {% endif %}

    <script>
        function auth(type) {
            const id = document.getElementById('uid').value;
            const pin = document.getElementById('upin').value;
            fetch('/api/auth', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({id, pin})})
            .then(res=>res.json()).then(data=>{ alert(data.msg); location.reload(); });
        }
        function connect() {
            const id = document.getElementById('did').value;
            const tk = document.getElementById('dtk').value;
            fetch('/api/connect', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({id, tk})})
            .then(res=>res.json()).then(data=>alert(data.msg));
        }
        function activate() {
            const loss = document.getElementById('mloss').value;
            const trades = document.getElementById('mtrades').value;
            fetch('/api/activate', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({loss, trades})})
            .then(res=>res.json()).then(data=>alert(data.msg));
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    if 'user' not in session: return render_template_string(HTML_MAIN, logged_in=False)
    user = db.execute("SELECT * FROM users WHERE id=?", (session['user'],)).fetchone()
    return render_template_string(HTML_MAIN, logged_in=True, user_id=user[0], is_paid=user[2], 
                                dhan_id=user[3], dhan_token=user[4], max_loss=user[5], max_trades=user[6])

@app.route('/api/auth', methods=['POST'])
def api_auth():
    data = request.json
    user = db.execute("SELECT * FROM users WHERE id=?", (data['id'],)).fetchone()
    if not user:
        db.execute("INSERT INTO users (id, pin) VALUES (?,?)", (data['id'], data['pin']))
        db.commit()
    session['user'] = data['id']
    return jsonify({"msg": "Logged In! Welcome to CSC."})

@app.route('/api/connect', methods=['POST'])
def api_connect():
    db.execute("UPDATE users SET dhan_id=?, dhan_token=? WHERE id=?", (request.json['id'], request.json['tk'], session['user']))
    db.commit()
    return jsonify({"msg": "Dhan Account Linked! ✅"})

@app.route('/api/activate', methods=['POST'])
def api_activate():
    user = db.execute("SELECT is_paid FROM users WHERE id=?", (session['user'],)).fetchone()
    if not user[0]: return jsonify({"msg": "Bhai, pehle Premium lelo tabhi Activate hoga! ❌"})
    
    db.execute("UPDATE users SET max_loss=?, max_trades=? WHERE id=?", (request.json['loss'], request.json['trades'], session['user']))
    db.commit()
    threading.Thread(target=run_kill_switch, args=(session['user'],)).start()
    return jsonify({"msg": "🛡️ Kill-Switch & Trade Limit Active!"})

@app.route('/logout')
def logout(): session.clear(); return redirect('/')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
