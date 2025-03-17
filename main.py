import os
import logging
from flask import Flask, render_template, request, jsonify
from bot import RupertBot
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev_secret_key")

# Create a route for the main page
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/start-bot", methods=["POST"])
def start_bot():
    # This route would be called to start the bot (in a real implementation)
    # For this demo, we'll just return a success message
    return jsonify({"status": "success", "message": "Bot would start here in a full implementation"})

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
