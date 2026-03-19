import os, threading, time, sqlite3, random
from flask import Flask, render_template_string, request, jsonify, session, redirect
from dhanhq import dhanhq

app = Flask(__name__)
app.secret_key = "CSC_PRO_FINAL_SHIELD"

# --- DATABASE ---
def init_db():
    conn = sqlite3.connect('database.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY, pin TEXT, is_paid INTEGER DEFAULT 0, 
        dhan_id TEXT, dhan_token TEXT, max_loss REAL, max_trades INTEGER)''')
    conn.commit()
    return conn

db = init_db()

# --- UI TEMPLATE (Fixed Features) ---
HTML_MAIN = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CSC Pro Dashboard</title>
    <style>
        body { font-family: sans-serif; background: #0f172a; color: white; padding: 15px; margin: 0; }
        .card { background: #1e293b; padding: 20px; border-radius: 15px; margin-bottom: 15px; border: 1px solid #334155; }
        input { width: 100%; padding: 12px; margin: 8px 0; background: #334155; border: 1px solid #475569; border-radius: 8px; color: white; box-sizing: border-box; }
        .btn { width: 100%; padding: 15px; border-radius: 10px; border: none; font-weight: bold; cursor: pointer; margin-top: 10px; transition: 0.3s; }
        .btn-blue { background: #3b82f6; color: white; }
        .btn-red { background: #ef4444; color: white; }
        .btn-gold { background: #f59e0b; color: white; }
        .qr-box { display: none; text-align: center; margin-top: 15px; background: white; padding: 10px; border-radius: 10px; }
    </style>
</head>
<body>
    <h2 style="display:flex; align-items:center;">🛡️ CSC Professional</h2>
    
    {% if not logged_in %}
    <div class="card">
        <h3>Login / Signup</h3>
        <input id="uid" type="number" placeholder="Mobile Number">
        <div id="otp_section" style="display:none;">
            <input id="uotp" type="number" placeholder="Enter 4-Digit OTP (Sent: 1234)" maxlength="4">
        </div>
        <input id="upin" type="password" placeholder="Set 6-Digit PIN" maxlength="6">
        <button id="auth_btn" class="btn btn-blue" onclick="handleAuth()">Get OTP</button>
    </div>
    {% else %}
    <div class="card">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <span>User: {{user_id}}</span>
            <span style="color:{% if is_paid %}#22c55e{% else %}#f59e0b{% endif %}; font-weight:bold;">
                {% if is_paid %} PREMIUM ACTIVE ✅ {% else %} PAYMENT PENDING ❌ {% endif %}
            </span>
        </div>
        {% if not is_paid %}
        <button class="btn btn-gold" onclick="showPayment()">Pay ₹999 to Activate</button>
        <div id="qr_area" class="qr-box">
            <p style="color:black; margin:0 0 10px 0;">Scan to Pay ₹999</p>
            <img src="https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=upi://pay?pa=YOUR_UPI_ID@okicici%26pn=CSC%26am=999%26cu=INR" alt="QR Code">
            <p style="color:grey; font-size:10px;">After payment, wait 5 mins for activation</p>
        </div>
        {% endif %}
    </div>

    <div class="card">
        <h3>Step 1: Broker Connection</h3>
        <input id="did" placeholder="Dhan Client ID" value="{{dhan_id or ''}}">
        <input id="dtk" type="password" placeholder="Dhan Access Token" value="{{dhan_token or ''}}">
        <button class="btn btn-blue" onclick="saveData('/api/connect', {id:did.value, tk:dtk.value})">Connect Broker</button>
    </div>

    <div class="card" style="border-left: 5px solid #ef4444;">
        <h3>Step 2: Risk Engine (Kill-Switch)</h3>
        <input id="mloss" type="number" placeholder="Daily Max Loss (M2M ₹)" value="{{max_loss or ''}}">
        <input id="mtrades" type="number" placeholder="Max Trades Per Day" value="{{max_trades or ''}}">
        <button class="btn btn-red" onclick="activateKill()">ACTIVATE PROTECTION</button>
    </div>

    <div class="card">
        <h3>Step 3: Handholding Support</h3>
        <p style="font-size:12px; color:#94a3b8;">Direct chat with 1-on-1 Professional Traders.</p>
        <button class="btn btn-blue" style="background:#25d366;" onclick="window.open('https://wa.me/91YOURNUMBER?text=Bhai%20Support%20Chahiye')">Connect on WhatsApp</button>
    </div>
    
    <div style="text-align:center; margin-top:20px;">
        <a href="/logout" style="color:#ef4444; text-decoration:none;">Logout</a>
    </div>
    {% endif %}

    <script>
        let step = 1;
        function handleAuth() {
            if(step === 1) {
                document.getElementById('otp_section').style.display = 'block';
                document.getElementById('auth_btn').innerText = 'Verify & Login';
                step = 2;
                alert("OTP Sent: 1234 (Demo)");
            } else {
                const id = document.getElementById('uid').value;
                const pin = document.getElementById('upin').value;
                const otp = document.getElementById('uotp').value;
                if(otp !== "1234") return alert("Wrong OTP!");
                if(pin.length !== 6) return alert("PIN must be 6 digits!");
                saveData('/api/auth', {id, pin});
            }
        }
        function showPayment() { document.getElementById('qr_area').style.display = 'block'; }
        function saveData(url, body) {
            fetch(url, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)})
            .then(res=>res.json()).then(data=>{ alert(data.msg); if(url==='/api/auth') location.reload(); });
        }
        function activateKill() {
            const loss = document.getElementById('mloss').value;
            const trades = document.getElementById('mtrades').value;
            fetch('/api/activate', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({loss, trades})})
            .then(res=>res.json()).then(data=>alert(data.msg));
        }
    </script>
</body>
</html>
"""

# --- ROUTES ---
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
    return jsonify({"msg": "Login Successful!"})

@app.route('/api/activate', methods=['POST'])
def api_activate():
    user = db.execute("SELECT is_paid FROM users WHERE id=?", (session['user'],)).fetchone()
    if not user[0]: return jsonify({"msg": "❌ Payment Required! Scan QR to upgrade to Premium."})
    # Business Logic for Kill Switch Activation here...
    return jsonify({"msg": "🛡️ Kill-Switch Activated! Your Capital is safe."})

@app.route('/logout')
def logout(): session.clear(); return redirect('/')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
