import subprocess
import logging
import threading

class LlamaService:
    def __init__(self, config, status_update_callback, output_update_callback):
        self.config = config
        self.llama_model = self.config['llama']['model']
        self.logger = logging.getLogger(self.__class__.__name__)
        self.status_update_callback = status_update_callback
        self.output_update_callback = output_update_callback

    def update_status(self, message):
        if self.status_update_callback:
            self.status_update_callback(message)

    def update_output(self, message):
        if self.output_update_callback:
            self.output_update_callback(message)

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

    def process_llama_request(self, prompt, is_music):
        """Process the Llama request in a separate thread."""
        def llama_thread():
            self.update_status("Processing with Llama...")
            if is_music:
                result = self.get_llama_musicprompt(prompt)
            else:
                result = self.get_llama_sfx(prompt)
            
            if result:
                self.update_output(result)
                self.update_status("Llama processing completed.")
            else:
                self.update_output("Error: Failed to process input with Llama.")
                self.update_status("Llama processing failed.")

        thread = threading.Thread(target=llama_thread)
        thread.start()

    def get_llama_musicprompt(self, prompt):
        """Generate a music prompt using Llama."""
        self.logger.info("Generating music prompt with Llama...")
        music_prompt = ("At the end of this prompt you will find the description of a music piece. "
                      "Read this description carefully and think of ways to describe the music piece in the best possible way "
                      "with technical genre, style, theme and further adjectives. Then create a description of "
                      "the music piece with at least 5 words or expressions, separated by a comma. Only output those words or "
                      "expressions with not a single word before or after. Here is the music description:")
        full_prompt = f"{music_prompt} {prompt}"
        return self.run_llama(full_prompt)

    def get_llama_sfx(self, prompt):
        """Generate an SFX description using Llama."""
        self.logger.info("Generating SFX description with Llama...")
        sfx_prompt = ("At the end of this prompt you will find a detailed description of a sound effect. "
                      "Read this description carefully and think of ways to describe the sound in the best possible way "
                      "with technical aspects, timbre, volume level and further adjectives. Then create a description of "
                      "the sound with at least 5 words or expressions, separated by a comma. Only output those words or "
                      "expressions with not a single word before or after. Here is the sound description:")
        full_prompt = f"{sfx_prompt} {prompt}"
        return self.run_llama(full_prompt)