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
Please analyze the following script and provide a structured JSON output. Sort all sentences by their speakers and give them an index indicating at what place the sentence is in the script.
Recognize instructions for sound effects and music and list them with an index. The index should later be used to restore the exact order of the sentences in the script.
Therefore, each index number may only occur once. If sentences are spoken at the same time, give them a consecutive index number. Output the analysis as JSON text in the following format:

"speech": {
    "Narrator": {
        "(index)": "(sentence)", 
        "(index)": "(next-character-sentence)",
         ... 
        }, 
    "(speaker name)": {
        "(index)": "(sentence)",
        ...
        },
    ...
    }
}
"sfx:" {
    "(index)": "(precise sound effect description)",
    ...
    }
"music:" {
    "(index)": "(music description)",
    ...
    }

Also analyze the emotional content of the sentence and describe the voice characteristics of each speaker and add it to the JSON file using this format:

"voice_characteristics": {
    "(speaker-name/narrator)": {
        "Gender": "(male/female)",
        "Age": "(young/middle_aged,/old)",
        "Accent": "(none/american/british/african/australian/indian)",
        "Voice Description": "(1 adjective)"
        },
    ...
    }
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