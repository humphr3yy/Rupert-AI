import subprocess
import asyncio
import logging
import os
from typing import Optional

from utils import create_temp_file

logger = logging.getLogger(__name__)

class PiperTTS:
    def __init__(self, voice: str = "en_US-lessac-medium"):
        """
        Initialize the Piper TTS engine
        
        Args:
            voice: The voice model to use for synthesis
        """
        self.voice = voice
        self.check_piper_installation()
    
    def check_piper_installation(self):
        """Check if Piper is properly installed and available"""
        try:
            result = subprocess.run(["piper", "--help"], 
                                   stdout=subprocess.PIPE, 
                                   stderr=subprocess.PIPE, 
                                   text=True)
            if result.returncode != 0:
                logger.warning("Piper TTS may not be properly installed")
                logger.warning(f"Piper error: {result.stderr}")
        except FileNotFoundError:
            logger.error("Piper TTS is not installed or not in PATH")
            logger.error("Please install Piper: https://github.com/rhasspy/piper")
    
    async def text_to_speech(self, text: str) -> str:
        """
        Convert text to speech using Piper TTS
        
        Args:
            text: The text to convert to speech
            
        Returns:
            Path to the generated audio file
        """
        # Create a temporary file for the output
        output_file = f"temp_tts_{os.urandom(4).hex()}.wav"
        
        try:
            # Prepare the command for Piper
            # First ensure model directory exists
            model_dir = f"piper_models/{self.voice}"
            os.makedirs(model_dir, exist_ok=True)
            
            # Check if model exists, if not download it
            model_path = f"{model_dir}/model.onnx"
            if not os.path.exists(model_path):
                logger.info(f"Downloading Piper voice model: {self.voice}")
                download_cmd = [
                    "pip", "install", "--upgrade", "piper-phonemize",
                    "&&", "python", "-m", "piper.download", 
                    "--model", self.voice,
                    "--output_dir", "piper_models"
                ]
                subprocess.run(download_cmd, check=True)

            cmd = [
                "piper",
                "--model", model_path,
                "--output_file", output_file
            ]
            
            # Run Piper in a subprocess
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Send the text to Piper
            stdout, stderr = await process.communicate(text.encode('utf-8'))
            
            if process.returncode != 0:
                logger.error(f"Piper TTS error: {stderr.decode()}")
                raise Exception(f"Piper TTS failed: {stderr.decode()}")
            
            return output_file
            
        except Exception as e:
            logger.error(f"Error during TTS synthesis: {e}")
            # Fallback: create a simple message saying there was an error
            return await self.create_fallback_audio("I'm having trouble speaking right now.")
    
    async def create_fallback_audio(self, message: str) -> str:
        """Create a fallback audio file when Piper fails"""
        try:
            # Try to use espeak as a fallback if available
            output_file = f"temp_tts_fallback_{os.urandom(4).hex()}.wav"
            
            process = await asyncio.create_subprocess_exec(
                "espeak", "-w", output_file, message,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            await process.communicate()
            
            if os.path.exists(output_file):
                return output_file
        except:
            logger.error("Failed to create fallback audio with espeak")
        
        # If all else fails, create a silent audio file
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
