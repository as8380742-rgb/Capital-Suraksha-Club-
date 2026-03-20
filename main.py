import os
import sqlite3
import random
import requests
from flask import Flask, request, jsonify, session, render_template_string, redirect

app = Flask(__name__)
app.secret_key = "CSC_OFFICIAL_2026"

# --- CONFIGURATION ---
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
        "message": f"Welcome to Capital Suraksha Club. Your Private OTP is {otp}",
        "numbers": str(mobile)
    }
    try:
        response = requests.get(url, params=querystring)
        return response.json()
    except: return None

# --- MODERN UI (HTML/CSS) ---
HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Capital Suraksha Club</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        :root { --primary: #2563eb; --dark: #1e293b; --success: #22c55e; --danger: #ef4444; }
        body { font-family: 'Inter', sans-serif; background: #f8fafc; margin: 0; color: var(--dark); }
        .navbar { background: white; padding: 15px 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); display: flex; justify-content: space-between; align-items: center; }
        .logo { font-size: 1.2rem; font-weight: 800; color: var(--primary); display: flex; align-items: center; gap: 8px; }
        .container { padding: 20px; max-width: 500px; margin: auto; }
        .card { background: white; border-radius: 16px; padding: 20px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); margin-bottom: 20px; border: 1px solid #e2e8f0; }
        input { width: 100%; padding: 12px; margin: 8px 0; border: 1px solid #cbd5e1; border-radius: 8px; box-sizing: border-box; font-size: 16px; }
        button { width: 100%; padding: 12px; border-radius: 8px; border: none; font-weight: 600; cursor: pointer; transition: 0.2s; margin-top: 10px; }
        .btn-primary { background: var(--primary); color: white; }
        .btn-outline { background: transparent; border: 2px solid var(--primary); color: var(--primary); }
        .stat-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-top: 15px; }
        .stat-box { background: #f1f5f9; padding: 15px; border-radius: 12px; text-align: center; }
        .stat-val { display: block; font-size: 1.1rem; font-weight: 700; color: var(--primary); }
        .support-row { display: flex; justify-content: space-around; padding: 10px 0; }
        .support-item { text-align: center; text-decoration: none; color: var(--dark); font-size: 0.9rem; }
        .support-item i { display: block; font-size: 1.5rem; margin-bottom: 5px; color: var(--primary); }
        .footer { font-size: 0.75rem; color: #64748b; text-align: center; padding: 20px; line-height: 1.5; }
    </style>
</head>
<body>

<div class="navbar">
    <div class="logo"><i class="fas fa-shield-halved"></i> CSC Official</div>
    {% if logged_in %}<a href="/logout" style="color:var(--danger); text-decoration:none;"><i class="fas fa-sign-out-alt"></i></a>{% endif %}
</div>

<div class="container">
    {% if not logged_in %}
        <div class="card" id="login-section">
            <h2 style="margin-top:0;">Welcome Back</h2>
            <p style="color:#64748b; font-size:0.9rem;">Protect your capital with discipline.</p>
            <input id="num" type="tel" placeholder="Mobile Number" maxlength="10">
            <input id="pin" type="password" placeholder="4-Digit PIN" maxlength="4" inputmode="numeric">
            <button class="btn-primary" onclick="requestOTP()">Get Secure OTP</button>
        </div>

        <div class="card" id="otp-section" style="display:none;">
            <h2 style="margin-top:0;">Verify OTP</h2>
            <input id="otp" type="text" placeholder="Enter 4-Digit OTP" maxlength="4">
            <button class="btn-primary" onclick="verifyOTP()">Verify & Start Trading</button>
        </div>
    {% else %}
        <div class="card">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span style="font-weight:700;">Dashboard</span>
                <span style="font-size:0.8rem; background:#dcfce7; color:#166534; padding:2px 8px; border-radius:10px;">{{plan}} Plan</span>
            </div>
            <div class="stat-grid">
                <div class="stat-box">Loss Today<span class="stat-val">₹{{loss}}</span></div>
                <div class="stat-box">Score<span class="stat-val">{{score}}</span></div>
            </div>
            <button class="btn-outline" style="margin-top:20px;"><i class="fas fa-link"></i> Connect Broker (Soon)</button>
        </div>

        <div class="card" style="text-align:center;">
            <button class="btn-primary" style="background:var(--success);" onclick="trade('win')">Add Win Trade</button>
            <button class="btn-primary" style="background:var(--danger);" onclick="trade('loss')">Add Loss Trade</button>
            <button class="btn-outline" style="border-color:var(--danger); color:var(--danger); margin-top:20px;" onclick="kill()"><i class="fas fa-skull"></i> Active Kill Switch</button>
        </div>

        <div class="card" style="background: linear-gradient(135deg, #1e293b 0%, #334155 100%); color: white; border:none;">
            <h3 style="margin-top:0;"><i class="fas fa-crown" style="color:#fbbf24;"></i> Join Pro Club</h3>
            <ul style="font-size:0.85rem; padding-left:20px; line-height:1.8;">
                <li>Exclusive Risk Management E-Book</li>
                <li>Personal Handholding Support</li>
                <li>Custom Capital Protection Rules</li>
            </ul>
            <p style="font-size:0.75rem; margin-bottom:5px;">Transfer to UPI: <b>8587965337-1@nyes</b></p>
            <button class="btn-primary" style="background:#fbbf24; color:#1e293b;" onclick="window.location.href='/payment'">Check Benefits</button>
        </div>
    {% endif %}

    <div class="card">
        <div class="support-row">
            <a href="https://wa.me/918287550979" class="support-item"><i class="fab fa-whatsapp"></i>WhatsApp</a>
            <a href="mailto:CapitalSurakshaClub@Gmail.com" class="support-item"><i class="far fa-envelope"></i>Email</a>
            <a href="#" class="support-item" onclick="alert('Coming Soon')"><i class="fas fa-book"></i>E-Book</a>
        </div>
    </div>

    <div class="footer">
        <b>Disclaimer:</b> Capital Suraksha Club is an educational platform. We provide risk management tools and capital protection coaching. We do NOT provide call/tips or buy/sell recommendations. Trading involves risk. <br>© 2026 CSC Official
    </div>
</div>

<script>
function requestOTP(){
    let num = document.getElementById('num').value;
    let pin = document.getElementById('pin').value;
    if(num.length < 10 || pin.length < 4) return alert("Enter 10 digit mobile and 4 digit PIN");
    
    fetch('/request_otp', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({num:num, pin:pin})
    }).then(r=>r.json()).then(d=>{
        alert(d.msg);
        if(d.success){
            document.getElementById('login-section').style.display='none';
            document.getElementById('otp-section').style.display='block';
        }
    });
}

function verifyOTP(){
    let otp = document.getElementById('otp').value;
    fetch('/verify_otp', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({otp:otp})
    }).then(r=>r.json()).then(d=>{
        if(d.success) location.reload(); else alert(d.msg);
    });
}

function trade(type){
    fetch('/trade', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({type:type})
    }).then(r=>r.json()).then(d=>{ alert(d.msg); location.reload(); });
}

function kill(){ if(confirm("This will stop your trading for today. Confirm?")) fetch('/kill').then(()=>location.reload()); }
</script>
</body>
</html>
"""

# --- BACKEND LOGIC ---

@app.route('/')
def home():
    if 'user' not in session: return render_template_string(HTML, logged_in=False)
    user = db.execute("SELECT * FROM users WHERE id=?", (session['user'],)).fetchone()
    return render_template_string(HTML, logged_in=True, uid=user[0], plan=user[2], loss=user[3], trades=user[4], score=user[8])

@app.route('/request_otp', methods=['POST'])
def req_otp():
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
    if res and res.get("return"): return jsonify({"success": True, "msg": "OTP Sent Successfully! ✅"})
    return jsonify({"success": False, "msg": "SMS Error. Check Balance/Key."})

@app.route('/verify_otp', methods=['POST'])
def ver_otp():
    data = request.json
    if data.get('otp') == session.get('temp_otp'):
        session['user'] = session.get('temp_user')
        return jsonify({"success": True})
    return jsonify({"success": False, "msg": "Wrong OTP! ❌"})

@app.route('/trade', methods=['POST'])
def trade():
    user_id = session.get('user')
    if not user_id: return jsonify({"msg": "Login first"})
    data = request.json
    user = db.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    daily_loss, trades, max_loss, kill, last, score = user[3], user[4], user[5], user[6], user[7], user[8]

    if kill == 1: return jsonify({"msg": "Kill Switch is Active! 🛑"})
    if trades >= 2: return jsonify({"msg": "Max 2 trades allowed per day! 🔒"})
    if daily_loss >= max_loss: return jsonify({"msg": "Daily Loss Limit Reached! 🚫"})

    trades += 1
    if data['type'] == "loss":
        daily_loss += 250
        score -= 5
        msg = "Loss Recorded. Stop if needed! ❌"
    else:
        score += 2
        msg = "Win Recorded! Keep Discipline. ✅"

    db.execute("UPDATE users SET daily_loss=?, trade_count=?, last_result=?, discipline_score=? WHERE id=?", (daily_loss, trades, data['type'], score, user_id))
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
