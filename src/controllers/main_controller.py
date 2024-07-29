from controllers.audio_controller import AudioController
from controllers.script_editor_controller import ScriptEditorController
from controllers.timeline_controller import TimelineController
from tkinter import filedialog, simpledialog, messagebox
import os
import logging

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

        timeline_model = self.project_model.get_timeline_model()
        self.timeline_controller = TimelineController(self.view, timeline_model, self.project_model)
        self.timeline_controller.master_controller = self
        self.view.set_timeline_controller(self.timeline_controller)

        script_model = self.model.get_script_model()
        script_view = self.view.get_script_editor_view()
        self.script_editor_controller = ScriptEditorController(
            script_model, 
            script_view, 
            self.config, 
            self.project_model, 
            self.audio_controller,
            self.timeline_controller  # Pass the timeline_controller here
        )

        timeline_model = self.project_model.get_timeline_model()
        self.timeline_controller = TimelineController(self.view, timeline_model, self.project_model)
        self.timeline_controller.master_controller = self
        self.view.set_timeline_controller(self.timeline_controller)

    def setup_callbacks(self):
        self.view.set_new_project_callback(self.new_project)
        self.view.set_open_project_callback(self.open_project)
        self.view.set_save_project_callback(self.save_project)
        self.view.set_import_audio_callback(self.import_audio)
        
        # Set up the connection between Timeline and Audio Creator
        self.timeline_controller.set_toggle_audio_creator_command(self.view.toggle_visibility)
        self.audio_controller.set_show_timeline_command(self.timeline_controller.show)
        self.audio_controller.set_add_to_timeline_callback(self.add_audio_to_timeline)
        self.audio_controller.set_add_to_new_audio_files_callback(self.add_to_new_audio_files)
    
    def load_default_project(self):
        try:
            self.project_model.ensure_default_project()
            self.update_current_project(self.project_model.current_project)
            self.update_output_directories()
            if self.timeline_controller:
                self.timeline_controller.on_project_change()
            self.load_last_opened_script()
        except Exception as e:
            error_message = f"Error loading default project: {str(e)}"
            print(error_message)  # Print to console for debugging
            self.view.update_status(error_message)
            self.view.show_error("Error", error_message)

    def load_last_opened_script(self):
        last_script = self.project_model.get_last_opened_script()
        if last_script:
            full_path = os.path.join(self.project_model.get_scripts_dir(), last_script)
            if os.path.exists(full_path):
                self.script_editor_controller.load_script(full_path)
            else:
                self.view.update_status(f"Last opened script not found: {last_script}")
                
    def update_current_project(self, project_name):
        self.view.update_current_project(project_name)
        if self.timeline_controller:
            self.timeline_controller.on_project_change()

    def new_project(self):
        project_name = self.view.ask_string("New Project", "Enter project name:")
        if project_name:
            try:
                self.project_model.create_project(project_name)
                self.update_current_project(project_name)
                self.update_output_directories()
                self.clear_input_fields()
                self.view.update_status(f"Project '{project_name}' created successfully.")
                self.view.show_info("Success", f"Project '{project_name}' created successfully.")
            except ValueError as e:
                error_message = str(e)
                self.view.update_status(f"Error: {error_message}")
                self.view.show_error("Error", error_message)
        else:
            self.view.update_status("Project creation cancelled.")
        
    def save_project(self):
        success, message = self.project_model.save_project()
        if success:
            if self.timeline_controller:
                self.timeline_controller.on_project_saved()
            self.view.show_info("Project Saved", message)
            self.view.update_status("Project saved successfully")
        else:
            self.view.show_error("Save Error", message)
            self.view.update_status("Failed to save project")

    def open_project(self, project_name):
        try:
            if self.timeline_controller:
                self.timeline_controller.hide()  # Hide the timeline view before changing projects
            self.project_model.load_project(project_name)
            self.update_current_project(project_name)
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
            self.view.show_info("Success", f"Project '{project_name}' opened successfully.")
        except ValueError as e:
            error_message = str(e)
            self.view.update_status(f"Error: {error_message}")
            self.view.show_error("Error", error_message)

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

    def toggle_timeline(self):
        self.timeline_controller.toggle_visibility()

    def run(self):
        self.audio_controller.load_voices()
        self.view.run()

    def import_audio(self):
        if not self.project_model.current_project:
            self.view.show_warning("No Project", "Please open a project before importing audio.")
            return

        if self.timeline_controller.timeline_model.is_playing:
            self.view.show_error("Playback in Progress", "Cannot import audio while playback is running. Stop playback and try again.")
            return

        file_path = filedialog.askopenfilename(
            title="Select Audio File",
            filetypes=[("Audio Files", "*.mp3 *.wav")]
        )

        if file_path:
            try:
                # Import the audio file
                new_file_path = self.project_model.import_audio_file(file_path)
                logging.info(f"Audio file imported: {new_file_path}")
                
                # Add the audio clip to the timeline
                if self.timeline_controller:
                    self.timeline_controller.add_audio_clip(new_file_path)
                    self.timeline_controller.unsaved_changes = True
                else:
                    logging.error("Timeline controller is not initialized")
                    self.view.show_error("Error", "Timeline controller is not initialized")
                
                self.view.update_status(f"Audio file imported: {os.path.basename(new_file_path)}")
            except Exception as e:
                logging.error(f"Failed to import audio file: {str(e)}", exc_info=True)
                self.view.show_error("Import Error", f"Failed to import audio file: {str(e)}")

    def add_audio_to_timeline(self, file_path, track_index):
        if self.timeline_controller:
            self.timeline_controller.add_audio_clip(file_path, track_index)
        else:
            logging.warning("Timeline controller is not available")
    
    def add_to_new_audio_files(self, file_path):
        self.project_model.new_audio_files.add(file_path)

    def show_open_project_dialog(self):
        self.view.open_project()

    def show_new_project_dialog(self):
        project_name = simpledialog.askstring("New Project", "Enter project name:")
        if project_name:
            try:
                self.project_model.create_project(project_name)
                self.update_current_project(project_name)
                self.update_output_directories()
                self.clear_input_fields()
                self.view.update_status(f"Project '{project_name}' created successfully.")
                self.view.show_info("Success", f"Project '{project_name}' created successfully.")
            except ValueError as e:
                error_message = str(e)
                self.view.update_status(f"Error: {error_message}")
                self.view.show_error("Error", error_message)

    def quit(self):
        if self.audio_controller:
            self.audio_controller.quit()
        self.view.quit()

    def on_close(self):
        if self.timeline_controller and self.timeline_controller.unsaved_changes:
            response = messagebox.askyesnocancel("Unsaved Changes", "You have unsaved changes. Do you want to save before closing?")
            if response is None:  # Cancel
                return
            elif response:  # Yes
                self.save_project()
            else:  # No
                self.timeline_controller.discard_unsaved_changes()
        self.view.quit()