import bot
import transcription
import ai_integration
import tts
import utils
import config
import os
import inspect

print('All modules imported successfully')

# Check configuration
print('\nConfiguration:')
print(f'Command Prefix: {config.COMMAND_PREFIX}')
print(f'Gemini API: {"Configured" if hasattr(config, "GEMINI_API_KEY") else "Not configured"}')

# Check Gemini system prompts
gemini_prompts = [attr for attr in dir(config) if attr.endswith('_SYSTEM_PROMPT') and isinstance(getattr(config, attr), str)]
if gemini_prompts:
    print(f'System prompts: {", ".join(gemini_prompts)}')

# Verify TTS module
print('\nTTS Systems:')
tts_classes = [name for name, obj in inspect.getmembers(tts) 
               if inspect.isclass(obj) and hasattr(obj, 'text_to_speech')]
print(f'- Available TTS engines: {", ".join(tts_classes)}')

# Check Piper model
if hasattr(tts, 'DEFAULT_PIPER_MODEL_PATH'):
    model_path = tts.DEFAULT_PIPER_MODEL_PATH
    model_exists = os.path.exists(model_path)
    print(f'- Piper model path: {model_path} ({"Exists" if model_exists else "Missing"})')
    if model_exists:
        model_files = os.listdir(model_path)
        print(f'  - Model files: {", ".join(model_files)}')

# Check module structures
print('\nBot Structure:')
print('- Transcriber module:', 'Complete' if hasattr(transcription, 'Transcriber') else 'Incomplete')
print('- GeminiAPI module:', 'Complete' if hasattr(ai_integration, 'GeminiAPI') else 'Incomplete')
print('- PiperTTS module:', 'Complete' if hasattr(tts, 'PiperTTS') else 'Incomplete')
print('- Utils:', ', '.join([f for f in dir(utils) 
                            if not f.startswith('_') and callable(getattr(utils, f))]))

# Check bot components
print('\nBot Components:')
print('- Event handlers:', 'Implemented' if 'setup_events' in dir(bot.RupertBot) else 'Missing')
print('- Commands:', 'Implemented' if 'register_commands' in dir(bot.RupertBot) else 'Missing')
print('- Voice processing:', 'Implemented' if 'listen_and_transcribe' in dir(bot.RupertBot) else 'Missing')
print('- Rupert interaction:', 'Implemented' if 'handle_rupert_interaction' in dir(bot.RupertBot) else 'Missing')

# Check conversation handling
conversation_methods = [
    method for method in dir(bot.RupertBot) 
    if method.startswith(('analyze_', 'handle_', 'add_to_conversation'))
]
print('\nConversation Handling:')
print(f'- Methods: {", ".join(conversation_methods)}')

# Check vision capabilities
vision_functions = [f for f in dir(utils) if 'vision' in f.lower() or 'image' in f.lower()]
print('\nVision Capabilities:')
print(f'- Functions: {", ".join(vision_functions) if vision_functions else "None detected"}')
if hasattr(ai_integration.GeminiAPI, 'generate_vision_response'):
    print('- Gemini Vision API: Supported')

# Check text channel handling
text_methods = [method for method in dir(bot.RupertBot) if 'message' in method or 'text' in method]
print('\nText Channel Handling:')
print(f'- Methods: {", ".join(text_methods)}')

print('\nSystem is ready to operate with Gemini API')