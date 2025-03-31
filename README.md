# Rupert AI - Advanced Discord Bot

Rupert is a sophisticated Discord bot leveraging Google's Gemini AI for intelligent conversation, voice interaction, and visual content analysis. With its signature British philosophical persona, Rupert can engage in voice calls, analyze screenshared content, and maintain contextual conversations across Discord channels.

![Rupert Picture](static/images/rupert-picture.png)

## Key Features

- **Voice Chat Interaction**: Joins Discord voice channels to listen, transcribe speech, and respond verbally
- **Multi-modal AI**: Leverages Google's Gemini models for both text and vision capabilities
- **Screenshare Analysis**: Recognizes and comments on screenshared content including:
  - GeoGuessr gameplay with location analysis
  - YouTube videos
  - Chess and checkers games
- **Sophisticated British Persona**: Communicates with a philosophical tone and proper British accent
- **Text-to-Speech**: Uses Piper TTS with customized British voice parameters
- **Web Dashboard**: Easy-to-use interface for configuration and monitoring

## System Requirements

- Python 3.8 or higher
- 4GB RAM minimum (8GB recommended)
- Discord Developer Account with Bot Token
- Google Gemini API Key
- Internet connection for API access

## Installation on Ubuntu

### Prerequisites

1. Update your system:
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

2. Install required system dependencies:
   ```bash
   sudo apt install -y python3 python3-pip python3-venv ffmpeg portaudio19-dev python3-dev
   ```

3. Create a Discord bot and get your token:
   - Visit [Discord Developer Portal](https://discord.com/developers/applications)
   - Create a new application
   - Go to the "Bot" tab and click "Add Bot"
   - Under the TOKEN section, click "Copy" to copy your bot token
   - Enable the following Privileged Gateway Intents:
     - Presence Intent
     - Server Members Intent
     - Message Content Intent

4. Get a Google Gemini API Key:
   - Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Create an API key

### Setup Instructions

1. Clone the repository:
   ```bash
   git clone https://github.com/humphr3yy/Rupert-AI.git
   cd rupert-ai
   ```

2. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   
   If no requirements.txt exists, install the following packages:
   ```bash
   pip install aiohttp discord.py flask flask-sqlalchemy \
               google-generativeai gunicorn piper-tts \
               pydub python-dotenv pyttsx3 speechrecognition \
               gtts
   ```

4. Create a `.env` file in the project root:
   ```bash
   touch .env
   ```

5. Add your API keys and configuration to the `.env` file:
   ```
   DISCORD_TOKEN=your_discord_bot_token_here
   GEMINI_API_KEY=your_gemini_api_key_here
   TTS_ENGINE=piper  # Options: piper, google, gtts
   COMMAND_PREFIX=!
   ```

### Running Rupert AI

#### Method 1: Web Interface (Recommended)

1. Start the Flask web server:
   ```bash
   gunicorn --bind 0.0.0.0:5000 main:app
   ```

2. Open a web browser and navigate to `http://localhost:5000`

3. Use the dashboard to:
   - Start/stop the bot
   - Check API connection status
   - Monitor conversations
   - View TTS settings

#### Method 2: Direct Execution

To run the bot directly without the web interface:

```bash
python run_bot.py
```

## Usage Guide

### Discord Commands

- `!join` - Invites Rupert to your current voice channel
- `!leave` - Disconnects Rupert from the voice channel
- `rupert` - Mention Rupert in a text channel to interact with him

### Voice Interaction

Once Rupert is in a voice channel:
1. Say "Rupert" or "Hey Rupert" to get his attention
2. Ask a question or have a conversation
3. Rupert will respond using his British TTS voice

### Screenshare Analysis

When someone is sharing their screen:
1. Ask Rupert about what's on screen
2. For GeoGuessr, ask for location hints or analysis
3. For YouTube videos, ask for commentary or summaries

## Development & Customization

### Project Structure

- `bot.py` - Core Discord bot functionality
- `ai_integration.py` - Gemini API integration
- `tts.py` - Text-to-speech functionality
- `transcription.py` - Speech recognition
- `config.py` - Configuration settings
- `main.py` - Web interface
- `utils.py` - Utility functions

### TTS Voice Customization

Rupert uses Piper TTS with specific parameters for a sophisticated British accent:
- **Speed**: 1.1 (slightly slower for British sophistication)
- **Variation**: 0.7 (more expressive speaking style)
- **Randomness**: 0.75 (natural British cadence)

To modify these settings, edit the `PiperTTS` class in `tts.py`.

### Detailed Documentation

For more detailed information, see the following documentation:

- [British Voice Configuration Guide](docs/british_voice_guide.md) - Comprehensive guide to Rupert's TTS voice settings
- [GeoGuessr Assistance Guide](docs/geoguessr_guide.md) - Details on Rupert's enhanced GeoGuessr gameplay analysis

### Easy Installation

For Ubuntu systems, a convenient installation script is provided:

```bash
chmod +x ubuntu_install.sh
./ubuntu_install.sh
```

This script will install all necessary dependencies, create a virtual environment, and set up a template `.env` file for your configuration.

## Troubleshooting

### Common Issues

1. **Bot not responding to voice commands**
   - Ensure your microphone is working
   - Check that Discord has microphone permissions
   - Verify the bot has joined the voice channel successfully

2. **TTS not working**
   - Check that ffmpeg is installed correctly
   - Ensure the Piper voice models are downloaded

3. **API Connection Errors**
   - Verify your Gemini API key is correct
   - Check your internet connection
   - Ensure you haven't exceeded API rate limits

### Logs

Check the following logs for troubleshooting:
- Console output for Python exceptions
- Discord Developer Portal for bot event logs

## License

This project is released under the MIT License. See the LICENSE file for details.

## Acknowledgments

- Google Gemini API for AI capabilities
- Piper TTS for high-quality voice synthesis
- Discord.py for Discord integration

## Credits
*Thank you* to ***all*** the Developers who worked on this!

*Humphr3yy* / *Kaiden K* - **Creator**, Developer

*Goofygoing* - *Developer*, *Contributer* to ***a lot*** of features and ideas.

An AI Agent - Some people may find the idea of crediting an AI stupid but I think it makes sense, it was a Developer who fixed up garbled code and helped a lot.

