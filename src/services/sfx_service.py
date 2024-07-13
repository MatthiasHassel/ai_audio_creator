import os
import re
from elevenlabs.client import ElevenLabs
import logging

class SFXService:
    def __init__(self, config, status_update_callback):
        self.config = config
        self.elevenlabs = ElevenLabs(api_key=self.config['api']['elevenlabs_api_key'])
        self.output_dir = self.config['sfx_gen']['output_dir']
        self.logger = logging.getLogger(self.__class__.__name__)
        self.status_update_callback = status_update_callback

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
                prompt_influence=0.3,
            )

            self.logger.info("Receiving and writing audio data...")
            self.update_status("Receiving and writing audio data...")
            with open(output_path, "wb") as f:
                for chunk in result:
                    f.write(chunk)
            return output_path
        except Exception as e:
            self.logger.error(f"Error generating sound effect: {str(e)}")
            self.update_status(f"Error generating sound effect: {str(e)}")
            return None

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