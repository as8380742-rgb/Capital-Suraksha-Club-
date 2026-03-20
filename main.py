import os
import sqlite3
import random
import requests
from flask import Flask, request, jsonify, session, render_template_string, redirect

app = Flask(__name__)
app.secret_key = "CSC_OFFICIAL_SECURE_2026"

# --- CONFIGURATION (Apni Key Yahan Daalein) ---
FAST2SMS_API_KEY = "plwdy58v3eLJWFKNcS0mksbBMHuxRhDIAPqaQfUY16TECig7oZ8FPoGwcg15XuAWZmfUhKOq3dijsM7x"

def init_db():
    conn = sqlite3.connect('db.db', check_same_thread=False)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY, 
            pin TEXT,
            plan TEXT DEFAULT 'Free',
            daily_loss INTEGER DEFAULT 0,
            trade_count INTEGER DEFAULT 0,
            max_loss INTEGER DEFAULT 500,
            kill_switch INTEGER DEFAULT 0,
            discipline_score INTEGER DEFAULT 100
        )
    ''')
    conn.commit()
    return conn

db = init_db()

def send_otp(mobile, otp):
    url = "https://www.fast2sms.com/dev/bulkV2"
    querystring = {
        "authorization": FAST2SMS_API_KEY,
        "route": "q",
        "message": f"Welcome to Capital Suraksha Club. Your OTP is {otp}",
        "numbers": str(mobile)
    }
    try:
        response = requests.get(url, params=querystring)
        return response.json()
    except: return None

# --- UI DESIGN SYSTEM ---
STYLE = """
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<style>
    :root { --primary: #0052FF; --bg: #F8FAFC; --dark: #0F172A; }
    body { font-family: 'Inter', sans-serif; background: var(--bg); margin: 0; }
    .nav { background: white; padding: 15px 20px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }
    .logo { color: var(--primary); font-weight: 800; font-size: 1.1rem; }
    .card { background: white; border-radius: 20px; padding: 25px; margin: 15px; box-shadow: 0 4px 20px rgba(0,0,0,0.05); border: 1px solid #edf2f7; }
    input { width: 100%; padding: 15px; margin: 10px 0; border: 1px solid #cbd5e1; border-radius: 12px; box-sizing: border-box; font-size: 16px; }
    .btn { width: 100%; padding: 15px; border-radius: 12px; border: none; font-weight: 700; cursor: pointer; transition: 0.2s; margin-top: 10px; }
    .btn-main { background: var(--primary); color: white; }
    .btn-broker { background: #f1f5f9; color: #475569; display: flex; align-items: center; justify-content: center; gap: 10px; font-size: 0.9rem; margin-bottom: 8px; }
    .footer-nav { position: fixed; bottom: 0; width: 100%; background: white; display: flex; justify-content: space-around; padding: 12px 0; border-top: 1px solid #eee; }
    .nav-item { text-decoration: none; color: #94A3B8; font-size: 0.75rem; text-align: center; }
    .nav-item i { display: block; font-size: 1.3rem; margin-bottom: 3px; }
    .nav-item.active { color: var(--primary); }
</style>
"""

# --- LOGIN PAGE (SAME AS WORKING VERSION) ---
LOGIN_HTML = STYLE + """
<div style="max-width:400px; margin:auto; padding-top:60px; text-align:center;">
    <h2 class="logo">CAPITAL SURAKSHA CLUB</h2>
    <div class="card" id="login-box">
        <input id="num" type="tel" placeholder="Mobile Number" maxlength="10">
        <input id="pin" type="password" placeholder="4-Digit PIN" maxlength="4">
        <button class="btn btn-main" onclick="requestOTP()">Get Secure OTP</button>
    </div>
    <div class="card" id="otp-box" style="display:none;">
        <input id="otp" type="text" placeholder="Enter 4-Digit OTP">
        <button class="btn btn-main" onclick="verifyOTP()">Verify & Login</button>
    </div>
</div>
<script>
function requestOTP(){
    let n = document.getElementById('num').value;
    let p = document.getElementById('pin').value;
    fetch('/request_otp', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({num:n, pin:p})})
    .then(r=>r.json()).then(d=>{ alert(d.msg); if(d.success){ document.getElementById('login-box').style.display='none'; document.getElementById('otp-box').style.display='block'; }});
}
function verifyOTP(){
    let o = document.getElementById('otp').value;
    fetch('/verify_otp', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({otp:o})})
    .then(r=>r.json()).then(d=>{ if(d.success) location.reload(); else alert(d.msg); });
}
</script>
"""

# --- DASHBOARD PAGE ---
DASHBOARD_HTML = STYLE + """
<div class="nav"><div class="logo">CSC DASHBOARD</div><a href="/logout" style="color:red;"><i class="fas fa-sign-out-alt"></i></a></div>
<div style="max-width:500px; margin:auto; padding-bottom:80px;">
    <div class="card">
        <div style="display:flex; justify-content:space-between; margin-bottom:15px;">
            <span>Welcome: <b>+91 {{uid}}</b></span>
            <span style="color:blue; font-weight:700;">{{plan}} Plan</span>
        </div>
        <div style="display:flex; gap:10px;">
            <div style="flex:1; background:#f8fafc; padding:15px; border-radius:15px; text-align:center;">
                <small>Loss Today</small><br><b style="color:red; font-size:1.2rem;">₹{{loss}}</b>
            </div>
            <div style="flex:1; background:#f8fafc; padding:15px; border-radius:15px; text-align:center;">
                <small>Score</small><br><b style="color:green; font-size:1.2rem;">{{score}}%</b>
            </div>
        </div>
    </div>

    <div class="card">
        <h4 style="margin:0 0 10px 0;">Broker API Connection</h4>
        <button class="btn btn-broker" onclick="window.location.href='/broker/dhan'">Connect Dhan API</button>
        <button class="btn btn-broker" onclick="window.location.href='/broker/zerodha'">Connect Zerodha API</button>
        <button class="btn btn-broker" onclick="window.location.href='/broker/angel'">Connect Angel One API</button>
        <button class="btn btn-broker" onclick="window.location.href='/broker/groww'">Connect Groww API</button>
    </div>

    <div class="card" style="text-align:center;">
        <div style="display:flex; gap:10px;">
            <button class="btn" style="background:green; color:white;" onclick="trade('win')">Add Win</button>
            <button class="btn" style="background:red; color:white;" onclick="trade('loss')">Add Loss</button>
        </div>
        <button class="btn" style="background:white; color:red; border:1px solid red; margin-top:15px;" onclick="kill()">
            <i class="fas fa-skull"></i> ACTIVE KILL SWITCH
        </button>
    </div>
</div>

<div class="footer-nav">
    <a href="/" class="nav-item active"><i class="fas fa-home"></i>Home</a>
    <a href="/payment" class="nav-item"><i class="fas fa-crown"></i>Pro Plan</a>
    <a href="/support" class="nav-item"><i class="fas fa-headset"></i>Support</a>
</div>

<script>
function trade(t){ fetch('/trade',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({type:t})}).then(r=>r.json()).then(d=>{alert(d.msg); location.reload();}); }
function kill(){ if(confirm("This will lock your trading. Are you sure?")) fetch('/kill').then(()=>location.reload()); }
</script>
"""

# --- BACKEND ROUTES ---

@app.route('/')
def home():
    if 'user' not in session: return render_template_string(LOGIN_HTML)
    user = db.execute("SELECT * FROM users WHERE id=?", (session['user'],)).fetchone()
    return render_template_string(DASHBOARD_HTML, uid=user[0], plan=user[2], loss=user[3], score=user[8])

@app.route('/request_otp', methods=['POST'])
def request_otp():
    data = request.json
    num, pin = data.get('num'), data.get('pin')
    user = db.execute("SELECT * FROM users WHERE id=?", (num,)).fetchone()
    if not user:
        db.execute("INSERT INTO users (id, pin) VALUES (?,?)", (num, pin))
        db.commit()
    elif user[1] != pin:
        return jsonify({"success": False, "msg": "Invalid PIN! ❌"})
    
    otp = random.randint(1111, 9999)
    session['temp_otp'] = str(otp)
    session['temp_user'] = num
    
    res = send_otp(num, otp)
    if res and res.get("return"): return jsonify({"success": True, "msg": "OTP Sent! ✅"})
    return jsonify({"success": False, "msg": "SMS Server Error. Check API Key."})

@app.route('/verify_otp', methods=['POST'])
def verify_otp():
    data = request.json
    if data.get('otp') == session.get('temp_otp'):
        session['user'] = session.get('temp_user')
        return jsonify({"success": True})
    return jsonify({"success": False, "msg": "Wrong OTP! ❌"})

@app.route('/support')
def support():
    return render_template_string(STYLE + """
    <div class="nav"><div class="logo">SUPPORT</div><a href="/"><i class="fas fa-arrow-left"></i></a></div>
    <div class="card" style="text-align:center; padding-top:40px;">
        <i class="fab fa-whatsapp" style="font-size:3rem; color:green;"></i>
        <h3>WhatsApp Help</h3>
        <p>+91 8287550979</p>
        <hr>
        <i class="far fa-envelope" style="font-size:3rem; color:blue;"></i>
        <h3>Official Email</h3>
        <p>CapitalSurakshaClub@Gmail.com</p>
    </div>
    """)

@app.route('/payment')
def payment():
    return render_template_string(STYLE + """
    <div class="nav"><div class="logo">PRO PLAN</div><a href="/"><i class="fas fa-arrow-left"></i></a></div>
    <div class="card" style="background:#0A192F; color:white;">
        <h2 style="color:gold;">Handholding Support</h2>
        <p>1. Weekly Trade Audit Calls</p>
        <p>2. Psychology & Discipline Coaching</p>
        <p>3. Advanced Risk Management E-Book</p>
        <div style="background:white; color:black; padding:10px; border-radius:10px; margin-top:20px;">
            UPI ID: <b>8587965337-1@nyes</b>
        </div>
    </div>
    """)

@app.route('/broker/<name>')
def connect_broker_api(name):
    return f"<h1>Connecting to {name.upper()}...</h1><script>setTimeout(()=>{{alert('{name.upper()} API Connected!'); window.location.href='/';}}, 2000);</script>"

@app.route('/trade', methods=['POST'])
def trade():
    uid = session.get('user')
    user = db.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
    if user[6] == 1: return jsonify({"msg": "Kill Switch Active! 🛑"})
    
    new_loss = user[3] + (250 if request.json['type'] == 'loss' else 0)
    db.execute("UPDATE users SET daily_loss=?, trade_count=trade_count+1 WHERE id=?", (new_loss, uid))
    db.commit()
    return jsonify({"msg": "Success"})

@app.route('/kill')
def kill_it():
    db.execute("UPDATE users SET kill_switch=1 WHERE id=?", (session['user'],))
    db.commit()
    return "Locked"

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
