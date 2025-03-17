import speech_recognition as sr
import logging
import asyncio
from typing import Optional
from utils import create_temp_file, cleanup_temp_file

logger = logging.getLogger(__name__)

class Transcriber:
    def __init__(self):
        """Initialize the transcription engine"""
        self.recognizer = sr.Recognizer()
        # Adjust these parameters for better transcription
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8
        self.language = "en-US"
    
    def transcribe(self, audio_data: bytes) -> Optional[str]:
        """
        Transcribe audio data to text
        
        Args:
            audio_data: Raw audio bytes
            
        Returns:
            Transcribed text or None if transcription failed
        """
        if not audio_data or len(audio_data) < 1000:  # Skip very short audio clips
            return None
        
        try:
            # Save audio data to a temporary file
            temp_file = create_temp_file(audio_data, "wav")
            
            # Convert audio file to AudioData object
            with sr.AudioFile(temp_file) as source:
                audio = self.recognizer.record(source)
            
            # Perform the actual transcription
            transcript = self.recognizer.recognize_google(audio, language=self.language)
            
            # Clean up the temporary file
            cleanup_temp_file(temp_file)
            
            return transcript if transcript else None
            
        except sr.UnknownValueError:
            # Speech was unintelligible
            return None
        except sr.RequestError as e:
            logger.error(f"Could not request results from Speech Recognition service: {e}")
            return None
        except Exception as e:
            logger.error(f"Error during transcription: {e}")
            return None
    
    async def transcribe_async(self, audio_data: bytes) -> Optional[str]:
        """
        Async wrapper around the transcribe method
        
        Args:
            audio_data: Raw audio bytes
            
        Returns:
            Transcribed text or None if transcription failed
        """
        # Run the synchronous transcribe method in an executor to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.transcribe, audio_data)
