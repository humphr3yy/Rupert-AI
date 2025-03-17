import os
import tempfile
import wave
import logging
import asyncio
import base64
import json
import datetime
from typing import Optional, Dict, Any, Tuple

logger = logging.getLogger(__name__)

def create_temp_file(data: bytes, extension: str = "bin") -> str:
    """
    Create a temporary file with the given data
    
    Args:
        data: Binary data to write to the file
        extension: File extension
        
    Returns:
        Path to the temporary file
    """
    try:
        # Create a temporary file with a random name
        fd, temp_path = tempfile.mkstemp(suffix=f".{extension}")
        
        # Write the data to the file
        with os.fdopen(fd, 'wb') as f:
            f.write(data)
        
        return temp_path
    
    except Exception as e:
        logger.error(f"Error creating temporary file: {e}")
        raise

def cleanup_temp_file(file_path: str) -> None:
    """
    Remove a temporary file
    
    Args:
        file_path: Path to the file to remove
    """
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception as e:
            logger.error(f"Error removing temporary file {file_path}: {e}")

def convert_audio_format(input_file: str, output_format: str = "wav") -> Optional[str]:
    """
    Convert an audio file to a different format using ffmpeg
    
    Args:
        input_file: Path to the input audio file
        output_format: Desired output format
        
    Returns:
        Path to the converted file or None if conversion failed
    """
    try:
        output_file = f"{os.path.splitext(input_file)[0]}.{output_format}"
        
        import subprocess
        result = subprocess.run([
            "ffmpeg", "-i", input_file, "-y", output_file
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"ffmpeg conversion error: {result.stderr}")
            return None
        
        return output_file
    
    except Exception as e:
        logger.error(f"Error converting audio format: {e}")
        return None

async def capture_screenshot(discord_client, channel_id: int) -> Optional[str]:
    """
    Capture a screenshot of an ongoing screen share in a Discord voice channel
    
    Args:
        discord_client: The Discord client instance
        channel_id: ID of the voice channel
        
    Returns:
        Path to the captured screenshot file or None if capture failed
    """
    try:
        # Get the voice channel by ID
        channel = discord_client.get_channel(channel_id)
        if not channel:
            logger.error(f"Could not find voice channel with ID {channel_id}")
            return None
        
        # Check if there are any users streaming in the channel
        streaming_members = [member for member in channel.members if member.voice and member.voice.self_stream]
        if not streaming_members:
            logger.info("No users are currently screen sharing in this channel")
            return None
        
        # For each streaming member, try to get their screen share data
        for member in streaming_members:
            try:
                # In a real implementation, this would use Discord's undocumented API
                # to capture the screen share stream. For this demo, we'll just create
                # a placeholder image to simulate this functionality.
                
                # Creating a placeholder temporary file for the screenshot
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot_path = f"temp_screenshot_{member.id}_{timestamp}.png"
                
                # In a real implementation, we would save the actual screenshot here
                # For this demo, we'll just log that we would capture it
                logger.info(f"Would capture screenshot of {member.display_name}'s screen share")
                
                # For the purposes of this demo, we'll just create an empty file
                with open(screenshot_path, 'wb') as f:
                    f.write(b'')
                
                return screenshot_path
                
            except Exception as e:
                logger.error(f"Error capturing screen share from {member.display_name}: {e}")
        
        return None
        
    except Exception as e:
        logger.error(f"Error during screen share capture: {e}")
        return None

async def analyze_image_with_vision_model(image_path: str, prompt: str, ollama_api, content_type: str = None) -> str:
    """
    Analyze an image using a vision-capable AI model in Ollama
    
    Args:
        image_path: Path to the image file
        prompt: Text prompt to guide the image analysis
        ollama_api: Instance of the OllamaAPI class
        content_type: Type of content detected in the image (youtube, chess, etc.)
        
    Returns:
        Analysis result as text
    """
    try:
        # Read the image file and encode as base64
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        # If the image is empty (in our demo case), generate a simulated analysis
        if len(image_data) == 0:
            logger.warning("Empty image file, generating simulated analysis for demo")
            
            # Generate appropriate simulated response based on content type
            if content_type == "youtube":
                return ("I can see you're watching a YouTube video. It looks like a documentary about "
                        "marine life. The narrator is currently explaining about coral reefs and their "
                        "importance to ocean ecosystems. I can see stunning footage of colorful fish "
                        "swimming through coral formations. The video appears to be from a nature channel "
                        "with high production quality.")
            
            elif content_type == "chess":
                return ("I can see you're playing chess. White has just moved the knight to f3, developing "
                        "a piece and controlling the center. Black has responded with e5, also fighting for "
                        "central control. The position looks balanced but with interesting tactical possibilities. "
                        "If white continues with d4, it would challenge black's central pawn and open lines for "
                        "the bishop. This appears to be in the early opening phase of the game.")
            
            elif content_type == "checkers":
                return ("I can see you're playing checkers. Red has just moved a piece to the king's row "
                        "and gotten a king. Black has several pieces in strong defensive positions. "
                        "Red seems to have a slight advantage with one more piece on the board. "
                        "Black should be careful about the potential double jump that red could execute "
                        "on the right side of the board.")
            
            elif content_type == "geoguesser":
                return ("Based on the screen share, I can see this is a GeoGuesser game. "
                        "I notice street signs in Cyrillic letters, which suggests we're in an Eastern European "
                        "or Russian-speaking country. The architecture features those distinctive onion domes "
                        "on a church in the distance, and I can see a sign that says 'Москва' which means 'Moscow'. "
                        "Given these clues, we're definitely in Russia, most likely in or near Moscow.")
            
            else:
                return ("I can see your screen share. It appears to be showing some content, "
                        "but I would need a more specific question to give you a detailed analysis.")
        
        # For a real implementation, we would use the Ollama API's multimodal capabilities
        # with a model that supports vision (like llava or bakllava)
        base64_image = base64.b64encode(image_data).decode('utf-8')
        
        # Select the appropriate system prompt based on content type
        system_prompt = None
        if content_type == "youtube":
            from config import YOUTUBE_SYSTEM_PROMPT
            system_prompt = YOUTUBE_SYSTEM_PROMPT
        elif content_type == "chess":
            from config import CHESS_SYSTEM_PROMPT
            system_prompt = CHESS_SYSTEM_PROMPT
        elif content_type == "checkers":
            from config import CHECKERS_SYSTEM_PROMPT
            system_prompt = CHECKERS_SYSTEM_PROMPT
        elif content_type == "geoguesser":
            from config import GEOGUESSER_SYSTEM_PROMPT
            system_prompt = GEOGUESSER_SYSTEM_PROMPT
        
        # Analyze the image using the vision model through Ollama API
        analysis = await ollama_api.generate_vision_response(prompt, base64_image, system_prompt)
        return analysis
        
    except Exception as e:
        logger.error(f"Error analyzing image: {e}")
        return "I'm having trouble analyzing what's on the screen right now."

def detect_content_type(image_path: str) -> str:
    """
    Detect the type of content in a screenshot
    
    Args:
        image_path: Path to the screenshot image
        
    Returns:
        String identifying the content type (youtube, chess, checkers, geoguesser, or None)
    """
    try:
        # For a real implementation, this would use image recognition to identify content
        # Here we'll just simulate detection with placeholder logic
        
        # If the file doesn't exist or is empty, return None
        if not os.path.exists(image_path) or os.path.getsize(image_path) == 0:
            return None
            
        # In a real implementation, we would:
        # 1. Use image recognition models to detect UI elements characteristic of each application
        # 2. Look for specific visual patterns (YouTube player controls, chess board grid, etc.)
        # 3. Use OCR to detect text that might indicate the content type
        
        # For this demonstration, we'll just return a random content type 
        # to simulate the detection process
        import random
        content_types = ["youtube", "chess", "checkers", "geoguesser", None]
        weights = [0.25, 0.25, 0.20, 0.20, 0.10]  # 10% chance of not recognizing anything
        
        # In a real implementation, this would be replaced with actual detection logic
        return random.choices(content_types, weights=weights, k=1)[0]
        
    except Exception as e:
        logger.error(f"Error detecting content type: {e}")
        return None

def analyze_conversation_intent(transcript: str) -> Tuple[bool, float]:
    """
    Analyze conversation to determine if the user is talking to Rupert (vs. about Rupert)
    
    Args:
        transcript: The transcribed text to analyze
        
    Returns:
        Tuple of (is_addressing_rupert, confidence_score)
    """
    # Convert to lowercase for easier matching
    text = transcript.lower()
    
    # Direct address indicators (high confidence)
    direct_patterns = [
        "hey rupert", "ok rupert", "okay rupert", "hi rupert", 
        "rupert,", "rupert?", "rupert!", "rupert can you", 
        "rupert could you", "rupert will you", "rupert please", 
        "can you rupert", "tell me rupert", "rupert tell me"
    ]
    
    # Question patterns when rupert is mentioned (medium confidence)
    question_patterns = [
        "what", "when", "where", "how", "why", "is", "are", "can", "could", 
        "would", "should", "did", "does", "do", "will", "has", "have"
    ]
    
    # Phrases indicating talking about Rupert, not to Rupert (negative indicators)
    about_patterns = [
        "rupert is", "rupert was", "about rupert", "that rupert", 
        "rupert doesn't", "rupert does not", "rupert didn't", 
        "rupert said", "rupert thinks", "i told rupert"
    ]
    
    # Check for direct address (highest confidence)
    for pattern in direct_patterns:
        if pattern in text:
            return True, 0.9
    
    # Check for negative indicators (talking about Rupert)
    for pattern in about_patterns:
        if pattern in text:
            return False, 0.8
    
    # If it contains "rupert" and a question word, it's likely addressing Rupert
    if "rupert" in text:
        for pattern in question_patterns:
            if pattern in text:
                return True, 0.7
        
        # Contains "rupert" but no question pattern - medium confidence
        return True, 0.5
    
    # No mention of Rupert - definitely not addressing Rupert
    return False, 0.0
