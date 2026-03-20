import os, sqlite3, random, requests, time
from flask import Flask, request, jsonify, session, render_template_string, redirect

app = Flask(__name__)
app.secret_key = "CSC_FOUNDER_FINAL_2026"

# --- CONFIG ---
SMS_KEY = "plwdy58v3eLJWFKNcS0mksbBMHuxRhDIAPqaQfUY16TECig7oZ8FPoGwcg15XuAWZmfUhKOq3dijsM7x"
SUPPORT_EMAIL = "CapitalSurakshaClub@Gmail.com"

# --- DATABASE SETUP ---
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

def send_sms(mobile, otp):
    url = "https://www.fast2sms.com/dev/bulkV2"
    params = {"authorization": SMS_KEY, "route": "q", "message": f"CSC: Your OTP is {otp}", "numbers": str(mobile)}
    try:
        r = requests.get(url, params=params, timeout=5)
        return r.json().get("return")
    except: return False

# --- CSS STYLES ---
STYLE = """
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<style>
    :root { --blue: #2563EB; --red: #EF4444; --green: #10B981; --dark: #0F172A; }
    body { font-family: 'Inter', sans-serif; background: #F1F5F9; margin: 0; padding-bottom: 80px; }
    .nav { background: var(--dark); color: white; padding: 18px; display: flex; justify-content: space-between; align-items: center; font-weight: bold; }
    .card { background: white; border-radius: 16px; padding: 20px; margin: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .btn { width: 100%; padding: 14px; border-radius: 10px; border: none; font-weight: bold; cursor: pointer; margin-top: 10px; font-size: 15px; transition: 0.2s; }
    .btn-main { background: var(--blue); color: white; }
    .btn-outline { border: 1px solid var(--blue); color: var(--blue); background: white; }
    .broker-btn { display: flex; align-items: center; justify-content: center; gap: 12px; background: #F8FAFC; border: 1px solid #E2E8F0; }
    .f-nav { position: fixed; bottom: 0; width: 100%; background: white; display: flex; justify-content: space-around; padding: 12px 0; border-top: 1px solid #ddd; }
    .f-item { text-decoration: none; color: #94A3B8; font-size: 11px; text-align: center; }
    .f-item.active { color: var(--blue); }
    input { width: 100%; padding: 12px; border: 1px solid #CBD5E1; border-radius: 8px; margin: 8px 0; box-sizing: border-box; }
    .kill-active { border: 2px solid var(--red); background: #FEF2F2; color: var(--red); text-align: center; }
</style>
"""

# --- PAGES ---

@app.route('/')
def home():
    if 'user' not in session:
        return render_template_string(STYLE + """
        <div style="max-width:400px; margin: 40px auto; padding: 20px;">
            <div class="card">
                <h2 style="text-align:center; color:var(--blue);">Capital Suraksha Club</h2>
                <input id="num" type="tel" placeholder="Mobile Number" maxlength="10">
                <input id="pin" type="password" placeholder="4-Digit PIN" maxlength="4">
                <button class="btn btn-main" onclick="otpOp('req')">Get OTP</button>
                <div id="otp_sec" style="display:none; margin-top:15px;">
                    <input id="otp_val" type="text" placeholder="Enter 4-Digit OTP">
                    <button class="btn btn-main" onclick="otpOp('ver')">Verify & Login</button>
                    <button id="resend" class="btn btn-outline" disabled onclick="otpOp('req')">Resend in <span id="sec">30</span>s</button>
                </div>
            </div>
        </div>
        <script>
        function otpOp(t){
            let body = t=='req' ? {num:document.getElementById('num').value, pin:document.getElementById('pin').value} : {otp:document.getElementById('otp_val').value};
            fetch('/api/otp/'+t, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)})
            .then(r=>r.json()).then(d=>{
                alert(d.msg);
                if(d.success && t=='req'){
                    document.getElementById('otp_sec').style.display='block';
                    startTimer();
                } else if(d.success && t=='ver'){ location.reload(); }
            });
        }
        function startTimer(){
            let s=30; let b=document.getElementById('resend'); b.disabled=true;
            let i=setInterval(()=>{
                s--; document.getElementById('sec').innerText=s;
                if(s<=0){ clearInterval(i); b.disabled=false; b.innerText="Resend OTP"; }
            },1000);
        }
        </script>""")
    
    u = db.execute("SELECT * FROM users WHERE id=?", (session['user'],)).fetchone()
    return render_template_string(STYLE + """
    <div class="nav"><span>Capital Suraksha Club</span> <a href="/logout" style="color:white"><i class="fas fa-sign-out-alt"></i></a></div>
    {% if u[6] == 1 %}
    <div class="card kill-active"><h3>⚠️ TRADING LOCKED</h3><p>Kill Switch is Active for 24h.</p></div>
    {% endif %}
    <div class="card">
        <div style="display:flex; justify-content:space-around; text-align:center;">
            <div><small>Loss Today</small><br><b style="font-size:1.4rem; color:var(--red);">₹{{u[3]}}</b></div>
            <div><small>Discipline</small><br><b style="font-size:1.4rem; color:var(--green);">{{u[9]}}%</b></div>
        </div>
    </div>
    <div class="card">
        <h4 style="margin-top:0;">Broker Terminals</h4>
        <a href="https://dhan.co/api-login" class="btn broker-btn" style="text-decoration:none; color:black;">
            <img src="https://dhan.co/wp-content/uploads/2021/09/dhan-logo.png" width="20"> Dhan Live Sync
        </a>
        <a href="https://kite.trade/connect/login?api_key=YOUR_API_KEY" class="btn broker-btn" style="text-decoration:none; color:black; margin-top:10px;">
            <i class="fas fa-leaf" style="color:var(--red);"></i> Zerodha Kite Connect
        </a>
    </div>
    <div class="card"><button class="btn" style="background:var(--red); color:white;" onclick="triggerKill()">ACTIVATE KILL SWITCH</button></div>
    <div class="f-nav">
        <a href="/" class="f-item active"><i class="fas fa-home fa-lg"></i><br>Home</a>
        <a href="/payment" class="f-item"><i class="fas fa-crown fa-lg"></i><br>Pro</a>
        <a href="/support" class="f-item"><i class="fas fa-headset fa-lg"></i><br>Support</a>
    </div>
    <script>function triggerKill(){ if(confirm("Activate Kill Switch?")) fetch('/api/kill').then(()=>location.reload()); }</script>
    """, u=u)

@app.route('/support')
def support():
    return render_template_string(STYLE + f"""
    <div class="nav">Support Center</div>
    <div class="card" style="text-align:center;">
        <i class="fab fa-whatsapp" style="font-size:3rem; color:var(--green);"></i>
        <h3>WhatsApp Help</h3>
        <p>+91 8287550979</p>
        <hr>
        <i class="far fa-envelope" style="font-size:3rem; color:var(--blue);"></i>
        <h3>Email Support</h3>
        <p>{SUPPORT_EMAIL}</p>
        <button class="btn btn-main" onclick="location.href='/'">Back to Home</button>
    </div>""")

@app.route('/payment')
def payment():
    return render_template_string(STYLE + """
    <div class="nav">Pro Membership</div>
    <div class="card" style="background:var(--dark); color:white;">
        <h2>Founder's Handholding</h2>
        <p><i class="fas fa-check-circle"></i> Personal Trade Audits</p>
        <p><i class="fas fa-check-circle"></i> Psychology Masterclass</p>
        <p><i class="fas fa-check-circle"></i> Risk Management E-Book</p>
        <div style="background:white; color:black; padding:15px; border-radius:10px; margin:15px 0; text-align:center;">
            UPI ID: <b>8587965337-1@nyes</b>
        </div>
        <button class="btn btn-main" onclick="location.href='/'">Back to Home</button>
    </div>""")

# --- API ---

@app.route('/api/otp/req', methods=['POST'])
def req_otp():
    d = request.json
    num, pin = d.get('num'), d.get('pin')
    u = db.execute("SELECT * FROM users WHERE id=?", (num,)).fetchone()
    if not u: db.execute("INSERT INTO users (id, pin) VALUES (?,?)", (num, pin)); db.commit()
    elif u[1] != pin: return jsonify({"success":False, "msg":"Incorrect PIN"})
    
    otp = str(random.randint(1111, 9999))
    db.execute("UPDATE users SET last_otp=?, otp_time=? WHERE id=?", (otp, time.time(), num))
    db.commit()
    if send_sms(num, otp): session['pre_user'] = num; return jsonify({"success":True, "msg":"OTP Sent!"})
    return jsonify({"success":False, "msg":"SMS API Error"})

@app.route('/api/otp/ver', methods=['POST'])
def ver_otp():
    num = session.get('pre_user')
    u = db.execute("SELECT last_otp FROM users WHERE id=?", (num,)).fetchone()
    if u and request.json.get('otp') == u[0]: session['user'] = num; return jsonify({"success":True})
    return jsonify({"success":False, "msg":"Wrong OTP"})

@app.route('/api/kill')
def kill():
    db.execute("UPDATE users SET kill_switch=1 WHERE id=?", (session.get('user'),))
    db.commit()
    return "OK"

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
