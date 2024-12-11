# services/pdf_analysis_service.py
import logging
import PyPDF2
import json
from openai import OpenAI
import os
import sys
from pathlib import Path
import requests
from utils.config_manager import get_base_dir, get_config_dir

class PDFAnalysisService:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.selected_model = self.config['api'].get('selected_model', 'llama')  # Default to llama (OpenRouter)
        self.client = None
        self.available = False
        
        # Initialize OpenAI client only if OpenAI is selected and API key is available
        if self.selected_model == 'openai':
            api_key = self.config['api'].get('openai_api_key')
            if api_key:
                try:
                    self.client = OpenAI(api_key=api_key)
                    self.available = True
                    self.logger.info("OpenAI client initialized successfully")
                except Exception as e:
                    self.logger.error(f"Failed to initialize OpenAI client: {str(e)}")
        else:
            # Check if OpenRouter API key is available
            if self.config['api'].get('openrouter_api_key'):
                self.available = True
                self.logger.info("OpenRouter configuration verified")
            else:
                self.logger.warning("OpenRouter API key not found")
        
        self.prompts_config = self.load_prompts_config()

    def load_prompts_config(self):
        try:
            config_dir = get_config_dir()
            prompts_file = os.path.join(config_dir, 'prompts.json')
            
            if os.path.exists(prompts_file):
                with open(prompts_file, 'r') as f:
                    return json.load(f)
            
            # Return default prompts if file doesn't exist
            return self._get_default_prompts()
            
        except Exception as e:
            self.logger.error(f"Error loading prompts config: {str(e)}")
            return self._get_default_prompts()

    def _get_default_prompts(self):
        """Return default prompts as fallback"""
        return {
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
        
    def extract_text_from_pdf(self, pdf_path):
        """Extract text from a PDF file."""
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
        return text

    def process_with_openrouter(self, system_prompt, user_prompt):
        """Process the request using OpenRouter API"""
        try:
            response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.config['api']['openrouter_api_key']}",
                    "HTTP-Referer": "localhost",
                    "X-Title": "AI Audio Creator",
                },
                json={
                    "model": "meta-llama/llama-3.2-3b-instruct:free",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 2000
                }
            )
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
        except Exception as e:
            self.logger.error(f"Error in OpenRouter API call: {str(e)}")
            raise

    def process_with_openai(self, system_prompt, user_prompt):
        """Process the request using OpenAI API"""
        if not self.client:
            raise ValueError("OpenAI client not initialized")
            
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                response_format={ "type": "json_object" },
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            self.logger.error(f"Error in OpenAI API call: {str(e)}")
            raise

    def analyze_script(self, script_text):
        """Analyze script text using the selected LLM."""
        if not self.available:
            error_msg = "No LLM service available. Please configure OpenAI or OpenRouter API key in preferences."
            self.logger.error(error_msg)
            return None

        try:
            # System prompt
            system_prompt = "You are a script analyzer. Analyze the given script for an audio play and provide structured output."

            # Formatting instructions
            formatting_instructions = """Without any additional text, output the analysis in the following JSON format:

{
  "script_analysis": [
    {
      "index": 1,
      "type": "character_line",
      "character": "CharacterName",
      "content": "Spoken sentence by the character."
    },
    {
      "index": 2,
      "type": "sfx",
      "content": "Description of the sound effect.",
      "duration": 3.0
    },
    {
      "index": 3,
      "type": "music",
      "content": "Description of the music.",
      "instrumental": "yes"
    },
    ...
  ],
  "needed_tracks": {
    "sfx",
    "music",
    "character1",
    ...
  },
  "voice_characteristics": {
    "CharacterName": {
      "Gender": "(male/female)",
      "Age": "(young/middle_aged/old)",
      "Accent": "(none/american/british/african/australian/indian)",
      "Voice Description": "(1 adjective)"
    },
    ...
  }
}

Here is the script to be analyzed:"""

            # Get the pre-prompt from config
            pre_prompt = self.prompts_config.get('script_analysis_pre', self._get_default_prompts()['script_analysis_pre'])

            # Combine the components
            full_prompt = f"{pre_prompt}\n\n{formatting_instructions}\n\n{script_text}"

            # Process with selected model
            if self.selected_model == 'openai':
                response_text = self.process_with_openai(system_prompt, full_prompt)
            else:
                response_text = self.process_with_openrouter(system_prompt, full_prompt)
            
            analysis = json.loads(response_text)
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing script: {str(e)}")
            return None
