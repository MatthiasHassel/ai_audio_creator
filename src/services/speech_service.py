import os
import uuid
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs
from services.base_service import BaseService

class SpeechService(BaseService):
    def __init__(self, app, config):
        super().__init__(app, config)
        self.api_key = self.config['api']['elevenlabs_api_key']
        
        print(f"SpeechService API Key: {self.api_key[:5]}...")
        
        self.client = ElevenLabs(api_key=self.api_key)
        self.output_dir = self.config['speech_gen']['output_dir']

    def get_available_voices(self):
        try:
            response = self.client.voices.get_all()
            
            # The response should have a 'voices' attribute containing a list of voice objects
            if hasattr(response, 'voices'):
                voices = response.voices
            else:
                raise AttributeError("The API response does not contain a 'voices' attribute")

            voice_list = []
            for voice in voices:
                # Each voice object should have 'voice_id' and 'name' attributes
                if hasattr(voice, 'voice_id') and hasattr(voice, 'name'):
                    voice_list.append((voice.name, voice.voice_id))
                else:
                    print(f"Warning: Voice object missing 'voice_id' or 'name' attribute: {voice}")

            return voice_list

        except Exception as e:
            self.handle_error(f"Failed to get available voices: {str(e)}")
            return []

    def text_to_speech_file(self, text_prompt: str, voice_id: str):
        self.update_status("Generating speech...")
        try:
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

            os.makedirs(self.output_dir, exist_ok=True)
            save_file_path = os.path.join(self.output_dir, f"{uuid.uuid4()}.mp3")

            with open(save_file_path, "wb") as f:
                for chunk in response:
                    if chunk:
                        f.write(chunk)

            self.update_status(f"Audio saved to {save_file_path}")
            return save_file_path
        except Exception as e:
            self.handle_error(f"Failed to generate speech: {str(e)}")
            return None

    def process_speech_request(self, text_prompt: str, voice_id: str):
        return self.text_to_speech_file(text_prompt, voice_id)