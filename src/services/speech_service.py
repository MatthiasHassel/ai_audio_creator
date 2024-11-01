import os
import re
import base64
import io
import requests
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs
import logging
from utils.file_utils import sanitize_filename
from mutagen.id3 import ID3, TIT2, COMM
from mutagen.mp3 import MP3

class SpeechService:
    def __init__(self, config, status_update_callback):
        self.config = config
        self.api_key = self.config['api']['elevenlabs_api_key']
        self.client = ElevenLabs(api_key=self.api_key)
        self.output_dir = self.config['speech_gen']['output_dir']
        self.logger = logging.getLogger(self.__class__.__name__)
        self.status_update_callback = status_update_callback
        self.preview_voices = []  # Store all preview voices
        self.current_preview_index = 0  # Track which preview we're currently playing
        self.preview_audio_files = []  # Store temporary preview files
        self.current_voice_description = None  # Store the description used to generate previews

    
    def update_output_directory(self, new_output_dir):
        self.output_dir = new_output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def update_status(self, message):
        if self.status_update_callback:
            self.status_update_callback(message)

    def ensure_voice_in_library(self, voice_id, voice_name):
        # First, check if the voice is already in the user's library
        user_voices = self.get_user_voices()
        if any(id == voice_id for _, id in user_voices):
            return True  # Voice is already in the library

        # If not, get the public_owner_id from available voices
        available_voices = self.get_available_voices()
        voice_info = next((v for v in available_voices if v['voice_id'] == voice_id), None)
        
        if not voice_info:
            self.logger.error(f"Voice {voice_id} not found in available voices.")
            return False

        public_owner_id = voice_info['public_owner_id']
        
        # Now add the voice to the library
        url = f"https://api.elevenlabs.io/v1/voices/add/{public_owner_id}/{voice_id}"
        payload = {"new_name": voice_name}
        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            self.logger.info(f"Voice '{voice_name}' (ID: {voice_id}) added to the library successfully.")
            return True
        except requests.RequestException as e:
            self.logger.error(f"Failed to add voice to library: {str(e)}")
            return False
    
    def get_available_voices(self):
        url = "https://api.elevenlabs.io/v1/shared-voices"
        querystring = {"category": "professional", "use_cases": "narrative_story", "language": "en"}
        headers = {"xi-api-key": self.api_key}

        try:
            response = requests.get(url, headers=headers, params=querystring)
            response.raise_for_status()
            data = response.json()
            return data.get('voices', [])
        except requests.RequestException as e:
            self.logger.error(f"Failed to fetch available voices: {str(e)}")
            return []
    
    def get_user_voices(self):
        url = "https://api.elevenlabs.io/v1/voices"
        headers = {"xi-api-key": self.api_key}

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            voices = response.json().get('voices', [])
            return [(voice['name'], voice['voice_id']) for voice in voices]
        except requests.RequestException as e:
            self.logger.error(f"Failed to fetch user voices: {str(e)}")
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
                output_format="mp3_44100_96",
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

            # Get the voice name from the user's voices
            user_voices = self.get_user_voices()
            voice_name = next((name for name, id in user_voices if id == voice_id), "Unknown")
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

            # Add ID3 tag with the prompt
            self.add_id3_tag(save_file_path, text_prompt)
            return save_file_path
        except Exception as e:
            self.logger.error(f"Failed to generate speech: {str(e)}", exc_info=True)
            return None
    
    def add_id3_tag(self, file_path, prompt):
        try:
            # Load the file
            audio = MP3(file_path, ID3=ID3)

            # Add ID3 tag if it doesn't exist
            if audio.tags is None:
                audio.add_tags()

            # Set the title
            audio.tags.add(TIT2(encoding=3, text="Generated Speech"))  # or "Generated SFX" or "Generated Music"

            # Add the prompt as a comment
            audio.tags.add(COMM(encoding=3, lang='eng', desc='Prompt', text=prompt))

            # Save the changes
            audio.save()

            self.logger.info(f"Successfully added ID3 tag to {file_path} with prompt: {prompt}")
        except Exception as e:
            self.logger.error(f"Failed to add ID3 tag: {str(e)}")

    def process_speech_request(self, text_prompt: str, voice_id: str):
        return self.text_to_speech_file(text_prompt, voice_id)
    
    def generate_voice_preview(self, voice_description: str, text: str):
        """Generate previews of unique voices."""
        self.logger.info(f"Generating voice previews with description: {voice_description}")
        self.current_voice_description = voice_description  # Store for later use

        try:
            # Ensure text meets minimum requirements
            if len(text) < 100:
                text = text * (100 // len(text) + 1)
            text = text[:1000]
            
            # Use the correct API endpoint for voice preview generation
            url = "https://api.elevenlabs.io/v1/text-to-voice/create-previews"
            
            headers = {
                "xi-api-key": self.api_key,
                "Content-Type": "application/json"
            }
            
            payload = {
                "voice_description": voice_description,
                "text": text
            }
            
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            if response.status_code == 200:
                response_data = response.json()
                previews = response_data.get('previews', [])
                
                if previews:
                    self.cleanup_previews()  # Clean up any existing previews
                    self.preview_voices = []
                    self.preview_audio_files = []
                    
                    # Process each preview
                    for i, preview in enumerate(previews):
                        voice_id = preview.get('generated_voice_id')
                        audio_base64 = preview.get('audio_base_64')
                        
                        if voice_id and audio_base64:
                            # Create a temporary file for this preview
                            temp_file = os.path.join(self.output_dir, f"temp_preview_{i}.mp3")
                            
                            # Decode and save the audio
                            audio_bytes = base64.b64decode(audio_base64)
                            with open(temp_file, 'wb') as f:
                                f.write(audio_bytes)
                            
                            self.preview_voices.append(voice_id)
                            self.preview_audio_files.append(temp_file)
                    
                    self.current_preview_index = 0
                    self.logger.info(f"Successfully generated {len(self.preview_voices)} voice previews")
                    
                    # Return the first preview file
                    return self.preview_audio_files[0] if self.preview_audio_files else None
                else:
                    self.logger.error("No previews received in API response")
                    return None
            else:
                self.logger.error(f"API request failed with status {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error generating voice previews: {str(e)}")
            return None

    def next_preview(self):
        """Switch to the next preview voice."""
        if self.preview_audio_files:
            self.current_preview_index = (self.current_preview_index + 1) % len(self.preview_audio_files)
            return self.preview_audio_files[self.current_preview_index]
        return None

    def previous_preview(self):
        """Switch to the previous preview voice."""
        if self.preview_audio_files:
            self.current_preview_index = (self.current_preview_index - 1) % len(self.preview_audio_files)
            return self.preview_audio_files[self.current_preview_index]
        return None

    def get_current_preview_id(self):
        """Get the voice ID of the currently selected preview."""
        if self.preview_voices and 0 <= self.current_preview_index < len(self.preview_voices):
            return self.preview_voices[self.current_preview_index]
        return None

    def save_preview_voice_to_library(self, voice_name: str):
        """Save the current preview voice to the user's voice library."""
        voice_id = self.get_current_preview_id()
        if not voice_id or not self.current_voice_description:
            self.logger.error("No preview voice ID or description available to save")
            return False
            
        try:
            url = "https://api.elevenlabs.io/v1/text-to-voice/create-voice-from-preview"
            
            headers = {
                "xi-api-key": self.api_key,
                "Content-Type": "application/json"
            }
            
            payload = {
                "voice_name": voice_name,
                "voice_description": self.current_voice_description,
                "generated_voice_id": voice_id,
                "labels": {},  # Optional, can be empty
                "played_not_selected_voice_ids": []  # Optional for RLHF
            }
            
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            if response.status_code == 200:
                self.logger.info(f"Voice '{voice_name}' successfully added to library")
                return True
            else:
                self.logger.error(f"Failed to add voice to library: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error saving voice to library: {str(e)}")
            return False
        finally:
            self.cleanup_previews()
            self.current_voice_description = None  # Clear stored description

    def cleanup_previews(self):
        """Clean up all temporary preview files and reset preview state."""
        for temp_file in self.preview_audio_files:
            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except Exception as e:
                    self.logger.error(f"Error removing temporary preview file: {str(e)}")
        
        self.preview_voices = []
        self.preview_audio_files = []
        self.current_preview_index = 0

    def discard_preview_voice(self):
        """Discard all preview voices and clean up."""
        self.cleanup_previews()
        self.logger.info("Voice previews discarded")