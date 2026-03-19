import os, threading, time, sqlite3, random
from flask import Flask, render_template_string, request, jsonify, session, redirect
from twilio.rest import Client
from dhanhq import dhanhq

app = Flask(__name__)
app.secret_key = "CSC_ULTIMATE_PRO_SHIELD"

# --- TWILIO CONFIG (Yahan apni details dalo) ---
TWILIO_SID = 'YOUR_ACTUAL_SID'
TWILIO_TOKEN = 'YOUR_ACTUAL_TOKEN'
TWILIO_PHONE = 'YOUR_TWILIO_NUMBER'

# --- BUSINESS CONFIG ---
YOUR_WHATSAPP = "919654197757"
YOUR_UPI = "as8380742-1@okicici"

# --- DATABASE ---
def init_db():
    conn = sqlite3.connect('database.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY, pin TEXT, plan TEXT DEFAULT 'Free', 
        dhan_id TEXT, dhan_token TEXT, max_loss REAL, max_trades INTEGER)''')
    conn.commit()
    return conn
db = init_db()

# --- SMS FUNCTION ---
def send_otp_sms(to_number, otp):
    try:
        client = Client(TWILIO_SID, TWILIO_TOKEN)
        client.messages.create(
            body=f"Your CSC Verification OTP is: {otp}. Do not share it.",
            from_=TWILIO_PHONE,
            to=f"+91{to_number}"
        )
        return True
    except: return False

# --- UI TEMPLATE ---
HTML_MAIN = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CSC Professional</title>
    <style>
        body { font-family: sans-serif; background: #0f172a; color: white; padding: 15px; margin: 0; }
        .card { background: #1e293b; padding: 20px; border-radius: 15px; margin-bottom: 15px; border: 1px solid #334155; }
        .plan-box { display: flex; gap: 10px; margin-top: 10px; overflow-x: auto; padding-bottom: 10px; }
        .plan-card { min-width: 120px; background: #334155; padding: 10px; border-radius: 10px; text-align: center; border: 1px solid #475569; }
        .active-plan { border-color: #f59e0b; background: #424136; }
        input { width: 100%; padding: 12px; margin: 8px 0; background: #334155; border: 1px solid #475569; border-radius: 8px; color: white; box-sizing: border-box; }
        .btn { width: 100%; padding: 15px; border-radius: 10px; border: none; font-weight: bold; cursor: pointer; margin-top: 10px; }
        .btn-blue { background: #3b82f6; color: white; }
        .btn-gold { background: #f59e0b; color: white; }
    </style>
</head>
<body>
    <h2>🛡️ CSC Professional</h2>

    {% if not logged_in %}
    <div class="card">
        <h3>Real OTP Login</h3>
        <input id="uid" type="number" placeholder="Mobile Number">
        <div id="otp_div" style="display:none;"><input id="uotp" type="number" placeholder="Enter SMS OTP"></div>
        <input id="upin" type="password" placeholder="Set 6-Digit PIN" maxlength="6">
        <button id="abtn" class="btn btn-blue" onclick="handleAuth()">Get Real OTP</button>
    </div>
    {% else %}
    <div class="card">
        <p>User: {{user_id}} | Plan: <b style="color:#f59e0b;">{{plan}}</b></p>
        
        <h3>Select Your Protection Plan:</h3>
        <div class="plan-box">
            <div class="plan-card {% if plan=='Basic' %}active-plan{% endif %}">
                <h4>Basic</h4>
                <p>₹499/mo</p>
                <small>Kill-Switch Only</small>
            </div>
            <div class="plan-card {% if plan=='Pro' %}active-plan{% endif %}">
                <h4>Pro</h4>
                <p>₹999/mo</p>
                <small>Kill + Trade Limit</small>
            </div>
            <div class="plan-card {% if plan=='Expert' %}active-plan{% endif %}">
                <h4>Expert</h4>
                <p>₹2499/mo</p>
                <small>1-on-1 Support</small>
            </div>
        </div>
        
        {% if plan == 'Free' %}
        <button class="btn btn-gold" onclick="document.getElementById('q').style.display='block'">Upgrade Now</button>
        <div id="q" style="display:none; text-align:center; margin-top:15px; background:white; padding:10px; border-radius:10px;">
            <img src="https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=upi://pay?pa={{upi}}%26pn=CSC%26cu=INR" width="150">
            <p style="color:black; font-size:12px;">Scan to Pay & WhatsApp Screenshot</p>
        </div>
        {% endif %}
    </div>

    <div class="card">
        <h3>Step 1: Broker Connection</h3>
        <input id="did" placeholder="Dhan Client ID" value="{{dhan_id or ''}}">
        <input id="dtk" type="password" placeholder="Dhan Access Token" value="{{dhan_token or ''}}">
        <button class="btn btn-blue" onclick="save('/api/connect', {id:did.value, tk:dtk.value})">Connect Dhan</button>
    </div>

    <div class="card">
        <h3>Step 2: Risk Engine</h3>
        <input id="ml" type="number" placeholder="Max Loss (₹)" value="{{max_loss or ''}}">
        <input id="mt" type="number" placeholder="Max Trades" value="{{max_trades or ''}}">
        <button class="btn btn-blue" style="background:#ef4444;" onclick="activate()">Activate Protection</button>
    </div>

    <div class="card">
        <h3>Handholding Support</h3>
        <button class="btn" style="background:#25d366; color:white;" onclick="window.open('https://api.whatsapp.com/send?phone={{wa}}&text=Bhai%20Support%20Chahiye')">Chat with Professional</button>
    </div>
    
    <div style="text-align:center;"><a href="/logout" style="color:#ef4444; text-decoration:none;">Logout</a></div>
    {% endif %}

    <script>
        let s = 1; let currentOtp = "";
        function handleAuth() {
            const id = document.getElementById('uid').value;
            if(s === 1) {
                fetch('/api/send_otp', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({id})})
                .then(res=>res.json()).then(data=>{
                    alert(data.msg); document.getElementById('otp_div').style.display='block';
                    document.getElementById('abtn').innerText='Verify & Login'; s=2;
                });
            } else {
                const pin = document.getElementById('upin').value;
                const otp = document.getElementById('uotp').value;
                save('/api/auth', {id, pin, otp});
            }
        }
        function save(url, body) {
            fetch(url, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)})
            .then(res=>res.json()).then(data=>{ alert(data.msg); if(url==='/api/auth') location.reload(); });
        }
        function activate() {
            fetch('/api/activate', {method:'POST', headers:{'Content-Type':'application/json'}, 
            body:JSON.stringify({loss:document.getElementById('ml').value, trades:document.getElementById('mt').value})})
            .then(res=>res.json()).then(data=>alert(data.msg));
        }
    </script>
</body>
</html>
"""

# --- API ROUTES ---
@app.route('/api/send_otp', methods=['POST'])
def api_send_otp():
    otp = str(random.randint(1000, 9999))
    session['temp_otp'] = otp
    if send_otp_sms(request.json['id'], otp):
        return jsonify({"msg": "OTP Sent to your Phone! ✅"})
    return jsonify({"msg": "Twilio Error! Check credentials."})

@app.route('/api/auth', methods=['POST'])
def api_auth():
    data = request.json
    if data['otp'] != session.get('temp_otp'): return jsonify({"msg": "Invalid OTP! ❌"})
    user = db.execute("SELECT * FROM users WHERE id=?", (data['id'],)).fetchone()
    if not user:
        db.execute("INSERT INTO users (id, pin) VALUES (?,?)", (data['id'], data['pin']))
        db.commit()
    session['user'] = data['id']
    return jsonify({"msg": "Success!"})

# ... baaki routes (connect, activate) purane jaise hi rahenge ...

@app.route('/')
def home():
    if 'user' not in session: return render_template_string(HTML_MAIN, logged_in=False)
    u = db.execute("SELECT * FROM users WHERE id=?", (session['user'],)).fetchone()
    return render_template_string(HTML_MAIN, logged_in=True, user_id=u[0], plan=u[2], 
                                dhan_id=u[3], dhan_token=u[4], max_loss=u[5], max_trades=u[6], wa=YOUR_WHATSAPP, upi=YOUR_UPI)

@app.route('/logout')
def logout(): session.clear(); return redirect('/')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
