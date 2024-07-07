import os
import uuid
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs
from services.base_service import BaseService

class SpeechService(BaseService):
    def __init__(self, app, config):
        super().__init__(app, config)
        self.api_key = self.config['api']['elevenlabs_api_key']
        self.client = ElevenLabs(api_key=self.api_key)
        self.output_dir = self.config['speech_gen']['output_dir']

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
            save_file_path = os.path.join(self.output_dir, f"{uuid.uuid4()}.mp3")

            self.update_status("Receiving and writing audio data...")
            with open(save_file_path, "wb") as f:
                for chunk in response:
                    if chunk:
                        f.write(chunk)

            self.update_output(f"Speech generated successfully. File saved to: {save_file_path}")
            return save_file_path
        except Exception as e:
            self.handle_error(f"Failed to generate speech: {str(e)}")
            return None

    # ... (rest of the class remains the same)

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
        
    def process_speech_request(self, text_prompt: str, voice_id: str):
        return self.text_to_speech_file(text_prompt, voice_id)