import os
import time
import requests
import re
import subprocess
from services.base_service import BaseService

class MusicService(BaseService):
    def __init__(self, app, config):
        super().__init__(app, config)
        self.base_url = self.config['api']['base_url']
        self.output_dir = self.config['music_gen']['output_dir']

    def start_api(self):
        """Start the API server."""
        self.update_status("Starting API server...")
        api_process = subprocess.Popen(['npm', 'run', 'dev'], cwd=self.config['music_gen']['api_directory'])
        
        if self.wait_for_api_start():
            self.update_status("API started successfully.")
            return api_process
        else:
            self.update_status("Failed to start API server.")
            api_process.terminate()
            return None

    def wait_for_api_start(self, timeout=30, interval=0.5):
        """
        Wait for the API to start and become responsive.
        
        :param timeout: Maximum time to wait in seconds
        :param interval: Time between checks in seconds
        :return: True if API is responsive, False otherwise
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f'{self.base_url}/api/get_limit', timeout=1)
                if response.status_code == 200:
                    return True
            except requests.RequestException:
                pass
            time.sleep(interval)
        return False
    
    def generate_audio_by_prompt(self, payload):
        """Generate audio based on the given prompt."""
        url = f"{self.base_url}/api/generate"
        try:
            response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'})
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            self.handle_error(f"Failed to generate audio: {str(e)}")
            return None

    def get_audio_information(self, audio_ids):
        """Get information about generated audio."""
        self.update_status("Fetching audio information...")
        url = f"{self.base_url}/api/get"
        try:
            response = requests.get(url, params={'ids': audio_ids})
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            self.handle_error(f"Failed to get audio information: {str(e)}")
            return None

    def download_audio(self, url, output_path):
        """Download the audio file."""
        self.update_status(f"Downloading audio...")
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            with open(output_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)
            return True
        except requests.RequestException as e:
            self.handle_error(f"Failed to download audio: {str(e)}")
            return False

    def create_song(self, text_prompt, make_instrumental):
        """Create a song based on the text prompt."""
        self.update_status("Starting music generation process...")
        api_process = self.start_api()
        if api_process is None:
            self.handle_error("Failed to start API server.")
            return None

        self.update_status("API started. Generating song...")

        try:
            os.makedirs(self.output_dir, exist_ok=True)

            data = self.generate_audio_by_prompt({
                "prompt": text_prompt,
                "make_instrumental": make_instrumental,
                "wait_audio": False
            })

            if data is None:
                raise Exception("Failed to generate audio")

            ids = f"{data[0]['id']},{data[1]['id']}"

            # Implement exponential backoff for polling
            max_attempts = 30
            base_wait_time = 2
            for attempt in range(max_attempts):
                self.update_status(f"Waiting for audio to be ready... (Attempt {attempt+1}/{max_attempts})")
                data = self.get_audio_information(ids)
                if data is None:
                    raise Exception("Failed to get audio information")
                if data[0]["status"] == 'streaming':
                    break
                wait_time = min(base_wait_time * 2 ** attempt, 60)  # Cap at 60 seconds
                time.sleep(wait_time)
            else:
                raise Exception("Timeout waiting for audio to be ready")

            # Retrieve the song title
            song_title = data[0].get('title', 'untitled')
            sanitized_title = re.sub(r'[\\/*?:"<>|]', "", song_title)
            output_filename = os.path.join(self.output_dir, f"music_{sanitized_title}.mp3")

            self.update_status("Audio ready. Downloading...")
            url = data[0]['audio_url']
            if self.download_audio(url, output_filename):
                return output_filename
            else:
                raise Exception("Failed to download audio file")

        except Exception as e:
            self.handle_error(str(e))
            return None
        finally:
            api_process.terminate()
            self.update_status("Music generation process completed.")
        
    def process_music_request(self, text_prompt: str, make_instrumental: bool):
        """Process a music generation request."""
        return self.create_song(text_prompt, make_instrumental)