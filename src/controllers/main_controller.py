from controllers.audio_controller import AudioController
from controllers.script_editor_controller import ScriptEditorController
from models.audio_model import AudioModel
from models.script_model import ScriptModel
from utils.script_analyzer import ScriptAnalyzer
from tkinter import filedialog
import json

class MainController:
    def __init__(self, model, view, config):
        self.model = model
        self.view = view
        self.config = config
        self.script_analyzer = ScriptAnalyzer()
        self.setup_controllers()

    def setup_controllers(self):
        audio_model = self.model.get_audio_model()
        audio_view = self.view.get_audio_generator_view()
        self.audio_controller = AudioController(audio_model, audio_view, self.config)

        script_model = self.model.get_script_model()
        script_view = self.view.get_script_editor_view()
        self.script_editor_controller = ScriptEditorController(script_model, script_view, self.config)

        # Connect script analysis to the script editor
        self.script_editor_controller.set_analysis_callback(self.analyze_script)

        # Set up save and load callbacks
        self.view.set_save_analysis_callback(self.save_analysis)
        self.view.set_load_analysis_callback(self.load_analysis)

    def analyze_script(self):
        script_text = self.script_editor_controller.get_script_text()
        analysis_result = self.script_analyzer.analyze_script(script_text)
        analyzed_script = analysis_result['analyzed_script']
        categorized_sentences = analysis_result['categorized_sentences']
        suggested_voices = self.script_analyzer.suggest_voices(analyzed_script)
        element_counts = self.script_analyzer.count_elements(analysis_result)
        estimated_duration = self.script_analyzer.estimate_duration(analysis_result)
        
        self.view.update_analysis_results(analyzed_script, suggested_voices, element_counts, estimated_duration, categorized_sentences)

    def save_analysis(self):
        script_text = self.script_editor_controller.get_script_text()
        analyzed_script = self.script_analyzer.analyze_script(script_text)
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if file_path:
            try:
                self.script_analyzer.save_analysis(analyzed_script, file_path)
                self.view.update_status(f"Analysis saved to {file_path}")
            except Exception as e:
                self.view.update_status(f"Error saving analysis: {str(e)}")

    def load_analysis(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if file_path:
            try:
                analyzed_script = self.script_analyzer.load_analysis(file_path)
                reconstructed_script = self.script_analyzer.reconstruct_script(analyzed_script)
                
                # Update the script editor with the reconstructed script
                self.script_editor_controller.set_script_text(reconstructed_script)
                
                # Update the view with the loaded analysis
                suggested_voices = self.script_analyzer.suggest_voices(analyzed_script)
                element_counts = self.script_analyzer.count_elements(analyzed_script)
                estimated_duration = self.script_analyzer.estimate_duration(analyzed_script)
                self.view.update_analysis_results(analyzed_script, suggested_voices, element_counts, estimated_duration)
                
                self.view.update_status(f"Analysis loaded from {file_path}")
            except Exception as e:
                self.view.update_status(f"Error loading analysis: {str(e)}")

    def generate_audio(self, analysis_result):
        categorized_sentences = analysis_result['categorized_sentences']
        
        # Generate speech for each speaker
        for speaker, sentences in categorized_sentences['speech'].items():
            for sentence in sentences:
                self.audio_controller.process_speech_request(sentence, speaker)
        
        # Generate narration
        for sentence in categorized_sentences['narration']:
            self.audio_controller.process_speech_request(sentence, "Narrator")
        
        # Generate SFX
        for sfx_description in categorized_sentences['sfx']:
            self.audio_controller.process_sfx_request(sfx_description, "0")  # Assuming default duration
        
        # Generate music
        for music_description in categorized_sentences['music']:
            self.audio_controller.process_music_request(music_description, False)  # Assuming not instrumental by default
        
        self.view.update_status("Audio generation complete")

    def search_script(self, search_term):
        script_text = self.script_editor_controller.get_script_text()
        analyzed_script = self.script_analyzer.analyze_script(script_text)
        search_results = self.script_analyzer.find_element(analyzed_script, search_term)
        self.view.display_search_results(search_results)

    def get_script_statistics(self):
        script_text = self.script_editor_controller.get_script_text()
        analyzed_script = self.script_analyzer.analyze_script(script_text)
        statistics = {
            "element_counts": self.script_analyzer.count_elements(analyzed_script),
            "estimated_duration": self.script_analyzer.estimate_duration(analyzed_script),
            "unique_speakers": len(self.script_analyzer.get_speakers(analyzed_script)),
            "unique_sfx": len(self.script_analyzer.get_sfx(analyzed_script)),
            "unique_music": len(self.script_analyzer.get_music(analyzed_script))
        }
        self.view.display_script_statistics(statistics)

    def run(self):
        self.audio_controller.load_voices()
        self.view.run()

    def quit(self):
        self.audio_controller.quit()
        self.view.quit()