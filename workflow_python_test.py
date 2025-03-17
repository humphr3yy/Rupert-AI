import bot
import transcription
import ai_integration
import tts
import utils
import config

print('All modules imported successfully')
print('Configuration:')
print(f'Command Prefix: {config.COMMAND_PREFIX}')
print(f'Gemini API Key set: {"Yes" if config.GEMINI_API_KEY else "No"}')
print('')
print('Bot Structure:')
print('- Transcriber module:', 'Complete' if hasattr(transcription, 'Transcriber') else 'Incomplete')
print('- GeminiAPI module:', 'Complete' if hasattr(ai_integration, 'GeminiAPI') else 'Incomplete')
print('- PiperTTS module:', 'Complete' if hasattr(tts, 'PiperTTS') else 'Incomplete')
print('- Utils:', ', '.join([f for f in dir(utils) if not f.startswith('_') and callable(getattr(utils, f))]))
print('')
print('Bot Components:')
print('- Event handlers:', 'Implemented' if 'setup_events' in dir(bot.RupertBot) else 'Missing')
print('- Commands:', 'Implemented' if 'register_commands' in dir(bot.RupertBot) else 'Missing')
print('- Voice processing:', 'Implemented' if 'listen_and_transcribe' in dir(bot.RupertBot) else 'Missing')
print('- Rupert interaction:', 'Implemented' if 'handle_rupert_interaction' in dir(bot.RupertBot) else 'Missing')
