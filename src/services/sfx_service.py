import os
import re
import sys
from pathlib import Path
from elevenlabs.client import ElevenLabs
import logging
from mutagen.id3 import ID3, TIT2, COMM
from mutagen.mp3 import MP3

class SFXService:
    def __init__(self, config, status_update_callback):
        self.config = config
        self.status_update_callback = status_update_callback
        self.logger = logging.getLogger(self.__class__.__name__)
        self.available = False
        
        # Initialize ElevenLabs client if API key is available
        api_key = self.config['api'].get('elevenlabs_api_key')
        if not api_key:
            self.logger.warning("ElevenLabs API key not found in configuration. SFX generation will be disabled.")
            self.elevenlabs = None
        else:
            try:
                self.elevenlabs = ElevenLabs(api_key=api_key)
                self.available = True
                self.logger.info("SFX Service initialized successfully")
            except Exception as e:
                self.logger.error(f"Failed to initialize ElevenLabs client: {str(e)}")
                self.elevenlabs = None
        
        # Get SFX generation settings with defaults
        sfx_config = self.config.get('sfx_gen', {})
        if getattr(sys, 'frozen', False):
            # When bundled, use user's home directory
            self.output_dir = os.path.join(Path.home(), 'AI Audio Creator Projects', 'SFX')
        else:
            # In development, use config directory
            self.output_dir = sfx_config.get('output_dir', 
                os.path.join(Path.home(), 'AI Audio Creator Projects', 'SFX'))
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.min_duration = sfx_config.get('min_duration', 0.5)
        self.max_duration = sfx_config.get('max_duration', 22.0)

    def update_output_directory(self, new_output_dir):
        """Update the output directory and ensure it exists."""
        self.output_dir = new_output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def update_status(self, message):
        """Update status through callback if available."""
        if self.status_update_callback:
            self.status_update_callback(message)

    def generate_sound_effect(self, text_prompt: str, duration: float = None):
        """Generate a sound effect using ElevenLabs API."""
        if not self.available:
            error_msg = "SFX generation is not available. Please configure ElevenLabs API key in preferences."
            self.logger.error(error_msg)
            self.update_status(error_msg)
            return None

        self.logger.info("Initializing sound effect generation...")

        try:
            # Sanitize text prompt for filename
            sanitized_text_prompt = re.sub(r'[\\/*?:"<>|]', "", text_prompt)
            output_filename = f"sfx_{sanitized_text_prompt[:30]}.mp3"
            output_path = os.path.join(self.output_dir, output_filename)

            self.logger.info("Ensuring output directory exists...")
            os.makedirs(self.output_dir, exist_ok=True)

            self.logger.info("Sending request to ElevenLabs API...")
            self.update_status("Sending request to ElevenLabs API...")
            
            # Generate sound effect
            result = self.elevenlabs.text_to_sound_effects.convert(
                text=sanitized_text_prompt,
                duration_seconds=duration,
                prompt_influence=0.5,
            )

            # Save the audio file
            self.logger.info("Receiving and writing audio data...")
            self.update_status("Receiving and writing audio data...")
            with open(output_path, "wb") as f:
                for chunk in result:
                    f.write(chunk)
                    
            # Add metadata
            self.add_id3_tag(output_path, text_prompt, duration)
            return output_path
            
        except Exception as e:
            error_msg = f"Error generating sound effect: {str(e)}"
            self.logger.error(error_msg)
            self.update_status(error_msg)
            return None

    def add_id3_tag(self, file_path, prompt, duration=None):
        """Add ID3 tags to the generated audio file."""
        try:
            audio = MP3(file_path, ID3=ID3)

            if audio.tags is None:
                audio.add_tags()

            # Set the title
            audio.tags.add(TIT2(encoding=3, text="Generated SFX"))

            # Add the prompt as a comment
            audio.tags.add(COMM(encoding=3, lang='eng', desc='Prompt', text=prompt))

            # Add duration as a comment if provided
            if duration:
                duration_text = f"{duration}s"
                audio.tags.add(COMM(encoding=3, lang='eng', desc='Duration', text=duration_text))

            audio.save()
            self.logger.info(f"Successfully added ID3 tag to {file_path}")
        except Exception as e:
            self.logger.error(f"Failed to add ID3 tag: {str(e)}")

    def validate_duration(self, duration: str) -> float:
        """Validate and convert duration input."""
        try:
            # Handle automatic duration
            if duration == "0":
                return None
                
            # Convert to float and validate
            duration_float = float(duration)
            if self.min_duration <= duration_float <= self.max_duration:
                return duration_float
                
            raise ValueError(f"Duration must be between {self.min_duration} and {self.max_duration} seconds.")
            
        except ValueError as e:
            self.logger.error(f"Invalid duration: {str(e)}")
            return None

    def process_sfx_request(self, text_prompt: str, duration: str):
        """Process an SFX generation request."""
        if not self.available:
            error_msg = "SFX generation is not available. Please configure ElevenLabs API key in preferences."
            self.logger.error(error_msg)
            self.update_status(error_msg)
            return None

        try:
            # Validate input
            if not text_prompt:
                raise ValueError("Text prompt is required")
                
            validated_duration = self.validate_duration(duration)
            if validated_duration is not None or duration == "0":
                return self.generate_sound_effect(text_prompt, validated_duration)
            else:
                error_msg = f"Invalid duration. Please enter a valid duration ({self.min_duration}-{self.max_duration}s) or 0 for automatic."
                self.logger.warning(error_msg)
                self.update_status(error_msg)
                return None
                
        except Exception as e:
            error_msg = f"Error processing SFX request: {str(e)}"
            self.logger.error(error_msg)
            self.update_status(error_msg)
            return None
