from flask import Flask
from threading import Thread
import requests
import time
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/')
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>🤖 Discord Bot Status</title>
        <meta http-equiv="refresh" content="30">
        <style>
            body { font-family: Arial; text-align: center; padding: 50px; }
            .status { color: green; font-size: 24px; margin: 20px; }
            .ping-time { color: #666; font-size: 14px; }
        </style>
    </head>
    <body>
        <h1>🤖 Discord Bot</h1>
        <div class="status">✅ Online and Monitoring</div>
        <p>Auto-pinging every 5 minutes to stay awake</p>
        <div class="ping-time" id="pingTime">Last ping: Loading...</div>
        <script>
            function updatePingTime() {
                const now = new Date().toLocaleTimeString();
                document.getElementById('pingTime').innerText = 'Last ping: ' + now;
            }
            updatePingTime();
            setInterval(updatePingTime, 60000); // Update every minute
        </script>
    </body>
    </html>
    """

@app.route('/ping')
def ping():
    return {"status": "alive", "timestamp": time.time()}, 200

@app.route('/health')
def health():
    return {"status": "healthy", "service": "discord-bot"}, 200

class SelfPinger:
    def __init__(self):
        self.last_ping = None
        self.is_running = True
        
    def get_own_url(self):
        """Get the bot's own URL on Render"""
        render_service_name = os.environ.get('RENDER_SERVICE_NAME', 'discord-bot')
        render_external_url = os.environ.get('RENDER_EXTERNAL_URL')
        
        if render_external_url:
            return render_external_url
        elif 'RENDER' in os.environ:
            # On Render, construct the URL
            return f"https://{render_service_name}.onrender.com"
        else:
            # Local development
            return "http://localhost:8080"
    
    def ping_self(self):
        """Ping our own server to keep it awake"""
        url = self.get_own_url()
        
        while self.is_running:
            try:
                response = requests.get(f"{url}/ping", timeout=10)
                now = time.strftime("%H:%M:%S")
                
                if response.status_code == 200:
                    logger.info(f"💓 [{now}] Self-ping successful - Status: {response.status_code}")
                    self.last_ping = now
                else:
                    logger.warning(f"⚠️  [{now}] Self-ping failed - Status: {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                now = time.strftime("%H:%M:%S")
                logger.error(f"❌ [{now}] Self-ping error: {e}")
            except Exception as e:
                now = time.strftime("%H:%M:%S")
                logger.error(f"❌ [{now}] Unexpected error: {e}")
            
            # Wait 5 minutes (300 seconds) before next ping
            for _ in range(300):  # Check every second if we should stop
                if not self.is_running:
                    break
                time.sleep(1)
    
    def start(self):
        """Start the self-pinging thread"""
        thread = Thread(target=self.ping_self, daemon=True)
        thread.start()
        logger.info("✅ Self-pinger started (pinging every 5 minutes)")
        return thread
    
    def stop(self):
        """Stop the self-pinging"""
        self.is_running = False
        logger.info("🛑 Self-pinger stopped")

# Global pinger instance
pinger = SelfPinger()

def run_flask():
    """Run the Flask web server"""
    port = int(os.environ.get('PORT', 8080))
    logger.info(f"🌐 Flask server starting on port {port}")
    
    # Disable Flask's default logging
    werkzeug_log = logging.getLogger('werkzeug')
    werkzeug_log.setLevel(logging.WARNING)
    
    # Run in production mode
    from waitress import serve
    serve(app, host='0.0.0.0', port=port)

def keep_alive():
    """Start both Flask server and self-pinger"""
    
    # Start Flask server in a thread
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logger.info("✅ Flask server started")
    
    # Wait a moment for server to start
    time.sleep(2)
    
    # Start self-pinger
    pinger.start()
    
    # Log the URL for testing
    url = pinger.get_own_url()
    logger.info(f"📡 Server URL: {url}")
    logger.info("🎯 Keep-alive system fully active")
    logger.info("⏰ Will auto-ping every 5 minutes")
    
    return True
