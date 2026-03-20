import os, sqlite3, random, requests, time
from flask import Flask, request, jsonify, session, render_template_string, redirect

app = Flask(__name__)
app.secret_key = "CSC_ULTIMATE_STABLE_V101"

# ==========================================
# 🔑 APNI API KEY YAHAN DAALEIN
# ==========================================
SMS_KEY = "plwdy58v3eLJWFKNcS0mksbBMHuxRhDIAPqaQfUY16TECig7oZ8FPoGwcg15XuAWZmfUhKOq3dijsM7x"
# ==========================================

UPI_ID = "8587965337-1@nyes"
SUPPORT_EMAIL = "CapitalSurakshaClub@Gmail.com"

def send_sms(number, otp):
    """Fast2SMS Integration Function"""
    url = "https://www.fast2sms.com/dev/bulkV2"
    payload = {
        "variables_values": otp,
        "route": "otp",
        "numbers": number,
    }
    headers = {"authorization": SMS_KEY}
    try:
        response = requests.get(url, headers=headers, params=payload)
        return response.json()
    except:
        return None

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

STYLE = """
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<style>
    body { font-family: sans-serif; background: #f3f4f6; margin: 0; padding-bottom: 80px; }
    .nav { background: #111827; color: white; padding: 15px; font-weight: bold; display: flex; justify-content: space-between; }
    .card { background: white; border-radius: 12px; padding: 20px; margin: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    .pnl { background: #1f2937; color: #10b981; padding: 15px; border-radius: 10px; text-align: center; margin: 10px 0; }
    .btn { width: 100%; padding: 12px; border-radius: 8px; border: none; font-weight: bold; cursor: pointer; margin-top: 10px; }
    .btn-p { background: #2563eb; color: white; }
    .btn-s { background: white; border: 1px solid #ddd; color: #333; display: block; text-decoration: none; text-align: center; line-height: 40px; border-radius: 8px; }
    .f-nav { position: fixed; bottom: 0; width: 100%; background: white; display: flex; justify-content: space-around; padding: 15px 0; border-top: 1px solid #ddd; }
    .f-item { text-decoration: none; color: #666; font-size: 12px; text-align: center; }
    .f-item.active { color: #2563eb; }
    input { width: 100%; padding: 12px; border: 1px solid #ccc; border-radius: 6px; margin: 5px 0; box-sizing: border-box; }
</style>
"""

@app.route('/')
def home():
    db = get_db()
    if 'user' not in session:
        return render_template_string(STYLE + """
        <div style="max-width:350px; margin: 50px auto; text-align:center;">
            <h2 style="color:#111827;">Capital Suraksha Club</h2>
            <div class="card">
                <input id="n" type="tel" placeholder="Mobile Number" maxlength="10">
                <input id="p" type="password" placeholder="4-Digit PIN" maxlength="4">
                <button class="btn btn-p" onclick="send()">Get OTP</button>
                <div id="os" style="display:none; margin-top:10px;">
                    <input id="ov" type="text" placeholder="Enter OTP">
                    <button class="btn btn-p" onclick="ver()">Verify & Login</button>
                </div>
            </div>
        </div>
        <script>
        function send(){
            let num = document.getElementById('n').value;
            let pin = document.getElementById('p').value;
            if(num.length!=10){ alert("Sahi number dalo bhai"); return; }
            fetch('/api/auth/req',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({num:num,pin:pin})})
            .then(r=>r.json()).then(d=>{alert(d.msg); if(d.success)document.getElementById('os').style.display='block';});
        }
        function ver(){
            fetch('/api/auth/ver',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({otp:document.getElementById('ov').value})})
            .then(r=>r.json()).then(d=>{if(d.success)location.reload();else alert(d.msg);});
        }
        </script>""")
    
    u = db.execute("SELECT trade_count, kill_switch FROM users WHERE id=?", (session['user'],)).fetchone()
    count = u[0]
    locked = (count >= 2) or (u[1] == 1)
    
    lock_html = '<div style="background:#fee2e2;color:#b91c1c;padding:10px;border-radius:8px;text-align:center;font-weight:bold;margin-top:10px;">LOCK ACTIVE: LIMIT REACHED</div>' if locked else ''
    status_text = "LOCKED" if locked else "ACTIVE"
    status_color = "red" if locked else "green"

    return render_template_string(STYLE + f"""
    <div class="nav"><span>CSC Dashboard</span> <a href="/logout" style="color:white">Logout</a></div>
    <div class="card">
        <div style="background:#dbeafe;color:#1e40af;padding:10px;border-radius:8px;text-align:center;font-size:12px;font-weight:bold;">DISCIPLINE IS KEY</div>
        <div class="pnl"><small>Broker Live PnL</small><br><b style="font-size:1.5rem;">+₹1,240.00</b></div>
        <div style="display:flex; justify-content:space-between; font-weight:bold; margin-top:10px;">
            <span>Trades: {count}/2</span>
            <span style="color:{status_color};">{status_text}</span>
        </div>
        {lock_html}
    </div>
    <div class="card">
        <h4 style="margin:0 0 10px 0;">Broker Access</h4>
        <a href="https://dhan.co/api-login" target="_blank" class="btn btn-s">Dhan Login</a>
        <a href="https://kite.zerodha.com/connect/login?api_key=KEY" target="_blank" class="btn btn-s" style="margin-top:10px;">Zerodha Kite</a>
    </div>
    <div class="f-nav">
        <a href="/" class="f-item active"><i class="fas fa-home"></i><br>Home</a>
        <a href="/payment" class="f-item"><i class="fas fa-crown"></i><br>Pro</a>
        <a href="/support" class="f-item"><i class="fas fa-headset"></i><br>Support</a>
    </div>
    """)

@app.route('/api/auth/req', methods=['POST'])
def req_api():
    db = get_db()
    d = request.json
    num, pin = d.get('num'), d.get('pin')
    u = db.execute("SELECT * FROM users WHERE id=?", (num,)).fetchone()
    if not u: 
        db.execute("INSERT INTO users (id, pin) VALUES (?,?)", (num, pin)); db.commit()
    elif u[1] != pin: 
        return jsonify({"success":False, "msg":"Incorrect PIN!"})
    
    otp = str(random.randint(1111, 9999))
    db.execute("UPDATE users SET last_otp=? WHERE id=?", (otp, num)); db.commit()
    
    # Send Actual SMS
    sms_res = send_sms(num, otp)
    msg = "OTP bhej diya gaya hai!" if sms_res and sms_res.get('return') else "OTP Sent (API Error, Check Balance)"
    
    session['temp_user'] = num
    return jsonify({"success":True, "msg": msg})

@app.route('/api/auth/ver', methods=['POST'])
def ver_api():
    db = get_db()
    u = db.execute("SELECT last_otp FROM users WHERE id=?", (session.get('temp_user'),)).fetchone()
    if u and request.json.get('otp') == u[0]:
        session['user'] = session.get('temp_user')
        return jsonify({"success":True})
    return jsonify({"success":False, "msg":"Wrong OTP!"})

@app.route('/payment')
def payment():
    return render_template_string(STYLE + f"""
    <div class="nav">Upgrade</div>
    <div class="card" style="text-align:center;">
        <h3>Pro Handholding</h3>
        <p>UPI ID: <b>{UPI_ID}</b></p>
        <button class="btn btn-p" onclick="navigator.clipboard.writeText('{UPI_ID}');alert('Copied!')">Copy UPI ID</button>
    </div>
    <div class="f-nav"><a href="/" class="f-item">Home</a><a href="/payment" class="f-item active">Pro</a><a href="/support" class="f-item">Support</a></div>
    """)

@app.route('/support')
def support():
    return render_template_string(STYLE + f"""
    <div class="nav">Support</div>
    <div class="card" style="text-align:center;">
        <i class="fab fa-whatsapp" style="font-size:3rem; color:green;"></i>
        <h3>Founder Support</h3>
        <button class="btn btn-p" onclick="window.open('https://wa.me/918287550979')">WhatsApp Now</button>
    </div>
    <div class="f-nav"><a href="/" class="f-item">Home</a><a href="/payment" class="f-item">Pro</a><a href="/support" class="f-item active">Support</a></div>
    """)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
