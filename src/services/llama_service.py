import subprocess
import logging

class LlamaService:
    def __init__(self, config, status_update_callback):
        self.config = config
        self.llama_model = self.config['llama']['model']
        self.logger = logging.getLogger(self.__class__.__name__)
        self.status_update_callback = status_update_callback

    def update_status(self, message):
        if self.status_update_callback:
            self.status_update_callback(message)

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
            self.logger.error(f"Llama model error: {e.stderr}")
            return None

    def get_llama_musicprompt(self, prompt):
        """Generate a music prompt using Llama."""
        self.logger.info("Generating music prompt with Llama...")
        full_prompt = f"Create a detailed music prompt based on the following description: {prompt}"
        response = self.run_llama(full_prompt)
        if response:
            self.logger.info("Music prompt generated successfully.")
        return response

    def get_llama_sfx(self, prompt):
        """Generate an SFX description using Llama."""
        self.logger.info("Generating SFX description with Llama...")
        sfx_prompt = ("At the end of this prompt you will find a detailed description of a sound effect. "
                      "Read this description carefully and think of ways to describe the sound in the best possible way "
                      "with technical aspects, timbre, volume level and further adjectives. Then create a description of "
                      "the sound with at least 5 words or expressions, separated by a comma. Only output those words or "
                      "expressions with not a single word before or after. Here is the sound description:")
        full_prompt = f"{sfx_prompt} {prompt}"
        response = self.run_llama(full_prompt)
        if response:
            self.logger.info("SFX description generated successfully.")
        return response