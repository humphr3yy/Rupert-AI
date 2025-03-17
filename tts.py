import logging
import os
from gtts import gTTS
from typing import Optional

logger = logging.getLogger(__name__)

class GoogleTTS:
    def __init__(self, language: str = "en"):
        self.language = language

    async def text_to_speech(self, text: str) -> str:
        """
        Convert text to speech using Google TTS

        Args:
            text: The text to convert to speech

        Returns:
            Path to the generated audio file
        """
        output_file = f"temp_tts_{os.urandom(4).hex()}.mp3"

        try:
            tts = gTTS(text=text, lang=self.language)
            tts.save(output_file)
            return output_file

        except Exception as e:
            logger.error(f"Error during TTS synthesis: {e}")
            return self.create_silent_audio()

    def create_silent_audio(self) -> str:
        """Create a short silent audio file as a last resort"""
        output_file = f"temp_tts_silent_{os.urandom(4).hex()}.wav"

        # Use ffmpeg to create a silent audio file
        subprocess.run([
            "ffmpeg", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono", 
            "-t", "1", output_file, "-y"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        return output_file

import subprocess