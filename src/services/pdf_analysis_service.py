# services/pdf_analysis_service.py
import logging
import PyPDF2
import json
from openai import OpenAI
import os

class PDFAnalysisService:
    def __init__(self, config):
        self.config = config
        self.client = OpenAI(api_key=self.config['api']['openai_api_key'])
        self.prompts_config = self.load_prompts_config()
        self.logger = logging.getLogger(__name__)

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
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
        return text

    def analyze_script(self, script_text):
        try:
            # Hard-coded system prompt
            system_prompt = "You are a script analyzer. Analyze the given script for an audio play and provide structured output."

            # Hard-coded formatting instructions
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
            pre_prompt = self.prompts_config.get('script_analysis_pre', 
                """I have a script for an audio play that I would like to analyze and categorize. Please analyze each line in the script and categorize it as follows:

1. Determine if the line is a spoken sentence by a character, a description of a sound effect (SFX), or a description of music. If the estimated length of a music piece is below 22s categorize it as SFX
2. If it is a spoken sentence by a character, identify the character's name.
3. If it is an SFX, estimate the duration of the sound (between 0.5 and 22 seconds).
4. If it is music, specify whether it is instrumental or with vocals. Use "instrumental": "yes" for instrumental music and "instrumental": "no" for music with vocals.
5. Maintain the order of the lines as they appear in the script, and assign an index to each line.
6. Include two additional parts in the JSON:
    - Needed Speaker Tracks: List all the characternames in the script. 
    - Voice Characteristics: Analyze the emotional content of the sentence and describe the voice characteristics of each speaker.""")

            # Combine the components
            full_prompt = f"{pre_prompt}\n\n{formatting_instructions}\n\n{script_text}"

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                response_format={ "type": "json_object" },
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": full_prompt}
                ]
            )
            
            analysis = json.loads(response.choices[0].message.content)
            return analysis
        except Exception as e:
            print(f"Error analyzing script: {str(e)}")
            return None
        
