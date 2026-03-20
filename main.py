import os
import sqlite3
import random
import requests
from flask import Flask, request, jsonify, session, render_template_string, redirect

app = Flask(__name__)
app.secret_key = "CSC_ULTIMATE_2026"

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
        "message": f"CSC: Your Login OTP is {otp}. Don't share it.",
        "numbers": str(mobile)
    }
    try:
        response = requests.get(url, params=querystring)
        return response.json()
    except: return None

# --- DESIGN SYSTEM ---
STYLE = """
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
<style>
    :root { --primary: #0052FF; --dark: #0A192F; --bg: #F5F7FA; }
    body { font-family: 'Segoe UI', sans-serif; background: var(--bg); margin: 0; padding: 0; }
    .nav { background: white; padding: 15px 20px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }
    .logo { color: var(--primary); font-weight: 800; text-transform: uppercase; }
    .card { background: white; border-radius: 20px; padding: 25px; margin: 15px; box-shadow: 0 10px 25px rgba(0,0,0,0.05); border: 1px solid #edf2f7; }
    input { width: 100%; padding: 15px; margin: 10px 0; border: 1px solid #cbd5e1; border-radius: 12px; box-sizing: border-box; font-size: 16px; }
    .btn { width: 100%; padding: 15px; border-radius: 12px; border: none; font-weight: 700; cursor: pointer; transition: 0.3s; margin-top: 10px; }
    .btn-blue { background: var(--primary); color: white; }
    .btn-outline { background: white; border: 1px solid #cbd5e1; color: #4a5568; display: flex; align-items: center; justify-content: center; gap: 10px; }
    .footer { font-size: 0.7rem; text-align: center; color: #a0aec0; padding: 20px; }
</style>
"""

# --- PAGE: LOGIN ---
LOGIN_HTML = STYLE + """
<div class="nav"><div class="logo">Capital Suraksha Club</div></div>
<div style="max-width:400px; margin:auto; padding-top:50px;">
    <div class="card" id="login-box">
        <h2 style="margin-top:0;">Secure Login</h2>
        <input id="num" type="tel" placeholder="Mobile Number" maxlength="10">
        <input id="pin" type="password" placeholder="4-Digit PIN" maxlength="4">
        <button class="btn btn-blue" onclick="requestOTP()">Get Login OTP</button>
    </div>
    <div class="card" id="otp-box" style="display:none;">
        <h2>Verify OTP</h2>
        <input id="otp" type="text" placeholder="Enter OTP">
        <button class="btn btn-blue" onclick="verifyOTP()">Verify & Enter Dashboard</button>
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

# --- PAGE: DASHBOARD ---
DASHBOARD_HTML = STYLE + """
<div class="nav"><div class="logo">Capital Suraksha Club</div> <a href="/logout"><i class="fas fa-power-off" style="color:red;"></i></a></div>
<div style="max-width:500px; margin:auto;">
    <div class="card">
        <div style="display:flex; justify-content:space-between; margin-bottom:15px;">
            <span>ID: <b>+91 {{uid}}</b></span>
            <span style="color:blue; font-weight:700;">{{plan}} Plan</span>
        </div>
        <div style="display:flex; gap:10px;">
            <div style="flex:1; background:#f8fafc; padding:15px; border-radius:15px; text-align:center;">
                <small>Loss Today</small><br><b style="font-size:1.2rem; color:red;">₹{{loss}}</b>
            </div>
            <div style="flex:1; background:#f8fafc; padding:15px; border-radius:15px; text-align:center;">
                <small>Disc. Score</small><br><b style="font-size:1.2rem; color:green;">{{score}}</b>
            </div>
        </div>
    </div>

    <div class="card">
        <h4 style="margin-top:0;">Broker Connect (Soon)</h4>
        <button class="btn btn-outline" onclick="alert('Dhan API Integration Coming Soon!')">Connect Dhan</button>
        <button class="btn btn-outline" onclick="alert('Zerodha API Integration Coming Soon!')">Connect Zerodha</button>
        <button class="btn btn-outline" onclick="alert('Angel One API Integration Coming Soon!')">Connect Angel One</button>
    </div>

    <div class="card" style="text-align:center;">
        <button class="btn" style="background:green; color:white;" onclick="trade('win')">Add Win Trade</button>
        <button class="btn" style="background:red; color:white;" onclick="trade('loss')">Add Loss Trade</button>
        <button class="btn btn-outline" style="border-color:red; color:red;" onclick="kill()">Activate Kill Switch</button>
    </div>

    <div class="card" style="background:#0A192F; color:white; text-align:center;">
        <h3 style="color:#FFD700;"><i class="fas fa-crown"></i> PRO BENEFITS</h3>
        <button class="btn" style="background:#FFD700; color:#0A192F;" onclick="window.location.href='/payment'">Upgrade Now</button>
    </div>

    <div class="footer">Educational App - Risk Management & Capital Protection<br>WhatsApp Support: +91 8287550979</div>
</div>
<script>
function trade(t){ fetch('/trade',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({type:t})}).then(r=>r.json()).then(d=>{alert(d.msg); location.reload();}); }
function kill(){ if(confirm("Stop trading?")) fetch('/kill').then(()=>location.reload()); }
</script>
"""

# --- BACKEND LOGIC ---
@app.route('/')
def home():
    if 'user' not in session: return render_template_string(LOGIN_HTML)
    user = db.execute("SELECT * FROM users WHERE id=?", (session['user'],)).fetchone()
    return render_template_string(DASHBOARD_HTML, uid=user[0], plan=user[2], loss=user[3], score=user[8])

@app.route('/payment')
def payment():
    return render_template_string(STYLE + """
    <div style="padding:20px; text-align:center;">
        <h2>PRO CLUB BENEFITS</h2>
        <ul style="text-align:left; max-width:300px; margin:auto;">
            <li>Exclusive Risk E-Book</li>
            <li>Handholding Support</li>
            <li>No Over-trading Locks</li>
        </ul>
        <div class="card">UPI ID: 8587965337-1@nyes</div>
        <p>Email: CapitalSurakshaClub@Gmail.com</p>
        <button class="btn btn-blue" onclick="window.location.href='/'">Go Back</button>
    </div>
    """)

@app.route('/request_otp', methods=['POST'])
def req_otp():
    data = request.json
    num, pin = data.get('num'), data.get('pin')
    user = db.execute("SELECT * FROM users WHERE id=?", (num,)).fetchone()
    if not user:
        db.execute("INSERT INTO users (id, pin) VALUES (?,?)", (num, pin))
        db.commit()
    elif user[1] != pin:
        return jsonify({"success": False, "msg": "Wrong PIN! ❌"})
    
    otp = random.randint(1111, 9999)
    session['temp_otp'] = str(otp)
    session['temp_user'] = num
    
    res = send_otp(num, otp)
    if res and res.get("return"): return jsonify({"success": True, "msg": "OTP Sent! ✅"})
    return jsonify({"success": False, "msg": "SMS Error! Check Balance."})

@app.route('/verify_otp', methods=['POST'])
def ver_otp():
    data = request.json
    if data.get('otp') == session.get('temp_otp'):
        session['user'] = session.get('temp_user')
        return jsonify({"success": True})
    return jsonify({"success": False, "msg": "Wrong OTP! ❌"})

@app.route('/trade', methods=['POST'])
def trade():
    uid = session.get('user')
    data = request.json
    user = db.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
    loss, trades, max_l, kill, score = user[3], user[4], user[5], user[6], user[8]
    if kill == 1 or trades >= 2 or loss >= max_l: return jsonify({"msg": "Limit Reached! 🛑"})
    
    trades += 1
    if data['type'] == "loss": loss += 250; score -= 5; msg = "Loss Recorded"
    else: score += 2; msg = "Win Recorded"
    
    db.execute("UPDATE users SET daily_loss=?, trade_count=?, discipline_score=? WHERE id=?", (loss, trades, score, uid))
    db.commit()
    return jsonify({"msg": msg})

@app.route('/kill')
def kill_switch():
    db.execute("UPDATE users SET kill_switch=1 WHERE id=?", (session['user'],))
    db.commit()
    return "OK"

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
