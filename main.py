import os
import sqlite3
import random
import requests
from flask import Flask, request, jsonify, session, render_template_string, redirect

app = Flask(__name__)
app.secret_key = "CSC_PHASE2"

# --- CONFIGURATION (Yahan apni API Key daalein) ---
FAST2SMS_API_KEY = "plwdy58v3eLJWFKNcS0mksbBMHuxRhDIAPqaQfUY16TECig7oZ8FPoGwcg15XuAWZmfUhKOq3dijsM7x"

def init_db():
    conn = sqlite3.connect('db.db', check_same_thread=False)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY, 
            pin TEXT,
            plan TEXT DEFAULT 'Free',
            daily_loss INTEGER DEFAULT 0,
            trade_count INTEGER DEFAULT 0,
            max_loss INTEGER DEFAULT 500,
            kill_switch INTEGER DEFAULT 0,
            last_result TEXT DEFAULT '',
            discipline_score INTEGER DEFAULT 100
        )
    ''')
    conn.commit()
    return conn

db = init_db()

# --- HELPER: SMS SENDER ---
def send_otp(mobile, otp):
    url = "https://www.fast2sms.com/dev/bulkV2"
    querystring = {
        "authorization": FAST2SMS_API_KEY,
        "route": "q",
        "message": f"Welcome to Capital Suraksha Club. Your Login OTP is {otp}",
        "numbers": str(mobile)
    }
    try:
        response = requests.get(url, params=querystring)
        return response.json()
    except:
        return None

# --- UI (HTML/JS) ---
HTML = """
<style>
    body { font-family: sans-serif; padding: 20px; background: #f4f4f4; }
    .card { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); margin-bottom: 20px; }
    button { padding: 10px; margin: 5px; cursor: pointer; border-radius: 5px; border: none; background: #007bff; color: white; }
    .support-link { color: #25d366; text-decoration: none; font-weight: bold; }
</style>

<div class="card">
    <h2>🛡️ Capital Suraksha Club</h2>
    
    {% if not logged_in %}
        <div id="login-box">
            <input id="num" placeholder="Mobile Number"><br><br>
            <input id="pin" type="password" placeholder="Set/Enter PIN"><br><br>
            <button onclick="requestOTP()">Get OTP & Login</button>
        </div>
        <div id="otp-box" style="display:none;">
            <input id="otp" placeholder="Enter 4-Digit OTP"><br><br>
            <button onclick="verifyAndLogin()">Verify OTP</button>
        </div>
    {% else %}
        <h3>Welcome, {{uid}}</h3>
        <p>📉 Daily Loss: <b>₹{{loss}}</b></p>
        <p>📊 Trades: <b>{{trades}} / 2</b></p>
        <p>⭐ Discipline Score: <b>{{score}}</b></p>
        
        <button onclick="addTrade('win')" style="background:green;">Add WIN</button>
        <button onclick="addTrade('loss')" style="background:orange;">Add LOSS</button><br>
        <button onclick="kill()" style="background:red;">🛑 KILL SWITCH (Stop Today)</button>
        <button onclick="resetDay()" style="background:gray;">Reset Day</button>
        <br><br>
        <a href="/logout">Logout</a>
    {% endif %}
</div>

<div class="card">
    <h3>💳 Payment & Subscription</h3>
    <p>Upgrade to Pro for handholding support:</p>
    <p><b>UPI ID:</b> 8587965337-1@nyes</p>
</div>

<div class="card">
    <h3>📞 Help & Support</h3>
    <p>WhatsApp: <a class="support-link" href="https://wa.me/918287550979">+91 8287550979</a></p>
    <p>Email: <a href="mailto:CapitalSurakshaClub@Gmail.com">CapitalSurakshaClub@Gmail.com</a></p>
</div>

<script>
function requestOTP(){
    let num = document.getElementById("num").value;
    let pin = document.getElementById("pin").value;
    if(!num || !pin) return alert("Please fill all details");
    
    fetch('/request_otp', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({num:num, pin:pin})
    })
    .then(r=>r.json()).then(d=>{
        alert(d.msg);
        if(d.success){
            document.getElementById('login-box').style.display = 'none';
            document.getElementById('otp-box').style.display = 'block';
        }
    });
}

function verifyAndLogin(){
    let otp = document.getElementById("otp").value;
    fetch('/verify_otp', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({otp:otp})
    })
    .then(r=>r.json()).then(d=>{
        alert(d.msg);
        if(d.success) location.reload();
    });
}

function addTrade(type){
    fetch('/trade', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({type:type})
    }).then(r=>r.json()).then(d=>{ alert(d.msg); location.reload(); });
}

function kill(){ if(confirm("Stop trading for today?")) fetch('/kill').then(()=>location.reload()); }
function resetDay(){ fetch('/reset').then(()=>location.reload()); }
</script>
"""

# --- ROUTES ---

@app.route('/')
def home():
    if 'user' not in session:
        return render_template_string(HTML, logged_in=False)
    
    user = db.execute("SELECT * FROM users WHERE id=?", (session['user'],)).fetchone()
    return render_template_string(HTML, logged_in=True, uid=user[0], loss=user[3], trades=user[4], score=user[8])

@app.route('/request_otp', methods=['POST'])
def req_otp():
    data = request.json
    num, pin = data.get('num'), data.get('pin')
    
    user = db.execute("SELECT * FROM users WHERE id=?", (num,)).fetchone()
    if not user:
        db.execute("INSERT INTO users (id, pin) VALUES (?,?)", (num, pin))
        db.commit()
    elif user[1] != pin:
        return jsonify({"success": False, "msg": "Wrong PIN! ❌"})

    otp = random.randint(1000, 9999)
    session['temp_otp'] = str(otp)
    session['temp_user'] = num
    
    res = send_otp(num, otp)
    if res and res.get("return"):
        return jsonify({"success": True, "msg": "OTP Sent! ✅"})
    else:
        return jsonify({"success": False, "msg": "SMS Failed. Check API Key/Balance."})

@app.route('/verify_otp', methods=['POST'])
def ver_otp():
    data = request.json
    if data.get('otp') == session.get('temp_otp'):
        session['user'] = session.get('temp_user')
        return jsonify({"success": True, "msg": "Welcome! 🚀"})
    return jsonify({"success": False, "msg": "Invalid OTP! ❌"})

@app.route('/trade', methods=['POST'])
def trade():
    user_id = session.get('user')
    if not user_id: return jsonify({"msg": "Login first"})
    
    data = request.json
    user = db.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    
    daily_loss, trades, max_loss, kill, last, score = user[3], user[4], user[5], user[6], user[7], user[8]

    if kill == 1: return jsonify({"msg": "Trading stopped by Kill Switch ❌"})
    if trades >= 2: return jsonify({"msg": "Max 2 trades reached for today 🔒"})
    if daily_loss >= max_loss: return jsonify({"msg": "Daily Loss limit hit 🚫"})

    trades += 1
    if data['type'] == "loss":
        daily_loss += 250
        score -= 5
        msg = "Loss recorded. Stay disciplined! ❌"
    else:
        score += 2
        msg = "Win recorded! Good job. ✅"

    db.execute("UPDATE users SET daily_loss=?, trade_count=?, last_result=?, discipline_score=? WHERE id=?", 
               (daily_loss, trades, data['type'], score, user_id))
    db.commit()
    return jsonify({"msg": msg})

@app.route('/kill')
def kill_switch():
    db.execute("UPDATE users SET kill_switch=1 WHERE id=?", (session['user'],))
    db.commit()
    return "Stopped"

@app.route('/reset')
def reset():
    db.execute("UPDATE users SET daily_loss=0, trade_count=0, kill_switch=0, last_result='' WHERE id=?", (session['user'],))
    db.commit()
    return "Reset"

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
