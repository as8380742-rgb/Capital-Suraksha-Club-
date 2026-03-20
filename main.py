import os
import sqlite3
import random
import requests
from flask import Flask, request, jsonify, session, render_template_string, redirect

app = Flask(__name__)
app.secret_key = "CSC_OFFICIAL_PRO_2026"

# --- CONFIGURATION (Apni Fast2SMS Key Yahan Daalein) ---
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
            last_result TEXT DEFAULT '',
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
        "message": f"Capital Suraksha Club: Your Secure OTP is {otp}",
        "numbers": str(mobile)
    }
    try:
        response = requests.get(url, params=querystring)
        return response.json()
    except: return None

# --- UI DESIGN (CSS) ---
COMMON_STYLE = """
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
<style>
    :root { --primary: #0052FF; --dark: #0A192F; --bg: #F5F7FA; }
    body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: var(--bg); margin: 0; color: #333; }
    .nav { background: white; padding: 15px 20px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }
    .logo { color: var(--primary); font-weight: 800; font-size: 1.2rem; }
    .card { background: white; border-radius: 20px; padding: 25px; margin: 15px; box-shadow: 0 10px 25px rgba(0,0,0,0.05); border: 1px solid #edf2f7; }
    .btn { width: 100%; padding: 14px; border-radius: 12px; border: none; font-weight: 600; cursor: pointer; transition: 0.3s; margin-bottom: 10px; font-size: 1rem; }
    .btn-main { background: var(--primary); color: white; }
    .btn-broker { background: white; border: 1px solid #cbd5e0; display: flex; align-items: center; justify-content: center; gap: 10px; color: #4a5568; }
    .stat-box { background: #f8fafc; padding: 15px; border-radius: 15px; text-align: center; flex: 1; }
    .label { font-size: 0.8rem; color: #718096; display: block; margin-bottom: 5px; }
    .val { font-size: 1.2rem; font-weight: 700; color: var(--dark); }
    .footer { font-size: 0.7rem; text-align: center; color: #a0aec0; padding: 30px; line-height: 1.6; }
</style>
"""

# --- DASHBOARD PAGE ---
DASHBOARD_HTML = COMMON_STYLE + """
<div class="nav">
    <div class="logo"><i class="fas fa-shield-alt"></i> CAPITAL SURAKSHA CLUB</div>
    <a href="/logout" style="color:#e53e3e;"><i class="fas fa-power-off"></i></a>
</div>

<div style="max-width:500px; margin:auto;">
    <div class="card">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px;">
            <div>
                <span class="label">Member ID</span>
                <span style="font-weight:700;">+91 {{uid}}</span>
            </div>
            <span style="background:#EBF8FF; color:#2B6CB0; padding:5px 12px; border-radius:20px; font-size:0.75rem; font-weight:700;">{{plan}} PLAN</span>
        </div>
        
        <div style="display:flex; gap:15px;">
            <div class="stat-box"><span class="label">Loss Today</span><span class="val" style="color:#e53e3e;">₹{{loss}}</span></div>
            <div class="stat-box"><span class="label">Disc. Score</span><span class="val" style="color:#38a169;">{{score}}</span></div>
        </div>
    </div>

    <div class="card">
        <h4 style="margin-top:0;"><i class="fas fa-plug"></i> Connect Broker (API)</h4>
        <button class="btn btn-broker" onclick="alert('Connecting Zerodha API...')"><img src="https://zerodha.com/static/images/favicon.png" width="20"> Zerodha (Kite)</button>
        <button class="btn btn-broker" onclick="alert('Connecting Dhan API...')"><img src="https://dhan.co/wp-content/uploads/2021/11/dhan-logo-fb.png" width="20"> Dhan</button>
        <button class="btn btn-broker" onclick="alert('Connecting Angel One API...')"><img src="https://www.angelone.in/favicon.ico" width="20"> Angel One</button>
        <button class="btn btn-broker" onclick="alert('Connecting Groww API...')"><img src="https://groww.in/favicon.ico" width="20"> Groww</button>
    </div>

    <div class="card" style="text-align:center;">
        <button class="btn btn-main" style="background:#38a169;" onclick="trade('win')">Record Win Trade</button>
        <button class="btn btn-main" style="background:#e53e3e;" onclick="trade('loss')">Record Loss Trade</button>
        <button class="btn" style="background:#fff; border:1px solid #e53e3e; color:#e53e3e;" onclick="kill()">⚠️ Activate Kill Switch</button>
    </div>

    <div class="card" style="background:var(--dark); color:white; border:none;">
        <h3 style="margin-top:0; color:#ECC94B;"><i class="fas fa-crown"></i> Join PRO CLUB</h3>
        <p style="font-size:0.85rem; opacity:0.8;">Get personal coaching & specialized Risk E-Book.</p>
        <button class="btn" style="background:#ECC94B; color:var(--dark);" onclick="window.location.href='/payment'">View Benefits & Pay</button>
    </div>

    <div class="footer">
        <b>Educational Disclaimer:</b> Capital Suraksha Club is only for Risk Management Coaching. We do NOT provide signals, tips, or advisory services.
    </div>
</div>

<script>
function trade(type){
    fetch('/trade', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({type:type})})
    .then(r=>r.json()).then(d=>{ alert(d.msg); location.reload(); });
}
function kill(){ if(confirm("Stop all trading for today?")) fetch('/kill').then(()=>location.reload()); }
</script>
"""

# --- PAYMENT PAGE ---
PAYMENT_HTML = COMMON_STYLE + """
<div class="nav">
    <div class="logo"><i class="fas fa-crown"></i> PRO SUBSCRIPTION</div>
    <a href="/" style="text-decoration:none; color:var(--primary);">Back</a>
</div>
<div style="max-width:500px; margin:auto; padding:20px;">
    <div class="card">
        <h2 style="margin-top:0;">What you get in PRO:</h2>
        <div style="margin-bottom:15px; display:flex; gap:15px; align-items:center;">
            <i class="fas fa-book-open" style="font-size:1.5rem; color:var(--primary);"></i>
            <span><b>The Master Risk E-Book:</b> Learn how to never blow your account.</span>
        </div>
        <div style="margin-bottom:15px; display:flex; gap:15px; align-items:center;">
            <i class="fas fa-hands-helping" style="font-size:1.5rem; color:var(--primary);"></i>
            <span><b>Handholding Support:</b> 1-on-1 WhatsApp assistance for 30 days.</span>
        </div>
        <div style="margin-bottom:15px; display:flex; gap:15px; align-items:center;">
            <i class="fas fa-lock" style="font-size:1.5rem; color:var(--primary);"></i>
            <span><b>Advanced Kill-Switch:</b> Hard-lock rules for revenge trading.</span>
        </div>
        
        <hr style="border:0; border-top:1px solid #eee; margin:20px 0;">
        <p style="text-align:center; color:#718096;">Pay <b>₹999</b> to upgrade</p>
        <div style="background:#F7FAFC; padding:15px; border-radius:10px; text-align:center; border:2px dashed #CBD5E0;">
            <span class="label">UPI ID</span>
            <b style="font-size:1.1rem;">8587965337-1@nyes</b>
        </div>
        <p style="font-size:0.8rem; text-align:center; margin-top:15px;">After payment, send screenshot to:<br>
        <a href="https://wa.me/918287550979" style="color:#25D366; text-decoration:none; font-weight:700;">+91 8287550979</a></p>
    </div>
</div>
"""

# --- BACKEND ---

@app.route('/')
def home():
    if 'user' not in session: return render_template_string(LOGIN_HTML, logged_in=False) # LOGIN_HTML uses same logic as before
    user = db.execute("SELECT * FROM users WHERE id=?", (session['user'],)).fetchone()
    return render_template_string(DASHBOARD_HTML, uid=user[0], plan=user[2], loss=user[3], score=user[8])

@app.route('/payment')
def payment():
    return render_template_string(PAYMENT_HTML)

# [Remaining Routes: /request_otp, /verify_otp, /trade, /kill, /logout are same as previous stable version]
