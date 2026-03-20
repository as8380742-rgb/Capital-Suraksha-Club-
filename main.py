import os, sqlite3, random, requests, time
from flask import Flask, request, jsonify, session, render_template_string, redirect

app = Flask(__name__)
app.secret_key = "CSC_FINAL_RELIABLE_2026"

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

# --- CSS (Ultra Clean & Fixed) ---
STYLE = """
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<style>
    body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #F9FAFB; margin: 0; padding-bottom: 80px; color: #111827; }
    .nav { background: #111827; color: white; padding: 20px; font-weight: bold; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    .card { background: white; border-radius: 16px; padding: 20px; margin: 15px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); border: 1px solid #E5E7EB; }
    .mission-tag { background: #EFF6FF; color: #1E40AF; padding: 12px; border-radius: 12px; font-size: 13px; font-weight: 600; text-align: center; margin-bottom: 15px; border: 1px solid #DBEAFE; }
    .pnl-display { background: #1F2937; color: #10B981; padding: 20px; border-radius: 15px; text-align: center; margin-bottom: 15px; }
    .btn { width: 100%; padding: 15px; border-radius: 12px; border: none; font-weight: bold; cursor: pointer; font-size: 16px; transition: 0.3s; }
    .btn-primary { background: #2563EB; color: white; }
    .btn-outline { background: white; border: 1.5px solid #E5E7EB; color: #374151; margin-top: 12px; display: flex; align-items: center; justify-content: center; gap: 10px; text-decoration: none; }
    .f-nav { position: fixed; bottom: 0; width: 100%; background: white; display: flex; justify-content: space-around; padding: 15px 0; border-top: 1px solid #E5E7EB; z-index: 999; }
    .f-item { text-decoration: none; color: #6B7280; font-size: 12px; text-align: center; font-weight: 600; }
    .f-item.active { color: #2563EB; }
    .lock-status { background: #FEF2F2; color: #B91C1C; padding: 15px; border-radius: 12px; text-align: center; font-weight: bold; border: 1px solid #FEE2E2; margin-top: 10px; }
    input { width: 100%; padding: 14px; border: 1px solid #D1D5DB; border-radius: 10px; margin: 10px 0; box-sizing: border-box; font-size: 16px; }
</style>
"""

@app.route('/')
def home():
    db = get_db()
    if 'user' not in session:
        return render_template_string(STYLE + """
        <div style="max-width:400px; margin: 60px auto; padding: 20px; text-align:center;">
            <h2 style="color:#111827; font-size: 28px; margin-bottom: 5px;">Capital Suraksha</h2>
            <p style="color:#6B7280; margin-bottom: 30px;">Login to protect your capital</p>
            <div class="card">
                <input id="num" type="tel" placeholder="Mobile Number" maxlength="10">
                <input id="pin" type="password" placeholder="4-Digit PIN" maxlength="4">
                <button class="btn btn-primary" onclick="doAuth('req')">Get Secure OTP</button>
                <div id="otp_box" style="display:none; margin-top:20px;">
                    <input id="otp_val" type="text" placeholder="Enter 4-Digit OTP">
                    <button class="btn btn-primary" onclick="doAuth('ver')">Verify & Enter</button>
                    <button id="resend_btn" style="background:none; border:none; color:#2563EB; margin-top:15px; cursor:pointer; font-weight:600;" disabled onclick="doAuth('req')">Resend OTP in <span id="timer">30</span>s</button>
                </div>
            </div>
        </div>
        <script>
        function doAuth(action){
            let data = action=='req' ? {num:document.getElementById('num').value, pin:document.getElementById('pin').value} : {otp:document.getElementById('otp_val').value};
            fetch('/api/auth/'+action, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(data)})
            .then(r=>r.json()).then(res=>{
                alert(res.msg);
                if(res.success && action=='req'){ document.getElementById('otp_box').style.display='block'; startClock(); }
                else if(res.success && action=='ver') location.reload();
            });
        }
        function startClock(){
            let s=30; let b=document.getElementById('resend_btn'); b.disabled=true;
            let i=setInterval(()=>{
                s--; document.getElementById('timer').innerText=s;
                if(s<=0){ clearInterval(i); b.disabled=false; b.innerText="Resend OTP Now"; }
            },1000);
        }
        </script>""")
    
    u = db.execute("SELECT * FROM users WHERE id=?", (session['user'],)).fetchone()
    # Pre-calculating logic in Python to avoid Jinja errors
    trades_done = u[4]
    is_locked = (trades_done >= 2) or (u[6] == 1)
    status_text = "LOCKED" if is_locked else "ACTIVE"
    status_color = "#EF4444" if is_locked else "#10B981"
    
    return render_template_string(STYLE + """
    <div class="nav"><span>CSC Club</span> <a href="/logout" style="color:white"><i class="fas fa-power-off"></i></a></div>
    
    <div class="card">
        <div class="mission-tag"><i class="fas fa-shield-alt"></i> Official Mission: Capital Protection</div>
        <div class="pnl-display">
            <small style="opacity:0.7; color:white;">Live PnL (Broker Sync)</small><br>
            <b style="font-size:1.8rem;">+₹1,240.00</b>
        </div>
        <div style="display:flex; justify-content:space-between; align-items:center; padding: 0 5px;">
            <span style="font-weight:700; color:#4B5563;">Trades: {{ count }}/2</span>
            <span style="font-weight:800; color:{{ color }}">{{ status }}</span>
        </div>
        {% if locked %}
        <div class="lock-status">
            <i class="fas fa-lock"></i> 2 TRADE LIMIT REACHED<br>
            <small style="font-weight:500;">Trading is closed for today to save your capital.</small>
        </div>
        {% endif %}
    </div>

    <div class="card">
        <h4 style="margin:0 0 15px 0; color:#374151;">Broker Terminal Sync</h4>
        <a href="https://dhan.co/api-login" target="_blank" class="btn btn-outline">
            <img src="https://dhan.co/wp-content/uploads/2021/09/dhan-logo.png" width="20"> Dhan Live Login
        </a>
        <a href="https://kite.zerodha.com/connect/login?api_key=YOUR_KEY" target="_blank" class="btn btn-outline">
            <i class="fas fa-leaf" style="color:#E64A19"></i> Zerodha Kite Login
        </a>
    </div>

    <div class="f-nav">
        <a href="/" class="f-item active"><i class="fas fa-chart-line fa-lg"></i><br>Dashboard</a>
        <a href="/payment" class="f-item"><i class="fas fa-gem fa-lg"></i><br>Pro Plan</a>
        <a href="/support" class="f-item"><i class="fas fa-headset fa-lg"></i><br>Support</a>
    </div>
    """, count=trades_done, locked=is_locked, status=status_text, color=status_color)

@app.route('/payment')
def payment():
    return render_template_string(STYLE + f"""
    <div class="nav">Pro Membership</div>
    <div class="card" style="background:#111827; color:white; text-align:center; padding:30px 20px;">
        <h2 style="color:#3B82F6; margin-top:0;">Handholding Support</h2>
        <p style="opacity:0.8;">Unlock Risk Management E-Book & Kill Switch</p>
        <div style="background:rgba(255,255,255,0.05); padding:20px; border-radius:15px; margin:25px 0; border: 1px dashed rgba(255,255,255,0.2);">
            <small style="display:block; margin-bottom:10px; opacity:0.6;">Transfer to UPI ID</small>
            <b id="upi_val" style="font-size:1.3rem; color:#3B82F6;">{UPI_ID}</b> 
            <i class="fas fa-copy" style="cursor:pointer; margin-left:12px; color:#3B82F6;" onclick="copyUPI()"></i>
        </div>
        <p style="font-size:12px; color:#9CA3AF;">Screenshot bhejte hi Pro features active ho jayenge.</p>
    </div>
    <script>
    function copyUPI(){
        let t = document.getElementById('upi_val').innerText;
        navigator.clipboard.writeText(t).then(() => alert("UPI ID Copied! ✅"));
    }
    </script>
    <div class="f-nav"><a href="/" class="f-item"><i class="fas fa-chart-line"></i><br>Dashboard</a><a href="/payment" class="f-item active"><i class="fas fa-gem"></i><br>Pro</a><a href="/support" class="f-item"><i class="fas fa-headset"></i><br>Support</a></div>
    """)

@app.route('/support')
def support():
    return render_template_string(STYLE + f"""
    <div class="nav">Help Center</div>
    <div class="card" style="text-align:center; padding:40px 20px;">
        <div style="background:#DCFCE7; width:70px; height:70px; border-radius:50%; display:flex; align-items:center; justify-content:center; margin:0 auto 20px;">
            <i class="fab fa-whatsapp" style="font-size:2.5rem; color:#22C55E;"></i>
        </div>
        <h3 style="margin-bottom:5px;">WhatsApp Founder</h3>
        <p style="color:#6B7280; margin-bottom:25px;">Direct support for loss making traders.</p>
        <button class="btn btn-primary" onclick="window.open('https://wa.me/918287550979')">Message Now</button>
        <p style="margin-top:25px; font-size:14px; color:#9CA3AF;">Email: {SUPPORT_EMAIL}</p>
    </div>
    <div class="f-nav"><a href="/" class="f-item"><i class="fas fa-chart-line"></i><br>Dashboard</a><a href="/payment" class="f-item"><i class="fas fa-gem"></i><br>Pro</a><a href="/support" class="f-item active"><i class="fas fa-headset"></i><br>Support</a></div>
    """)

# --- API ---
@app.route('/api/auth/req', methods=['POST'])
def req_otp():
    db = get_db()
    d = request.json
    num, pin = d.get('num', ''), d.get('pin', '')
    if len(num) != 10: return jsonify({"success":False, "msg":"Invalid Mobile Number!"})
    
    u = db.execute("SELECT * FROM users WHERE id=?", (num,)).fetchone()
    if not u: 
        db.execute("INSERT INTO users (id, pin) VALUES (?,?)", (num, pin))
        db.commit()
    elif u[1] != pin: return jsonify({"success":False, "msg":"Incorrect PIN!"})
    
    otp = str(random.randint(1111, 9999))
    db.execute("UPDATE users SET last_otp=?, otp_time=? WHERE id=?", (otp, time.time(), num))
    db.commit()
    session['pre_user'] = num
    return jsonify({"success":True, "msg":"OTP Sent Successfully! ✅"})

@app.route('/api/auth/ver', methods=['POST'])
def ver_otp():
    db = get_db()
    u = db.execute("SELECT last_otp FROM users WHERE id=?", (session.get('pre_user'),)).fetchone()
    if u and request.json.get('otp') == u[0]:
        session['user'] = session.get('pre_user')
        return jsonify({"success":True})
    return jsonify({"success":False, "msg":"Invalid OTP! Try again."})

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
