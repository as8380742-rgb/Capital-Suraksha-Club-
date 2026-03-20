import os, sqlite3, random, requests
from flask import Flask, request, jsonify, session, render_template_string, redirect

app = Flask(__name__)
app.secret_key = "CSC_OFFICIAL_SECRET_2026"

# --- API CONFIG ---
# Apni Fast2SMS Key yahan daalein
SMS_API_KEY = "plwdy58v3eLJWFKNcS0mksbBMHuxRhDIAPqaQfUY16TECig7oZ8FPoGwcg15XuAWZmfUhKOq3dijsM7x"

def get_db():
    db_path = os.path.join(os.getcwd(), 'database.db')
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.execute('''CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY, pin TEXT, plan TEXT DEFAULT 'Free',
        daily_loss INTEGER DEFAULT 0, trade_count INTEGER DEFAULT 0,
        max_loss INTEGER DEFAULT 500, kill_switch INTEGER DEFAULT 0,
        last_result TEXT, discipline_score INTEGER DEFAULT 100)''')
    conn.commit()
    return conn

db = get_db()

def send_otp(mobile, otp):
    url = "https://www.fast2sms.com/dev/bulkV2"
    params = {
        "authorization": SMS_API_KEY,
        "route": "q",
        "message": f"CSC: Your OTP is {otp}. Do not share it.",
        "numbers": str(mobile)
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        return r.json()
    except: return None

# --- UI (CSC Official Theme) ---
STYLE = """
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<style>
    :root { --blue: #0052FF; --red: #ff4d4d; --green: #2ecc71; --dark: #0f172a; }
    body { font-family: 'Segoe UI', sans-serif; background: #f4f7fe; margin: 0; padding-bottom: 80px; }
    .nav { background: white; padding: 18px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }
    .card { background: white; border-radius: 15px; padding: 20px; margin: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.03); }
    .btn { width: 100%; padding: 14px; border-radius: 10px; border: none; font-weight: 700; cursor: pointer; margin-top: 10px; transition: 0.2s; }
    .btn-blue { background: var(--blue); color: white; }
    .btn-outline { background: transparent; border: 1px solid #ddd; color: #555; display: flex; align-items: center; justify-content: center; gap: 10px; }
    .f-nav { position: fixed; bottom: 0; width: 100%; background: white; display: flex; justify-content: space-around; padding: 12px 0; border-top: 1px solid #eee; }
    .f-item { text-decoration: none; color: #999; font-size: 11px; text-align: center; }
    .f-item.active { color: var(--blue); }
    input { width: 100%; padding: 12px; margin: 8px 0; border: 1px solid #ddd; border-radius: 8px; box-sizing: border-box; }
</style>
"""

@app.route('/')
def home():
    if 'user' not in session:
        return render_template_string(STYLE + """
        <div class="nav"><b style="color:var(--blue)">CAPITAL SURAKSHA CLUB</b></div>
        <div class="card" id="lbox">
            <h3>Secure Login</h3>
            <input id="num" type="tel" placeholder="Mobile Number" maxlength="10">
            <input id="pin" type="password" placeholder="4-Digit PIN" maxlength="4">
            <button class="btn btn-blue" onclick="sendOTP()">Get OTP & Login</button>
        </div>
        <div class="card" id="obox" style="display:none;">
            <h3>Verify OTP</h3>
            <input id="otp" type="text" placeholder="Enter OTP">
            <button class="btn btn-blue" onclick="verifyOTP()">Verify</button>
        </div>
        <script>
        function sendOTP(){
            fetch('/api/req_otp', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({num:document.getElementById('num').value, pin:document.getElementById('pin').value})})
            .then(r=>r.json()).then(d=>{ alert(d.msg); if(d.success) {document.getElementById('lbox').style.display='none'; document.getElementById('obox').style.display='block';} });
        }
        function verifyOTP(){
            fetch('/api/ver_otp', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({otp:document.getElementById('otp').value})})
            .then(r=>r.json()).then(d=>{ if(d.success) location.reload(); else alert(d.msg); });
        }
        </script>""")
    
    u = db.execute("SELECT * FROM users WHERE id=?", (session['user'],)).fetchone()
    return render_template_string(STYLE + """
    <div class="nav"><b>CSC OFFICIAL</b> <a href="/logout" style="color:red"><i class="fas fa-power-off"></i></a></div>
    <div class="card" style="display:flex; justify-content:space-between; align-items:center;">
        <div><small>Loss Today</small><br><b style="color:var(--red); font-size:20px;">₹{{loss}}</b></div>
        <div style="text-align:right;"><small>Score</small><br><b style="color:var(--green); font-size:20px;">{{score}}</b></div>
    </div>
    <div class="card">
        <h4 style="margin:0 0 10px 0;">Broker Connection</h4>
        <button class="btn btn-outline" onclick="location.href='/conn/dhan'"><img src="https://dhan.co/wp-content/uploads/2021/09/dhan-logo.png" width="20"> Dhan</button>
        <button class="btn btn-outline" onclick="location.href='/conn/kite'"><i class="fas fa-kite"></i> Zerodha Kite</button>
        <button class="btn btn-outline" onclick="location.href='/conn/angel'"><i class="fas fa-shield-halved"></i> Angel One</button>
        <button class="btn btn-outline" onclick="location.href='/conn/groww'"><i class="fas fa-chart-line"></i> Groww</button>
    </div>
    <div class="card">
        <div style="display:flex; gap:10px;">
            <button class="btn" style="background:var(--green); color:white" onclick="trade('win')">Add Win</button>
            <button class="btn" style="background:var(--red); color:white" onclick="trade('loss')">Add Loss</button>
        </div>
        <button class="btn" style="border:1px solid var(--red); color:var(--red); margin-top:15px;" onclick="kill()">ACTIVATE KILL SWITCH</button>
    </div>
    <div class="f-nav">
        <a href="/" class="f-item active"><i class="fas fa-home fa-lg"></i><br>Home</a>
        <a href="/pro" class="f-item"><i class="fas fa-crown fa-lg"></i><br>Pro</a>
        <a href="/help" class="f-item"><i class="fas fa-headset fa-lg"></i><br>Help</a>
    </div>
    <script>
    function trade(t){ fetch('/api/trade',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({type:t})}).then(r=>r.json()).then(d=>{alert(d.msg);location.reload();}); }
    function kill(){ if(confirm("Activate Kill Switch?")) fetch('/api/kill').then(()=>location.reload()); }
    </script>
    """, loss=u[3], score=u[8])

# --- LOGIC ROUTES ---

@app.route('/api/req_otp', methods=['POST'])
def req_otp():
    d = request.get_json(silent=True)
    if not d: return jsonify({"success":False, "msg":"Invalid Request"})
    num, pin = d.get('num'), d.get('pin')
    
    u = db.execute("SELECT * FROM users WHERE id=?", (num,)).fetchone()
    if not u:
        db.execute("INSERT INTO users (id, pin) VALUES (?,?)", (num, pin))
        db.commit()
    elif u[1] != pin: return jsonify({"success":False, "msg":"Wrong PIN"})
    
    otp = str(random.randint(1111, 9999))
    session['temp_otp'], session['temp_user'] = otp, num
    res = send_otp(num, otp)
    if res and res.get("return"): return jsonify({"success":True, "msg":"OTP Sent!"})
    return jsonify({"success":False, "msg":"SMS API Error"})

@app.route('/api/ver_otp', methods=['POST'])
def ver_otp():
    d = request.get_json(silent=True)
    if d and d.get('otp') == session.get('temp_otp'):
        session['user'] = session.get('temp_user')
        return jsonify({"success":True})
    return jsonify({"success":False, "msg":"Wrong OTP"})

@app.route('/api/trade', methods=['POST'])
def record_trade():
    uid = session.get('user')
    u = db.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
    if u[6] == 1: return jsonify({"msg":"Kill Switch Active! 🛑"})
    
    t_type = request.json.get('type')
    new_loss = u[3] + (250 if t_type == 'loss' else 0)
    db.execute("UPDATE users SET daily_loss=?, trade_count=trade_count+1 WHERE id=?", (new_loss, uid))
    db.commit()
    return jsonify({"msg":"Recorded"})

@app.route('/api/kill')
def kill_switch():
    db.execute("UPDATE users SET kill_switch=1 WHERE id=?", (session.get('user'),))
    db.commit()
    return "OK"

@app.route('/conn/<broker>')
def connect_broker(broker):
    return f"<h1>Redirecting to {broker.upper()} Auth...</h1><script>setTimeout(()=>{{alert('{broker.upper()} API Connected!');location.href='/';}},2000);</script>"

@app.route('/pro')
def pro_page():
    return render_template_string(STYLE + "<div class='nav'>PRO CLUB</div><div class='card'><h2>Handholding Support</h2><p>UPI: 8587965337-1@nyes</p><button class='btn btn-blue' onclick='history.back()'>Back</button></div>")

@app.route('/help')
def help_page():
    return render_template_string(STYLE + "<div class='nav'>HELP</div><div class='card'><h3>WhatsApp: +91 8287550979</h3><button class='btn btn-blue' onclick='history.back()'>Back</button></div>")

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
