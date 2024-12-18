from openai import OpenAI
import logging
import threading
import os
import json
import requests

class LLMService:
    def __init__(self, config, status_update_callback, output_update_callback):
        self.config = config
        self.client = OpenAI(api_key=self.config['api']['openai_api_key'])
        self.prompts_config = self.load_prompts_config()
        self.logger = logging.getLogger(__name__)
        self.status_update_callback = status_update_callback
        self.output_update_callback = output_update_callback
        self.selected_model = self.config['api'].get('selected_model', 'openai')

    def update_status(self, message):
        if self.status_update_callback:
            self.status_update_callback(message)

    def update_output(self, message):
        if self.output_update_callback:
            self.output_update_callback(message)
    
    def load_prompts_config(self):
        try:
            src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            base_dir = os.path.dirname(src_dir)
            prompts_file = os.path.join(base_dir, 'config', 'prompts.json')
            
            if os.path.exists(prompts_file):
                try:
                    with open(prompts_file, 'r') as f:
                        return json.load(f)
                except json.JSONDecodeError:
                    # If the file is empty or invalid, proceed to create default config
                    pass
            
            # Default prompts
            default_prompts = {
                'sfx_improvement': "Generate a good prompt for a generative AI Model which creates Sound Effects based on this sound effect description:",
                'music_improvement': "Generate a good prompt for a generative AI Model which creates Music based on this music piece description:",
                'script_analysis_pre': """I have a script for an audio play that I would like to analyze and categorize. Please analyze each line in the script and categorize it as follows:

1. Determine if the line is a spoken sentence by a character, a description of a sound effect (SFX), or a description of music. If the estimated length of a music piece is below 22s categorize it as SFX
2. If it is a spoken sentence by a character, identify the character's name.
3. If it is an SFX, estimate the duration of the sound (between 0.5 and 22 seconds).
4. If it is music, specify whether it is instrumental or with vocals. Use "instrumental": "yes" for instrumental music and "instrumental": "no" for music with vocals.
5. Maintain the order of the lines as they appear in the script, and assign an index to each line.
6. Include two additional parts in the JSON:
    - Needed Speaker Tracks: List all the characternames in the script. 
    - Voice Characteristics: Analyze the emotional content of the sentence and describe the voice characteristics of each speaker."""
            }

            # Ensure config directory exists
            os.makedirs(os.path.dirname(prompts_file), exist_ok=True)
            
            # Write default config
            with open(prompts_file, 'w') as f:
                json.dump(default_prompts, f, indent=2)
            
            return default_prompts
            
        except Exception as e:
            self.logger.error(f"Error loading prompts config: {str(e)}")
            return self._get_default_prompts()

    def _get_default_prompts(self):
        """Return default prompts as fallback"""
        return {
            'sfx_improvement': "Generate a good prompt for a generative AI Model which creates Sound Effects based on this sound effect description:",
            'music_improvement': "Generate a good prompt for a generative AI Model which creates Music based on this music piece description:",
            'script_analysis_pre': """I have a script for an audio play that I would like to analyze and categorize. Please analyze each line in the script and categorize it as follows:

1. Determine if the line is a spoken sentence by a character, a description of a sound effect (SFX), or a description of music. If the estimated length of a music piece is below 22s categorize it as SFX
2. If it is a spoken sentence by a character, identify the character's name.
3. If it is an SFX, estimate the duration of the sound (between 0.5 and 22 seconds).
4. If it is music, specify whether it is instrumental or with vocals. Use "instrumental": "yes" for instrumental music and "instrumental": "no" for music with vocals.
5. Maintain the order of the lines as they appear in the script, and assign an index to each line.
6. Include two additional parts in the JSON:
    - Needed Speaker Tracks: List all the characternames in the script. 
    - Voice Characteristics: Analyze the emotional content of the sentence and describe the voice characteristics of each speaker."""
        }

    def process_llm_request(self, prompt, is_music):
        """Process the LLM request in a separate thread."""
        def llm_thread():
            self.update_status("Processing with LLM...")
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

    def process_with_openrouter(self, messages):
        """Process the request using OpenRouter API"""
        try:
            response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.config['api']['openrouter_api_key']}",
                    "HTTP-Referer": "localhost",  # Update with your site URL in production
                    "X-Title": "AI Audio Creator",
                },
                json={
                    "model": "meta-llama/llama-3.2-3b-instruct:free",
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 500
                }
            )
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
        except Exception as e:
            self.logger.error(f"Error in OpenRouter API call: {str(e)}")
            raise

    def process_with_openai(self, messages, response_format=None):
        """Process the request using OpenAI API"""
        try:
            kwargs = {
                "model": "gpt-4o-mini",
                "messages": messages
            }
            if response_format:
                kwargs["response_format"] = response_format

            response = self.client.chat.completions.create(**kwargs)
            return response.choices[0].message.content
        except Exception as e:
            self.logger.error(f"Error in OpenAI API call: {str(e)}")
            raise

    def get_llm_response(self, system_message, user_message, response_format=None):
        """Get response from the selected LLM"""
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ]
        
        try:
            if self.selected_model == 'llama':
                return self.process_with_openrouter(messages)
            else:
                return self.process_with_openai(messages, response_format)
        except Exception as e:
            self.logger.error(f"Error getting LLM response: {str(e)}")
            raise

    def get_llm_sfx(self, prompt):
        """Generate an SFX description using the selected LLM."""
        self.logger.info("Generating SFX description...")
        try:
            return self.get_llm_response(
                "You are a sound design expert. Generate descriptive keywords for sound effects. Only output the keywords separated by commas, without any additional text.",
                f"{self.prompts_config.get('sfx_improvement', '')} {prompt}"
            )
        except Exception as e:
            self.logger.error(f"Error generating SFX description: {str(e)}")
            return None

    def get_llm_musicprompt(self, prompt):
        """Generate a music prompt using the selected LLM."""
        self.logger.info("Generating music prompt...")
        try:
            return self.get_llm_response(
                "You are a music description expert. Generate descriptive keywords for music pieces. Only output the keywords separated by commas, without any additional text.",
                f"{self.prompts_config.get('music_improvement', '')} {prompt}"
            )
        except Exception as e:
            self.logger.error(f"Error generating music prompt: {str(e)}")
            return None

    def analyze_script(self, script_text):
        try:
            system_prompt = "You are a script analyzer. Analyze the given script for an audio play and provide structured output."
            formatting_instructions = """Without any additional text, output the analysis in the following JSON format:..."""
            pre_prompt = self.prompts_config.get('script_analysis_pre', """...""")
            full_prompt = f"{pre_prompt}\n\n{formatting_instructions}\n\n{script_text}"
            
            response = self.get_llm_response(
                system_prompt,
                full_prompt,
                response_format={ "type": "json_object" } if self.selected_model == 'openai' else None
            )
            
            analysis = json.loads(response)
            return analysis
        except Exception as e:
            self.logger.error(f"Error analyzing script: {str(e)}")
            return None