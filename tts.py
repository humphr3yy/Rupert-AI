
import logging
import os
import pyttsx3
from typing import Optional

logger = logging.getLogger(__name__)

class GoogleTTS:
    def __init__(self, language: str = "en"):
        self.language = language
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 175)  # Speed of speech
        self.engine.setProperty('volume', 1.0)  # Volume level

    async def text_to_speech(self, text: str) -> str:
        """
        Convert text to speech using pyttsx3

        Args:
            text: The text to convert to speech

        Returns:
            Path to the generated audio file
        """
        output_file = f"temp_tts_{os.urandom(4).hex()}.wav"

        try:
            self.engine.save_to_file(text, output_file)
            self.engine.runAndWait()
            return output_file

        except Exception as e:
            logger.error(f"Error during TTS synthesis: {e}")
            return None
