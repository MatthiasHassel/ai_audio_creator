import os
import hashlib
from tkinter import filedialog
from utils.script_analyzer import ScriptAnalyzer

class ScriptEditorController:
    def __init__(self, model, view, config, project_model):
        self.model = model
        self.view = view
        self.config = config
        self.project_model = project_model
        self.current_script_path = None
        self.script_analyzer = ScriptAnalyzer()
        self.setup_view_commands()

    def setup_view_commands(self):
        self.view.save_button.configure(command=self.save_script)
        self.view.load_button.configure(command=self.load_script)
        self.view.set_save_analysis_callback(self.save_analysis)
        self.view.set_load_analysis_callback(self.load_analysis)
        self.view.on_text_changed = self.on_text_changed

    def on_text_changed(self, event):
        self.view.text_area.edit_modified(False)  # Reset the modified flag
        self.analyze_script()

    def analyze_script(self):
        script_text = self.get_script_text()
        analysis_result = self.script_analyzer.analyze_script(script_text)
        analyzed_script = analysis_result['analyzed_script']
        categorized_sentences = analysis_result['categorized_sentences']
        suggested_voices = self.script_analyzer.suggest_voices(analyzed_script)
        element_counts = self.script_analyzer.count_elements(analysis_result)
        estimated_duration = self.script_analyzer.estimate_duration(analysis_result)
        
        self.view.update_analysis_results(analyzed_script, suggested_voices, element_counts, estimated_duration, categorized_sentences)

    def save_analysis(self):
        if not self.current_script_path:
            self.view.update_status("No script loaded. Please save the script first.")
            return

        analysis_file_path = self.current_script_path + ".analysis.json"
        script_text = self.get_script_text()
        analysis_result = self.script_analyzer.analyze_script(script_text)
        self.script_analyzer.save_analysis(analysis_result, analysis_file_path)
        self.view.update_status(f"Analysis saved to {analysis_file_path}")

    def load_analysis(self):
        if not self.current_script_path:
            self.view.update_status("No script loaded. Please load a script first.")
            return

        analysis_file_path = self.current_script_path + ".analysis.json"
        if os.path.exists(analysis_file_path):
            analysis_result = self.script_analyzer.load_analysis(analysis_file_path)
            analyzed_script = analysis_result['analyzed_script']
            categorized_sentences = analysis_result['categorized_sentences']
            suggested_voices = self.script_analyzer.suggest_voices(analyzed_script)
            element_counts = self.script_analyzer.count_elements(analysis_result)
            estimated_duration = self.script_analyzer.estimate_duration(analysis_result)
            
            self.view.update_analysis_results(analyzed_script, suggested_voices, element_counts, estimated_duration, categorized_sentences)
            self.view.update_status(f"Analysis loaded from {analysis_file_path}")
        else:
            self.view.update_status("No saved analysis found. Analyzing current script...")
            self.analyze_script()

    def format_text(self, style):
        self.view.format_text(style)

    def get_script_hash(self):
        return hashlib.md5(self.get_script_text().encode()).hexdigest()

    def is_script_modified(self):
        return self.last_saved_hash != self.get_script_hash()

    def save_script(self):
        if not self.project_model.current_project:
            self.view.update_status("No active project. Please open or create a project first.")
            return

        initial_dir = self.project_model.get_scripts_dir()
        initial_file = os.path.basename(self.current_script_path) if self.current_script_path else ""
        
        file_path = filedialog.asksaveasfilename(
            initialdir=initial_dir,
            initialfile=initial_file,
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )

        if file_path:
            with open(file_path, 'w') as file:
                file.write(self.get_script_text())
            self.current_script_path = file_path
            relative_path = os.path.relpath(file_path, self.project_model.get_scripts_dir())
            self.project_model.set_last_opened_script(relative_path)
            self.view.update_status(f"Script saved to {file_path}")

    def load_script(self, file_path=None):
        if not self.project_model.current_project:
            self.view.update_status("No active project. Please open or create a project first.")
            return

        if not file_path:
            file_path = filedialog.askopenfilename(
                initialdir=self.project_model.get_scripts_dir(),
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
            )
        
        if file_path:
            try:
                with open(file_path, 'r') as file:
                    script_content = file.read()
                self.set_script_text(script_content)
                self.current_script_path = file_path
                relative_path = os.path.relpath(file_path, self.project_model.get_scripts_dir())
                self.project_model.set_last_opened_script(relative_path)
                self.view.update_status(f"Script loaded from {file_path}")
                self.analyze_script()  # Analyze the loaded script
            except Exception as e:
                error_message = f"Error loading script: {str(e)}"
                self.view.update_status(error_message)
                self.view.show_error("Error", error_message)

    def get_script_text(self):
        return self.view.get_text()

    def set_script_text(self, text):
        self.model.set_content(text)
        self.view.set_text(text)

    def clear_text(self):
        self.set_script_text("")
        self.current_script_path = None

    def update_scripts_directory(self, directory):
        # This method might not be necessary anymore, but keep it for potential future use
        pass