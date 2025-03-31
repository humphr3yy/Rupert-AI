#!/bin/bash

# Rupert AI - Ubuntu Installation Script
# This script automates the setup process for Rupert AI on Ubuntu systems

echo "=== Rupert AI Installation Script ==="
echo "This script will install all necessary dependencies for Rupert AI on Ubuntu."
echo ""

# Update system packages
echo "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install system dependencies
echo "Installing system dependencies..."
sudo apt install -y python3 python3-pip python3-venv ffmpeg portaudio19-dev python3-dev

# Create virtual environment
echo "Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install aiohttp discord.py flask flask-sqlalchemy \
            google-generativeai gunicorn piper-tts \
            pydub python-dotenv pyttsx3 speechrecognition \
            gtts ffmpeg-python psycopg2-binary email-validator wget

# Set up .env file template
echo "Creating .env file template..."
if [ ! -f .env ]; then
    cat > .env << EOL
# Rupert AI Configuration
# Replace with your actual tokens and settings

# Discord Bot Token (required)
DISCORD_TOKEN=your_discord_bot_token_here

# Google Gemini API Key (required)
GEMINI_API_KEY=your_gemini_api_key_here

# Bot Configuration
COMMAND_PREFIX=!

# TTS Settings
TTS_ENGINE=piper
TTS_LANGUAGE=en-GB

# Piper Voice Parameters (for British accent)
PIPER_SPEED=1.1
PIPER_VARIATION=0.7
PIPER_RANDOMNESS=0.75

# Web Interface Settings
WEB_PORT=5000
EOL
    echo ".env template created. Please edit it with your actual API keys and settings."
else
    echo ".env file already exists. Skipping creation."
fi

# Download Piper voice model if needed
if [ ! -d "piper_models/en_US-lessac-medium" ]; then
    echo "Downloading Piper voice model (British English)..."
    mkdir -p piper_models
    wget -P /tmp https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx
    wget -P /tmp https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json
    mv /tmp/en_US-lessac-medium.onnx piper_models/
    mv /tmp/en_US-lessac-medium.onnx.json piper_models/
else
    echo "Piper voice model already exists. Skipping download."
fi

echo ""
echo "=== Installation Complete ==="
echo ""
echo "To run Rupert AI with the web interface:"
echo "1. Activate the virtual environment: source venv/bin/activate"
echo "2. Start the web server: gunicorn --bind 0.0.0.0:5000 main:app"
echo "3. Open a browser and navigate to: http://localhost:5000"
echo ""
echo "To run Rupert AI directly (without web interface):"
echo "1. Activate the virtual environment: source venv/bin/activate"
echo "2. Run the bot: python run_bot.py"
echo ""
echo "Remember to edit the .env file with your actual API keys before starting!"