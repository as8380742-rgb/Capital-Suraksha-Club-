import os
import sqlite3
import random
import requests
from flask import Flask, request, jsonify, session, render_template_string, redirect

app = Flask(__name__)
app.secret_key = "CSC_FINAL_PRO_KEY_2026"

# --- CONFIGURATION (Fast2SMS Key Daalein) ---
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
        "message": f"CSC: Your login OTP is {otp}. Protect your capital!",
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
    :root { --cobalt: #0052FF; --slate: #0F172A; --emerald: #10B981; --rose: #F43F5E; }
    body { font-family: 'Inter', sans-serif; background: #F8FAFC; margin: 0; color: #1E293B; }
    .nav { background: white; padding: 18px 24px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 4px 12px rgba(0,0,0,0.03); }
    .logo { color: var(--cobalt); font-weight: 800; font-size: 1.1rem; letter-spacing: -0.5px; }
    .card { background: white; border-radius: 24px; padding: 28px; margin: 16px; box-shadow: 0 10px 30px rgba(0,0,0,0.04); border: 1px solid #F1F5F9; }
    .btn { width: 100%; padding: 16px; border-radius: 16px; border: none; font-weight: 700; cursor: pointer; transition: all 0.2s ease; margin-top: 12px; font-size: 0.95rem; }
    .btn-blue { background: var(--cobalt); color: white; }
    .btn-blue:hover { transform: translateY(-2px); box-shadow: 0 8px 20px rgba(0,82,255,0.2); }
    .btn-broker { background: #F1F5F9; color: #334155; display: flex; align-items: center; justify-content: center; gap: 12px; border: 1px solid #E2E8F0; }
    .btn-broker:hover { background: #E2E8F0; }
    .stat-card { background: #F8FAFC; padding: 20px; border-radius: 20px; flex: 1; text-align: center; }
    .footer-nav { position: fixed; bottom: 0; width: 100%; background: white; display: flex; justify-content: space-around; padding: 15px 0; border-top: 1px solid #F1F5F9; }
    .footer-nav a { color: #94A3B8; text-decoration: none; font-size: 0.8rem; text-align: center; }
    .footer-nav a.active { color: var(--cobalt); }
    .footer-nav i { display: block; font-size: 1.4rem; margin-bottom: 4px; }
</style>
"""

# --- PAGES ---

LOGIN_HTML = STYLE + """
<div style="max-width:400px; margin:auto; padding-top:80px;">
    <div style="text-align:center; margin-bottom:40px;">
        <h1 class="logo">CAPITAL SURAKSHA CLUB</h1>
        <p style="color:#64748B;">Disciplined Trading Starts Here</p>
    </div>
    <div class="card" id="login-box">
        <input id="num" type="tel" placeholder="Mobile Number" style="width:100%; padding:15px; border-radius:12px; border:1px solid #CBD5E1; margin-bottom:15px;">
        <input id="pin" type="password" placeholder="4-Digit PIN" style="width:100%; padding:15px; border-radius:12px; border:1px solid #CBD5E1;">
        <button class="btn btn-blue" onclick="requestOTP()">Get Secure OTP</button>
    </div>
    <div class="card" id="otp-box" style="display:none;">
        <h2 style="margin:0 0 10px 0;">Verify Identity</h2>
        <input id="otp" type="text" placeholder="Enter 4-Digit OTP" style="width:100%; padding:15px; border-radius:12px; border:1px solid #CBD5E1;">
        <button class="btn btn-blue" onclick="verifyOTP()">Login Now</button>
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

DASHBOARD_HTML = STYLE + """
<div class="nav">
    <div class="logo">CSC DASHBOARD</div>
    <a href="/logout" style="color:var(--rose);"><i class="fas fa-power-off"></i></a>
</div>
<div style="max-width:500px; margin:auto; padding-bottom:100px;">
    <div class="card">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px;">
            <div><small style="color:#64748B;">Member ID</small><br><b>+91 {{uid}}</b></div>
            <span style="background:#EEF2FF; color:var(--cobalt); padding:6px 14px; border-radius:20px; font-weight:700; font-size:0.75rem;">{{plan}} PLAN</span>
        </div>
        <div style="display:flex; gap:16px;">
            <div class="stat-card"><small>Loss Today</small><br><b style="color:var(--rose); font-size:1.3rem;">₹{{loss}}</b></div>
            <div class="stat-card"><small>Discipline</small><br><b style="color:var(--emerald); font-size:1.3rem;">{{score}}%</b></div>
        </div>
    </div>

    <div class="card">
        <h4 style="margin:0 0 15px 0;"><i class="fas fa-link"></i> Active Broker API</h4>
        <button class="btn btn-broker" onclick="window.location.href='/broker/dhan'"><img src="https://dhan.co/wp-content/uploads/2021/11/dhan-logo-fb.png" width="20"> Connect Dhan</button>
        <button class="btn btn-broker" onclick="window.location.href='/broker/zerodha'"><img src="https://zerodha.com/static/images/favicon.png" width="20"> Connect Zerodha (Kite)</button>
        <button class="btn btn-broker" onclick="window.location.href='/broker/angel'"><img src="https://www.angelone.in/favicon.ico" width="20"> Connect Angel One</button>
    </div>

    <div class="card" style="text-align:center;">
        <div style="display:flex; gap:10px;">
            <button class="btn" style="background:var(--emerald); color:white;" onclick="trade('win')">Win Trade</button>
            <button class="btn" style="background:var(--rose); color:white;" onclick="trade('loss')">Loss Trade</button>
        </div>
        <button class="btn" style="background:white; color:var(--rose); border:2px solid var(--rose);" onclick="kill()"><i class="fas fa-skull"></i> ACTIVATE KILL SWITCH</button>
    </div>
</div>

<div class="footer-nav">
    <a href="/" class="active"><i class="fas fa-home"></i>Home</a>
    <a href="/payment"><i class="fas fa-crown"></i>Pro</a>
    <a href="/support"><i class="fas fa-headset"></i>Support</a>
</div>

<script>
function trade(t){ fetch('/trade',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({type:t})}).then(r=>r.json()).then(d=>{alert(d.msg); location.reload();}); }
function kill(){ if(confirm("This will lock your trading for today. Are you sure?")) fetch('/kill').then(()=>location.reload()); }
</script>
"""

SUPPORT_HTML = STYLE + """
<div class="nav"><div class="logo">HELP CENTER</div><a href="/"><i class="fas fa-arrow-left"></i></a></div>
<div style="max-width:500px; margin:auto; padding-top:20px;">
    <div class="card" style="text-align:center;">
        <i class="fas fa-headset" style="font-size:3rem; color:var(--cobalt); margin-bottom:20px;"></i>
        <h2>Direct Support</h2>
        <p style="color:#64748B;">Hamari team aapki help ke liye ready hai.</p>
        
        <a href="https://wa.me/918287550979" class="btn btn-blue" style="text-decoration:none; display:block; background:#25D366;">
            <i class="fab fa-whatsapp"></i> Chat on WhatsApp
        </a>
        <a href="mailto:CapitalSurakshaClub@Gmail.com" class="btn btn-broker" style="text-decoration:none; display:flex; margin-top:15px;">
            <i class="far fa-envelope"></i> Official Email
        </a>
    </div>
</div>
<div class="footer-nav">
    <a href="/"><i class="fas fa-home"></i>Home</a>
    <a href="/payment"><i class="fas fa-crown"></i>Pro</a>
    <a href="/support" class="active"><i class="fas fa-headset"></i>Support</a>
</div>
"""

# --- BACKEND LOGIC ---

@app.route('/')
def home():
    if 'user' not in session: return render_template_string(LOGIN_HTML)
    user = db.execute("SELECT * FROM users WHERE id=?", (session['user'],)).fetchone()
    return render_template_string(DASHBOARD_HTML, uid=user[0], plan=user[2], loss=user[3], score=user[8])

@app.route('/support')
def support():
    return render_template_string(SUPPORT_HTML)

@app.route('/payment')
def payment():
    # Realistic Pro Logic
    return render_template_string(STYLE + """
    <div class="nav"><div class="logo">PRO BENEFITS</div><a href="/"><i class="fas fa-arrow-left"></i></a></div>
    <div style="max-width:500px; margin:auto; padding:20px;">
        <div class="card" style="background:var(--slate); color:white; border:none;">
            <h2 style="color:#FFD700;"><i class="fas fa-gem"></i> CSC Pro Club</h2>
            <p>Upgrade for real handholding support:</p>
            <ul style="line-height:2; font-size:0.9rem;">
                <li><i class="fas fa-check-circle" style="color:var(--emerald);"></i> <b>1-on-1 Trade Audit:</b> Weekly zoom calls.</li>
                <li><i class="fas fa-check-circle" style="color:var(--emerald);"></i> <b>Psychology Session:</b> Controlling revenge trades.</li>
                <li><i class="fas fa-check-circle" style="color:var(--emerald);"></i> <b>Master E-Book:</b> Advanced Risk Strategies.</li>
            </ul>
            <div style="background:#1E293B; padding:15px; border-radius:15px; text-align:center; margin-top:20px;">
                <small>Pay ₹999 to UPI</small><br><b>8587965337-1@nyes</b>
            </div>
            <button class="btn" style="background:var(--cobalt); color:white;" onclick="window.location.href='/support'">Submit Screenshot</button>
        </div>
    </div>
    """)

@app.route('/broker/<name>')
def connect_broker(name):
    return f"<h1>Redirecting to {name.upper()} API Login...</h1><script>setTimeout(()=>{{alert('{name.upper()} Connected Successfully!'); window.location.href='/';}}, 2000);</script>"

@app.route('/trade', methods=['POST'])
def trade():
    uid = session.get('user')
    user = db.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
    if user[6] == 1: return jsonify({"msg": "Kill Switch Active! Trade Locked. 🛑"})
    if user[4] >= 2: return jsonify({"msg": "Daily limit reached (2 trades). 🔒"})
    
    new_trades = user[4] + 1
    new_loss = user[3] + (250 if request.json['type'] == 'loss' else 0)
    new_score = user[7] - (5 if request.json['type'] == 'loss' else -2)
    
    db.execute("UPDATE users SET daily_loss=?, trade_count=?, discipline_score=? WHERE id=?", (new_loss, new_trades, new_score, uid))
    db.commit()
    return jsonify({"msg": "Trade Recorded Successfully!"})

@app.route('/kill')
def kill():
    db.execute("UPDATE users SET kill_switch=1 WHERE id=?", (session['user'],))
    db.commit()
    return "Locked"

# [Baki routes login, logout, otp wahi same secure method hai jo work kar raha tha]
