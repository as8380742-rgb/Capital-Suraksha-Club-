from flask import Flask, render_template_string, request, redirect, url_for

app = Flask(__name__)

# Dashboard ka HTML aur CSS (Login, API aur Risk Rules ke liye)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Capital Suraksha Club - Dashboard</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f0f2f5; margin: 0; padding: 20px; text-align: center; }
        .container { max-width: 500px; margin: auto; background: white; padding: 30px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
        h1 { color: #1a73e8; margin-bottom: 10px; }
        p { color: #5f6368; }
        .card { background: #e8f0fe; padding: 15px; border-radius: 10px; margin: 20px 0; border-left: 5px solid #1a73e8; text-align: left; }
        input[type="text"], input[type="number"] { width: 90%; padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 5px; }
        button { background-color: #1a73e8; color: white; border: none; padding: 12px 25px; border-radius: 5px; cursor: pointer; font-size: 16px; width: 100%; }
        button:hover { background-color: #1557b0; }
        .status { font-weight: bold; color: green; margin-top: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🛡️ Capital Suraksha Club</h1>
        <p>Loss se bachao, Capital bachao!</p>
        
        <hr>

        <div class="card">
            <h3>👤 Step 1: Login</h3>
            <input type="text" placeholder="Enter Username/Mobile" id="user">
            <button onclick="alert('Logged in Successfully!')">Login Now</button>
        </div>

        <div class="card">
            <h3>🔌 Step 2: Connect Broker API</h3>
            <select id="broker" style="width: 100%; padding: 10px; margin-bottom: 10px;">
                <option>Select Broker</option>
                <option>Angel One</option>
                <option>Dhan</option>
                <option>Fyers</option>
            </select>
            <input type="text" placeholder="Enter API Key">
            <button onclick="alert('API Connection Initialized...')">Connect Broker</button>
        </div>

        <div class="card" style="border-left-color: #d93025; background: #fce8e6;">
            <h3>⚠️ Step 3: Set Risk Rules</h3>
            <label>Daily Max Loss (M2M):</label>
            <input type="number" placeholder="Example: 2000" id="loss">
            <label>Max Trades Per Day:</label>
            <input type="number" placeholder="Example: 5" id="trades">
            <button style="background-color: #d93025;" onclick="alert('Risk Rules Saved! Kill Switch Active.')">Activate Protection</button>
        </div>

        <p class="status">System Status: Online & Protecting ✅</p>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

if __name__ == "__main__":
    # Railway/Replit ke liye port 8080 zaroori hai
    app.run(host='0.0.0.0', port=8080)
