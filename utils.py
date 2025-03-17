import os
import tempfile
import wave
import logging
from typing import Optional

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
