import sqlite3, random, requests
from flask import Flask, request, jsonify, session, render_template_string, redirect

app = Flask(__name__)
app.secret_key = "CSC_FINAL_FIX_2026"

# --- CONFIGURATION (Fast2SMS Key Yahan Daalein) ---
FAST2SMS_API_KEY = "plwdy58v3eLJWFKNcS0mksbBMHuxRhDIAPqaQfUY16TECig7oZ8FPoGwcg15XuAWZmfUhKOq3dijsM7x"

def get_db():
    conn = sqlite3.connect('db.db', check_same_thread=False)
    conn.execute('''CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY, pin TEXT, plan TEXT DEFAULT 'Free',
        daily_loss INTEGER DEFAULT 0, trade_count INTEGER DEFAULT 0,
        max_loss INTEGER DEFAULT 500, kill_switch INTEGER DEFAULT 0,
        discipline_score INTEGER DEFAULT 100)''')
    conn.commit()
    return conn

db = get_db()

def send_otp(mobile, otp):
    url = "https://www.fast2sms.com/dev/bulkV2"
    params = {"authorization": FAST2SMS_API_KEY, "route": "q", 
              "message": f"CSC: Your Login OTP is {otp}", "numbers": str(mobile)}
    try:
        r = requests.get(url, params=params, timeout=5)
        return r.json()
    except: return None

# --- UI DESIGN ---
STYLE = """
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<style>
    :root { --blue: #0052FF; --bg: #F8FAFC; }
    body { font-family: sans-serif; background: var(--bg); margin: 0; padding-bottom: 70px; }
    .nav { background: white; padding: 15px; text-align: center; box-shadow: 0 2px 5px rgba(0,0,0,0.05); font-weight: 800; color: var(--blue); }
    .card { background: white; border-radius: 20px; padding: 20px; margin: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }
    input { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ddd; border-radius: 10px; box-sizing: border-box; }
    .btn { width: 100%; padding: 12px; border-radius: 10px; border: none; font-weight: 700; cursor: pointer; margin-top: 5px; }
    .btn-blue { background: var(--blue); color: white; }
    .btn-broker { background: #f1f5f9; color: #444; border: 1px solid #ddd; display: flex; align-items: center; justify-content: center; gap: 10px; font-size: 0.9rem; margin-bottom: 8px; }
    .f-nav { position: fixed; bottom: 0; width: 100%; background: white; display: flex; justify-content: space-around; padding: 10px 0; border-top: 1px solid #eee; }
    .f-item { text-decoration: none; color: #999; font-size: 0.7rem; text-align: center; }
    .f-item.active { color: var(--blue); }
</style>
"""

# --- LOGIN PAGE ---
LOGIN_HTML = STYLE + """
<div class="nav">CAPITAL SURAKSHA CLUB</div>
<div style="max-width:400px; margin:auto; padding-top:40px;">
    <div class="card" id="l-box">
        <h3>Secure Login</h3>
        <input id="num" type="tel" placeholder="Mobile Number" maxlength="10">
        <input id="pin" type="password" placeholder="4-Digit PIN" maxlength="4">
        <button class="btn btn-blue" onclick="reqOTP()">Get OTP</button>
    </div>
    <div class="card" id="o-box" style="display:none;">
        <h3>Verify OTP</h3>
        <input id="otp" type="text" placeholder="Enter OTP">
        <button class="btn btn-blue" onclick="verOTP()">Login</button>
    </div>
</div>
<script>
function reqOTP(){
    fetch('/request_otp', {method:'POST', headers:{'Content-Type':'application/json'}, 
    body:JSON.stringify({num:document.getElementById('num').value, pin:document.getElementById('pin').value})})
    .then(r=>r.json()).then(d=>{ alert(d.msg); if(d.success){ document.getElementById('l-box').style.display='none'; document.getElementById('o-box').style.display='block'; }});
}
function verOTP(){
    fetch('/verify_otp', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({otp:document.getElementById('otp').value})})
    .then(r=>r.json()).then(d=>{ if(d.success) location.reload(); else alert(d.msg); });
}
</script>
"""

# --- DASHBOARD ---
DASHBOARD_HTML = STYLE + """
<div class="nav">CSC DASHBOARD <a href="/logout" style="float:right; color:red; text-decoration:none;"><i class="fas fa-power-off"></i></a></div>
<div style="max-width:500px; margin:auto;">
    <div class="card">
        <p>Member: <b>+91 {{uid}}</b> <span style="float:right; color:blue;">{{plan}}</span></p>
        <div style="display:flex; gap:10px; text-align:center;">
            <div style="flex:1; background:#fef2f2; padding:10px; border-radius:10px;"><small>Loss Today</small><br><b style="color:red;">₹{{loss}}</b></div>
            <div style="flex:1; background:#f0fdf4; padding:10px; border-radius:10px;"><small>Score</small><br><b style="color:green;">{{score}}%</b></div>
        </div>
    </div>
    <div class="card">
        <h4 style="margin-top:0;">Connect Broker API</h4>
        <button class="btn btn-broker" onclick="window.location.href='/b/dhan'">Connect Dhan</button>
        <button class="btn btn-broker" onclick="window.location.href='/b/zerodha'">Connect Zerodha</button>
        <button class="btn btn-broker" onclick="window.location.href='/b/angel'">Connect Angel One</button>
    </div>
    <div class="card" style="text-align:center;">
        <div style="display:flex; gap:10px;">
            <button class="btn" style="background:green; color:white;" onclick="trd('win')">Win</button>
            <button class="btn" style="background:red; color:white;" onclick="trd('loss')">Loss</button>
        </div>
        <button class="btn" style="background:white; color:red; border:1px solid red; margin-top:10px;" onclick="ks()">ACTIVATE KILL SWITCH</button>
    </div>
</div>
<div class="f-nav">
    <a href="/" class="f-item active"><i class="fas fa-home"></i>Home</a>
    <a href="/payment" class="f-item"><i class="fas fa-crown"></i>Pro</a>
    <a href="/support" class="f-item"><i class="fas fa-headset"></i>Support</a>
</div>
<script>
function trd(t){ fetch('/trade',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({type:t})}).then(r=>r.json()).then(d=>{alert(d.msg); location.reload();}); }
function ks(){ if(confirm("Lock trading?")) fetch('/kill').then(()=>location.reload()); }
</script>
"""

@app.route('/')
def home():
    if 'user' not in session: return render_template_string(LOGIN_HTML)
    u = db.execute("SELECT * FROM users WHERE id=?", (session['user'],)).fetchone()
    return render_template_string(DASHBOARD_HTML, uid=u[0], plan=u[2], loss=u[3], score=u[8])

@app.route('/request_otp', methods=['POST'])
def req_otp():
    d = request.json
    num, pin = d.get('num'), d.get('pin')
    if not num or not pin: return jsonify({"success":False, "msg":"Fill all fields!"})
    u = db.execute("SELECT * FROM users WHERE id=?", (num,)).fetchone()
    if not u:
        db.execute("INSERT INTO users (id, pin) VALUES (?,?)", (num, pin))
        db.commit()
    elif u[1] != pin: return jsonify({"success":False, "msg":"Wrong PIN!"})
    
    otp = random.randint(1111, 9999)
    session['temp_otp'], session['temp_user'] = str(otp), num
    res = send_otp(num, otp)
    if res and res.get("return"): return jsonify({"success":True, "msg":"OTP Sent!"})
    return jsonify({"success":False, "msg":"SMS Error!"})

@app.route('/verify_otp', methods=['POST'])
def ver_otp():
    if request.json.get('otp') == session.get('temp_otp'):
        session['user'] = session.get('temp_user')
        return jsonify({"success":True})
    return jsonify({"success":False, "msg":"Wrong OTP!"})

@app.route('/trade', methods=['POST'])
def trade():
    uid = session.get('user')
    u = db.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
    if u[6] == 1 or u[4] >= 2: return jsonify({"msg":"Trading Locked! 🛑"})
    
    t_type = request.json.get('type')
    new_loss = u[3] + (250 if t_type == 'loss' else 0)
    db.execute("UPDATE users SET daily_loss=?, trade_count=trade_count+1 WHERE id=?", (new_loss, uid))
    db.commit()
    return jsonify({"msg":"Trade Recorded"})

@app.route('/kill')
def kill():
    db.execute("UPDATE users SET kill_switch=1 WHERE id=?", (session['user'],))
    db.commit()
    return "OK"

@app.route('/support')
def support():
    return render_template_string(STYLE + """
    <div class="nav">HELP CENTER</div>
    <div class="card" style="text-align:center;">
        <p>WhatsApp: <b>+91 8287550979</b></p>
        <p>Email: <b>CapitalSurakshaClub@Gmail.com</b></p>
        <button class="btn btn-blue" onclick="window.location.href='/'">Back</button>
    </div>""")

@app.route('/payment')
def payment():
    return render_template_string(STYLE + """
    <div class="nav">PRO PLAN</div>
    <div class="card" style="background:#0A192F; color:white;">
        <h3>Realistic Handholding:</h3>
        <p>- Weekly Trade Audit Calls</p>
        <p>- Psychology Sessions</p>
        <p>- Master E-Book Access</p>
        <div style="background:white; color:black; padding:10px; border-radius:10px;">UPI: 8587965337-1@nyes</div>
        <button class="btn btn-blue" onclick="window.location.href='/'" style="margin-top:15px;">Back</button>
    </div>""")

@app.route('/b/<name>')
def broker(name):
    return f"Connecting to {name}...<script>setTimeout(()=>{{alert('{name} API Connected!');location.href='/';}},2000);</script>"

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
