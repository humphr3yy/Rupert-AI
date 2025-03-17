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
OLLAMA_VISION_MODEL = os.getenv("OLLAMA_VISION_MODEL", "llava")

# Vision Features
VISION_ENABLED = os.getenv("VISION_ENABLED", "True").lower() == "true"
VISION_CONVERSATION_THRESHOLD = float(os.getenv("VISION_CONVERSATION_THRESHOLD", "0.6"))

# Text Interaction Features
TEXT_ENABLED = os.getenv("TEXT_ENABLED", "True").lower() == "true"
MESSAGE_HISTORY_LIMIT = int(os.getenv("MESSAGE_HISTORY_LIMIT", "20"))
TEXT_COOLDOWN_SECONDS = int(os.getenv("TEXT_COOLDOWN_SECONDS", "5"))

# Piper TTS Configuration
PIPER_VOICE = os.getenv("PIPER_VOICE", "en_US-lessac-medium")

# Speech Recognition Configuration
SPEECH_LANGUAGE = os.getenv("SPEECH_LANGUAGE", "en-US")
ENERGY_THRESHOLD = int(os.getenv("ENERGY_THRESHOLD", "300"))
PAUSE_THRESHOLD = float(os.getenv("PAUSE_THRESHOLD", "0.8"))
DYNAMIC_ENERGY = os.getenv("DYNAMIC_ENERGY", "True").lower() == "true"

# Conversation Intent Analysis
INTENT_ANALYSIS_ENABLED = os.getenv("INTENT_ANALYSIS_ENABLED", "True").lower() == "true"
INTENT_CONFIDENCE_THRESHOLD = float(os.getenv("INTENT_CONFIDENCE_THRESHOLD", "0.6"))

# System Prompts for Different Contexts
SYSTEM_PROMPT = os.getenv("SYSTEM_PROMPT", 
    "You are Rupert, a friendly and helpful AI assistant in a Discord voice channel. "
    "Keep your responses concise and natural for voice conversations. "
    "If someone is talking about you but not to you, don't respond unless they ask you a direct question."
)

# Vision System Prompt
VISION_SYSTEM_PROMPT = os.getenv("VISION_SYSTEM_PROMPT",
    "You are Rupert, an AI assistant with vision capabilities that can analyze screen shares in a Discord channel. "
    "When asked about what's on screen, provide detailed observations about the content. "
    "If you see a game like GeoGuesser, analyze visual clues like architecture, signs, vegetation, and road markings "
    "to help determine the location. Be specific but concise in your analysis."
)

# DM System Prompt
DM_SYSTEM_PROMPT = os.getenv("DM_SYSTEM_PROMPT",
    "You are Rupert, a friendly and helpful AI assistant responding to a direct message (DM) on Discord. "
    "You're having a one-on-one conversation with this user. Be conversational but respectful and helpful. "
    "You can access the message history to provide context-aware responses. Remember that in DMs, the conversation "
    "is private between you and the user."
)

# Text Channel System Prompt
TEXT_CHANNEL_SYSTEM_PROMPT = os.getenv("TEXT_CHANNEL_SYSTEM_PROMPT",
    "You are Rupert, a friendly and helpful AI assistant in a Discord text channel. "
    "You're responding to a message in a public server where multiple users can see your response. "
    "You can see the message history in this channel for context. "
    "Be aware of the channel's name and purpose when responding. If someone mentions you with @Rupert "
    "or addresses you by name, you should respond to their query. Be helpful but concise and avoid "
    "unnecessarily long responses in public channels."
)