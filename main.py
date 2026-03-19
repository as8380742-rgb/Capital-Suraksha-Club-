import os, sqlite3, random, requests
from flask import Flask, render_template_string, request, jsonify, session, redirect

app = Flask(__name__)
app.secret_key = "CSC_ULTRA_SECURE_KEY_2026"

# --- CONFIGURATION ---
FAST2SMS_KEY = 'plwd********************' # Teri API Key yahan hai
YOUR_WHATSAPP = "919654197757"
YOUR_UPI = "as8380742-1@okicici"

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('database.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY, pin TEXT, plan TEXT DEFAULT 'Free', 
        dhan_id TEXT, dhan_token TEXT, max_loss REAL, max_trades INTEGER)''')
    conn.commit()
    return conn
db = init_db()

# --- FAST2SMS OTP ROUTE ---
def send_otp_sms(to_number, otp):
    url = "https://www.fast2sms.com/dev/bulkV2"
    payload = {
        "variables_values": str(otp),
        "route": "otp", 
        "numbers": str(to_number),
    }
    headers = {"authorization": FAST2SMS_KEY}
    try:
        response = requests.post(url, data=payload, headers=headers)
        # Agar wallet mein balance hai toh ye True bhejega
        return response.json().get("return") 
    except:
        return False

# --- UI DESIGN (New Professional Dashboard) ---
HTML_MAIN = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CSC Professional</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #0f172a; color: white; padding: 15px; margin: 0; }
        .card { background: #1e293b; padding: 20px; border-radius: 15px; margin-bottom: 15px; border: 1px solid #334155; }
        .plan-box { display: flex; gap: 10px; margin: 15px 0; overflow-x: auto; padding-bottom: 10px; }
        .plan-card { min-width: 120px; background: #334155; padding: 15px; border-radius: 12px; text-align: center; border: 2px solid transparent; }
        .active-plan { border-color: #f59e0b; background: #424136; }
        input { width: 100%; padding: 12px; margin: 8px 0; background: #334155; border: 1px solid #475569; border-radius: 8px; color: white; box-sizing: border-box; }
        .btn { width: 100%; padding: 15px; border-radius: 10px; border: none; font-weight: bold; cursor: pointer; transition: 0.3s; }
        .btn-blue { background: #3b82f6; color: white; }
        .btn-gold { background: #f59e0b; color: white; margin-top: 10px; }
        .btn-red { background: #ef4444; color: white; margin-top: 10px; }
        .status-badge { padding: 4px 8px; border-radius: 5px; font-size: 12px; font-weight: bold; }
    </style>
</head>
<body>
    <h2 style="text-align:center;">🛡️ Capital Suraksha Club</h2>

    {% if not logged_in %}
    <div class="card">
        <h3 style="margin-top:0;">Login via OTP</h3>
        <p style="color:#94a3b8; font-size:14px;">Enter your mobile to receive a real SMS OTP.</p>
        <input id="uid" type="number" placeholder="Mobile Number (10 Digits)">
        <div id="otp_section" style="display:none;">
            <input id="uotp" type="number" placeholder="Enter 4-Digit OTP">
            <input id="upin" type="password" placeholder="Create 6-Digit PIN (For future login)" maxlength="6">
        </div>
        <button id="auth_btn" class="btn btn-blue" onclick="handleAuth()">Get OTP via SMS</button>
    </div>
    {% else %}
    <div class="card">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <span>User: <b>{{user_id}}</b></span>
            <span class="status-badge" style="background:#424136; color:#f59e0b;">{{plan}} Plan</span>
        </div>
        
        <h3 style="margin-bottom:10px;">Select Protection Plan</h3>
        <div class="plan-box">
            <div class="plan-card {% if plan=='Basic' %}active-plan{% endif %}"><h4>Basic</h4><p>₹499</p></div>
            <div class="plan-card {% if plan=='Pro' %}active-plan{% endif %}"><h4>Pro</h4><p>₹999</p></div>
            <div class="plan-card {% if plan=='Expert' %}active-plan{% endif %}"><h4>Expert</h4><p>₹2499</p></div>
        </div>
        
        {% if plan == 'Free' %}
        <button class="btn btn-gold" onclick="document.getElementById('qr').style.display='block'">Upgrade to Activate Kill-Switch</button>
        <div id="qr" style="display:none; text-align:center; margin-top:15px; background:white; padding:15px; border-radius:12px; color:black;">
            <p><b>Scan to Pay ₹999 (Pro)</b></p>
            <img src="https://api.qrserver.com/v1/create-qr-code/?size=180x180&data=upi://pay?pa={{upi}}%26pn=CSC%26am=999%26cu=INR" width="180">
            <p style="font-size:12px; color:grey;">After payment, send screenshot on WhatsApp.</p>
        </div>
        {% endif %}
    </div>

    <div class="card">
        <h3>1. Broker Connection</h3>
        <input id="did" placeholder="Dhan Client ID" value="{{dhan_id or ''}}">
        <input id="dtk" type="password" placeholder="Dhan Access Token" value="{{dhan_token or ''}}">
        <button class="btn btn-blue" onclick="sendData('/api/connect', {id:did.value, tk:dtk.value})">Save Connection</button>
    </div>

    <div class="card">
        <h3>2. Set Risk Limits</h3>
        <input id="mloss" type="number" placeholder="Max Daily Loss (₹)" value="{{max_loss or ''}}">
        <input id="mtrades" type="number" placeholder="Max Trades Today" value="{{max_trades or ''}}">
        <button class="btn btn-red" onclick="activateEngine()">ACTIVATE PROTECTION</button>
    </div>

    <div class="card" style="text-align:center;">
        <h3>3. Support & Handholding</h3>
        <button class="btn" style="background:#25d366; color:white;" onclick="window.open('https://api.whatsapp.com/send?phone={{wa}}&text=Bhai%20Premium%20Plan%20Activate%20Kar%20Do')">Chat on WhatsApp</button>
    </div>
    
    <div style="text-align:center;"><a href="/logout" style="color:#ef4444; text-decoration:none;">Logout</a></div>
    {% endif %}

    <script>
        let step = 1;
        function handleAuth() {
            const id = document.getElementById('uid').value;
            if(step === 1) {
                if(id.length < 10) return alert("Valid mobile number dalo!");
                fetch('/api/send_otp', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({id})})
                .then(res=>res.json()).then(data=>{
                    alert(data.msg); 
                    if(data.success) {
                        document.getElementById('otp_section').style.display='block';
                        document.getElementById('auth_btn').innerText='Verify & Login';
                        step=2;
                    }
                });
            } else {
                const pin = document.getElementById('upin').value;
                const otp = document.getElementById('uotp').value;
                if(pin.length !== 6) return alert("PIN 6-digit ka hona chahiye!");
                sendData('/api/auth', {id, pin, otp});
            }
        }
        function sendData(url, body) {
            fetch(url, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)})
            .then(res=>res.json()).then(data=>{ 
                alert(data.msg); 
                if(data.success && url==='/api/auth') location.reload(); 
            });
        }
        function activateEngine() {
            const loss = document.getElementById('mloss').value;
            const trades = document.getElementById('mtrades').value;
            fetch('/api/activate', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({loss, trades})})
            .then(res=>res.json()).then(data=>alert(data.msg));
        }
    </script>
</body>
</html>
"""

# --- BACKEND LOGIC ---
@app.route('/')
def home():
    if 'user' not in session: return render_template_string(HTML_MAIN, logged_in=False)
    u = db.execute("SELECT * FROM users WHERE id=?", (session['user'],)).fetchone()
    return render_template_string(HTML_MAIN, logged_in=True, user_id=u[0], plan=u[2], 
                                dhan_id=u[3], dhan_token=u[4], max_loss=u[5], max_trades=u[6], wa=YOUR_WHATSAPP, upi=YOUR_UPI)

@app.route('/api/send_otp', methods=['POST'])
def api_send_otp():
    otp = str(random.randint(1111, 9999))
    session['temp_otp'] = otp
    success = send_otp_sms(request.json['id'], otp)
    if success:
        return jsonify({"success": True, "msg": "OTP aapke phone par bhej diya gaya hai! ✅"})
    else:
        return jsonify({"success": False, "msg": "SMS bhejne mein error! Fast2SMS Wallet check karein (₹100 recharge required)."})

@app.route('/api/auth', methods=['POST'])
def api_auth():
    data = request.json
    if data['otp'] != session.get('temp_otp'): return jsonify({"success": False, "msg": "Wrong OTP! ❌"})
    user = db.execute("SELECT * FROM users WHERE id=?", (data['id'],)).fetchone()
    if not user:
        db.execute("INSERT INTO users (id, pin) VALUES (?,?)", (data['id'], data['pin']))
        db.commit()
    session['user'] = data['id']
    return jsonify({"success": True, "msg": "Login Successful!"})

@app.route('/api/connect', methods=['POST'])
def api_connect():
    db.execute("UPDATE users SET dhan_id=?, dhan_token=? WHERE id=?", (request.json['id'], request.json['tk'], session['user']))
    db.commit()
    return jsonify({"success": True, "msg": "Dhan API Linked Successfully! 🏦"})

@app.route('/api/activate', methods=['POST'])
def api_activate():
    u = db.execute("SELECT plan FROM users WHERE id=?", (session['user'],)).fetchone()
    if u[0] == 'Free': return jsonify({"msg": "❌ Premium Plan Required! Upgrade karein pehle."})
    db.execute("UPDATE users SET max_loss=?, max_trades=? WHERE id=?", (request.json['loss'], request.json['trades'], session['user']))
    db.commit()
    return jsonify({"msg": "🛡️ Risk Protection Live! Kill-Switch active."})

@app.route('/logout')
def logout(): session.clear(); return redirect('/')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
