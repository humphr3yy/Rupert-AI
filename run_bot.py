#!/usr/bin/env python
import os
import logging
from dotenv import load_dotenv
from bot import RupertBot
import config
import tts

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def run_directly():
    """
    Run the bot directly (not through the web interface)
    """
    logger.info("Starting Rupert Bot in direct mode")
    
    # Get Discord token
    discord_token = os.getenv("DISCORD_TOKEN")
    
    if not discord_token:
        logger.error("DISCORD_TOKEN environment variable not set")
        print("Error: DISCORD_TOKEN environment variable is required")
        print("Please set it in your environment or .env file")
        return
    
    # Display bot configuration
    logger.info(f"Command Prefix: {config.COMMAND_PREFIX}")
    logger.info(f"Gemini API: {'Configured' if config.GEMINI_API_KEY else 'Not configured'}")
    
    # Initialize TTS with British accent
    logger.info("Initializing TTS with British accent")
    piper_tts = tts.PiperTTS()
    # Set slightly slower speed for British sophistication
    piper_tts.set_voice_parameters(speed=1.1, variation=0.7, randomness=0.75)
    
    # Initialize and run the bot
    bot = RupertBot(discord_token)
    logger.info("Bot initialized, connecting to Discord...")
    bot.run()

if __name__ == "__main__":
    # Load environment variables from .env file if present
    load_dotenv()
    run_directly()