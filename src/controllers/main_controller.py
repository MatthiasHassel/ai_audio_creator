from controllers.audio_controller import AudioController
from controllers.script_editor_controller import ScriptEditorController
from controllers.timeline_controller import TimelineController
from utils.script_analyzer import ScriptAnalyzer
from tkinter import simpledialog, messagebox
import os

class MainController:
    def __init__(self, model, view, config, project_model):
        self.model = model
        self.view = view
        self.config = config
        self.project_model = project_model
        self.audio_controller = None
        self.script_editor_controller = None
        self.timeline_controller = None

        self.setup_controllers()
        self.setup_callbacks()
        self.load_default_project()

    def setup_controllers(self):
        audio_model = self.model.get_audio_model()
        audio_view = self.view.get_audio_generator_view()
        self.audio_controller = AudioController(audio_model, audio_view, self.config)

        script_model = self.model.get_script_model()
        script_view = self.view.get_script_editor_view()
        self.script_editor_controller = ScriptEditorController(script_model, script_view, self.config, self.project_model)

        self.timeline_controller = TimelineController(self.view, self.model)
        self.view.set_timeline_controller(self.timeline_controller)

    def setup_callbacks(self):
        self.view.set_new_project_callback(self.new_project)
        self.view.set_open_project_callback(self.open_project)
        self.view.set_save_project_callback(self.save_project)
        
        # Set up the connection between Timeline and Audio Creator
        self.timeline_controller.set_toggle_audio_creator_command(self.view.toggle_visibility)
        self.audio_controller.set_show_timeline_command(self.timeline_controller.show)

    def load_default_project(self):
        try:
            self.project_model.ensure_default_project()
            self.view.update_current_project(self.project_model.current_project)
            self.update_output_directories()
        except Exception as e:
            self.view.update_status(f"Error loading default project: {str(e)}")


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
        if self.audio_controller:
            self.audio_controller.update_output_directories(
                music_dir=self.project_model.get_output_dir('music'),
                sfx_dir=self.project_model.get_output_dir('sfx'),
                speech_dir=self.project_model.get_output_dir('speech')
            )
        if self.script_editor_controller:
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

    def toggle_timeline(self):
        self.timeline_controller.toggle_visibility()

    def run(self):
        self.audio_controller.load_voices()
        self.view.run()

    def run(self):
        if self.audio_controller:
            self.audio_controller.load_voices()
        self.view.run()

    def quit(self):
        if self.audio_controller:
            self.audio_controller.quit()
        self.view.quit()