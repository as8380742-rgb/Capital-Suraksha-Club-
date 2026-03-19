import os, sqlite3, random, requests
from flask import Flask, render_template_string, request, jsonify, session, redirect

app = Flask(__name__)
app.secret_key = "CSC_FINAL_UPDATED_2026"

# --- CONFIGURATION ---
# Bhai, yahan apni Fast2SMS API Key dalo
FAST2SMS_KEY = 'Plwd********************' 
YOUR_WHATSAPP = "918287550979"
YOUR_UPI = "8587965337-1@nyes"

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('database.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY, pin TEXT, plan TEXT DEFAULT 'Free', 
        dhan_id TEXT, dhan_token TEXT, max_loss REAL, max_trades INTEGER)''')
    conn.commit()
    return conn
db = init_db()

# --- SMS LOGIC ---
def send_otp_sms(to_number, otp):
    url = "https://www.fast2sms.com/dev/bulkV2"
    headers = {"authorization": FAST2SMS_KEY}
    payload = {
        "route": "q",
        "message": f"Aapka Capital Suraksha Club OTP hai: {otp}",
        "language": "english",
        "numbers": str(to_number),
    }
    try:
        response = requests.post(url, data=payload, headers=headers)
        return response.json().get("return")
    except:
        return False

# --- UI DESIGN ---
HTML_MAIN = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Capital Suraksha Club</title>
    <style>
        body { font-family: sans-serif; background: #0b0f19; color: white; padding: 20px; text-align:center; }
        .card { background: #161b22; padding: 20px; border-radius: 12px; border: 1px solid #30363d; margin-bottom: 20px; text-align:left; }
        input { width: 100%; padding: 12px; margin: 10px 0; background: #0d1117; border: 1px solid #30363d; color: white; border-radius: 6px; box-sizing: border-box; }
        .btn { width: 100%; padding: 14px; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; background: #238636; color: white; }
    </style>
</head>
<body>
    <h2>🛡️ Capital Suraksha Club</h2>
    {% if not logged_in %}
    <div class="card">
        <h3>Login via SMS</h3>
        <input id="uid" type="number" placeholder="Mobile Number">
        <div id="otp_box" style="display:none;">
            <input id="uotp" type="number" placeholder="Enter OTP">
            <input id="upin" type="password" placeholder="Set 6-Digit PIN">
        </div>
        <button id="abtn" class="btn" onclick="handleAuth()">Get OTP</button>
    </div>
    {% else %}
    <div class="card">
        <p>Welcome: {{user_id}} | Plan: <b>{{plan}}</b></p>
        <button class="btn" style="background:#f0883e;" onclick="document.getElementById('qr').style.display='block'">Upgrade to Pro</button>
        <div id="qr" style="display:none; margin-top:10px; background:white; padding:10px; border-radius:8px;">
            <img src="https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=upi://pay?pa={{upi}}%26pn=CSC%26am=999">
            <p style="color:black; font-size:12px; margin-top:5px;">Pay ₹999 to {{upi}}</p>
        </div>
    </div>
    <div style="text-align:center;"><a href="/logout" style="color:grey;">Logout</a></div>
    {% endif %}
    <script>
        let step = 1;
        function handleAuth() {
            const id = document.getElementById('uid').value;
            if(step === 1) {
                fetch('/api/send_otp', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({id})})
                .then(r=>r.json()).then(d=>{ alert(d.msg); if(d.success){ document.getElementById('otp_box').style.display='block'; step=2; document.getElementById('abtn').innerText='Verify & Login'; }});
            } else {
                const otp = document.getElementById('uotp').value;
                const pin = document.getElementById('upin').value;
                fetch('/api/auth', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({id, otp, pin})})
                .then(r=>r.json()).then(d=>{ alert(d.msg); if(d.success) location.reload(); });
            }
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    if 'user' not in session: return render_template_string(HTML_MAIN, logged_in=False)
    u = db.execute("SELECT * FROM users WHERE id=?", (session['user'],)).fetchone()
    return render_template_string(HTML_MAIN, logged_in=True, user_id=u[0], plan=u[2], upi=YOUR_UPI)

@app.route('/api/send_otp', methods=['POST'])
def api_send_otp():
    otp = str(random.randint(1000, 9999))
    session['temp_otp'] = otp
    if send_otp_sms(request.json['id'], otp):
        return jsonify({"success": True, "msg": "OTP Bhej Diya Gaya Hai! ✅"})
    return jsonify({"success": False, "msg": "SMS Failed! Wallet ya API Key check karein."})

@app.route('/api/auth', methods=['POST'])
def api_auth():
    d = request.json
    if d['otp'] != session.get('temp_otp'): return jsonify({"success": False, "msg": "Incorrect OTP!"})
    if not db.execute("SELECT * FROM users WHERE id=?", (d['id'],)).fetchone():
        db.execute("INSERT INTO users (id, pin) VALUES (?,?)", (d['id'], d['pin']))
        db.commit()
    session['user'] = d['id']
    return jsonify({"success": True, "msg": "Login Ho Gaya!"})

@app.route('/logout')
def logout(): session.clear(); return redirect('/')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
