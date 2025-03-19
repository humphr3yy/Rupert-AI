import os
import logging
import threading
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from bot import RupertBot
from dotenv import load_dotenv
import config
from threading import Thread
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Rupert-AI is running!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)


# Load environment variables from .env file if present
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev_secret_key")

# Global variable to store the bot instance
bot_instance = None
bot_thread = None
bot_status = {
    "running": False,
    "connected_guild": None,
    "voice_channel": None,
    "active_users": [],
    "conversation_log": []
}

# Create a route for the main page
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/settings", methods=["GET", "POST"])
def settings():
    if request.method == "POST":
        # Handle settings form submission
        settings_data = request.form.to_dict()
        
        # Save settings to session or config file
        session["settings"] = settings_data
        
        # Update config variables
        if 'command_prefix' in settings_data:
            config.COMMAND_PREFIX = settings_data['command_prefix']
        if 'gemini_api_key' in settings_data:
            config.GEMINI_API_KEY = settings_data['gemini_api_key']
        if 'piper_voice' in settings_data:
            config.PIPER_VOICE = settings_data['piper_voice']
        
        return redirect(url_for('settings'))
    
    # Load current settings
    current_settings = session.get("settings", {})
    
    return render_template("settings.html", settings=current_settings)

@app.route("/start-bot", methods=["POST"])
def start_bot():
    global bot_instance, bot_thread, bot_status
    
    try:
        if not bot_status["running"]:
            # Get Discord token from environment variable or request
            discord_token = os.getenv("DISCORD_TOKEN")
            
            if not discord_token:
                return jsonify({
                    "status": "error", 
                    "message": "Discord token not set. Please configure it in the settings."
                })
            
            # Initialize the bot in a separate thread
            bot_instance = RupertBot(discord_token)
            
            def run_bot():
                try:
                    logger.info("Starting bot in separate thread")
                    bot_instance.run()
                except Exception as e:
                    logger.error(f"Error in bot thread: {e}")
                    bot_status["running"] = False
            
            bot_thread = threading.Thread(target=run_bot)
            bot_thread.daemon = True
            bot_thread.start()
            
            bot_status["running"] = True
            
            return jsonify({
                "status": "success", 
                "message": "Bot started successfully"
            })
        else:
            return jsonify({
                "status": "success", 
                "message": "Bot is already running"
            })
            
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        return jsonify({
            "status": "error", 
            "message": f"Error starting bot: {str(e)}"
        })

@app.route("/stop-bot", methods=["POST"])
def stop_bot():
    global bot_instance, bot_status
    
    try:
        if bot_status["running"] and bot_instance:
            # Stop the bot
            logger.info("Stopping bot")
            # This would be implemented in the real bot
            # bot_instance.stop()
            
            bot_status["running"] = False
            return jsonify({
                "status": "success", 
                "message": "Bot stopped successfully"
            })
        else:
            return jsonify({
                "status": "success", 
                "message": "Bot is not running"
            })
            
    except Exception as e:
        logger.error(f"Error stopping bot: {e}")
        return jsonify({
            "status": "error", 
            "message": f"Error stopping bot: {str(e)}"
        })

@app.route("/bot-status", methods=["GET"])
def get_bot_status():
    return jsonify(bot_status)

@app.route("/check-gemini", methods=["POST"])
def check_gemini():
    try:
        import google.generativeai as genai
        import asyncio
        
        async def test_gemini_connection():
            api_key = request.json.get("api_key", "")
            
            if not api_key:
                return {
                    "status": "error",
                    "message": "No API key provided"
                }
            
            try:
                # Configure the Gemini API with the provided key
                genai.configure(api_key=api_key)
                
                # Get available models to verify the API key works
                models = genai.list_models()
                available_models = [model.name for model in models if 'generateContent' in model.supported_generation_methods]
                
                return {
                    "status": "success",
                    "message": "Connected to Gemini API successfully",
                    "models": available_models
                }
            except Exception as e:
                return {
                    "status": "error",
                    "message": f"Error connecting to Gemini API: {str(e)}"
                }
        
        result = asyncio.run(test_gemini_connection())
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error checking Gemini API: {str(e)}"
        })

@app.route("/check-piper", methods=["GET"])
def check_piper():
    try:
        import subprocess
        
        # Check if Piper is installed
        result = subprocess.run(
            ["which", "piper"], 
            capture_output=True, 
            text=True
        )
        
        if result.returncode == 0:
            # Piper is installed, check version
            version_result = subprocess.run(
                ["piper", "--help"], 
                capture_output=True, 
                text=True
            )
            
            return jsonify({
                "status": "success",
                "message": "Piper TTS is installed",
                "path": result.stdout.strip()
            })
        else:
            return jsonify({
                "status": "error",
                "message": "Piper TTS is not installed"
            })
            
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error checking Piper: {str(e)}"
        })

# Add a conversation log entry
@app.route("/log-conversation", methods=["POST"])
def log_conversation():
    data = request.json
    if "speaker" in data and "message" in data:
        entry = {
            "timestamp": data.get("timestamp"),
            "speaker": data["speaker"],
            "message": data["message"]
        }
        bot_status["conversation_log"].append(entry)
        # Keep only the last 100 entries
        if len(bot_status["conversation_log"]) > 100:
            bot_status["conversation_log"] = bot_status["conversation_log"][-100:]
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "Missing required fields"})

# This is the entry point when run directly
if __name__ == "__main__":
    # Check if running as a standalone script or as part of the web app
    if os.environ.get("RUN_BOT_DIRECTLY", "false").lower() == "true":
        # Get Discord token from environment variable
        discord_token = os.getenv("DISCORD_TOKEN")
        
        if not discord_token:
            logging.error("DISCORD_TOKEN environment variable not set")
            raise ValueError("DISCORD_TOKEN environment variable is required")
        
        # Initialize and run the bot
        bot = RupertBot(discord_token)
        bot.run()
    else:
        # Run the Flask web app
        app.run(host="0.0.0.0", port=5000, debug=True)
