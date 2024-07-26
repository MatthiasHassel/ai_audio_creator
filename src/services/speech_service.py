import os
import re
import time
import requests
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs
import logging
from utils.file_utils import sanitize_filename

class SpeechService:
    def __init__(self, config, status_update_callback):
        self.config = config
        self.api_key = self.config['api']['elevenlabs_api_key']
        self.client = ElevenLabs(api_key=self.api_key)
        self.output_dir = self.config['speech_gen']['output_dir']
        self.logger = logging.getLogger(self.__class__.__name__)
        self.status_update_callback = status_update_callback
    
    def update_output_directory(self, new_output_dir):
        self.output_dir = new_output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def update_status(self, message):
        if self.status_update_callback:
            self.status_update_callback(message)

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
                    self.logger.warning(f"Voice object missing 'voice_id' or 'name' attribute: {voice}")

            return voice_list

        except Exception as e:
            self.logger.error(f"Failed to get available voices: {str(e)}")
            return []

    def get_next_file_number(self, voice_name):
        pattern = re.compile(fr"^{re.escape(voice_name)}_(\d+)\.mp3$")
        existing_numbers = [
            int(match.group(1))
            for file in os.listdir(self.output_dir)
            if (match := pattern.match(file))
        ]
        return max(existing_numbers, default=0) + 1

    def text_to_speech_file(self, text_prompt: str, voice_id: str):
        self.logger.info("Initializing speech generation...")
        try:
            self.logger.info("Sending request to ElevenLabs API...")
            response = self.client.text_to_speech.convert(
                voice_id=voice_id,
                optimize_streaming_latency="0",
                output_format="mp3_22050_32",
                text=text_prompt,
                model_id="eleven_multilingual_v2",
                voice_settings=VoiceSettings(
                    stability=0.0,
                    similarity_boost=1.0,
                    style=0.0,
                    use_speaker_boost=True,
                ),
            )

            self.logger.info("Ensuring output directory exists...")
            os.makedirs(self.output_dir, exist_ok=True)

            # Get the voice name from the voice_id
            voice_name = next((voice[0] for voice in self.get_available_voices() if voice[1] == voice_id), "Unknown")
            sanitized_voice_name = sanitize_filename(voice_name)

            # Get the next available number for this voice
            next_number = self.get_next_file_number(sanitized_voice_name)

            # Create the filename
            filename = f"{sanitized_voice_name}_{next_number}.mp3"
            save_file_path = os.path.join(self.output_dir, filename)

            self.logger.info("Receiving and writing audio data...")
            with open(save_file_path, "wb") as f:
                for chunk in response:
                    if chunk:
                        f.write(chunk)
            return save_file_path
        except Exception as e:
            self.logger.error(f"Failed to generate speech: {str(e)}")
            return None
    
    def process_speech_request(self, text_prompt: str, voice_id: str):
        return self.text_to_speech_file(text_prompt, voice_id)
    
    def generate_unique_voice(self, gender, accent, age, accent_strength, text):
        url = "https://api.elevenlabs.io/v1/voice-generation/generate-voice"
        
        # Ensure text length is between 100 and 1000 characters
        if len(text) < 100:
            text = text * (100 // len(text) + 1)  # Repeat text to meet minimum length
        text = text[:1000]  # Truncate if longer than 1000 characters
        
        payload = {
            "gender": gender,
            "accent": accent,
            "age": age,
            "accent_strength": float(accent_strength),  # Ensure this is a float
            "text": text
        }
        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()

            if response.status_code == 200:
                # Generate a unique filename
                filename = f"unique_voice_{int(time.time())}.mp3"
                file_path = os.path.join(self.output_dir, filename)

                with open(file_path, 'wb') as f:
                    f.write(response.content)

                return file_path
            else:
                self.logger.error(f"Failed to generate unique voice: {response.text}")
                return None

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error generating unique voice: {str(e)}")
            if hasattr(e.response, 'text'):
                self.logger.error(f"Response content: {e.response.text}")
            return None

    def process_unique_voice_request(self, gender, accent, age, accent_strength, text):
        return self.generate_unique_voice(gender, accent, age, accent_strength, text)
