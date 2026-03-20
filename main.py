import os, sqlite3, random, requests, time
from flask import Flask, request, jsonify, session, render_template_string, redirect

app = Flask(__name__)
app.secret_key = "CSC_CORE_PRO_2026_FIXED"

# --- REAL CONFIG (Apni Key Bharna) ---
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

# --- UI / UX DESIGN ---
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
    .btn-outline { border: 1px solid var(--blue); color: var(--blue); background: white; }
    .broker-btn { display: flex; align-items: center; justify-content: center; gap: 10px; background: #F8FAFC; border: 1px solid #E2E8F0; margin-top: 8px; }
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
                <h2 style="text-align:center;">CSC Official</h2>
                <input id="num" type="tel" placeholder="Mobile Number">
                <input id="pin" type="password" placeholder="4-Digit PIN">
                <button class="btn btn-main" onclick="reqOTP()">Get OTP & Login</button>
                <div id="otp_sec" style="display:none; margin-top:20px;">
                    <input id="otp_val" type="text" placeholder="Enter 4-Digit OTP">
                    <button class="btn btn-main" onclick="verifyOTP()">Verify OTP</button>
                    <button id="resend" class="btn btn-outline" disabled onclick="reqOTP()">Resend in <span id="sec">30</span>s</button>
                </div>
            </div>
        </div>
        <script>
        function reqOTP(){
            fetch('/api/otp/request', {method:'POST', headers:{'Content-Type':'application/json'}, 
            body:JSON.stringify({num:document.getElementById('num').value, pin:document.getElementById('pin').value})})
            .then(r=>r.json()).then(d=>{
                alert(d.msg); if(d.success){ 
                    document.getElementById('otp_sec').style.display='block';
                    let s = 30; let b = document.getElementById('resend'); b.disabled = true;
                    let i = setInterval(()=>{
                        s--; document.getElementById('sec').innerText = s;
                        if(s<=0){ clearInterval(i); b.disabled = false; b.innerText = "Resend Now"; }
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
    status_msg = "⚠️ TRADING STOPPED" if u[6] == 1 else "✅ System Active"
    
    return render_template_string(STYLE + f"""
    <div class="nav"><span>CSC DASHBOARD</span> <a href="/logout" style="color:white"><i class="fas fa-power-off"></i></a></div>
    <div class="card {"kill-active" if u[6]==1 else ""}">
        <div style="display:flex; gap:10px;">
            <div class="stat-box" style="background:#DBEAFE"><small>Loss Today</small><br><b style="font-size:1.2rem;">₹{u[3]}</b></div>
            <div class="stat-box" style="background:#DCFCE7"><small>Score</small><br><b style="font-size:1.2rem;">{u[9]}</b></div>
        </div>
        <p style="text-align:center; font-weight:bold; margin-top:15px; color:{"red" if u[6]==1 else "green"};">{status_msg}</p>
    </div>

    <div class="card">
        <h3>Broker Integration</h3>
        <button class="btn broker-btn" onclick="connect('Dhan')"><img src="https://dhan.co/wp-content/uploads/2021/09/dhan-logo.png" width="20"> Connect Dhan</button>
        <button class="btn broker-btn" onclick="connect('Kite')"><i class="fas fa-leaf" style="color:red"></i> Connect Zerodha</button>
    </div>

    <div class="card">
        <h3>Discipline Controls</h3>
        <button class="btn" style="background:var(--red); color:white;" onclick="triggerKill()">ACTIVATE KILL SWITCH</button>
    </div>

    <div style="padding:15px; font-size:14px; color:#666;">
        <b>Handholding Support:</b><br>
        <i class="fab fa-whatsapp"></i> +91 8287550979<br>
        <i class="far fa-envelope"></i> {SUPPORT_EMAIL}
    </div>

    <script>
    function triggerKill(){ if(confirm("Activate Kill Switch? This will block API trading for 24h.")) fetch('/api/kill_switch').then(()=>location.reload()); }
    function connect(b){ alert("Redirecting to " + b + " Official API Login..."); }
    </script>
    """)

# --- BACKEND LOGIC ---

@app.route('/api/otp/request', methods=['POST'])
def handle_req():
    d = request.json
    num, pin = d.get('num'), d.get('pin')
    if not num or len(num) != 10: return jsonify({"success":False, "msg":"Invalid Number"})
    
    u = db.execute("SELECT * FROM users WHERE id=?", (num,)).fetchone()
    if not u:
        db.execute("INSERT INTO users (id, pin) VALUES (?,?)", (num, pin))
    elif u[1] != pin: return jsonify({"success":False, "msg":"Incorrect PIN"})
    
    otp = str(random.randint(1111, 9999))
    db.execute("UPDATE users SET last_otp=?, otp_time=? WHERE id=?", (otp, time.time(), num))
    db.commit()
    
    # Fast2SMS Call
    if send_fast2sms(num, otp):
        session['pre_user'] = num
        return jsonify({"success":True, "msg":"OTP Sent!"})
    return jsonify({"success":False, "msg":"SMS API Error. Check Balance/Key."})

@app.route('/api/otp/verify', methods=['POST'])
def handle_ver():
    num = session.get('pre_user')
    u = db.execute("SELECT last_otp FROM users WHERE id=?", (num,)).fetchone()
    if u and request.json.get('otp') == u[0]:
        session['user'] = num
        return jsonify({"success":True})
    return jsonify({"success":False, "msg":"Wrong OTP"})

@app.route('/api/kill_switch')
def activate_kill():
    if 'user' in session:
        db.execute("UPDATE users SET kill_switch=1 WHERE id=?", (session['user'],))
        db.commit()
        return "OK"
    return "Error", 401

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
