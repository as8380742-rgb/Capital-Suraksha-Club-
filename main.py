import os, sqlite3, random, requests, time
from flask import Flask, request, jsonify, session, render_template_string, redirect

app = Flask(__name__)
app.secret_key = "CSC_STABLE_V10_2026"

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

# --- CSS (Minimal & High Performance) ---
STYLE = """
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<style>
    body { font-family: 'Inter', sans-serif; background: #F8FAFC; margin: 0; padding-bottom: 80px; }
    .nav { background: #0F172A; color: white; padding: 18px; font-weight: bold; display: flex; justify-content: space-between; }
    .card { background: white; border-radius: 14px; padding: 20px; margin: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .mission { background: #E0E7FF; color: #4338CA; padding: 12px; border-radius: 10px; font-size: 13px; font-weight: 600; text-align: center; margin-bottom: 15px; }
    .btn { width: 100%; padding: 14px; border-radius: 10px; border: none; font-weight: bold; cursor: pointer; font-size: 15px; }
    .btn-blue { background: #2563EB; color: white; }
    .btn-broker { background: white; border: 1px solid #E2E8F0; color: #1E293B; margin-top: 10px; display: flex; align-items: center; justify-content: center; gap: 8px; text-decoration: none; }
    .f-nav { position: fixed; bottom: 0; width: 100%; background: white; display: flex; justify-content: space-around; padding: 15px 0; border-top: 1px solid #E2E8F0; }
    .f-item { text-decoration: none; color: #64748B; font-size: 12px; text-align: center; font-weight: 600; }
    .f-item.active { color: #2563EB; }
    input { width: 100%; padding: 12px; border: 1px solid #CBD5E1; border-radius: 8px; margin: 8px 0; box-sizing: border-box; }
</style>
"""

@app.route('/')
def home():
    db = get_db()
    if 'user' not in session:
        return render_template_string(STYLE + """
        <div style="max-width:400px; margin: 60px auto; padding: 20px; text-align:center;">
            <h2>Capital Suraksha</h2>
            <div class="card">
                <input id="n" type="tel" placeholder="Mobile Number">
                <input id="p" type="password" placeholder="4-Digit PIN">
                <button class="btn btn-blue" onclick="auth('req')">Login</button>
                <div id="o_sec" style="display:none; margin-top:15px;">
                    <input id="o_val" type="text" placeholder="Enter OTP">
                    <button class="btn btn-blue" onclick="auth('ver')">Verify</button>
                </div>
            </div>
        </div>
        <script>
        function auth(t){
            let b = t=='req' ? {num:document.getElementById('n').value, pin:document.getElementById('p').value} : {otp:document.getElementById('o_val').value};
            fetch('/api/auth/'+t, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(b)})
            .then(r=>r.json()).then(d=>{
                alert(d.msg);
                if(d.success && t=='req') document.getElementById('o_sec').style.display='block';
                else if(d.success && t=='ver') location.reload();
            });
        }
        </script>""")
    
    u = db.execute("SELECT * FROM users WHERE id=?", (session['user'],)).fetchone()
    # PRE-CALCULATE TO AVOID JINJA CRASH
    count = u[4]
    lock_ui = '<div style="background:#FEE2E2; color:#B91C1C; padding:12px; border-radius:8px; text-align:center; font-weight:bold; margin-top:10px;">⚠️ 2 TRADE LIMIT REACHED</div>' if count >= 2 else ''
    
    return render_template_string(STYLE + """
    <div class="nav">CSC Dashboard <a href="/logout" style="color:white"><i class="fas fa-power-off"></i></a></div>
    
    <div class="card">
        <div class="mission"><i class="fas fa-shield-alt"></i> Mission: Discipline & Capital Protection</div>
        <div style="background:#1E293B; color:#10B981; padding:20px; border-radius:12px; text-align:center;">
            <small style="color:white; opacity:0.7;">Live PnL Status</small><br>
            <b style="font-size:1.6rem;">+₹1,240.00</b>
        </div>
        <div style="display:flex; justify-content:space-between; margin-top:15px; font-weight:bold;">
            <span>Trades: {{ count }}/2</span>
            <span style="color:blue;">Handholding Active</span>
        </div>
        {{ lock_status | safe }}
    </div>

    <div class="card">
        <h4 style="margin:0;">Broker Sync</h4>
        <a href="https://dhan.co/api-login" target="_blank" class="btn btn-broker"><img src="https://dhan.co/wp-content/uploads/2021/09/dhan-logo.png" width="18"> Dhan Login</a>
        <a href="https://kite.zerodha.com/connect/login?api_key=YOUR_KEY" target="_blank" class="btn btn-broker"><i class="fas fa-leaf" style="color:#E64A19"></i> Zerodha Kite</a>
    </div>

    <div class="f-nav">
        <a href="/" class="f-item active"><i class="fas fa-home fa-lg"></i><br>Home</a>
        <a href="/payment" class="f-item"><i class="fas fa-crown fa-lg"></i><br>Pro</a>
        <a href="/support" class="f-item"><i class="fas fa-headset fa-lg"></i><br>Support</a>
    </div>
    """, count=count, lock_status=lock_ui)

@app.route('/payment')
def payment():
    return render_template_string(STYLE + f"""
    <div class="nav">Upgrade to Pro</div>
    <div class="card" style="background:#0F172A; color:white; text-align:center;">
        <h3 style="color:#2563EB;">Pro Handholding</h3>
        <p>E-Book + Strategy Support</p>
        <div style="background:rgba(255,255,255,0.1); padding:15px; border-radius:10px; margin:20px 0;">
            UPI: <b id="u_id">{UPI_ID}</b> 
            <i class="fas fa-copy" style="cursor:pointer; margin-left:10px; color:#2563EB;" onclick="copy()"></i>
        </div>
    </div>
    <script>
    function copy(){
        navigator.clipboard.writeText(document.getElementById('u_id').innerText);
        alert("Copied!");
    }
    </script>
    <div class="f-nav"><a href="/" class="f-item"><i class="fas fa-home"></i><br>Home</a><a href="/payment" class="f-item active"><i class="fas fa-crown"></i><br>Pro</a><a href="/support" class="f-item"><i class="fas fa-headset"></i><br>Support</a></div>
    """)

@app.route('/support')
def support():
    return render_template_string(STYLE + f"""
    <div class="nav">Support</div>
    <div class="card" style="text-align:center; padding:40px 10px;">
        <i class="fab fa-whatsapp" style="font-size:3rem; color:#22C55E;"></i>
        <h3>WhatsApp Help</h3>
        <p>+91 8287550979</p>
        <button class="btn btn-blue" onclick="window.open('https://wa.me/918287550979')">Chat Now</button>
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
    return jsonify({"success":True, "msg":"OTP Sent!"})

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
