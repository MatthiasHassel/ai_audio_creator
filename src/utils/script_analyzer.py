import re
import json
from typing import List, Dict, Any

class ScriptAnalyzer:
    def __init__(self):
        self.speaker_pattern = re.compile(r'\*\*(.*?):\*\* "(.*?)"')
        self.sfx_pattern = re.compile(r'\[SFX: (.*?)\]')
        self.music_pattern = re.compile(r'\[MUSIC: (.*?)\]')

    def analyze_script(self, script_text: str) -> Dict[str, Any]:
        analyzed_script = []
        categorized_sentences = {
            'speech': {},
            'sfx': [],
            'music': [],
            'narration': []
        }
        lines = script_text.split('\n')
        current_speaker = None
        current_sentence = ""

        for line in lines:
            line = line.strip()
            if not line:
                continue

            speaker_match = self.speaker_pattern.match(line)
            sfx_match = self.sfx_pattern.match(line)
            music_match = self.music_pattern.match(line)

            if speaker_match:
                if current_sentence:
                    self._add_sentence_to_category(current_speaker, current_sentence, categorized_sentences)
                current_speaker = speaker_match.group(1)
                current_sentence = speaker_match.group(2)
                analyzed_script.append({
                    'type': 'speech',
                    'speaker': current_speaker,
                    'text': current_sentence
                })
            elif sfx_match:
                if current_sentence:
                    self._add_sentence_to_category(current_speaker, current_sentence, categorized_sentences)
                sfx_description = sfx_match.group(1)
                categorized_sentences['sfx'].append(sfx_description)
                analyzed_script.append({
                    'type': 'sfx',
                    'description': sfx_description
                })
                current_speaker = None
                current_sentence = ""
            elif music_match:
                if current_sentence:
                    self._add_sentence_to_category(current_speaker, current_sentence, categorized_sentences)
                music_description = music_match.group(1)
                categorized_sentences['music'].append(music_description)
                analyzed_script.append({
                    'type': 'music',
                    'description': music_description
                })
                current_speaker = None
                current_sentence = ""
            else:
                if current_sentence:
                    current_sentence += " " + line
                else:
                    current_sentence = line
                analyzed_script.append({
                    'type': 'narration',
                    'text': line
                })

        # Add the last sentence if there is one
        if current_sentence:
            self._add_sentence_to_category(current_speaker, current_sentence, categorized_sentences)

        return {
            'analyzed_script': analyzed_script,
            'categorized_sentences': categorized_sentences
        }

    def _add_sentence_to_category(self, speaker, sentence, categorized_sentences):
        if speaker:
            if speaker not in categorized_sentences['speech']:
                categorized_sentences['speech'][speaker] = []
            categorized_sentences['speech'][speaker].append(sentence)
        else:
            categorized_sentences['narration'].append(sentence)

    def suggest_voices(self, analyzed_script: List[Dict[str, Any]]) -> List[str]:
        speakers = set()
        for element in analyzed_script:
            if element['type'] == 'speech':
                speakers.add(element['speaker'])
        return list(speakers)

    def save_analysis(self, analysis_result: Dict[str, Any], filename: str) -> None:
        """Save the analyzed script to a JSON file."""
        with open(filename, 'w') as f:
            json.dump(analysis_result, f, indent=2)

    def load_analysis(self, filename: str) -> Dict[str, Any]:
        """Load an analyzed script from a JSON file."""
        with open(filename, 'r') as f:
            return json.load(f)

    def reconstruct_script(self, analysis_result: Dict[str, Any]) -> str:
        """Reconstruct the original script text from the analysis."""
        analyzed_script = analysis_result['analyzed_script']
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

    def get_speakers(self, analysis_result: Dict[str, Any]) -> List[str]:
        """Get a list of unique speakers from the analyzed script."""
        return list(analysis_result['categorized_sentences']['speech'].keys())

    def get_sfx(self, analysis_result: Dict[str, Any]) -> List[str]:
        """Get a list of unique SFX descriptions from the analyzed script."""
        return analysis_result['categorized_sentences']['sfx']

    def get_music(self, analysis_result: Dict[str, Any]) -> List[str]:
        """Get a list of unique music descriptions from the analyzed script."""
        return analysis_result['categorized_sentences']['music']

    def count_elements(self, analysis_result: Dict[str, Any]) -> Dict[str, int]:
        """Count the number of each type of element in the analyzed script."""
        categorized_sentences = analysis_result['categorized_sentences']
        return {
            'speech': sum(len(sentences) for sentences in categorized_sentences['speech'].values()),
            'sfx': len(categorized_sentences['sfx']),
            'music': len(categorized_sentences['music']),
            'narration': len(categorized_sentences['narration'])
        }

    def estimate_duration(self, analysis_result: Dict[str, Any], words_per_minute: int = 150) -> float:
        """Estimate the duration of the script in minutes."""
        categorized_sentences = analysis_result['categorized_sentences']
        total_words = sum(len(sentence.split()) for sentences in categorized_sentences['speech'].values() for sentence in sentences)
        total_words += sum(len(sentence.split()) for sentence in categorized_sentences['narration'])
        return total_words / words_per_minute

    def find_element(self, analysis_result: Dict[str, Any], search_term: str) -> List[Dict[str, Any]]:
        """Find elements in the analyzed script that contain the search term."""
        return [
            element for element in analysis_result['analyzed_script']
            if search_term.lower() in json.dumps(element).lower()
        ]