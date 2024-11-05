from openai import OpenAI
import logging
import threading

class LLMService:
    def __init__(self, config, status_update_callback, output_update_callback):
        self.config = config
        self.client = OpenAI(api_key=self.config['api']['openai_api_key'])
        self.logger = logging.getLogger(self.__class__.__name__)
        self.status_update_callback = status_update_callback
        self.output_update_callback = output_update_callback

    def update_status(self, message):
        if self.status_update_callback:
            self.status_update_callback(message)

    def update_output(self, message):
        if self.output_update_callback:
            self.output_update_callback(message)

    def process_llm_request(self, prompt, is_music):
        """Process the LLM request in a separate thread."""
        def llm_thread():
            self.update_status("Processing with GPT-4...")
            if is_music:
                result = self.get_llm_musicprompt(prompt)
            else:
                result = self.get_llm_sfx(prompt)
            
            if result:
                self.update_output(result)
                self.update_status("LLM processing completed.")
            else:
                self.update_output("Error: Failed to process input with LLM.")
                self.update_status("LLM processing failed.")

        thread = threading.Thread(target=llm_thread)
        thread.start()

    def get_llm_musicprompt(self, prompt):
        """Generate a music prompt using GPT-4."""
        self.logger.info("Generating music prompt with GPT-4...")
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a music description expert. Generate descriptive keywords for music pieces. Only output the keywords separated by commas, without any additional text."},
                    {"role": "user", "content": f"Generate a good prompt for a generative AI Model which creates Music based on this music piece description: {prompt}"}
                ]
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            self.logger.error(f"Error generating music prompt: {str(e)}")
            return None

    def get_llm_sfx(self, prompt):
        """Generate an SFX description using GPT-4."""
        self.logger.info("Generating SFX description with GPT-4...")
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a sound design expert. Generate descriptive keywords for sound effects. Only output the keywords separated by commas, without any additional text."},
                    {"role": "user", "content": f"Generate a good prompt for a generative AI Model which creates Sound Effects based on this sound effect description: {prompt}"}
                ]
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            self.logger.error(f"Error generating SFX description: {str(e)}")
            return None