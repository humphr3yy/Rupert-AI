import aiohttp
import logging
import json
from typing import Optional

logger = logging.getLogger(__name__)

class OllamaAPI:
    def __init__(self, host: str = "localhost", port: int = 11434, model: str = "llama2"):
        """
        Initialize the Ollama API client
        
        Args:
            host: Hostname where Ollama is running
            port: Port number for Ollama API
            model: The model to use for generation
        """
        self.base_url = f"http://{host}:{port}"
        self.model = model
        self.generate_endpoint = f"{self.base_url}/api/generate"
    
    async def generate_response(self, prompt: str) -> str:
        """
        Generate a response from Ollama based on the given prompt
        
        Args:
            prompt: The text prompt to send to the model
            
        Returns:
            Generated text response
        """
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "system": "You are Rupert, a friendly and helpful AI assistant in a Discord voice channel. "
                          "Keep your responses concise and natural for voice conversations.",
                "stream": False
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.generate_endpoint, json=payload) as response:
                    if response.status != 200:
                        error_msg = await response.text()
                        logger.error(f"Ollama API error: {response.status} - {error_msg}")
                        return "I'm having trouble thinking right now. Can you try again?"
                    
                    result = await response.json()
                    return result.get("response", "").strip()
        
        except aiohttp.ClientError as e:
            logger.error(f"Error connecting to Ollama API: {e}")
            return "I'm unable to connect to my thinking module right now. Please check if Ollama is running."
        except Exception as e:
            logger.error(f"Unexpected error with Ollama API: {e}")
            return "Something unexpected happened. Can you try again later?"
