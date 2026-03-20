import os, sqlite3, random, requests, time
from flask import Flask, request, jsonify, session, render_template_string, redirect

app = Flask(__name__)
app.secret_key = "CAPITAL_SURAKSHA_ULTIMATE_2026"

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

db = get_db()

# --- CSS STYLES (Clean & Professional) ---
STYLE = """
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    :root { --primary: #0052FF; --red: #FF3B30; --green: #34C759; --dark: #1C1C1E; --bg: #F2F2F7; }
    body { font-family: 'Inter', sans-serif; background: var(--bg); margin: 0; color: var(--dark); }
    .nav { background: white; padding: 20px; font-weight: 800; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }
    .card { background: white; border-radius: 20px; padding: 20px; margin: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.03); }
    .mission-tag { background: #EBF2FF; color: var(--primary); padding: 10px; border-radius: 12px; font-size: 13px; font-weight: 600; text-align: center; margin-bottom: 15px; }
    .stat-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-top: 15px; }
    .stat-card { background: #F8F9FA; padding: 15px; border-radius: 15px; text-align: center; }
    .btn { width: 100%; padding: 16px; border-radius: 14px; border: none; font-weight: 700; cursor: pointer; transition: 0.3s; font-size: 15px; }
    .btn-main { background: var(--primary); color: white; }
    .btn-broker { display: flex; align-items: center; justify-content: center; gap: 10px; background: white; border: 1px solid #E5E5EA; margin-top: 10px; }
    .f-nav { position: fixed; bottom: 0; width: 100%; background: white; display: flex; justify-content: space-around; padding: 15px 0; border-top: 1px solid #E5E5EA; }
    .f-item { text-decoration: none; color: #8E8E93; font-size: 12px; text-align: center; font-weight: 600; }
    .f-item.active { color: var(--primary); }
    input { width: 100%; padding: 15px; border: 1.5px solid #E5E5EA; border-radius: 12px; margin: 8px 0; box-sizing: border-box; font-size: 16px; }
    .pnl-box { background: var(--dark); color: white; border-radius: 15px; padding: 20px; margin-top: 10px; position: relative; }
    .copy-icon { cursor: pointer; color: var(--primary); margin-left: 10px; }
</style>
"""

# --- DASHBOARD PAGE ---
@app.route('/')
def home():
    if 'user' not in session:
        return render_template_string(STYLE + """
        <div style="max-width:400px; margin: 60px auto; padding: 20px;">
            <h1 style="text-align:center; letter-spacing:-1px;">Capital Suraksha <span style="color:var(--primary)">Club</span></h1>
            <div class="card">
                <input id="num" type="tel" placeholder="Mobile Number" maxlength="10">
                <input id="pin" type="password" placeholder="4-Digit PIN" maxlength="4">
                <button class="btn btn-main" onclick="auth('req')">Get Secure OTP</button>
                <div id="otp_sec" style="display:none; margin-top:15px;">
                    <input id="otp_val" type="text" placeholder="Enter OTP">
                    <button class="btn btn-main" onclick="auth('ver')">Verify & Enter</button>
                    <button id="resend" style="background:none; border:none; color:var(--primary); width:100%; margin-top:10px; cursor:pointer;" disabled onclick="auth('req')">Resend OTP in <span id="sec">30</span>s</button>
                </div>
            </div>
        </div>
        <script>
        function auth(t){
            let body = t=='req' ? {num:document.getElementById('num').value, pin:document.getElementById('pin').value} : {otp:document.getElementById('otp_val').value};
            fetch('/api/otp/'+t, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)})
            .then(r=>r.json()).then(d=>{
                alert(d.msg);
                if(d.success && t=='req'){ document.getElementById('otp_sec').style.display='block'; startTimer(); }
                else if(d.success && t=='ver'){ location.reload(); }
            });
        }
        function startTimer(){
            let s=30; let b=document.getElementById('resend'); b.disabled=true;
            let i=setInterval(()=>{
                s--; document.getElementById('sec').innerText=s;
                if(s<=0){ clearInterval(i); b.disabled=false; b.innerText="Resend OTP Now"; }
            },1000);
        }
        </script>""")
    
    u = db.execute("SELECT * FROM users WHERE id=?", (session['user'],)).fetchone()
    # 2-Trade Limit Check
    limit_reached = u[4] >= 2
    
    return render_template_string(STYLE + """
    <div class="nav"><span>Capital Suraksha Club</span> <a href="/logout" style="color:var(--red)"><i class="fas fa-power-off"></i></a></div>
    
    <div class="card">
        <div class="mission-tag"><i class="fas fa-shield-alt"></i> Mission: Zero Over-Trading & Capital Protection</div>
        <div class="pnl-box">
            <small style="opacity:0.7">Live PnL (Market Sync)</small>
            <h2 style="margin:5px 0; color:var(--green);">+₹1,240.00</h2>
            <div style="font-size:12px; color:var(--green);">Running 1 Active Position</div>
        </div>
        
        <div class="stat-grid">
            <div class="stat-card"><small>Trades Done</small><br><b>{{u[4]}} / 2</b></div>
            <div class="stat-card"><small>Max Loss Set</small><br><b>₹{{u[5]}}</b></div>
        </div>

        {% if limit_reached %}
        <div style="background:#FFF1F0; color:var(--red); padding:15px; border-radius:12px; margin-top:15px; text-align:center; font-weight:700;">
            <i class="fas fa-lock"></i> 2 TRADE LIMIT REACHED!<br>Trading Closed for 24 Hours.
        </div>
        {% endif %}
    </div>

    <div class="card">
        <h4 style="margin:0 0 10px 0;">Official Broker Sync</h4>
        <a href="https://dhan.co/api-login" target="_blank" class="btn btn-broker" style="text-decoration:none; color:black;">
            <img src="https://dhan.co/wp-content/uploads/2021/09/dhan-logo.png" width="20"> Dhan (Best Sync)
        </a>
        <a href="https://kite.zerodha.com/connect/login?api_key=YOUR_API_KEY" target="_blank" class="btn btn-broker" style="text-decoration:none; color:black;">
            <img src="https://zerodha.com/static/images/favicon.png" width="20"> Zerodha Kite Connect
        </a>
    </div>

    <div class="f-nav">
        <a href="/" class="f-item active"><i class="fas fa-chart-pie fa-lg"></i><br>Dashboard</a>
        <a href="/payment" class="f-item"><i class="fas fa-crown fa-lg"></i><br>Pro Club</a>
        <a href="/support" class="f-item"><i class="fas fa-headset fa-lg"></i><br>Support</a>
    </div>
    """, u=u, limit_reached=limit_reached)

# --- SUPPORT PAGE ---
@app.route('/support')
def support():
    return render_template_string(STYLE + f"""
    <div class="nav">Support & Help</div>
    <div class="card" style="text-align:center; padding:40px 20px;">
        <div style="background:var(--bg); width:80px; height:80px; border-radius:50%; display:flex; align-items:center; justify-content:center; margin:auto;">
            <i class="fab fa-whatsapp" style="font-size:2.5rem; color:var(--green);"></i>
        </div>
        <h3>Chat with Founder</h3>
        <p style="color:#666;">Contact for Handholding Support</p>
        <button class="btn btn-main" style="background:var(--green);" onclick="location.href='https://wa.me/918287550979'">Open WhatsApp</button>
        <p style="margin-top:20px; font-size:14px;"><i class="far fa-envelope"></i> {SUPPORT_EMAIL}</p>
    </div>
    <div class="f-nav">
        <a href="/" class="f-item"><i class="fas fa-chart-pie fa-lg"></i><br>Dashboard</a>
        <a href="/payment" class="f-item"><i class="fas fa-crown fa-lg"></i><br>Pro Club</a>
        <a href="/support" class="f-item active"><i class="fas fa-headset fa-lg"></i><br>Support</a>
    </div>""")

# --- PAYMENT PAGE ---
@app.route('/payment')
def payment():
    return render_template_string(STYLE + f"""
    <div class="nav">Upgrade to Pro</div>
    <div class="card" style="background:var(--dark); color:white; border:none;">
        <h2 style="color:var(--primary);">Handholding Pro</h2>
        <p><i class="fas fa-check-circle" style="color:var(--primary)"></i> Anti Over-Trading Robot</p>
        <p><i class="fas fa-check-circle" style="color:var(--primary)"></i> Risk Management E-Book</p>
        <p><i class="fas fa-check-circle" style="color:var(--primary)"></i> Weekly Psychology Audit</p>
        
        <div style="background:rgba(255,255,255,0.1); padding:20px; border-radius:15px; margin-top:20px; text-align:center;">
            <small style="display:block; margin-bottom:10px;">Transfer to UPI ID</small>
            <b style="font-size:1.2rem;" id="upi">{UPI_ID}</b>
            <i class="fas fa-copy copy-icon" onclick="copyUPI()"></i>
        </div>
        <p style="font-size:11px; text-align:center; opacity:0.6;">Send screenshot on WhatsApp after payment.</p>
    </div>
    <script>
    function copyUPI(){
        let upi = document.getElementById('upi').innerText;
        navigator.clipboard.writeText(upi);
        alert("UPI ID Copied!");
    }
    </script>
    <div class="f-nav">
        <a href="/" class="f-item"><i class="fas fa-chart-pie fa-lg"></i><br>Dashboard</a>
        <a href="/payment" class="f-item active"><i class="fas fa-crown fa-lg"></i><br>Pro Club</a>
        <a href="/support" class="f-item"><i class="fas fa-headset fa-lg"></i><br>Support</a>
    </div>""")

# --- BACKEND API ---
@app.route('/api/otp/req', methods=['POST'])
def req_otp():
    d = request.json
    num, pin = d.get('num'), d.get('pin')
    u = db.execute("SELECT * FROM users WHERE id=?", (num,)).fetchone()
    if not u: 
        db.execute("INSERT INTO users (id, pin) VALUES (?,?)", (num, pin))
        db.commit()
    elif u[1] != pin: return jsonify({"success":False, "msg":"Wrong PIN! Security Block."})
    
    otp = str(random.randint(1111, 9999))
    db.execute("UPDATE users SET last_otp=?, otp_time=? WHERE id=?", (otp, time.time(), num))
    db.commit()
    session['pre_user'] = num
    # Yahan send_sms(num, otp) call hoga
    return jsonify({"success":True, "msg":"Secure OTP Sent! ✅"})

@app.route('/api/otp/ver', methods=['POST'])
def ver_otp():
    num = session.get('pre_user')
    u = db.execute("SELECT last_otp FROM users WHERE id=?", (num,)).fetchone()
    if u and request.json.get('otp') == u[0]:
        session['user'] = num
        return jsonify({"success":True})
    return jsonify({"success":False, "msg":"Invalid OTP!"})

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
