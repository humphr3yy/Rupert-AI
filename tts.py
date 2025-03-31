
import logging
import os
import pyttsx3
import subprocess
import asyncio
from typing import Optional, List, Dict, Any
from utils import create_temp_file

# Setup logging
logger = logging.getLogger(__name__)

# Define default piper model path
DEFAULT_PIPER_MODEL_PATH = os.path.join("piper_models", "en_US-lessac-medium")

class GoogleTTS:
    def __init__(self, language: str = "en-GB"):
        self.language = language
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 165)  # Slightly slower for British accent
        self.engine.setProperty('volume', 1.0)  # Volume level
        
        # Try to set a British voice if available
        voices = self.engine.getProperty('voices')
        british_voice = None
        
        # Look for a British English voice
        for voice in voices:
            if 'en_GB' in voice.id or 'british' in voice.id.lower():
                british_voice = voice.id
                break
                
        # Set British voice if found
        if british_voice:
            self.engine.setProperty('voice', british_voice)

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


class PiperTTS:
    def __init__(self, model_path: str = None):
        """
        Initialize the Piper TTS engine with the specified model
        
        Args:
            model_path: Path to the Piper voice model. If None, uses default
        """
        self.model_path = model_path or DEFAULT_PIPER_MODEL_PATH
        
        # Check if model exists
        self._verify_model()
        
        # Default voice settings - tuned for a suave British accent
        self.speaker = 0
        self.length_scale = 1.1  # Slightly slower for British sophistication
        self.noise_scale = 0.7  # Slightly more variations for expressiveness
        self.noise_w = 0.75  # Balanced phoneme randomness for a natural British cadence
        
        logger.info(f"Initialized Piper TTS with model: {self.model_path}")
    
    def _verify_model(self) -> None:
        """Verify that the model files exist or can be downloaded"""
        model_file = os.path.join(self.model_path, "model.onnx")
        config_file = os.path.join(self.model_path, "config.json")
        
        missing_files = []
        if not os.path.exists(model_file):
            missing_files.append("model.onnx")
        if not os.path.exists(config_file):
            missing_files.append("config.json")
            
        if missing_files:
            # Simply log the missing files but don't raise an exception
            # This allows the class to be instantiated even if models need to be downloaded
            logger.warning(f"Piper model files missing: {', '.join(missing_files)}")
            logger.warning(f"Models need to be downloaded to: {self.model_path}")
            logger.warning("Will attempt to use fallback TTS methods until models are available")
    
    async def text_to_speech(self, text: str) -> str:
        """
        Convert text to speech using Piper
        
        Args:
            text: The text to convert to speech
            
        Returns:
            Path to the generated audio file
        """
        # Check if model files exist
        model_file = os.path.join(self.model_path, "model.onnx")
        config_file = os.path.join(self.model_path, "config.json")
        
        # If model files are missing, fall back to other TTS engines
        if not os.path.exists(model_file) or not os.path.exists(config_file):
            logger.warning("Piper model files missing, falling back to GoogleTTS")
            fallback_tts = GoogleTTS()
            return await fallback_tts.text_to_speech(text)
        
        # Create a temporary file for the text
        text_file = f"temp_text_{os.urandom(4).hex()}.txt"
        output_file = f"temp_tts_{os.urandom(4).hex()}.wav"
        
        try:
            # Write the text to a file
            with open(text_file, "w") as f:
                f.write(text)
            
            # Construct the piper command
            command = [
                "piper",
                "--model", model_file,
                "--config", config_file,
                "--output-file", output_file,
                "--speaker", str(self.speaker),
                "--length-scale", str(self.length_scale),
                "--noise-scale", str(self.noise_scale),
                "--noise-w", str(self.noise_w)
            ]
            
            # Run piper with the text file as input
            process = await asyncio.create_subprocess_exec(
                *command,
                stdin=open(text_file, "r"),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Wait for the process to complete with timeout
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=15.0)
                if process.returncode != 0:
                    logger.error(f"Piper TTS error: {stderr.decode()}")
                    # If piper fails, fall back to GoogleTTS
                    logger.warning("Piper TTS failed, falling back to GoogleTTS")
                    fallback_tts = GoogleTTS()
                    return await fallback_tts.text_to_speech(text)
                
                if not os.path.exists(output_file) or os.path.getsize(output_file) == 0:
                    logger.error("Piper TTS output file is empty or does not exist")
                    # If output is empty, fall back to GoogleTTS
                    logger.warning("Piper TTS output invalid, falling back to GoogleTTS")
                    fallback_tts = GoogleTTS()
                    return await fallback_tts.text_to_speech(text)
                
                return output_file
                
            except asyncio.TimeoutError:
                logger.error("Piper TTS process timed out")
                process.kill()
                # If timeout occurs, fall back to GoogleTTS
                logger.warning("Piper TTS timed out, falling back to GoogleTTS")
                fallback_tts = GoogleTTS()
                return await fallback_tts.text_to_speech(text)
                
        except Exception as e:
            logger.error(f"Error during Piper TTS synthesis: {e}")
            # For any exception, fall back to GoogleTTS
            logger.warning(f"Falling back to GoogleTTS due to error: {e}")
            fallback_tts = GoogleTTS()
            return await fallback_tts.text_to_speech(text)
            
        finally:
            # Clean up the text file
            if os.path.exists(text_file):
                try:
                    os.remove(text_file)
                except Exception as e:
                    logger.error(f"Error removing temporary text file: {e}")
    
    def set_voice_parameters(self, speed: float = None, variation: float = None, randomness: float = None) -> None:
        """
        Set voice parameters
        
        Args:
            speed: Speed multiplier (lower = faster). Range: 0.5-2.0
            variation: Voice variation level. Range: 0.1-1.0
            randomness: Phoneme randomness level. Range: 0.1-1.0
        """
        if speed is not None:
            self.length_scale = max(0.5, min(2.0, speed))
            
        if variation is not None:
            self.noise_scale = max(0.1, min(1.0, variation))
            
        if randomness is not None:
            self.noise_w = max(0.1, min(1.0, randomness))
            
        logger.info(f"Updated voice parameters: speed={self.length_scale}, variation={self.noise_scale}, randomness={self.noise_w}")


# Google Text-to-Speech using gTTS library
class gTTS:
    def __init__(self, language: str = "en-gb"):
        """
        Initialize Google Text-to-Speech with British English accent
        
        Args:
            language: Language code (e.g., 'en-gb', 'en-us', 'fr', 'es')
        """
        try:
            # Lazily import to avoid dependency issues
            from gtts import gTTS as GoogleTTS
            
            self.language = language
            self.gtts_available = True
            logger.info(f"Initialized Google TTS with language: {language}")
        except ImportError:
            logger.warning("gTTS library not available. Install with 'pip install gtts'")
            self.gtts_available = False
    
    async def text_to_speech(self, text: str) -> Optional[str]:
        """
        Convert text to speech using Google TTS
        
        Args:
            text: Text to convert to speech
            
        Returns:
            Path to audio file or None if conversion failed
        """
        if not self.gtts_available:
            logger.error("gTTS is not available")
            return None
            
        # Import here to allow the class to be defined even if gtts is not installed
        from gtts import gTTS as GoogleTTS
        
        output_file = f"temp_tts_{os.urandom(4).hex()}.mp3"
        
        try:
            # Create gTTS object with text and language
            tts = GoogleTTS(text=text, lang=self.language, slow=False)
            
            # Save to file
            tts.save(output_file)
            
            return output_file
            
        except Exception as e:
            logger.error(f"Error during Google TTS synthesis: {e}")
            return None
