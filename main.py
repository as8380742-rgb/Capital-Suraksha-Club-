import os, sqlite3, random, requests, time
from flask import Flask, request, jsonify, session, render_template_string, redirect

app = Flask(__name__)
app.secret_key = "CSC_PRO_STABLE_V3"

# --- CONFIG ---
SMS_KEY = "plwdy58v3eLJWFKNcS0mksbBMHuxRhDIAPqaQfUY16TECig7oZ8FPoGwcg15XuAWZmfUhKOq3dijsM7x"
SUPPORT_EMAIL = "CapitalSurakshaClub@Gmail.com"
UPI_ID = "8587965337-1@nyes"

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

# --- CSS STYLES ---
STYLE = """
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<style>
    body { font-family: 'Segoe UI', sans-serif; background: #F8FAFC; margin: 0; padding-bottom: 80px; color: #1E293B; }
    .nav { background: #0F172A; color: white; padding: 18px; font-weight: bold; display: flex; justify-content: space-between; align-items: center; }
    .card { background: white; border-radius: 16px; padding: 20px; margin: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
    .mission { background: #EEF2FF; color: #4338CA; padding: 12px; border-radius: 10px; font-size: 13px; font-weight: 600; text-align: center; margin-bottom: 15px; border: 1px solid #C7D2FE; }
    .pnl-box { background: #1E293B; color: #10B981; padding: 15px; border-radius: 12px; margin-bottom: 15px; }
    .btn { width: 100%; padding: 15px; border-radius: 12px; border: none; font-weight: bold; cursor: pointer; font-size: 15px; transition: 0.2s; }
    .btn-blue { background: #2563EB; color: white; }
    .btn-outline { background: white; border: 1px solid #E2E8F0; color: #1E293B; margin-top: 10px; display: flex; align-items: center; justify-content: center; gap: 10px; text-decoration: none; }
    .f-nav { position: fixed; bottom: 0; width: 100%; background: white; display: flex; justify-content: space-around; padding: 12px 0; border-top: 1px solid #E2E8F0; z-index: 100; }
    .f-item { text-decoration: none; color: #64748B; font-size: 12px; text-align: center; font-weight: 600; }
    .f-item.active { color: #2563EB; }
    .lock-msg { background: #FEF2F2; color: #DC2626; padding: 12px; border-radius: 10px; text-align: center; font-weight: bold; margin-top: 10px; border: 1px solid #FEE2E2; }
    input { width: 100%; padding: 14px; border: 1px solid #E2E8F0; border-radius: 10px; margin: 8px 0; box-sizing: border-box; }
</style>
"""

@app.route('/')
def home():
    db = get_db()
    if 'user' not in session:
        return render_template_string(STYLE + """
        <div style="max-width:400px; margin: 50px auto; padding: 20px; text-align:center;">
            <h2 style="color:#0F172A;">Capital Suraksha Club</h2>
            <div class="card">
                <input id="num" type="tel" placeholder="Mobile Number" maxlength="10">
                <input id="pin" type="password" placeholder="4-Digit PIN" maxlength="4">
                <button class="btn btn-blue" onclick="handleAuth('req')">Get OTP</button>
                <div id="otp_div" style="display:none; margin-top:15px;">
                    <input id="otp_val" type="text" placeholder="Enter 4-Digit OTP">
                    <button class="btn btn-blue" onclick="handleAuth('ver')">Verify & Login</button>
                    <button id="resend_btn" style="background:none; border:none; color:#2563EB; margin-top:10px; cursor:pointer;" disabled onclick="handleAuth('req')">Resend in <span id="timer">30</span>s</button>
                </div>
            </div>
        </div>
        <script>
        function handleAuth(type){
            let val = type=='req' ? {num:document.getElementById('num').value, pin:document.getElementById('pin').value} : {otp:document.getElementById('otp_val').value};
            fetch('/api/auth/'+type, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(val)})
            .then(r=>r.json()).then(d=>{
                alert(d.msg);
                if(d.success && type=='req'){ document.getElementById('otp_div').style.display='block'; startTimer(); }
                else if(d.success && type=='ver') location.reload();
            });
        }
        function startTimer(){
            let s=30; let b=document.getElementById('resend_btn'); b.disabled=true;
            let i=setInterval(()=>{
                s--; document.getElementById('timer').innerText=s;
                if(s<=0){ clearInterval(i); b.disabled=false; b.innerText="Resend OTP Now"; }
            },1000);
        }
        </script>""")
    
    u = db.execute("SELECT * FROM users WHERE id=?", (session['user'],)).fetchone()
    trade_locked = (u[4] >= 2) or (u[6] == 1)
    
    return render_template_string(STYLE + """
    <div class="nav"><span>CSC Dashboard</span> <a href="/logout" style="color:white"><i class="fas fa-sign-out"></i></a></div>
    
    <div class="card">
        <div class="mission"><i class="fas fa-shield-alt"></i> Mission: Capital Protection & Discipline</div>
        <div class="pnl-box">
            <small style="color:white; opacity:0.7;">Live PnL (Broker Sync)</small><br>
            <b style="font-size:1.6rem;">+₹1,240.00</b>
        </div>
        <div style="display:flex; justify-content:space-between; font-weight:600;">
            <span>Trades: {{ count }}/2</span>
            <span style="color:{{ 'red' if locked else 'green' }}">{{ 'Locked' if locked else 'Active' }}</span>
        </div>
        {% if locked %}
        <div class="lock-msg">⚠️ TRADING LIMIT REACHED<br><small>Locked for 24 Hours</small></div>
        {% endif %}
    </div>

    <div class="card">
        <h4 style="margin-top:0;">Broker Terminals</h4>
        <a href="https://dhan.co/api-login" target="_blank" class="btn btn-outline"><img src="https://dhan.co/wp-content/uploads/2021/09/dhan-logo.png" width="18"> Dhan Login</a>
        <a href="https://kite.zerodha.com/connect/login?api_key=YOUR_KEY" target="_blank" class="btn btn-outline"><i class="fas fa-leaf" style="color:#E64A19"></i> Zerodha Kite</a>
    </div>

    <div class="f-nav">
        <a href="/" class="f-item active"><i class="fas fa-home fa-lg"></i><br>Home</a>
        <a href="/payment" class="f-item"><i class="fas fa-crown fa-lg"></i><br>Pro</a>
        <a href="/support" class="f-item"><i class="fas fa-headset fa-lg"></i><br>Support</a>
    </div>
    """, count=u[4], locked=trade_locked)

@app.route('/payment')
def payment():
    return render_template_string(STYLE + f"""
    <div class="nav">Upgrade to Pro</div>
    <div class="card" style="background:#0F172A; color:white; text-align:center;">
        <h3 style="color:#2563EB;">Pro Handholding</h3>
        <p>Unlock Risk Management E-Book & 24/7 Protection</p>
        <div style="background:rgba(255,255,255,0.1); padding:15px; border-radius:12px; margin:20px 0;">
            <small>UPI ID (Click to Copy)</small><br>
            <b id="upi_id" style="font-size:1.1rem; color:#2563EB;">{UPI_ID}</b> 
            <i class="fas fa-copy" style="cursor:pointer; margin-left:10px;" onclick="copyMe()"></i>
        </div>
        <p style="font-size:12px; opacity:0.6;">After payment, send screenshot on WhatsApp.</p>
    </div>
    <script>
    function copyMe(){
        let t = document.getElementById('upi_id').innerText;
        navigator.clipboard.writeText(t);
        alert("UPI ID Copied!");
    }
    </script>
    <div class="f-nav"><a href="/" class="f-item"><i class="fas fa-home"></i><br>Home</a><a href="/payment" class="f-item active"><i class="fas fa-crown"></i><br>Pro</a><a href="/support" class="f-item"><i class="fas fa-headset"></i><br>Support</a></div>
    """)

@app.route('/support')
def support():
    return render_template_string(STYLE + f"""
    <div class="nav">Help & Support</div>
    <div class="card" style="text-align:center; padding:40px 20px;">
        <i class="fab fa-whatsapp" style="font-size:3.5rem; color:#22C55E;"></i>
        <h3>Founder Chat</h3>
        <p>WhatsApp: +91 8287550979</p>
        <p>Email: {SUPPORT_EMAIL}</p>
    </div>
    <div class="f-nav"><a href="/" class="f-item"><i class="fas fa-home"></i><br>Home</a><a href="/payment" class="f-item"><i class="fas fa-crown"></i><br>Pro</a><a href="/support" class="f-item active"><i class="fas fa-headset"></i><br>Support</a></div>
    """)

# --- API ---
@app.route('/api/auth/req', methods=['POST'])
def req_otp():
    db = get_db()
    d = request.json
    num, pin = d.get('num'), d.get('pin')
    u = db.execute("SELECT * FROM users WHERE id=?", (num,)).fetchone()
    if not u: db.execute("INSERT INTO users (id, pin) VALUES (?,?)", (num, pin)); db.commit()
    elif u[1] != pin: return jsonify({"success":False, "msg":"Incorrect PIN!"})
    otp = str(random.randint(1111, 9999))
    db.execute("UPDATE users SET last_otp=?, otp_time=? WHERE id=?", (otp, time.time(), num))
    db.commit()
    session['pre_user'] = num
    return jsonify({"success":True, "msg":"OTP Sent Successfully!"})

@app.route('/api/auth/ver', methods=['POST'])
def ver_otp():
    db = get_db()
    u = db.execute("SELECT last_otp FROM users WHERE id=?", (session.get('pre_user'),)).fetchone()
    if u and request.json.get('otp') == u[0]: session['user'] = session.get('pre_user'); return jsonify({"success":True})
    return jsonify({"success":False, "msg":"Invalid OTP!"})

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
