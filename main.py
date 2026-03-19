import os, sqlite3, random, requests
from flask import Flask, render_template_string, request, jsonify, session, redirect

app = Flask(__name__)
app.secret_key = "CSC_ULTRA_FIXED_V3"

# --- CONFIG ---
FAST2SMS_KEY = "YOUR_API_KEY_HERE"
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

# --- SEND OTP ---
def send_otp_sms(number, otp):
    url = "https://www.fast2sms.com/dev/bulkV2"
    headers = {"authorization": FAST2SMS_KEY}

    payload = {
        "route": "v3",
        "sender_id": "TXTIND",
        "message": f"Your CSC OTP is {otp}",
        "language": "english",
        "numbers": number
    }

    try:
        response = requests.post(url, data=payload, headers=headers)
        data = response.json()
        print("SMS RESPONSE:", data)

        return data.get("status") == "success"
    except Exception as e:
        print("ERROR:", e)
        return False

# --- UI ---
HTML = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CSC</title>
<style>
body{background:#0b0f19;color:white;text-align:center;font-family:sans-serif;}
.card{background:#161b22;padding:20px;border-radius:10px;margin:20px;}
input{width:100%;padding:10px;margin:10px 0;background:#0d1117;border:1px solid #333;color:white;}
.btn{width:100%;padding:12px;background:#238636;color:white;border:none;border-radius:5px;}
</style>
</head>
<body>

<h2>🛡️ Capital Suraksha Club</h2>

{% if not logged_in %}
<div class="card">
    <input id="u" type="number" placeholder="Enter Mobile Number">
    <div id="otpBox" style="display:none;">
        <input id="o" type="number" placeholder="Enter OTP">
        <input id="p" type="password" placeholder="Set PIN">
    </div>
    <button id="btn" class="btn" onclick="go()">Get OTP</button>
</div>
{% else %}
<div class="card">
    <p>Welcome: {{uid}}</p>
    <p>UPI: {{upi}}</p>
</div>
<a href="/logout">Logout</a>
{% endif %}

<script>
let step = 1;

function go(){
    let num = document.getElementById('u').value;

    if(num.length != 10){
        alert("Enter valid 10 digit number");
        return;
    }

    if(step === 1){
        fetch('/api/send_otp',{
            method:'POST',
            headers:{'Content-Type':'application/json'},
            body:JSON.stringify({id:num})
        })
        .then(r=>r.json())
        .then(d=>{
            alert(d.msg);
            if(d.success){
                document.getElementById('otpBox').style.display='block';
                document.getElementById('btn').innerText='Verify OTP';
                step = 2;
            }
        });
    }
    else{
        let otp = document.getElementById('o').value;
        let pin = document.getElementById('p').value;

        fetch('/api/auth',{
            method:'POST',
            headers:{'Content-Type':'application/json'},
            body:JSON.stringify({id:num,otp:otp,pin:pin})
        })
        .then(r=>r.json())
        .then(d=>{
            alert(d.msg);
            if(d.success) location.reload();
        });
    }
}
</script>

</body>
</html>
"""

# --- ROUTES ---
@app.route('/')
def home():
    if 'user' not in session:
        return render_template_string(HTML, logged_in=False)
    return render_template_string(HTML, logged_in=True, uid=session['user'], upi=YOUR_UPI)

@app.route('/api/send_otp', methods=['POST'])
def send_otp():
    number = request.json['id']

    otp = str(random.randint(1000,9999))
    session['otp'] = otp

    if send_otp_sms(number, otp):
        return jsonify({"success":True,"msg":"OTP Sent Successfully ✅"})
    else:
        return jsonify({"success":False,"msg":"SMS Failed ❌ (Check API / Wallet)"})

@app.route('/api/auth', methods=['POST'])
def auth():
    data = request.json

    if data['otp'] != session.get('otp'):
        return jsonify({"success":False,"msg":"Wrong OTP ❌"})

    if not db.execute("SELECT * FROM users WHERE id=?", (data['id'],)).fetchone():
        db.execute("INSERT INTO users (id, pin) VALUES (?,?)", (data['id'], data['pin']))
        db.commit()

    session['user'] = data['id']
    return jsonify({"success":True,"msg":"Login Success ✅"})

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# --- RUN ---
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
