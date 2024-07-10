import os
import re
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs
from services.base_service import BaseService
from utils.file_utils import sanitize_filename

class SpeechService(BaseService):
    def __init__(self, app, config):
        super().__init__(app, config)
        self.api_key = self.config['api']['elevenlabs_api_key']
        self.client = ElevenLabs(api_key=self.api_key)
        self.output_dir = self.config['speech_gen']['output_dir']
    
    def get_available_voices(self):
        try:
            response = self.client.voices.get_all()
            
            if hasattr(response, 'voices'):
                voices = response.voices
            else:
                raise AttributeError("The API response does not contain a 'voices' attribute")

            voice_list = []
            for voice in voices:
                if hasattr(voice, 'voice_id') and hasattr(voice, 'name'):
                    voice_list.append((voice.name, voice.voice_id))
                else:
                    print(f"Warning: Voice object missing 'voice_id' or 'name' attribute: {voice}")

            return voice_list

        except Exception as e:
            self.handle_error(f"Failed to get available voices: {str(e)}")
            return []

    def get_next_file_number(self, voice_name):
        pattern = re.compile(f"^{re.escape(voice_name)}_(\d+)\.mp3$")
        existing_numbers = [
            int(match.group(1))
            for file in os.listdir(self.output_dir)
            if (match := pattern.match(file))
        ]
        return max(existing_numbers, default=0) + 1

    def text_to_speech_file(self, text_prompt: str, voice_id: str):
        self.update_status("Initializing speech generation...")
        try:
            self.update_status("Sending request to ElevenLabs API...")
            response = self.client.text_to_speech.convert(
                voice_id=voice_id,
                optimize_streaming_latency="0",
                output_format="mp3_22050_32",
                text=text_prompt,
                model_id="eleven_turbo_v2",
                voice_settings=VoiceSettings(
                    stability=0.0,
                    similarity_boost=1.0,
                    style=0.0,
                    use_speaker_boost=True,
                ),
            )

            self.update_status("Ensuring output directory exists...")
            os.makedirs(self.output_dir, exist_ok=True)

            # Get the voice name from the voice_id
            voice_name = next((voice[0] for voice in self.get_available_voices() if voice[1] == voice_id), "Unknown")
            sanitized_voice_name = sanitize_filename(voice_name)

            # Get the next available number for this voice
            next_number = self.get_next_file_number(sanitized_voice_name)

            # Create the filename
            filename = f"{sanitized_voice_name}_{next_number}.mp3"
            save_file_path = os.path.join(self.output_dir, filename)

            self.update_status("Receiving and writing audio data...")
            with open(save_file_path, "wb") as f:
                for chunk in response:
                    if chunk:
                        f.write(chunk)
            return save_file_path
        except Exception as e:
            self.handle_error(f"Failed to generate speech: {str(e)}")
            return None
    
    def process_speech_request(self, text_prompt: str, voice_id: str):
        return self.text_to_speech_file(text_prompt, voice_id)