import os
import re
from elevenlabs.client import ElevenLabs
import logging
from mutagen.id3 import ID3, TIT2, COMM
from mutagen.mp3 import MP3

class SFXService:
    def __init__(self, config, status_update_callback):
        self.config = config
        self.elevenlabs = ElevenLabs(api_key=self.config['api']['elevenlabs_api_key'])
        self.output_dir = self.config['sfx_gen']['output_dir']
        self.logger = logging.getLogger(self.__class__.__name__)
        self.status_update_callback = status_update_callback

    def update_output_directory(self, new_output_dir):
        self.output_dir = new_output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def update_status(self, message):
        if self.status_update_callback:
            self.status_update_callback(message)

    def generate_sound_effect(self, text_prompt: str, duration: float = None):
        self.logger.info("Initializing sound effect generation...")

        sanitized_text_prompt = re.sub(r'[\\/*?:"<>|]', "", text_prompt)
        output_filename = f"sfx_{sanitized_text_prompt[:30]}.mp3"
        output_path = os.path.join(self.output_dir, output_filename)

        try:
            self.logger.info("Ensuring output directory exists...")
            os.makedirs(self.output_dir, exist_ok=True)

            self.logger.info("Sending request to ElevenLabs API...")
            self.update_status("Sending request to ElevenLabs API...")
            result = self.elevenlabs.text_to_sound_effects.convert(
                text=sanitized_text_prompt,
                duration_seconds=duration,
                prompt_influence=0.5,
            )

            self.logger.info("Receiving and writing audio data...")
            self.update_status("Receiving and writing audio data...")
            with open(output_path, "wb") as f:
                for chunk in result:
                    f.write(chunk)
            self.add_id3_tag(output_path, text_prompt, duration)
            return output_path
        except Exception as e:
            self.logger.error(f"Error generating sound effect: {str(e)}")
            self.update_status(f"Error generating sound effect: {str(e)}")
            return None

    def add_id3_tag(self, file_path, prompt, duration=None):
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
            self.logger.info(f"Successfully added ID3 tag to {file_path} with prompt: {prompt} and duration: {duration}")
        except Exception as e:
            self.logger.error(f"Failed to add ID3 tag: {str(e)}")

    def validate_duration(self, duration: str) -> float:
        """Validate and convert duration input."""
        try:
            duration_float = float(duration)
            if duration_float == 0:
                return None
            if 0.5 <= duration_float <= 22:
                return duration_float
            raise ValueError("Duration must be between 0.5 and 22 seconds.")
        except ValueError as e:
            self.logger.error(f"Invalid duration: {str(e)}")
            return None

    def process_sfx_request(self, text_prompt: str, duration: str):
        """Process an SFX generation request."""
        validated_duration = self.validate_duration(duration)
        if validated_duration is not None or duration == "0":
            return self.generate_sound_effect(text_prompt, validated_duration)
        else:
            self.logger.warning("Invalid duration. Please enter a valid duration (0.5-22s) or 0 for automatic.")
            return None