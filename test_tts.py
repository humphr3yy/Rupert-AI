#!/usr/bin/env python3
"""
Rupert AI - TTS Testing Script
This script allows testing of Rupert's TTS functionality without running the full bot.
"""

import os
import sys
import asyncio
from dotenv import load_dotenv
from tts import PiperTTS, GoogleTTS, gTTS

# Load environment variables
load_dotenv()

async def test_tts(text=None, engine=None):
    """Test text-to-speech with the specified engine"""
    if not text:
        text = "Greetings! I am Rupert, your philosophical British assistant. It is a pleasure to make your acquaintance."
    
    # Determine which TTS engine to use
    engine = engine or os.getenv("TTS_ENGINE", "piper").lower()
    
    print(f"Testing TTS with engine: {engine}")
    print(f"Text: {text}")
    
    # Initialize TTS engine
    if engine == "piper":
        tts_engine = PiperTTS()
        # Set British voice parameters
        tts_engine.set_voice_parameters(
            speed=float(os.getenv("PIPER_SPEED", "1.1")),
            variation=float(os.getenv("PIPER_VARIATION", "0.7")),
            randomness=float(os.getenv("PIPER_RANDOMNESS", "0.75"))
        )
        print("Using Piper TTS with British voice parameters:")
        print(f"  Speed: {os.getenv('PIPER_SPEED', '1.1')}")
        print(f"  Variation: {os.getenv('PIPER_VARIATION', '0.7')}")
        print(f"  Randomness: {os.getenv('PIPER_RANDOMNESS', '0.75')}")
    elif engine == "google":
        tts_engine = GoogleTTS(language="en-GB")
        print("Using Google TTS with British English voice")
    elif engine == "gtts":
        tts_engine = gTTS(language="en-gb")
        print("Using gTTS with British English voice")
    else:
        print(f"Error: Unknown TTS engine '{engine}'. Please use one of: piper, google, gtts")
        return
    
    # Generate speech
    print("Generating speech...")
    output_file = await tts_engine.text_to_speech(text)
    
    if output_file:
        print(f"Speech generated successfully: {output_file}")
        print("Playing audio...")
        
        # Play the audio using whatever is available
        if sys.platform == "darwin":  # macOS
            os.system(f"afplay {output_file}")
        elif sys.platform == "linux":  # Linux
            os.system(f"aplay {output_file}")
        else:  # Windows or other
            print(f"Audio file generated at: {output_file}")
            print("Please play it with your system's audio player.")
    else:
        print("Error: Failed to generate speech.")

if __name__ == "__main__":
    # Get text from command line arguments
    text = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else None
    
    # Run the test function
    asyncio.run(test_tts(text))