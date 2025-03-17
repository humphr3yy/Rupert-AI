import discord
import logging
import asyncio
from discord.ext import commands
from typing import Dict, Optional

from transcription import Transcriber
from ai_integration import OllamaAPI
from tts import PiperTTS
from utils import create_temp_file, cleanup_temp_file
from config import COMMAND_PREFIX, OLLAMA_HOST, OLLAMA_PORT, OLLAMA_MODEL

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
        self.ollama_api = OllamaAPI(host=OLLAMA_HOST, port=OLLAMA_PORT, model=OLLAMA_MODEL)
        self.tts = PiperTTS()
        
        # Voice client tracking
        self.voice_clients: Dict[int, discord.VoiceClient] = {}
        
        # Speaker tracking (mapping user IDs to usernames)
        self.speakers = {}
        
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
                await ctx.send(f"Joined {channel.name}!")
                
                # Start listening and transcribing
                asyncio.create_task(self.listen_and_transcribe(ctx.guild, voice_client))
                
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
                        transcript = self.transcriber.transcribe(audio_data)
                        if transcript:
                            speaker = self.speakers.get(user_id, "Unknown User")
                            logger.info(f"{speaker}: {transcript}")
                            
                            # Check if the user is talking to Rupert
                            if self.is_talking_to_rupert(transcript):
                                await self.handle_rupert_interaction(voice_client, speaker, transcript)
            
            await asyncio.sleep(0.5)
    
    def is_talking_to_rupert(self, transcript: str) -> bool:
        """Check if the transcript contains a mention of Rupert"""
        return "rupert" in transcript.lower() or "ruppert" in transcript.lower()
    
    async def handle_rupert_interaction(self, voice_client, speaker: str, transcript: str):
        """Handle an interaction with Rupert by generating and playing a response"""
        logger.info(f"Detected interaction with Rupert from {speaker}: {transcript}")
        
        # Clean the transcript to use as a prompt for Ollama
        prompt = self.clean_transcript_for_prompt(transcript)
        
        try:
            # Get AI response from Ollama
            ai_response = await self.ollama_api.generate_response(prompt)
            logger.info(f"Ollama response: {ai_response}")
            
            # Convert AI response to speech using Piper TTS
            audio_file = await self.tts.text_to_speech(ai_response)
            
            # Play the audio response in the voice channel
            if voice_client.is_connected():
                source = discord.FFmpegPCMAudio(audio_file)
                voice_client.play(source)
                
                # Wait until the audio finishes playing
                while voice_client.is_playing():
                    await asyncio.sleep(0.1)
                
                # Clean up the temporary audio file
                cleanup_temp_file(audio_file)
            
        except Exception as e:
            logger.error(f"Error handling Rupert interaction: {e}")
    
    def clean_transcript_for_prompt(self, transcript: str) -> str:
        """Clean the transcript to make it a better prompt for Ollama"""
        # Remove "Rupert" mentions and prepare as a prompt
        cleaned = transcript.lower().replace("rupert", "").replace("ruppert", "").strip()
        
        # Remove filler words and clean up the prompt
        filler_words = ["um", "uh", "like", "you know", "basically", "actually"]
        for word in filler_words:
            cleaned = cleaned.replace(f" {word} ", " ")
        
        return cleaned.strip()
    
    def run(self):
        """Run the Discord bot"""
        self.bot.run(self.token)
