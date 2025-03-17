import discord
import logging
import asyncio
import io
import os
import re
import time
import datetime
from discord.ext import commands
from typing import Dict, Optional, List, Tuple, Union, Any

from transcription import Transcriber
from ai_integration import GeminiAPI
from tts import PiperTTS
from utils import create_temp_file, cleanup_temp_file, capture_screenshot, analyze_image_with_vision_model, detect_content_type, analyze_conversation_intent
from config import (
    COMMAND_PREFIX, SYSTEM_PROMPT, VISION_SYSTEM_PROMPT, DM_SYSTEM_PROMPT, 
    TEXT_CHANNEL_SYSTEM_PROMPT, YOUTUBE_SYSTEM_PROMPT, CHESS_SYSTEM_PROMPT, 
    CHECKERS_SYSTEM_PROMPT, GEOGUESSER_SYSTEM_PROMPT, VISION_ENABLED, 
    VISION_CONVERSATION_THRESHOLD, SCREENSHOT_INTERVAL, YOUTUBE_DETECTION_ENABLED, 
    BOARD_GAMES_DETECTION_ENABLED, GEOGUESSER_DETECTION_ENABLED, CHESS_ANALYSIS_DEPTH, 
    PROACTIVE_COMMENTARY, INTENT_ANALYSIS_ENABLED, INTENT_CONFIDENCE_THRESHOLD,
    TEXT_ENABLED, MESSAGE_HISTORY_LIMIT, TEXT_COOLDOWN_SECONDS
)

logger = logging.getLogger(__name__)

class RupertBot:
    def __init__(self, token: str):
        """Initialize the Discord bot with necessary components and settings"""
        self.token = token
        
        # Set up Discord bot with required intents
        intents = discord.Intents.default()
        intents.message_content = True
        intents.voice_states = True
        
        self.bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)
        
        # Initialize components
        self.transcriber = Transcriber()
        self.ai_api = GeminiAPI()  # Using Gemini API instead of Ollama
        self.tts = PiperTTS()
        
        # Voice client tracking
        self.voice_clients: Dict[int, discord.VoiceClient] = {}
        
        # Speaker tracking (mapping user IDs to usernames)
        self.speakers = {}
        
        # Screenshare tracking
        self.screenshare_users: Dict[int, discord.Member] = {}  # Guild ID -> Member
        self.last_screenshot: Dict[int, str] = {}  # Guild ID -> Screenshot path
        self.screenshot_interval = SCREENSHOT_INTERVAL  # Seconds between screenshots
        self.vision_tasks: Dict[int, asyncio.Task] = {}  # Guild ID -> Screenshot task
        
        # Conversation context tracking
        self.conversation_history: Dict[int, List[Dict]] = {}  # Guild ID -> Conversation history
        
        # Set up event handlers
        self.setup_events()
        
        # Register commands
        self.register_commands()
    
    def setup_events(self):
        """Setup event handlers for the bot"""
        @self.bot.event
        async def on_ready():
            logger.info(f"{self.bot.user} has connected to Discord!")
            await self.bot.change_presence(activity=discord.Game(name="Listening..."))
        
        @self.bot.event
        async def on_voice_state_update(member, before, after):
            """Track when users start/stop screensharing"""
            if member.bot:
                return
                
            # Check if the user started screensharing
            if not before.self_stream and after.self_stream:
                logger.info(f"User {member.display_name} started screensharing")
                self.screenshare_users[member.guild.id] = member
                
                # Start screenshot capture task if vision is enabled
                if VISION_ENABLED and member.guild.id in self.voice_clients:
                    self.vision_tasks[member.guild.id] = asyncio.create_task(
                        self.capture_screenshare_periodically(member.guild.id, member)
                    )
            
            # Check if the user stopped screensharing
            elif before.self_stream and not after.self_stream:
                logger.info(f"User {member.display_name} stopped screensharing")
                if member.guild.id in self.screenshare_users and self.screenshare_users[member.guild.id].id == member.id:
                    del self.screenshare_users[member.guild.id]
                    
                    # Cancel screenshot task if it exists
                    if member.guild.id in self.vision_tasks:
                        self.vision_tasks[member.guild.id].cancel()
                        del self.vision_tasks[member.guild.id]
    
    def register_commands(self):
        """Register bot commands"""
        @self.bot.command(name="join", help="Join the voice channel you are in")
        async def join(ctx):
            if not ctx.author.voice:
                await ctx.send("You're not in a voice channel!")
                return
            
            channel = ctx.author.voice.channel
            guild_id = ctx.guild.id
            
            # Check if already connected to a voice channel in this guild
            if guild_id in self.voice_clients:
                await ctx.send("I'm already in a voice channel!")
                return
            
            try:
                # Connect to the voice channel
                voice_client = await channel.connect()
                self.voice_clients[guild_id] = voice_client
                
                # Initialize conversation history for this guild
                self.conversation_history[guild_id] = []
                
                await ctx.send(f"Joined {channel.name}!")
                
                # Start listening and transcribing
                asyncio.create_task(self.listen_and_transcribe(ctx.guild, voice_client))
                
                # Check if someone is already screensharing
                for member in channel.members:
                    if member.voice and member.voice.self_stream:
                        logger.info(f"Found active screenshare from {member.display_name}")
                        self.screenshare_users[guild_id] = member
                        if VISION_ENABLED:
                            self.vision_tasks[guild_id] = asyncio.create_task(
                                self.capture_screenshare_periodically(guild_id, member)
                            )
                        break
                
            except Exception as e:
                logger.error(f"Error joining voice channel: {e}")
                await ctx.send(f"Error joining voice channel: {e}")
        
        @self.bot.command(name="leave", help="Leave the voice channel")
        async def leave(ctx):
            guild_id = ctx.guild.id
            if guild_id in self.voice_clients:
                voice_client = self.voice_clients[guild_id]
                await voice_client.disconnect()
                del self.voice_clients[guild_id]
                
                # Clean up conversation history
                if guild_id in self.conversation_history:
                    del self.conversation_history[guild_id]
                
                # Clean up screenshare tracking
                if guild_id in self.screenshare_users:
                    del self.screenshare_users[guild_id]
                
                # Cancel screenshot task if it exists
                if guild_id in self.vision_tasks:
                    self.vision_tasks[guild_id].cancel()
                    del self.vision_tasks[guild_id]
                
                # Clean up last screenshot if exists
                if guild_id in self.last_screenshot and os.path.exists(self.last_screenshot[guild_id]):
                    cleanup_temp_file(self.last_screenshot[guild_id])
                    del self.last_screenshot[guild_id]
                
                await ctx.send("Left the voice channel!")
            else:
                await ctx.send("I'm not in a voice channel!")
    
    async def listen_and_transcribe(self, guild, voice_client):
        """Listen to the voice channel and transcribe speech"""
        logger.info(f"Started listening in guild: {guild.name}")
        
        # Map voice users to their usernames
        for member in voice_client.channel.members:
            if not member.bot:
                self.speakers[member.id] = member.display_name
        
        # Setup the voice receiver and start listening
        voice_client.listen(discord.WaveSink("./temp_audio"))
        
        while voice_client.is_connected():
            # Process audio data and detect speakers
            if hasattr(voice_client, 'voice_data'):
                for user_id, audio_data in voice_client.voice_data.items():
                    if user_id in self.speakers:
                        # Transcribe the audio
                        transcript = await self.transcriber.transcribe_async(audio_data)
                        if transcript:
                            speaker = self.speakers.get(user_id, "Unknown User")
                            logger.info(f"{speaker}: {transcript}")
                            
                            # Add to conversation history
                            self.add_to_conversation_history(guild.id, speaker, transcript)
                            
                            # Analyze if the user is talking to Rupert vs. about Rupert
                            await self.analyze_and_respond(voice_client, guild.id, user_id, speaker, transcript)
            
            await asyncio.sleep(0.5)
    
    def add_to_conversation_history(self, guild_id: int, speaker: str, transcript: str):
        """Add a message to the conversation history"""
        if guild_id not in self.conversation_history:
            self.conversation_history[guild_id] = []
            
        # Add the message with timestamp
        self.conversation_history[guild_id].append({
            "timestamp": time.time(),
            "speaker": speaker,
            "message": transcript
        })
        
        # Keep only the last 10 messages for context
        if len(self.conversation_history[guild_id]) > 10:
            self.conversation_history[guild_id] = self.conversation_history[guild_id][-10:]
    
    async def analyze_and_respond(self, voice_client, guild_id: int, user_id: int, speaker: str, transcript: str):
        """Analyze the transcript and respond if appropriate"""
        # Skip if the transcript doesn't contain "rupert" at all
        if "rupert" not in transcript.lower() and "ruppert" not in transcript.lower():
            return
            
        # Determine if the user is talking to Rupert or about Rupert
        is_addressing_rupert = False
        confidence = 0.0
        
        # Use the local utility function first (faster)
        is_addressing_rupert, confidence = analyze_conversation_intent(transcript)
        
        # If confidence is low and we have AI-based intent analysis enabled, use the more sophisticated method
        if INTENT_ANALYSIS_ENABLED and confidence < INTENT_CONFIDENCE_THRESHOLD:
            try:
                # Get conversation context for better analysis
                context = self.get_recent_conversation_context(guild_id)
                
                # Use the AI to analyze the conversation intent
                analysis = await self.ai_api.analyze_conversation_context(transcript, context)
                
                # Update our decision based on the AI analysis
                is_addressing_rupert = analysis.get("is_addressing_rupert", is_addressing_rupert)
                requires_response = analysis.get("requires_response", True)
                confidence = analysis.get("confidence", confidence)
                
                logger.info(f"AI conversation analysis: {analysis}")
                
                # If AI determined we don't need to respond, exit
                if not requires_response:
                    logger.info(f"AI determined no response needed for: '{transcript}'")
                    return
                    
            except Exception as e:
                logger.error(f"Error in AI conversation analysis: {e}")
                # Continue with the simple detection result in case of error
        
        # Check if we should respond based on our analysis
        if is_addressing_rupert and confidence >= INTENT_CONFIDENCE_THRESHOLD:
            # Check if this is related to a screenshare that needs visual analysis
            if VISION_ENABLED and self.is_asking_about_screen(transcript, guild_id):
                await self.handle_vision_interaction(voice_client, guild_id, speaker, transcript)
            else:
                # Normal Rupert interaction
                await self.handle_rupert_interaction(voice_client, speaker, transcript)
        else:
            logger.info(f"Detected mention of Rupert but not addressing Rupert directly (confidence: {confidence})")
    
    def get_recent_conversation_context(self, guild_id: int) -> str:
        """Get recent conversation context as a string"""
        if guild_id not in self.conversation_history or not self.conversation_history[guild_id]:
            return ""
            
        # Format the recent conversation history (last 5 messages)
        context_messages = self.conversation_history[guild_id][-5:]
        context = "\n".join([f"{msg['speaker']}: {msg['message']}" for msg in context_messages])
        return context
    
    def is_asking_about_screen(self, transcript: str, guild_id: int) -> bool:
        """Determine if the user is asking about what's on screen"""
        # Check if someone is screensharing in this guild
        if guild_id not in self.screenshare_users:
            return False
            
        # Keywords that suggest visual analysis is needed
        vision_keywords = [
            "screen", "showing", "look at", "can you see", "what's on", "what is on",
            "what do you see", "analyze this", "check this out", "geoguesser",
            "where am i", "where is this", "what country", "what place"
        ]
        
        lower_transcript = transcript.lower()
        for keyword in vision_keywords:
            if keyword in lower_transcript:
                return True
                
        return False
    
    async def capture_screenshare_periodically(self, guild_id: int, member: discord.Member):
        """Continuously capture screenshots of a user's screenshare at regular intervals"""
        try:
            logger.info(f"Starting periodic screenshot capture for {member.display_name}")
            
            # Keep track of when we last made a comment about each content type
            last_content_comment = {}
            
            # For proactive commentary, track time of last comment and content type
            last_comment_time = 0
            last_content_type = None
            
            while guild_id in self.voice_clients and guild_id in self.screenshare_users:
                # Capture the screenshot
                if self.bot.user:  # Make sure bot is fully initialized
                    voice_channel = member.voice.channel if member.voice else None
                    if voice_channel:
                        screenshot_path = await capture_screenshot(self.bot, voice_channel.id)
                        
                        if screenshot_path:
                            # Clean up previous screenshot if it exists
                            if guild_id in self.last_screenshot and os.path.exists(self.last_screenshot[guild_id]):
                                cleanup_temp_file(self.last_screenshot[guild_id])
                                
                            # Store the new screenshot path
                            self.last_screenshot[guild_id] = screenshot_path
                            logger.info(f"Updated screenshot for {member.display_name}")
                            
                            # If proactive commentary is enabled, analyze the content and potentially comment
                            if PROACTIVE_COMMENTARY:
                                voice_client = self.voice_clients.get(guild_id)
                                if voice_client and not voice_client.is_playing():  # Only if we're not already speaking
                                    try:
                                        # Detect content type
                                        content_type = detect_content_type(screenshot_path)
                                        
                                        current_time = time.time()
                                        # Decide if we should make a comment based on several factors:
                                        # 1. At least 60 seconds since last comment of any type
                                        # 2. Content type is recognized (not None)
                                        # 3. Either the content type changed OR it's been at least 3 minutes since 
                                        #    we last commented on this specific content type
                                        should_comment = (
                                            current_time - last_comment_time >= 60 and  # At least 60 seconds between any comments
                                            content_type is not None and
                                            (
                                                content_type != last_content_type or  # Content changed
                                                content_type not in last_content_comment or  # Never commented on this type
                                                current_time - last_content_comment.get(content_type, 0) >= 180  # 3 minutes since last comment
                                            )
                                        )
                                        
                                        if should_comment:
                                            # Create an appropriate prompt based on content type
                                            if content_type == "youtube" and YOUTUBE_DETECTION_ENABLED:
                                                prompt = "What's happening in this YouTube video right now? Provide a brief, conversational commentary."
                                                system_prompt = YOUTUBE_SYSTEM_PROMPT
                                            elif content_type == "chess" and BOARD_GAMES_DETECTION_ENABLED:
                                                prompt = "What's the current state of this chess game? Analyze the position and suggest a good move."
                                                system_prompt = CHESS_SYSTEM_PROMPT
                                            elif content_type == "checkers" and BOARD_GAMES_DETECTION_ENABLED:
                                                prompt = "What's the current state of this checkers game? Analyze the position and suggest a good move."
                                                system_prompt = CHECKERS_SYSTEM_PROMPT
                                            elif content_type == "geoguesser" and GEOGUESSER_DETECTION_ENABLED:
                                                prompt = "Based on what you can see in this GeoGuesser scene, where might this location be? Look for clues."
                                                system_prompt = GEOGUESSER_SYSTEM_PROMPT
                                            else:
                                                # Skip commentary for unknown content
                                                should_comment = False
                                            
                                            if should_comment:
                                                # Generate and speak a proactive comment
                                                response = await analyze_image_with_vision_model(
                                                    screenshot_path,
                                                    prompt,
                                                    self.ai_api,
                                                    content_type
                                                )
                                                
                                                # Convert to speech and play
                                                audio_file = await self.tts.text_to_speech(response)
                                                await self.play_audio_response(voice_client, audio_file)
                                                
                                                # Update tracking variables
                                                last_comment_time = current_time
                                                last_content_type = content_type
                                                last_content_comment[content_type] = current_time
                                                
                                                logger.info(f"Made proactive comment about {content_type}")
                                    except Exception as e:
                                        logger.error(f"Error in proactive commentary: {e}")
                
                # Wait before taking the next screenshot
                await asyncio.sleep(SCREENSHOT_INTERVAL)
                
        except asyncio.CancelledError:
            logger.info(f"Screenshot capture task for {member.display_name} was cancelled")
        except Exception as e:
            logger.error(f"Error in screenshot capture task: {e}")
    
    async def handle_vision_interaction(self, voice_client, guild_id: int, speaker: str, transcript: str):
        """Handle an interaction that requires analysis of a screenshare"""
        logger.info(f"Detected vision interaction from {speaker}: {transcript}")
        
        try:
            # Check if we have a recent screenshot
            if guild_id not in self.last_screenshot or not os.path.exists(self.last_screenshot[guild_id]):
                # Try to capture a screenshot now
                member = self.screenshare_users.get(guild_id)
                if not member or not member.voice or not member.voice.channel:
                    # No valid screenshare to analyze
                    ai_response = "I don't see anyone sharing their screen right now."
                else:
                    screenshot_path = await capture_screenshot(self.bot, member.voice.channel.id)
                    if screenshot_path:
                        self.last_screenshot[guild_id] = screenshot_path
                    else:
                        # Could not capture screenshot
                        ai_response = "I'm having trouble seeing what's on the screen right now."
                        
                        # Skip to TTS and playback
                        audio_file = await self.tts.text_to_speech(ai_response)
                        await self.play_audio_response(voice_client, audio_file)
                        return
            
            # We have a screenshot, now detect what kind of content it shows
            screenshot_path = self.last_screenshot[guild_id]
            content_type = detect_content_type(screenshot_path)
            logger.info(f"Detected content type in screenshare: {content_type}")
            
            # Clean and prepare the transcript
            clean_transcript = self.clean_transcript_for_prompt(transcript)
            
            # Create an appropriate prompt based on content type
            if content_type == "youtube" and YOUTUBE_DETECTION_ENABLED:
                vision_prompt = f"I'm watching a YouTube video. {speaker} asked: {clean_transcript}"
                vision_prompt += " Please analyze the video content, title, channel, and current scene."
                system_prompt = YOUTUBE_SYSTEM_PROMPT
                
            elif content_type == "chess" and BOARD_GAMES_DETECTION_ENABLED:
                vision_prompt = f"I'm looking at a chess board. {speaker} asked: {clean_transcript}"
                vision_prompt += f" Please analyze the board position, suggest good moves, and evaluate the position. Look ahead {CHESS_ANALYSIS_DEPTH} moves if possible."
                system_prompt = CHESS_SYSTEM_PROMPT
                
            elif content_type == "checkers" and BOARD_GAMES_DETECTION_ENABLED:
                vision_prompt = f"I'm looking at a checkers/draughts game. {speaker} asked: {clean_transcript}"
                vision_prompt += " Please analyze the board position, suggest good moves, and evaluate the position."
                system_prompt = CHECKERS_SYSTEM_PROMPT
                
            elif content_type == "geoguesser" and GEOGUESSER_DETECTION_ENABLED:
                vision_prompt = f"I'm playing GeoGuesser. {speaker} asked: {clean_transcript}"
                vision_prompt += " Please analyze the location clues such as architecture, road signs, vegetation, driving side, and other geographical markers."
                system_prompt = GEOGUESSER_SYSTEM_PROMPT
                
            else:
                # Generic prompt for unknown content
                vision_prompt = f"In this Discord screenshare: {clean_transcript}"
                system_prompt = VISION_SYSTEM_PROMPT
            
            # Analyze the screenshot with the appropriate vision model and system prompt
            ai_response = await analyze_image_with_vision_model(
                screenshot_path, 
                vision_prompt,
                self.ai_api,
                content_type
            )
            
            logger.info(f"Vision model response: {ai_response}")
            
            # Convert AI response to speech and play it
            audio_file = await self.tts.text_to_speech(ai_response)
            await self.play_audio_response(voice_client, audio_file)
            
        except Exception as e:
            logger.error(f"Error handling vision interaction: {e}")
            
            # Send a fallback response
            try:
                fallback = "I'm having trouble analyzing what's on the screen right now."
                audio_file = await self.tts.text_to_speech(fallback)
                await self.play_audio_response(voice_client, audio_file)
            except:
                logger.error("Failed to send fallback vision response")
    
    def is_talking_to_rupert(self, transcript: str) -> bool:
        """
        LEGACY METHOD: Check if the transcript contains a mention of Rupert
        This is now replaced by the more sophisticated analyze_and_respond method
        """
        return "rupert" in transcript.lower() or "ruppert" in transcript.lower()
    
    async def handle_rupert_interaction(self, voice_client, speaker: str, transcript: str):
        """Handle an interaction with Rupert by generating and playing a response"""
        logger.info(f"Handling direct interaction with Rupert from {speaker}: {transcript}")
        
        # Clean the transcript to use as a prompt for Gemini
        prompt = self.clean_transcript_for_prompt(transcript)
        
        try:
            # Get conversation context
            context = self.get_recent_conversation_context(
                voice_client.guild.id if hasattr(voice_client, 'guild') else 0
            )
            
            # Add context if available
            if context:
                full_prompt = f"Recent conversation:\n{context}\n\nCurrent question: {prompt}"
            else:
                full_prompt = prompt
            
            # Get AI response from Gemini
            ai_response = await self.ai_api.generate_response(full_prompt)
            logger.info(f"Gemini response: {ai_response}")
            
            # Convert AI response to speech and play it
            audio_file = await self.tts.text_to_speech(ai_response)
            await self.play_audio_response(voice_client, audio_file)
            
        except Exception as e:
            logger.error(f"Error handling Rupert interaction: {e}")
    
    async def play_audio_response(self, voice_client, audio_file: str):
        """Play an audio file in the voice channel and clean up afterwards"""
        if voice_client.is_connected():
            try:
                source = discord.FFmpegPCMAudio(audio_file)
                voice_client.play(source)
                
                # Wait until the audio finishes playing
                while voice_client.is_playing():
                    await asyncio.sleep(0.1)
            finally:
                # Clean up the temporary audio file
                cleanup_temp_file(audio_file)
    
    def clean_transcript_for_prompt(self, transcript: str) -> str:
        """Clean the transcript to make it a better prompt for Gemini"""
        # Remove "Rupert" mentions and prepare as a prompt
        lower_transcript = transcript.lower()
        
        # List of patterns to remove (variations of addressing Rupert)
        patterns_to_remove = [
            "hey rupert", "hi rupert", "hello rupert", "ok rupert", "okay rupert",
            "rupert,", "rupert.", "rupert?", "rupert!", "rupert can you", "rupert could you",
            "can you rupert", "rupert please"
        ]
        
        cleaned = lower_transcript
        for pattern in patterns_to_remove:
            cleaned = cleaned.replace(pattern, "")
        
        # Remove filler words and clean up the prompt
        filler_words = ["um", "uh", "like", "you know", "basically", "actually"]
        for word in filler_words:
            cleaned = cleaned.replace(f" {word} ", " ")
        
        # Clean up any double spaces and trim
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        return cleaned
    
    async def on_message(self, message):
        """
        Handle text messages in both DMs and server text channels
        This is called whenever a message is received
        """
        # Skip messages from bots (including ourselves)
        if message.author.bot:
            return
            
        # Skip if text interactions are disabled
        if not TEXT_ENABLED:
            return
            
        # Process the message
        is_dm = isinstance(message.channel, discord.DMChannel)
        is_mentioned = self.bot.user in message.mentions if self.bot.user else False
        contains_rupert = "rupert" in message.content.lower()
        
        if is_dm or is_mentioned or contains_rupert:
            # We should process this message
            logger.info(f"Processing {'DM' if is_dm else 'text channel'} message from {message.author.display_name}")
            
            # Log the message
            channel_name = "DM" if is_dm else f"#{message.channel.name}"
            logger.info(f"[{channel_name}] {message.author.display_name}: {message.content}")
            
            # Get message history for context
            context = await self.get_message_history(message.channel)
            
            # Generate response appropriate to the channel type
            response = None
            try:
                if is_dm:
                    # This is a DM, handle it accordingly
                    response = await self.handle_dm_message(message, context)
                else:
                    # This is a text channel message, check if we need to respond
                    if is_mentioned or (contains_rupert and await self.should_respond_to_text(message)):
                        response = await self.handle_text_channel_message(message, context)
                
                # Send the response if we have one
                if response:
                    # Split long messages if needed
                    if len(response) > 1900:  # Discord has a 2000 char limit
                        chunks = [response[i:i+1900] for i in range(0, len(response), 1900)]
                        for chunk in chunks:
                            await message.channel.send(chunk)
                    else:
                        await message.channel.send(response)
                        
            except Exception as e:
                logger.error(f"Error handling message: {e}")
                if is_dm:  # Only send error messages in DMs to avoid cluttering servers
                    await message.channel.send("I encountered an error processing your message. Please try again later.")
    
    async def handle_dm_message(self, message, context: str) -> str:
        """
        Handle a direct message from a user
        
        Args:
            message: The Discord message object
            context: String containing message history
            
        Returns:
            Response text to send back to the user
        """
        # Prepare prompt with DM-specific context
        prompt = (
            f"The following is a direct message from a Discord user named {message.author.display_name}:\n\n"
            f"Message: {message.content}\n\n"
        )
        
        # Add conversation history if available
        if context:
            prompt += f"Recent conversation history:\n{context}\n\n"
        
        # Send to Gemini with the DM system prompt
        response = await self.ai_api.generate_response(prompt, DM_SYSTEM_PROMPT)
        
        return response
    
    async def handle_text_channel_message(self, message, context: str) -> str:
        """
        Handle a message from a server text channel
        
        Args:
            message: The Discord message object
            context: String containing message history
            
        Returns:
            Response text to send back to the user
        """
        # Prepare prompt with text channel specific context
        guild_name = message.guild.name if message.guild else "Unknown Server"
        channel_name = message.channel.name if hasattr(message.channel, 'name') else "Unknown Channel"
        
        prompt = (
            f"The following message was sent in a Discord server text channel.\n"
            f"Server: {guild_name}\n"
            f"Channel: #{channel_name}\n"
            f"User: {message.author.display_name}\n\n"
            f"Message: {message.content}\n\n"
        )
        
        # Add conversation history if available
        if context:
            prompt += f"Recent conversation history in this channel:\n{context}\n\n"
        
        # Send to Gemini with the text channel system prompt
        response = await self.ai_api.generate_response(prompt, TEXT_CHANNEL_SYSTEM_PROMPT)
        
        return response
    
    async def get_message_history(self, channel, limit: int = None) -> str:
        """
        Get recent message history from a channel for context
        
        Args:
            channel: The Discord channel to get history from
            limit: Maximum number of messages to retrieve (uses config if None)
            
        Returns:
            Formatted message history as a string
        """
        if limit is None:
            limit = MESSAGE_HISTORY_LIMIT
            
        messages = []
        try:
            async for msg in channel.history(limit=limit):
                if not msg.author.bot:  # Skip bot messages in history
                    messages.append({
                        'author': msg.author.display_name,
                        'content': msg.content,
                        'timestamp': msg.created_at.isoformat()
                    })
        except Exception as e:
            logger.error(f"Error retrieving message history: {e}")
            return ""
            
        # Reverse to get chronological order
        messages.reverse()
        
        # Format the messages
        formatted_history = "\n".join([
            f"[{msg['timestamp']}] {msg['author']}: {msg['content']}"
            for msg in messages
        ])
        
        return formatted_history
    
    async def should_respond_to_text(self, message) -> bool:
        """
        Determine if we should respond to a text message that contains 'rupert'
        but doesn't explicitly mention the bot
        
        Args:
            message: The Discord message
            
        Returns:
            True if we should respond, False otherwise
        """
        # If the message explicitly mentions Rupert, analyze the intent
        # This is similar to voice chat intent analysis but for text
        is_addressing_rupert = False
        
        # Use the utility function to analyze intent
        is_addressing_rupert, confidence = analyze_conversation_intent(message.content)
        
        # If confidence is high enough, return immediately
        if confidence >= INTENT_CONFIDENCE_THRESHOLD:
            return is_addressing_rupert
            
        # If confidence is low and AI intent analysis is enabled, use it
        if INTENT_ANALYSIS_ENABLED:
            try:
                # Get recent message history for context
                context = await self.get_message_history(message.channel, 5)
                
                # Analyze using AI
                analysis = await self.ai_api.analyze_conversation_context(message.content, context)
                
                # Update based on AI analysis
                is_addressing_rupert = analysis.get("is_addressing_rupert", is_addressing_rupert)
                requires_response = analysis.get("requires_response", True)
                
                return is_addressing_rupert and requires_response
                
            except Exception as e:
                logger.error(f"Error in text message intent analysis: {e}")
                # Fall back to the simple analysis result
                
        return is_addressing_rupert
    
    def run(self):
        """Run the Discord bot"""
        # Register the message handler
        self.bot.add_listener(self.on_message, 'on_message')
        
        # Run the bot
        self.bot.run(self.token)
