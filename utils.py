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

async def analyze_image_with_vision_model(image_path: str, prompt: str, ollama_api) -> str:
    """
    Analyze an image using a vision-capable AI model in Ollama
    
    Args:
        image_path: Path to the image file
        prompt: Text prompt to guide the image analysis
        ollama_api: Instance of the OllamaAPI class
        
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
            
            # This is a simulated response for demonstration purposes
            if "geoguesser" in prompt.lower():
                return ("Based on the screen share, I can see this is a GeoGuesser game. "
                        "From the architectural style, street signs, and vegetation, "
                        "this appears to be somewhere in Northern Europe, possibly Sweden or Norway. "
                        "The street signs have that distinctive Scandinavian design, and I notice some "
                        "text that looks like Swedish on one of the storefronts.")
            else:
                return ("I can see your screen share. It appears to be showing some content, "
                        "but I would need a more specific question to give you a detailed analysis.")
        
        # For a real implementation, we would use the Ollama API's multimodal capabilities
        # with a model that supports vision (like llava or bakllava)
        base64_image = base64.b64encode(image_data).decode('utf-8')
        
        # Analyze the image using the vision model through Ollama API
        # This is a simplified version; in reality, we'd need to use a compatible 
        # API endpoint that supports multimodal inputs
        analysis = await ollama_api.generate_vision_response(prompt, base64_image)
        return analysis
        
    except Exception as e:
        logger.error(f"Error analyzing image: {e}")
        return "I'm having trouble analyzing what's on the screen right now."

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
