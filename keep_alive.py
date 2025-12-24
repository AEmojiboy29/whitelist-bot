from flask import Flask
from threading import Thread
import os
import logging

# Disable Flask logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask('')

@app.route('/')
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>🤖 Discord Bot Status</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                text-align: center;
                padding: 50px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
            .container {
                background: rgba(255, 255, 255, 0.1);
                padding: 30px;
                border-radius: 15px;
                backdrop-filter: blur(10px);
                max-width: 500px;
                margin: 0 auto;
            }
            h1 {
                font-size: 2.5em;
                margin-bottom: 20px;
            }
            .status {
                font-size: 1.2em;
                margin: 20px 0;
                padding: 10px;
                background: rgba(0, 255, 0, 0.2);
                border-radius: 10px;
                border: 2px solid rgba(0, 255, 0, 0.5);
            }
            .info {
                margin-top: 20px;
                font-size: 0.9em;
                opacity: 0.8;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 Discord Bot</h1>
            <div class="status">✅ Bot is alive and running!</div>
            <p>This bot automatically responds to "script" and "key" messages in Discord.</p>
            <div class="info">
                Hosted on Render • Auto-deploy from GitHub • 24/7 Uptime
            </div>
        </div>
    </html>
    """

@app.route('/health')
def health():
    return {"status": "healthy", "service": "discord-bot"}, 200

def run():
    port = int(os.environ.get('PORT', 8080))
    print(f"🌐 Starting keep-alive server on port {port}")
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()
    print("✅ Keep-alive server started")
