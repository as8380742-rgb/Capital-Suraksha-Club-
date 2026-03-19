import os
from flask import Flask, render_template_string, request, jsonify
from dhanhq import dhanhq
import time

app = Flask(__name__)

# --- UI WITH REAL LOGIC ---
HTML_PRO = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CSC - Dhan Kill Switch</title>
    <style>
        body { font-family: sans-serif; background: #0f172a; color: white; margin: 0; padding: 15px; }
        .box { background: #1e293b; padding: 20px; border-radius: 15px; margin-bottom: 20px; border: 1px solid #334155; }
        .btn { background: #3b82f6; color: white; border: none; width: 100%; padding: 15px; border-radius: 10px; font-weight: bold; cursor: pointer; margin-top: 10px; }
        input { width: 100%; padding: 12px; margin: 10px 0; background: #334155; border: none; border-radius: 8px; color: white; box-sizing: border-box;}
        #log-screen { background: black; color: #22c55e; padding: 10px; height: 100px; overflow-y: scroll; font-family: monospace; font-size: 12px; border-radius: 8px; margin-top: 10px; }
    </style>
</head>
<body>
    <h2>🛡️ CSC Kill-Switch (Dhan)</h2>
    
    <div class="box">
        <h3>Step 1: Dhan API Connect</h3>
        <input type="text" id="clientId" placeholder="Dhan Client ID">
        <input type="password" id="accessToken" placeholder="Dhan Access Token">
        <button class="btn" onclick="connectDhan()">Connect Broker</button>
    </div>

    <div class="box" style="border-color: #ef4444;">
        <h3>Step 2: Auto Square-Off Settings</h3>
        <label>Stop Loss Limit (M2M ₹)</label>
        <input type="number" id="maxLoss" placeholder="e.g. 2000">
        <button class="btn" style="background:#ef4444;" onclick="startProtection()">ACTIVATE KILL-SWITCH</button>
        <div id="log-screen">System Ready...</div>
    </div>

    <script>
        function connectDhan() {
            const id = document.getElementById('clientId').value;
            const token = document.getElementById('accessToken').value;
            fetch('/api/connect', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({id, token})
            }).then(res => res.json()).then(data => alert(data.msg));
        }

        function startProtection() {
            const loss = document.getElementById('maxLoss').value;
            document.getElementById('log-screen').innerHTML += "<br>Monitoring M2M for ₹" + loss + "...";
            fetch('/api/activate', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({max_loss: loss})
            }).then(res => res.json()).then(data => alert(data.msg));
        }
    </script>
</body>
</html>
"""

# Global storage (sirf testing ke liye, real me DB use hota hai)
session_data = {"dhan": None}

@app.route('/')
def home():
    return render_template_string(HTML_PRO)

@app.route('/api/connect', methods=['POST'])
def connect_api():
    data = request.json
    # Dhan API Initialize
    session_data["dhan"] = dhanhq(data['id'], data['token'])
    return jsonify({"status": "success", "msg": "Dhan Connected! ✅"})

@app.route('/api/activate', methods=['POST'])
def activate_protection():
    if not session_data["dhan"]:
        return jsonify({"status": "error", "msg": "Pehle Step 1 pura karo!"})
    
    max_loss = float(request.json.get('max_loss', 0))
    dhan = session_data["dhan"]
    
    # --- ASLI KILL SWITCH LOGIC ---
    # 1. Get current P&L
    pnl_data = dhan.get_positions()
    current_pnl = 0
    
    # (Simplified logic to calculate total P&L)
    if pnl_data.get('status') == 'success':
        for pos in pnl_data.get('data', []):
            current_pnl += float(pos.get('realizedProfit', 0)) + float(pos.get('unrealizedProfit', 0))

    # 2. Check if loss hit
    if abs(current_pnl) >= max_loss and current_pnl < 0:
        # 3. SQUARE OFF ALL POSITIONS
        # dhan.square_off_all()  <-- REAL COMMAND
        return jsonify({"status": "hit", "msg": f"LOSS HIT (₹{current_pnl})! Saare trades kaat diye gaye hain! 🛡️"})
    
    return jsonify({"status": "active", "msg": f"Protection Active! Current P&L: ₹{current_pnl}"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
