import os, sqlite3, random, requests
from flask import Flask, render_template_string, request, jsonify, session, redirect

app = Flask(__name__)
app.secret_key = "CSC_ULTRA_FIXED_V2"

# --- CONFIGURATION ---
# Bhai, yahan apni REAL API KEY dalo bina * ke
FAST2SMS_KEY = 'plwdy58v3eLJWFKNcS0mksbBMHuxRhDIAPqaQfUY16TECig7oZ8FPoGwcg15XuAWZmfUhKOq3dijsM7x' 
YOUR_WHATSAPP = "918287550979"
YOUR_UPI = "8587965337-1@nyes"

# --- DATABASE ---
def init_db():
    conn = sqlite3.connect('database.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY, pin TEXT, plan TEXT DEFAULT 'Free')''')
    conn.commit()
    return conn
db = init_db()

# --- QUICK SMS LOGIC ---
def send_otp_sms(to_number, otp):
    url = "https://www.fast2sms.com/dev/bulkV2"
    headers = {"authorization": FAST2SMS_KEY}
    # Direct Quick SMS Route (₹5.00 cost)
    payload = {
        "route": "q",
        "message": f"CSC OTP: {otp}",
        "language": "english",
        "numbers": str(to_number),
    }
    try:
        r = requests.post(url, data=payload, headers=headers).json()
        return r.get("return")
    except:
        return False

# --- UI ---
HTML = """
<!DOCTYPE html>
<html>
<head><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>CSC</title>
<style>body{background:#0b0f19;color:white;text-align:center;font-family:sans-serif;} .card{background:#161b22;padding:20px;border-radius:10px;margin:20px;text-align:left;} input{width:100%;padding:10px;margin:10px 0;background:#0d1117;border:1px solid #333;color:white;box-sizing:border-box;} .btn{width:100%;padding:12px;background:#238636;color:white;border:none;border-radius:5px;cursor:pointer;}</style></head>
<body>
<h2>🛡️ Capital Suraksha Club</h2>
{% if not logged_in %}
<div class="card">
    <input id="u" type="number" placeholder="Mobile Number">
    <div id="o_box" style="display:none;"><input id="o" type="number" placeholder="Enter OTP"><input id="p" type="password" placeholder="Set PIN"></div>
    <button id="b" class="btn" onclick="go()">Get OTP</button>
</div>
{% else %}
<div class="card"><p>Welcome: {{uid}}</p><p>UPI: {{upi}}</p></div>
<a href="/logout" style="color:grey;">Logout</a>
{% endif %}
<script>let s=1;function go(){const i=document.getElementById('u').value;if(s===1){fetch('/api/send_otp',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:i})}).then(r=>r.json()).then(d=>{alert(d.msg);if(d.success){document.getElementById('o_box').style.display='block';s=2;document.getElementById('b').innerText='Verify';}});}else{const o=document.getElementById('o').value;const p=document.getElementById('p').value;fetch('/api/auth',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:i,otp:o,pin:p})}).then(r=>r.json()).then(d=>{alert(d.msg);if(d.success)location.reload();});}}</script>
</body></html>"""

@app.route('/')
def home():
    if 'user' not in session: return render_template_string(HTML, logged_in=False)
    return render_template_string(HTML, logged_in=True, uid=session['user'], upi=YOUR_UPI)

@app.route('/api/send_otp', methods=['POST'])
def api_send_otp():
    otp = str(random.randint(1000, 9999))
    session['otp'] = otp
    if send_otp_sms(request.json['id'], otp): return jsonify({"success":True,"msg":"OTP Sent! ✅"})
    return jsonify({"success":False,"msg":"SMS Failed! Key ya Wallet check karein."})

@app.route('/api/auth', methods=['POST'])
def api_auth():
    d = request.json
    if d['otp'] != session.get('otp'): return jsonify({"success":False,"msg":"Wrong OTP!"})
    if not db.execute("SELECT * FROM users WHERE id=?", (d['id'],)).fetchone():
        db.execute("INSERT INTO users (id, pin) VALUES (?,?)", (d['id'], d['pin']))
        db.commit()
    session['user'] = d['id']
    return jsonify({"success":True,"msg":"Success!"})

@app.route('/logout')
def logout(): session.clear(); return redirect('/')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
