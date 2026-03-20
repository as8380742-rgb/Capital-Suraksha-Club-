import os, sqlite3, random, requests, time
from flask import Flask, request, jsonify, session, render_template_string, redirect

# Broker libraries ko safe import kar rahe hain taaki crash na ho
try:
    from kiteconnect import KiteConnect
    BROKER_LIB = True
except ImportError:
    BROKER_LIB = False

app = Flask(__name__)
app.secret_key = "CSC_FINAL_STABLE_2026"

# --- CONFIG ---
SMS_KEY = "plwdy58v3eLJWFKNcS0mksbBMHuxRhDIAPqaQfUY16TECig7oZ8FPoGwcg15XuAWZmfUhKOq3dijsM7x"
SUPPORT_EMAIL = "CapitalSurakshaClub@Gmail.com"

def get_db():
    db_path = os.path.join(os.getcwd(), 'database.db')
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.execute('''CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY, pin TEXT, plan TEXT DEFAULT 'Free',
        daily_loss REAL DEFAULT 0.0, trade_count INTEGER DEFAULT 0,
        max_loss REAL DEFAULT 500.0, kill_switch INTEGER DEFAULT 0,
        last_otp TEXT, otp_time REAL, discipline_score INTEGER DEFAULT 100)''')
    conn.commit()
    return conn

db = get_db()

def send_fast2sms(mobile, otp):
    url = "https://www.fast2sms.com/dev/bulkV2"
    payload = {"authorization": SMS_KEY, "route": "q", "message": f"CSC OTP: {otp}", "numbers": str(mobile)}
    try:
        r = requests.get(url, params=payload, timeout=5)
        return r.json().get("return")
    except: return False

# --- UI DESIGN ---
STYLE = """
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<style>
    :root { --blue: #2563EB; --red: #EF4444; --green: #10B981; --dark: #0F172A; }
    body { font-family: 'Inter', sans-serif; background: #F1F5F9; margin: 0; padding-bottom: 70px; }
    .nav { background: var(--dark); color: white; padding: 18px; display: flex; justify-content: space-between; align-items: center; }
    .card { background: white; border-radius: 16px; padding: 20px; margin: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .stat-box { padding: 15px; border-radius: 12px; text-align: center; flex: 1; }
    .btn { width: 100%; padding: 14px; border-radius: 10px; border: none; font-weight: bold; cursor: pointer; margin-top: 10px; }
    .btn-main { background: var(--blue); color: white; }
    .btn-outline { border: 1px solid var(--blue); color: var(--blue); background: white; font-size: 14px; }
    input { width: 100%; padding: 12px; border: 1px solid #CBD5E1; border-radius: 8px; margin: 5px 0; box-sizing: border-box; }
    .kill-active { border: 2px solid var(--red); background: #FEF2F2; }
</style>
"""

@app.route('/')
def home():
    if 'user' not in session:
        return render_template_string(STYLE + """
        <div style="max-width:400px; margin: 40px auto; padding: 20px;">
            <div class="card">
                <h2 style="text-align:center; color:var(--blue)">Capital Suraksha</h2>
                <input id="num" type="tel" placeholder="Mobile Number" maxlength="10">
                <input id="pin" type="password" placeholder="4-Digit PIN" maxlength="4">
                <button class="btn btn-main" onclick="reqOTP()">Get OTP</button>
                <div id="otp_sec" style="display:none; margin-top:20px;">
                    <input id="otp_val" type="text" placeholder="Enter OTP">
                    <button class="btn btn-main" onclick="verifyOTP()">Verify & Login</button>
                    <button id="resend" class="btn btn-outline" disabled onclick="reqOTP()">Resend in <span id="sec">30</span>s</button>
                </div>
            </div>
        </div>
        <script>
        function reqOTP(){
            let n = document.getElementById('num').value;
            let p = document.getElementById('pin').value;
            fetch('/api/otp/request', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({num:n, pin:p})})
            .then(r=>r.json()).then(d=>{
                alert(d.msg); 
                if(d.success){ 
                    document.getElementById('otp_sec').style.display='block';
                    let s = 30; let b = document.getElementById('resend'); b.disabled = true;
                    let i = setInterval(()=>{
                        s--; document.getElementById('sec').innerText = s;
                        if(s<=0){ clearInterval(i); b.disabled = false; b.innerHTML = "Resend OTP Now"; }
                    }, 1000);
                }
            });
        }
        function verifyOTP(){
            fetch('/api/otp/verify', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({otp:document.getElementById('otp_val').value})})
            .then(r=>r.json()).then(d=>{ if(d.success) location.reload(); else alert(d.msg); });
        }
        </script>""")

    u = db.execute("SELECT * FROM users WHERE id=?", (session['user'],)).fetchone()
    return render_template_string(STYLE + """
    <div class="nav"><span>CSC DASHBOARD</span> <a href="/logout" style="color:white"><i class="fas fa-power-off"></i></a></div>
    <div class="card {{ 'kill-active' if u6 == 1 else '' }}">
        <div style="display:flex; gap:10px;">
            <div class="stat-box" style="background:#DBEAFE"><small>Loss Today</small><br><b>₹{{ u3 }}</b></div>
            <div class="stat-box" style="background:#DCFCE7"><small>Score</small><br><b>{{ u9 }}</b></div>
        </div>
        <p style="text-align:center; font-weight:bold; margin-top:15px; color:{{ 'red' if u6 == 1 else 'green' }};">
            {{ '⚠️ TRADING LOCKED' if u6 == 1 else '✅ System Active' }}
        </p>
    </div>
    <div class="card">
        <h3>Broker Connect</h3>
        <button class="btn" style="background:#f8fafc; border:1px solid #ddd; text-align:left; padding:15px;" onclick="alert('Dhan API Link...')">1. Dhan Terminal</button>
        <button class="btn" style="background:#f8fafc; border:1px solid #ddd; text-align:left; padding:15px; margin-top:10px;" onclick="alert('Kite API Link...')">2. Zerodha Kite</button>
    </div>
    <div class="card">
        <button class="btn" style="background:var(--red); color:white;" onclick="triggerKill()">ACTIVATE KILL SWITCH</button>
    </div>
    <div style="padding:15px; font-size:13px; color:#666;">
        <b>Support:</b> WhatsApp +91 8287550979 | Email: {{ email }}
    </div>
    <script>
    function triggerKill(){ if(confirm("Activate Kill Switch?")) fetch('/api/kill_switch').then(()=>location.reload()); }
    </script>
    """, u3=u[3], u6=u[6], u9=u[9], email=SUPPORT_EMAIL)

# --- BACKEND ---

@app.route('/api/otp/request', methods=['POST'])
def handle_req():
    d = request.json
    num, pin = d.get('num'), d.get('pin')
    if not num or len(num) != 10: return jsonify({"success":False, "msg":"Mobile Number sahi daalo!"})
    
    u = db.execute("SELECT * FROM users WHERE id=?", (num,)).fetchone()
    if not u:
        db.execute("INSERT INTO users (id, pin) VALUES (?,?)", (num, pin))
    elif u[1] != pin: return jsonify({"success":False, "msg":"Wrong PIN!"})
    
    otp = str(random.randint(1111, 9999))
    db.execute("UPDATE users SET last_otp=?, otp_time=? WHERE id=?", (otp, time.time(), num))
    db.commit()
    
    if send_fast2sms(num, otp):
        session['pre_user'] = num
        return jsonify({"success":True, "msg":"OTP bhej diya hai! ✅"})
    return jsonify({"success":False, "msg":"SMS nahi gaya. API check karo."})

@app.route('/api/otp/verify', methods=['POST'])
def handle_ver():
    num = session.get('pre_user')
    u = db.execute("SELECT last_otp FROM users WHERE id=?", (num,)).fetchone()
    if u and request.json.get('otp') == u[0]:
        session['user'] = num
        return jsonify({"success":True})
    return jsonify({"success":False, "msg":"OTP galat hai! ❌"})

@app.route('/api/kill_switch')
def activate_kill():
    if 'user' in session:
        db.execute("UPDATE users SET kill_switch=1 WHERE id=?", (session['user'],))
        db.commit()
    return "OK"

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
