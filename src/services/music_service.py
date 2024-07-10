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
        return subprocess.Popen(['npm', 'run', 'dev'], cwd=self.config['music_gen']['api_directory'])

    def generate_audio_by_prompt(self, payload):
        """Generate audio based on the given prompt."""
        url = f"{self.base_url}/api/generate"
        response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'})
        return response.json()

    def get_audio_information(self, audio_ids):
        """Get information about generated audio."""
        self.update_status("Getting audio information...\nThis can take several minutes.")
        url = f"{self.base_url}/api/get?ids={audio_ids}"
        response = requests.get(url)
        return response.json()

    def download_audio(self, url, output_filename):
        """Download the generated audio file."""
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
        response = requests.get(url, headers=headers, stream=True)

        if response.status_code == 200:
            with open(output_filename, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            return True
        return False

    def create_song(self, text_prompt, make_instrumental):
        """Create a song based on the given text prompt."""
        self.update_status("Starting music generation process...")
        api_process = self.start_api()
        time.sleep(3)  # Wait for API to start
        self.update_status("API started. Generating song...")

        sanitized_text_prompt = re.sub(r'[\\/*?:"<>|]', "", text_prompt)[:30]
        output_filename = os.path.join(self.output_dir, f"music_{sanitized_text_prompt}.mp3")

        try:
            # Ensure output directory exists
            os.makedirs(self.output_dir, exist_ok=True)

            data = self.generate_audio_by_prompt({
                "prompt": text_prompt,
                "make_instrumental": make_instrumental,
                "wait_audio": False
            })

            ids = f"{data[0]['id']},{data[1]['id']}"

            for i in range(60):  # Wait up to 5 minutes
                self.update_status(f"Waiting for audio to be ready... (Attempt {i+1}/60)")
                data = self.get_audio_information(ids)
                if data[0]["status"] == 'streaming':
                    break
                time.sleep(5)

            if data[0]["status"] != 'streaming':
                raise Exception("Timeout waiting for audio to be ready")

            self.update_status("Audio ready. Downloading...")
            url = data[0]['audio_url']
            if self.download_audio(url, output_filename):
                return output_filename
            else:
                raise Exception("Failed to download audio file")

        except Exception as e:
            self.handle_error(e)
            return None
        finally:
            api_process.terminate()
            self.update_status("Music generation process completed.")

    def process_music_request(self, text_prompt: str, make_instrumental: bool):
        """Process a music generation request."""
        return self.create_song(text_prompt, make_instrumental)