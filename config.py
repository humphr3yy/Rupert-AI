import os
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

# Discord Bot Configuration
COMMAND_PREFIX = os.getenv("COMMAND_PREFIX", "!")

# Ollama API Configuration
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "localhost")
OLLAMA_PORT = int(os.getenv("OLLAMA_PORT", "11434"))
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama2")

# Piper TTS Configuration
PIPER_VOICE = os.getenv("PIPER_VOICE", "en_US-lessac-medium")

# Speech Recognition Configuration
SPEECH_LANGUAGE = os.getenv("SPEECH_LANGUAGE", "en-US")
ENERGY_THRESHOLD = int(os.getenv("ENERGY_THRESHOLD", "300"))
PAUSE_THRESHOLD = float(os.getenv("PAUSE_THRESHOLD", "0.8"))
DYNAMIC_ENERGY = os.getenv("DYNAMIC_ENERGY", "True").lower() == "true"

# System Prompt for AI
SYSTEM_PROMPT = os.getenv("SYSTEM_PROMPT", 
    "You are Rupert, a friendly and helpful AI assistant in a Discord voice channel. "
    "Keep your responses concise and natural for voice conversations."
)