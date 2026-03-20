import os, sqlite3, random, requests, time
from flask import Flask, request, jsonify, session, render_template_string, redirect

app = Flask(__name__)
app.secret_key = "CSC_CORE_PRO_2026"

# --- REAL CONFIG (Keys yahan bharna) ---
SMS_KEY = "plwdy58v3eLJWFKNcS0mksbBMHuxRhDIAPqaQfUY16TECig7oZ8FPoGwcg15XuAWZmfUhKOq3dijsM7x"
SUPPORT_EMAIL = "CapitalSurakshaClub@Gmail.com"

def get_db():
    db_path = os.path.join(os.getcwd(), 'database.db')
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.execute('''CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY, pin TEXT, plan TEXT DEFAULT 'Free',
        daily_loss REAL DEFAULT 0.0, trade_count INTEGER DEFAULT 0,
        max_loss REAL DEFAULT 500.0, kill_switch INTEGER DEFAULT 0,
        last_otp TEXT, otp_time REAL)''')
    conn.commit()
    return conn

db = get_db()

# --- REAL LOGIC FUNCTIONS ---

def send_fast2sms(mobile, otp):
    url = "https://www.fast2sms.com/dev/bulkV2"
    payload = {"authorization": SMS_KEY, "route": "q", "message": f"CSC OTP: {otp}", "numbers": str(mobile)}
    try:
        r = requests.get(url, params=payload, timeout=5)
        return r.json().get("return")
    except: return False

# --- UI / UX (Premium Dark Mode Dashboard) ---
STYLE = """
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<style>
    :root { --blue: #2563EB; --red: #EF4444; --green: #10B981; --dark: #0F172A; }
    body { font-family: 'Inter', sans-serif; background: #F1F5F9; margin: 0; color: var(--dark); }
    .nav { background: var(--dark); color: white; padding: 20px; font-weight: bold; display: flex; justify-content: space-between; }
    .card { background: white; border-radius: 16px; padding: 20px; margin: 15px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }
    .stat-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
    .stat-box { padding: 15px; border-radius: 12px; text-align: center; }
    .btn { width: 100%; padding: 14px; border-radius: 10px; border: none; font-weight: bold; cursor: pointer; margin-top: 10px; transition: 0.2s; }
    .btn-primary { background: var(--blue); color: white; }
    .btn-ghost { background: #E2E8F0; color: #475569; }
    .broker-card { border: 1px solid #E2E8F0; display: flex; align-items: center; gap: 15px; padding: 12px; border-radius: 12px; margin-bottom: 10px; cursor: pointer; }
    .kill-active { background: #FEE2E2; border: 2px solid var(--red); color: var(--red); animation: pulse 2s infinite; }
    @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.7; } 100% { opacity: 1; } }
    input { width: 100%; padding: 12px; border: 1px solid #CBD5E1; border-radius: 8px; margin: 5px 0; }
</style>
"""

@app.route('/')
def home():
    if 'user' not in session:
        return render_template_string(STYLE + """
        <div style="max-width:400px; margin: 50px auto; padding: 20px;">
            <div class="card">
                <h2 style="text-align:center; color:var(--blue);">CSC LOGIN</h2>
                <input id="num" type="tel" placeholder="Mobile Number">
                <input id="pin" type="password" placeholder="4-Digit PIN">
                <button class="btn btn-primary" onclick="reqOTP()">Get OTP</button>
                <div id="otp_sec" style="display:none; margin-top:20px;">
                    <input id="otp_val" type="text" placeholder="Enter 4-Digit OTP">
                    <button class="btn btn-primary" onclick="verifyOTP()">Verify & Login</button>
                    <button id="resend" class="btn btn-ghost" disabled onclick="reqOTP()">Resend OTP (<span id="sec">30</span>s)</button>
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
                    startTimer();
                }
            });
        }
        function startTimer(){
            let s = 30; let b = document.getElementById('resend'); b.disabled = true;
            let i = setInterval(()=>{
                s--; document.getElementById('sec').innerText = s;
                if(s<=0){ clearInterval(i); b.disabled = false; document.getElementById('sec').innerText = "0"; }
            }, 1000);
        }
        function verifyOTP(){
            fetch('/api/otp/verify', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({otp:document.getElementById('otp_val').value})})
            .then(r=>r.json()).then(d=>{ if(d.success) location.reload(); else alert(d.msg); });
        }
        </script>""")

    u = db.execute("SELECT * FROM users WHERE id=?", (session['user'],)).fetchone()
    is_killed = "kill-active" if u[6] == 1 else ""
    
    return render_template_string(STYLE + f"""
    <div class="nav"><span>CSC PRO</span> <a href="/logout" style="color:white"><i class="fas fa-sign-out-alt"></i></a></div>
    <div class="card {is_killed}">
        <div class="stat-grid">
            <div class="stat-box" style="background:#DBEAFE"> <small>Daily Loss</small><br><b>₹{u[3]}</b> </div>
            <div class="stat-box" style="background:#DCFCE7"> <small>Discipline</small><br><b>{u[7]}%</b> </div>
        </div>
        <p style="text-align:center; margin-top:15px; font-weight:bold;">Status: {"⚠️ TRADING LOCKED" if u[6]==1 else "✅ Active"}</p>
    </div>

    <div class="card">
        <h3>Real Broker Sync</h3>
        <div class="broker-card" onclick="alert('Dhan OAuth Redirect...')">
            <img src="https://dhan.co/wp-content/uploads/2021/09/dhan-logo.png" width="30"> <b>Dhan (Live Terminal)</b>
        </div>
        <div class="broker-card" onclick="alert('Kite Connect Redirect...')">
            <i class="fas fa-k" style="color:#E64A19"></i> <b>Zerodha Kite</b>
        </div>
    </div>

    <div class="card" style="text-align:center;">
        <h3>Emergency Controls</h3>
        <button class="btn btn-primary" style="background:var(--red);" onclick="triggerKill()">⚡ ACTIVATE KILL SWITCH</button>
        <p style="font-size:12px; color:#666; margin-top:10px;">This will block your API access for 24 hours.</p>
    </div>

    <div style="padding:15px;">
        <h4>Support</h4>
        <p><i class="fab fa-whatsapp"></i> +91 8287550979</p>
        <p><i class="far fa-envelope"></i> {SUPPORT_EMAIL}</p>
    </div>
    <script>
    function triggerKill(){ if(confirm("Are you sure? This cannot be undone today.")) fetch('/api/kill_switch').then(()=>location.reload()); }
    </script>
    """)

# --- BACKEND API LOGIC ---

@app.route('/api/otp/request', methods=['POST'])
def handle_req():
    d = request.json
    num, pin = d.get('num'), d.get('pin')
    if len(num) != 10: return jsonify({"success":False, "msg":"Invalid Number"})
    
    # DB Sync
    u = db.execute("SELECT * FROM users WHERE id=?", (num,)).fetchone()
    if not u:
        db.execute("INSERT INTO users (id, pin) VALUES (?,?)", (num, pin))
    elif u[1] != pin: return jsonify({"success":False, "msg":"Incorrect PIN"})
    
    otp = str(random.randint(1111, 9999))
    db.execute("UPDATE users SET last_otp=?, otp_time=? WHERE id=?", (otp, time.time(), num))
    db.commit()
    
    if send_fast2sms(num, otp):
        session['pre_user'] = num
        return jsonify({"success":True, "msg":"OTP Sent Successfully!"})
    return jsonify({"success":False, "msg":"SMS API Error! Check Balance."})

@app.route('/api/otp/verify', methods=['POST'])
def handle_ver():
    num = session.get('pre_user')
    u = db.execute("SELECT last_otp, otp_time FROM users WHERE id=?", (num,)).fetchone()
    if u and request.json.get('otp') == u[0]:
        session['user'] = num
        return jsonify({"success":True})
    return jsonify({"success":False, "msg":"Wrong OTP"})

@app.route('/api/kill_switch')
def activate_kill():
    # Real Logic: Backend se DB update aur session lock
    db.execute("UPDATE users SET kill_switch=1 WHERE id=?", (session['user'],))
    db.commit()
    return "Locked"

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
