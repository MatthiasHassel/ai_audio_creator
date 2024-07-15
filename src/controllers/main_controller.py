from controllers.audio_controller import AudioController
from controllers.script_editor_controller import ScriptEditorController
from models.audio_model import AudioModel
from models.script_model import ScriptModel
from utils.script_analyzer import ScriptAnalyzer
from tkinter import simpledialog, messagebox
import os

class MainController:
    def __init__(self, model, view, config, project_model):
        self.model = model
        self.view = view
        self.config = config
        self.project_model = project_model
        self.script_analyzer = ScriptAnalyzer()
        self.setup_controllers()
        self.setup_callbacks()

    def setup_controllers(self):
        audio_model = self.model.get_audio_model()
        audio_view = self.view.get_audio_generator_view()
        self.audio_controller = AudioController(audio_model, audio_view, self.config)

        script_model = self.model.get_script_model()
        script_view = self.view.get_script_editor_view()
        self.script_editor_controller = ScriptEditorController(script_model, script_view, self.config, self.project_model)

        self.script_editor_controller.set_analysis_callback(self.analyze_script)

    def setup_callbacks(self):
        self.view.set_new_project_callback(self.new_project)
        self.view.set_open_project_callback(self.open_project)
        self.view.set_save_project_callback(self.save_project)

    def new_project(self):
        project_name = simpledialog.askstring("New Project", "Enter project name:")
        if project_name:
            try:
                self.project_model.create_project(project_name)
                self.view.update_current_project(project_name)
                self.update_output_directories()
                self.clear_input_fields()
                self.view.update_status(f"Project '{project_name}' created successfully.")
                messagebox.showinfo("Success", f"Project '{project_name}' created successfully.")
            except ValueError as e:
                error_message = str(e)
                self.view.update_status(f"Error: {error_message}")
                messagebox.showerror("Error", error_message)

    def open_project(self, project_name):
        try:
            self.project_model.load_project(project_name)
            self.view.update_current_project(project_name)
            self.update_output_directories()
            self.clear_input_fields()
            last_script = self.project_model.get_last_opened_script()
            if last_script:
                full_path = os.path.join(self.project_model.get_scripts_dir(), last_script)
                if os.path.exists(full_path):
                    self.script_editor_controller.load_script(full_path)
                else:
                    self.view.update_status(f"Last opened script not found: {last_script}")
            self.view.update_status(f"Project '{project_name}' opened successfully.")
            messagebox.showinfo("Success", f"Project '{project_name}' opened successfully.")
        except ValueError as e:
            error_message = str(e)
            self.view.update_status(f"Error: {error_message}")
            messagebox.showerror("Error", error_message)

    def save_project(self):
        if not self.project_model.current_project:
            messagebox.showwarning("No Project", "No project is currently open.")
            return
        try:
            self.project_model.save_project_metadata()
            self.view.update_status("Project metadata saved successfully.")
            messagebox.showinfo("Success", "Project metadata saved successfully.")
        except Exception as e:
            error_message = f"Failed to save project metadata: {str(e)}"
            self.view.update_status(error_message)
            messagebox.showerror("Error", error_message)

    def clear_input_fields(self):
        self.script_editor_controller.clear_text()
        self.audio_controller.clear_input()

    def update_output_directories(self):
        self.audio_controller.update_output_directories(
            music_dir=self.project_model.get_output_dir('music'),
            sfx_dir=self.project_model.get_output_dir('sfx'),
            speech_dir=self.project_model.get_output_dir('speech')
        )
        self.script_editor_controller.update_scripts_directory(
            self.project_model.get_scripts_dir()
        )

    def analyze_script(self):
        script_text = self.script_editor_controller.get_script_text()
        analysis_result = self.script_analyzer.analyze_script(script_text)
        analyzed_script = analysis_result['analyzed_script']
        categorized_sentences = analysis_result['categorized_sentences']
        suggested_voices = self.script_analyzer.suggest_voices(analyzed_script)
        element_counts = self.script_analyzer.count_elements(analysis_result)
        estimated_duration = self.script_analyzer.estimate_duration(analysis_result)
        
        self.view.update_analysis_results(analyzed_script, suggested_voices, element_counts, estimated_duration, categorized_sentences)

    def run(self):
        self.audio_controller.load_voices()
        self.view.run()

    def quit(self):
        self.audio_controller.quit()
        self.view.quit()