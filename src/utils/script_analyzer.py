import re
import json
from typing import List, Dict, Any

class ScriptAnalyzer:
    def __init__(self):
        self.speaker_pattern = re.compile(r'\*\*(.*?):\*\* "(.*?)"')
        self.sfx_pattern = re.compile(r'\[SFX: (.*?)\]')
        self.music_pattern = re.compile(r'\[MUSIC: (.*?)\]')

    def analyze_script(self, script_text: str) -> List[Dict[str, Any]]:
        analyzed_script = []
        lines = script_text.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue

            speaker_match = self.speaker_pattern.match(line)
            sfx_match = self.sfx_pattern.match(line)
            music_match = self.music_pattern.match(line)

            if speaker_match:
                analyzed_script.append({
                    'type': 'speech',
                    'speaker': speaker_match.group(1),
                    'text': speaker_match.group(2)
                })
            elif sfx_match:
                analyzed_script.append({
                    'type': 'sfx',
                    'description': sfx_match.group(1)
                })
            elif music_match:
                analyzed_script.append({
                    'type': 'music',
                    'description': music_match.group(1)
                })
            else:
                analyzed_script.append({
                    'type': 'narration',
                    'text': line
                })

        return analyzed_script

    def suggest_voices(self, analyzed_script: List[Dict[str, Any]]) -> List[str]:
        speakers = set()
        for element in analyzed_script:
            if element['type'] == 'speech':
                speakers.add(element['speaker'])
        return list(speakers)

    def save_analysis(self, analyzed_script: List[Dict[str, Any]], filename: str) -> None:
        """Save the analyzed script to a JSON file."""
        with open(filename, 'w') as f:
            json.dump(analyzed_script, f, indent=2)

    def load_analysis(self, filename: str) -> List[Dict[str, Any]]:
        """Load an analyzed script from a JSON file."""
        with open(filename, 'r') as f:
            return json.load(f)

    def reconstruct_script(self, analyzed_script: List[Dict[str, Any]]) -> str:
        """Reconstruct the original script text from the analysis."""
        script_lines = []
        for element in analyzed_script:
            if element['type'] == 'speech':
                script_lines.append(f"**{element['speaker']}:** \"{element['text']}\"")
            elif element['type'] == 'sfx':
                script_lines.append(f"[SFX: {element['description']}]")
            elif element['type'] == 'music':
                script_lines.append(f"[MUSIC: {element['description']}]")
            else:  # narration
                script_lines.append(element['text'])
        return "\n".join(script_lines)

    def get_speakers(self, analyzed_script: List[Dict[str, Any]]) -> List[str]:
        """Get a list of unique speakers from the analyzed script."""
        return list(set(element['speaker'] for element in analyzed_script if element['type'] == 'speech'))

    def get_sfx(self, analyzed_script: List[Dict[str, Any]]) -> List[str]:
        """Get a list of unique SFX descriptions from the analyzed script."""
        return list(set(element['description'] for element in analyzed_script if element['type'] == 'sfx'))

    def get_music(self, analyzed_script: List[Dict[str, Any]]) -> List[str]:
        """Get a list of unique music descriptions from the analyzed script."""
        return list(set(element['description'] for element in analyzed_script if element['type'] == 'music'))

    def count_elements(self, analyzed_script: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count the number of each type of element in the analyzed script."""
        counts = {
            'speech': 0,
            'sfx': 0,
            'music': 0,
            'narration': 0
        }
        for element in analyzed_script:
            counts[element['type']] += 1
        return counts

    def estimate_duration(self, analyzed_script: List[Dict[str, Any]], words_per_minute: int = 150) -> float:
        """Estimate the duration of the script in minutes."""
        total_words = sum(len(element['text'].split()) for element in analyzed_script if element['type'] in ['speech', 'narration'])
        return total_words / words_per_minute

    def find_element(self, analyzed_script: List[Dict[str, Any]], search_term: str) -> List[Dict[str, Any]]:
        """Find elements in the analyzed script that contain the search term."""
        return [
            element for element in analyzed_script
            if search_term.lower() in json.dumps(element).lower()
        ]