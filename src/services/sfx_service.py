import os
import re
from elevenlabs.client import ElevenLabs
from services.base_service import BaseService

class SFXService(BaseService):
    def __init__(self, app, config):
        super().__init__(app, config)
        self.elevenlabs = ElevenLabs(api_key=self.config['api']['elevenlabs_api_key'])
        self.output_dir = self.config['sfx_gen']['output_dir']

    def generate_sound_effect(self, text_prompt: str, duration: float = None):
        self.update_status("Generating sound effects...")

        # Remove invalid characters from the text prompt to create a valid filename
        sanitized_text_prompt = re.sub(r'[\\/*?:"<>|]', "", text_prompt)

        # Set output file path
        output_filename = f"sfx_{sanitized_text_prompt[:30]}.mp3"
        output_path = os.path.join(self.output_dir, output_filename)

        try:
            # Ensure output directory exists
            os.makedirs(self.output_dir, exist_ok=True)

            result = self.elevenlabs.text_to_sound_effects.convert(
                text=sanitized_text_prompt,
                duration_seconds=duration,
                prompt_influence=0.3,
            )

            with open(output_path, "wb") as f:
                for chunk in result:
                    f.write(chunk)

            self.update_status(f"Audio saved to {output_path}")
            return output_path
        except Exception as e:
            self.handle_error(e)
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
            self.handle_error(e)
            return None

    def process_sfx_request(self, text_prompt: str, duration: str):
        """Process an SFX generation request."""
        validated_duration = self.validate_duration(duration)
        if validated_duration is not None or duration == "0":
            return self.generate_sound_effect(text_prompt, validated_duration)
        else:
            self.update_status("Invalid duration. Please enter a valid duration (0.5-22s) or 0 for automatic.")
            return None