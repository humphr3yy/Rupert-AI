import aiohttp
import logging
import json
import base64
from typing import Optional, Dict, Any, List
import config

logger = logging.getLogger(__name__)

class OllamaAPI:
    def __init__(self, host: str = "localhost", port: int = 11434, model: str = "llama2", vision_model: str = "llava"):
        """
        Initialize the Ollama API client
        
        Args:
            host: Hostname where Ollama is running
            port: Port number for Ollama API
            model: The model to use for text generation
            vision_model: The model to use for vision tasks
        """
        self.base_url = f"http://{host}:{port}"
        self.model = model
        self.vision_model = vision_model
        self.generate_endpoint = f"{self.base_url}/api/generate"
        self.chat_endpoint = f"{self.base_url}/api/chat"
    
    async def generate_response(self, prompt: str, system_prompt: str = None) -> str:
        """
        Generate a response from Ollama based on the given prompt
        
        Args:
            prompt: The text prompt to send to the model
            system_prompt: Optional custom system prompt to override the default
            
        Returns:
            Generated text response
        """
        try:
            if system_prompt is None:
                system_prompt = config.SYSTEM_PROMPT
                
            payload = {
                "model": self.model,
                "prompt": prompt,
                "system": system_prompt,
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
    
    async def generate_vision_response(self, prompt: str, base64_image: str) -> str:
        """
        Generate a response from a vision model based on text prompt and image
        
        Args:
            prompt: Text prompt to guide the image analysis
            base64_image: Base64-encoded image data
            
        Returns:
            Generated text response describing the image
        """
        try:
            # Simplified implementation - real implementation would use appropriate
            # multimodal API endpoints for Ollama's vision models
            
            # Using the chat endpoint with multimodal data
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image", "image": base64_image}
                    ]
                }
            ]
            
            payload = {
                "model": self.vision_model,
                "messages": messages,
                "stream": False
            }
            
            # Using the chat endpoint for multimodal models
            async with aiohttp.ClientSession() as session:
                async with session.post(self.chat_endpoint, json=payload) as response:
                    if response.status != 200:
                        error_msg = await response.text()
                        logger.error(f"Ollama Vision API error: {response.status} - {error_msg}")
                        return "I'm having trouble analyzing the image right now."
                    
                    result = await response.json()
                    return result.get("message", {}).get("content", "").strip()
                    
        except aiohttp.ClientError as e:
            logger.error(f"Error connecting to Ollama Vision API: {e}")
            return "I'm unable to analyze the image right now. Please check if Ollama is running with a vision-capable model."
        except Exception as e:
            logger.error(f"Unexpected error with Ollama Vision API: {e}")
            return "I encountered an issue while trying to analyze the image."
    
    async def analyze_conversation_context(self, transcript: str, context: str = None) -> Dict[str, Any]:
        """
        Analyze a conversation transcript to determine if it's addressed to Rupert
        and extract relevant context
        
        Args:
            transcript: The transcribed speech to analyze
            context: Optional additional context about the conversation
            
        Returns:
            Dictionary with analysis results including whether the user is addressing Rupert
        """
        try:
            prompt = (
                f"Analyze this conversation transcript and determine if the person is talking TO Rupert "
                f"(the AI assistant) or just talking ABOUT Rupert to someone else. "
                f"Also determine if they're asking a question that requires a response.\n\n"
                f"Transcript: \"{transcript}\"\n\n"
                f"Return JSON with these fields: {{\"is_addressing_rupert\": true/false, "
                f"\"requires_response\": true/false, \"confidence\": 0-1, \"explanation\": \"brief explanation\"}}"
            )
            
            # Use a more analytical system prompt for this task
            system_prompt = (
                "You are an AI language analyzer that evaluates conversation transcripts "
                "to determine who is being addressed. Respond only with the requested JSON format."
            )
            
            response = await self.generate_response(prompt, system_prompt)
            
            # Try to parse the response as JSON
            try:
                # Find JSON in the response (the model might wrap it in text)
                import re
                json_match = re.search(r'({.*})', response.replace('\n', ' '))
                if json_match:
                    result = json.loads(json_match.group(1))
                    return result
                else:
                    # Fallback to simpler analysis
                    logger.warning("Could not extract JSON from analyzer response")
                    return {"is_addressing_rupert": "rupert" in transcript.lower(), 
                            "requires_response": True, 
                            "confidence": 0.5, 
                            "explanation": "Basic keyword detection"}
            except json.JSONDecodeError:
                logger.warning("Could not parse JSON from analyzer response")
                return {"is_addressing_rupert": "rupert" in transcript.lower(), 
                        "requires_response": True, 
                        "confidence": 0.5, 
                        "explanation": "Basic keyword detection"}
                
        except Exception as e:
            logger.error(f"Error analyzing conversation context: {e}")
            # Conservative default is to assume we're being addressed if Rupert is mentioned
            return {"is_addressing_rupert": "rupert" in transcript.lower(), 
                    "requires_response": True, 
                    "confidence": 0.5, 
                    "explanation": "Error in analysis, defaulting to keyword detection"}
