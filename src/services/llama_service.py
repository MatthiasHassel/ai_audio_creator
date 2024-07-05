import subprocess
from services.base_service import BaseService

class LlamaService(BaseService):
    def __init__(self, app, config):
        super().__init__(app, config)
        self.llama_model = self.config['llama']['model']

    def run_llama(self, prompt):
        """Run the Llama model with the given prompt."""
        try:
            result = subprocess.run(
                ['ollama', 'run', self.llama_model],
                input=prompt,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            self.handle_error(f"Llama model error: {e.stderr}")
            return None

    def get_llama_musicprompt(self, prompt):
        """Generate a music prompt using Llama."""
        self.update_status("Generating music prompt with Llama...")
        full_prompt = f"Create a detailed music prompt based on the following description: {prompt}"
        response = self.run_llama(full_prompt)
        if response:
            self.update_status("Music prompt generated successfully.")
        return response

    def get_llama_sfx(self, prompt):
        """Generate an SFX description using Llama."""
        self.update_status("Generating SFX description with Llama...")
        sfx_prompt = ("At the end of this prompt you will find a detailed description of a sound effect. "
                      "Read this description carefully and think of ways to describe the sound in the best possible way "
                      "with technical aspects, timbre, volume level and further adjectives. Then create a description of "
                      "the sound with at least 5 words or expressions, separated by a comma. Only output those words or "
                      "expressions with not a single word before or after. Here is the sound description:")
        full_prompt = f"{sfx_prompt} {prompt}"
        response = self.run_llama(full_prompt)
        if response:
            self.update_status("SFX description generated successfully.")
        return response

    def get_llama_speech(self, prompt):
        """Generate a speech script using Llama."""
        self.update_status("Generating speech script with Llama...")
        speech_prompt = f"Create a natural-sounding speech script based on the following prompt: {prompt}"
        response = self.run_llama(speech_prompt)
        if response:
            self.update_status("Speech script generated successfully.")
        return response

    def process_llama_request(self, prompt, request_type):
        """Process a Llama request based on the type."""
        if request_type == "music":
            return self.get_llama_musicprompt(prompt)
        elif request_type == "sfx":
            return self.get_llama_sfx(prompt)
        elif request_type == "speech":
            return self.get_llama_speech(prompt)
        else:
            self.handle_error(f"Invalid request type: {request_type}")
            return None