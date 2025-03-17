
import os
import logging
import json
import base64
from typing import Optional, Dict, Any, List
import google.generativeai as genai

logger = logging.getLogger(__name__)

class GeminiAPI:
    def __init__(self):
        """Initialize the Gemini API client"""
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")

        genai.configure(api_key=self.api_key)
        self.text_model = genai.GenerativeModel('gemini-pro')
        self.vision_model = genai.GenerativeModel('gemini-pro-vision')

    async def generate_response(self, prompt: str, system_prompt: str = None) -> str:
        """Generate a response using Gemini"""
        try:
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            else:
                full_prompt = prompt

            response = await self.text_model.generate_content_async(full_prompt)
            return response.text

        except Exception as e:
            logger.error(f"Error with Gemini API: {e}")
            return "I'm having trouble thinking right now. Can you try again?"

    async def generate_vision_response(self, prompt: str, image_path: str, system_prompt: str = None) -> str:
        """Generate a response from vision model based on text prompt and image"""
        try:
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            else:
                full_prompt = prompt

            # Read image file
            with open(image_path, 'rb') as img_file:
                image_data = img_file.read()

            # Create image parts for the model
            response = await self.vision_model.generate_content_async([
                full_prompt,
                {"mime_type": "image/jpeg", "data": image_data}
            ])

            return response.text

        except Exception as e:
            logger.error(f"Error with Gemini Vision API: {e}")
            return "I'm having trouble analyzing the image right now."

    async def analyze_conversation_context(self, transcript: str, context: str = None) -> Dict[str, Any]:
        """Analyze if the conversation is directed at Rupert"""
        try:
            prompt = (
                f"Analyze this conversation transcript and determine if the person is talking TO Rupert "
                f"(the AI assistant) or just talking ABOUT Rupert to someone else. "
                f"Also determine if they're asking a question that requires a response.\n\n"
                f"Transcript: \"{transcript}\"\n\n"
                f"Return JSON with these fields: {{\"is_addressing_rupert\": true/false, "
                f"\"requires_response\": true/false, \"confidence\": 0-1, \"explanation\": \"brief explanation\"}}"
            )

            response = await self.text_model.generate_content_async(prompt)

            try:
                # Extract JSON from response
                json_match = response.text.strip()
                result = json.loads(json_match)
                return result
            except json.JSONDecodeError:
                # Fallback to basic detection
                return {
                    "is_addressing_rupert": "rupert" in transcript.lower(),
                    "requires_response": True,
                    "confidence": 0.5,
                    "explanation": "Basic keyword detection"
                }

        except Exception as e:
            logger.error(f"Error analyzing conversation context: {e}")
            return {
                "is_addressing_rupert": "rupert" in transcript.lower(),
                "requires_response": True,
                "confidence": 0.5,
                "explanation": "Error in analysis"
            }
