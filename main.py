import os, sqlite3, random
from flask import Flask, request, jsonify, session, render_template_string, redirect

app = Flask(__name__)
app.secret_key = "CSC_PHASE2"

# --- DATABASE ---
def init_db():
    conn = sqlite3.connect('db.db', check_same_thread=False)
    conn.execute("""
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
    """)
    conn.commit()
    return conn

db = init_db()

# --- UI ---
HTML = """
<h2>🛡️ Capital Suraksha Club</h2>

{% if not logged_in %}

<input id="num" placeholder="Enter Mobile"><br><br>
<input id="pin" placeholder="PIN"><br><br>

<button onclick="login()">Login</button>

{% else %}

<h3>Welcome {{uid}}</h3>

<p>Daily Loss: ₹{{loss}}</p>
<p>Trades Today: {{trades}} / 2</p>
<p>Max Loss Limit: ₹{{max_loss}}</p>
<p>Discipline Score: {{score}}</p>

<button onclick="addTrade('win')">Add WIN</button>
<button onclick="addTrade('loss')">Add LOSS</button>

<br><br>

<button onclick="kill()">🔴 STOP TRADING</button>
<button onclick="resetDay()">Reset Day</button>

<br><br>

<a href="/logout">Logout</a>

{% endif %}

<script>
function login(){
    let num = document.getElementById("num").value;
    let pin = document.getElementById("pin").value;

    fetch('/login',{
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({num:num,pin:pin})
    })
    .then(r=>r.json())
    .then(d=>{
        alert(d.msg);
        if(d.success) location.reload();
    });
}

function addTrade(type){
    fetch('/trade',{
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({type:type})
    })
    .then(r=>r.json())
    .then(d=>{
        alert(d.msg);
        location.reload();
    });
}

function kill(){
    fetch('/kill').then(()=>location.reload());
}

function resetDay(){
    fetch('/reset').then(()=>location.reload());
}
</script>
"""

# --- ROUTES ---
@app.route('/')
def home():
    if 'user' not in session:
        return render_template_string(HTML, logged_in=False)

    user = db.execute("SELECT * FROM users WHERE id=?", (session['user'],)).fetchone()

    return render_template_string(
        HTML,
        logged_in=True,
        uid=session['user'],
        loss=user[3],
        trades=user[4],
        max_loss=user[5],
        score=user[8]
    )

# --- LOGIN ---
@app.route('/login', methods=['POST'])
def login():
    data = request.json

    user = db.execute("SELECT * FROM users WHERE id=?", (data['num'],)).fetchone()

    if not user:
        db.execute("INSERT INTO users (id, pin) VALUES (?,?)", (data['num'], data['pin']))
        db.commit()
        session['user'] = data['num']
        return jsonify({"success":True,"msg":"Account Created ✅"})

    if user[1] != data['pin']:
        return jsonify({"success":False,"msg":"Wrong PIN ❌"})

    session['user'] = data['num']
    return jsonify({"success":True,"msg":"Login Success ✅"})

# --- TRADE LOGIC ---
@app.route('/trade', methods=['POST'])
def trade():
    user_id = session['user']
    data = request.json

    user = db.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()

    daily_loss = user[3]
    trades = user[4]
    max_loss = user[5]
    kill = user[6]
    last = user[7]
    score = user[8]

    # ❌ Kill switch check
    if kill == 1:
        return jsonify({"msg":"Trading stopped by Kill Switch ❌"})

    # ❌ Max trade limit
    if trades >= 2:
        return jsonify({"msg":"Max 2 trades reached 🔒"})

    # ❌ Loss limit hit
    if daily_loss >= max_loss:
        return jsonify({"msg":"Loss limit hit 🚫"})

    # ❌ Overtrading logic (2 consecutive loss)
    if last == "loss" and data['type'] == "loss":
        score -= 10
        return jsonify({"msg":"Cooldown: consecutive losses 🚫"})

    # ✅ Process trade
    trades += 1

    if data['type'] == "loss":
        daily_loss += 250  # fixed loss per trade (edit later)
        score -= 5
        msg = "Loss recorded ❌"
    else:
        score += 2
        msg = "Win recorded ✅"

    db.execute("""
    UPDATE users SET daily_loss=?, trade_count=?, last_result=?, discipline_score=?
    WHERE id=?
    """, (daily_loss, trades, data['type'], score, user_id))

    db.commit()

    # Psychology alert
    if daily_loss >= max_loss:
        msg += " | ALERT: Stop trading now!"

    return jsonify({"msg":msg})

# --- KILL SWITCH ---
@app.route('/kill')
def kill():
    db.execute("UPDATE users SET kill_switch=1 WHERE id=?", (session['user'],))
    db.commit()
    return "Stopped"

# --- RESET DAY ---
@app.route('/reset')
def reset():
    db.execute("""
    UPDATE users 
    SET daily_loss=0, trade_count=0, kill_switch=0, last_result=''
    WHERE id=?
    """, (session['user'],))
    db.commit()
    return "Reset"

# --- LOGOUT ---
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

app.run()
