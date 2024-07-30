# services/pdf_analysis_service.py

import PyPDF2
import json
from openai import OpenAI
import os

class PDFAnalysisService:
    def __init__(self, config):
        self.config = config
        self.client = OpenAI(api_key=self.config['api']['openai_api_key'])

    def extract_text_from_pdf(self, pdf_path):
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
        return text

    def analyze_script(self, script_text):
        try:
            formatting_instructions = """
I have a script for an audio drama that I would like to analyze and categorize. Please analyze each line in the script and categorize it as follows:

1. Determine if the line is a spoken sentence by a character, a description of a sound effect (SFX), or a description of music.
2. If it is a spoken sentence by a character, identify the character's name.
3. If it is an SFX, estimate the duration of the sound (between 0.5 and 22 seconds).
4. If it is music, specify whether it is instrumental or with vocals. Use "instrumental": "yes" for instrumental music and "instrumental": "no" for music with vocals.
5. Maintain the order of the lines as they appear in the script, and assign an index to each line.
6. Include two additional parts in the JSON:
    - Needed Speaker Tracks: List all the characternames in the script. 
    - Voice Characteristics: Analyze the emotional content of the sentence and describe the voice characteristics of each speaker.

Without any additional text, output the analysis in the following JSON format:

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

Here is the script to be analyzed:
"""

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                response_format={ "type": "json_object" },
                messages=[
                    {"role": "system", "content": "You are a script analyzer. Analyze the given script for an audiobook and provide structured output."},
                    {"role": "user", "content": f"{formatting_instructions}\n\n{script_text}"}
                ]
            )
            
            analysis = json.loads(response.choices[0].message.content)
            return analysis
        except Exception as e:
            print(f"Error analyzing script: {str(e)}")
            return None
        
