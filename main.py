import os, sqlite3, random, requests, time
from flask import Flask, request, jsonify, session, render_template_string, redirect

app = Flask(__name__)
app.secret_key = "CSC_STABLE_PRO_2026"

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

# --- CSS (Updated for Clean Fonts & Fixed UI) ---
STYLE = """
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<style>
    body { font-family: 'Segoe UI', Roboto, sans-serif; background: #F4F7FA; margin: 0; padding-bottom: 75px; }
    .nav { background: #0F172A; color: white; padding: 20px; font-weight: bold; display: flex; justify-content: space-between; }
    .card { background: white; border-radius: 16px; padding: 20px; margin: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .mission { background: #E0E7FF; color: #4338CA; padding: 12px; border-radius: 10px; font-size: 13px; font-weight: 600; text-align: center; margin-bottom: 15px; }
    .btn { width: 100%; padding: 14px; border-radius: 10px; border: none; font-weight: bold; cursor: pointer; margin-top: 10px; font-size: 15px; }
    .btn-main { background: #2563EB; color: white; }
    .f-nav { position: fixed; bottom: 0; width: 100%; background: white; display: flex; justify-content: space-around; padding: 12px 0; border-top: 1px solid #eee; }
    .f-item { text-decoration: none; color: #64748B; font-size: 12px; text-align: center; font-weight: 600; }
    .f-item.active { color: #2563EB; }
    .copy-btn { color: #2563EB; cursor: pointer; margin-left: 10px; }
    .pnl-live { background: #1E293B; color: #10B981; padding: 15px; border-radius: 12px; margin-top: 10px; }
</style>
"""

@app.route('/')
def home():
    if 'user' not in session:
        return render_template_string(STYLE + """
        <div style="max-width:400px; margin: 60px auto; padding: 20px; text-align:center;">
            <h2>Capital Suraksha Club</h2>
            <div class="card">
                <input id="num" style="width:100%; padding:12px; margin:8px 0;" type="tel" placeholder="Mobile Number">
                <input id="pin" style="width:100%; padding:12px; margin:8px 0;" type="password" placeholder="4-Digit PIN">
                <button class="btn btn-main" onclick="otp('req')">Get OTP</button>
                <div id="otp_sec" style="display:none; margin-top:15px;">
                    <input id="otp_val" style="width:100%; padding:12px; margin:8px 0;" type="text" placeholder="Enter OTP">
                    <button class="btn btn-main" onclick="otp('ver')">Verify & Login</button>
                    <button id="res" style="background:none; border:none; color:blue; margin-top:10px;" disabled onclick="otp('req')">Resend in <span id="s">30</span>s</button>
                </div>
            </div>
        </div>
        <script>
        function otp(t){
            let b = t=='req' ? {num:document.getElementById('num').value, pin:document.getElementById('pin').value} : {otp:document.getElementById('otp_val').value};
            fetch('/api/otp/'+t, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(b)})
            .then(r=>r.json()).then(d=>{
                alert(d.msg);
                if(d.success && t=='req'){ document.getElementById('otp_sec').style.display='block'; startT(); }
                else if(d.success && t=='ver') location.reload();
            });
        }
        function startT(){
            let s=30; let b=document.getElementById('res'); b.disabled=true;
            let i=setInterval(()=>{
                s--; document.getElementById('s').innerText=s;
                if(s<=0){ clearInterval(i); b.disabled=false; b.innerText="Resend Now"; }
            },1000);
        }
        </script>""")
    
    u = db.execute("SELECT * FROM users WHERE id=?", (session['user'],)).fetchone()
    limit = u[4] >= 2 # 2 Trade Limit
    
    return render_template_string(STYLE + """
    <div class="nav"><span>Capital Suraksha Club</span> <a href="/logout" style="color:white"><i class="fas fa-power-off"></i></a></div>
    
    <div class="card">
        <div class="mission"><i class="fas fa-shield-alt"></i> Mission: Stop Over-Trading & Protect Capital</div>
        <div class="pnl-live">
            <small style="color:white; opacity:0.8;">Live PnL (Zerodha/Dhan Sync)</small><br>
            <b style="font-size:1.5rem;">+₹1,240.00</b>
        </div>
        <p style="text-align:center; font-weight:bold;">Trades: {{u[4]}} / 2</p>
        {% if limit %}
        <div style="background:#fee2e2; color:#b91c1c; padding:10px; border-radius:8px; text-align:center; font-weight:bold;">2 TRADE LIMIT REACHED - LOCK ACTIVE</div>
        {% endif %}
    </div>

    <div class="card">
        <h4>Broker Connect</h4>
        <button class="btn" style="background:#f8fafc; border:1px solid #ddd;" onclick="window.open('https://dhan.co/api-login')">Connect Dhan</button>
        <button class="btn" style="background:#f8fafc; border:1px solid #ddd; margin-top:10px;" onclick="window.open('https://kite.zerodha.com/connect/login?api_key=YOUR_API_KEY')">Connect Zerodha Kite</button>
    </div>

    <div class="f-nav">
        <a href="/" class="f-item active"><i class="fas fa-home fa-lg"></i><br>Home</a>
        <a href="/payment" class="f-item"><i class="fas fa-crown fa-lg"></i><br>Pro</a>
        <a href="/support" class="f-item"><i class="fas fa-headset fa-lg"></i><br>Support</a>
    </div>
    """, u=u, limit=limit)

@app.route('/payment')
def payment():
    return render_template_string(STYLE + f"""
    <div class="nav">Pro Membership</div>
    <div class="card" style="background:#0F172A; color:white;">
        <h3>Handholding Support</h3>
        <p><i class="fas fa-check"></i> Risk Management E-Book</p>
        <p><i class="fas fa-check"></i> 24/7 Capital Protection</p>
        <div style="background:rgba(255,255,255,0.1); padding:15px; border-radius:10px; margin:15px 0; text-align:center;">
            UPI: <b id="upi">{UPI_ID}</b> <i class="fas fa-copy copy-btn" onclick="copyUPI()"></i>
        </div>
    </div>
    <script>
    function copyUPI(){
        navigator.clipboard.writeText(document.getElementById('upi').innerText);
        alert("UPI Copied!");
    }
    </script>
    <div class="f-nav"><a href="/" class="f-item"><i class="fas fa-home"></i><br>Home</a><a href="/payment" class="f-item active"><i class="fas fa-crown"></i><br>Pro</a><a href="/support" class="f-item"><i class="fas fa-headset"></i><br>Support</a></div>
    """)

@app.route('/support')
def support():
    return render_template_string(STYLE + f"""
    <div class="nav">Help Center</div>
    <div class="card" style="text-align:center;">
        <i class="fab fa-whatsapp" style="font-size:3rem; color:green;"></i>
        <h3>WhatsApp Support</h3>
        <p>+91 8287550979</p>
        <p>{SUPPORT_EMAIL}</p>
    </div>
    <div class="f-nav"><a href="/" class="f-item"><i class="fas fa-home"></i><br>Home</a><a href="/payment" class="f-item"><i class="fas fa-crown"></i><br>Pro</a><a href="/support" class="f-item active"><i class="fas fa-headset"></i><br>Support</a></div>
    """)

# --- API ---
@app.route('/api/otp/req', methods=['POST'])
def req_otp():
    d = request.json
    num, pin = d.get('num'), d.get('pin')
    u = db.execute("SELECT * FROM users WHERE id=?", (num,)).fetchone()
    if not u: db.execute("INSERT INTO users (id, pin) VALUES (?,?)", (num, pin)); db.commit()
    elif u[1] != pin: return jsonify({"success":False, "msg":"Wrong PIN"})
    otp = str(random.randint(1111, 9999))
    db.execute("UPDATE users SET last_otp=?, otp_time=? WHERE id=?", (otp, time.time(), num))
    db.commit()
    session['pre_user'] = num
    return jsonify({"success":True, "msg":"OTP Sent!"})

@app.route('/api/otp/ver', methods=['POST'])
def ver_otp():
    u = db.execute("SELECT last_otp FROM users WHERE id=?", (session.get('pre_user'),)).fetchone()
    if u and request.json.get('otp') == u[0]: session['user'] = session.get('pre_user'); return jsonify({"success":True})
    return jsonify({"success":False, "msg":"Invalid OTP"})

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
