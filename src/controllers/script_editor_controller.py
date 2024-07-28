import os
import threading
import time
import json
import random # will not be needed after proper implementation of voice selection
import hashlib
from tkinter import filedialog
from services.pdf_analysis_service import PDFAnalysisService

class ScriptEditorController:
    def __init__(self, model, view, config, project_model, audio_controller, timeline_controller):
        self.model = model
        self.view = view
        self.config = config
        self.project_model = project_model
        self.audio_controller = audio_controller
        self.timeline_controller = timeline_controller
        self.view.set_create_audio_callback(self.create_audio)
        self.current_script_path = None
        self.pdf_analysis_service = PDFAnalysisService(config)
        self.setup_view_commands()

    def setup_view_commands(self):
        self.view.save_button.configure(command=self.save_script)
        self.view.load_button.configure(command=self.load_script)
        self.view.set_import_pdf_callback(self.import_pdf)
        self.view.set_analyze_script_callback(self.analyze_script)


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

    def import_pdf(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("PDF files", "*.pdf")]
        )
        if file_path:
            try:
                text = self.pdf_analysis_service.extract_text_from_pdf(file_path)
                self.view.set_text(text)
                self.view.update_status(f"PDF imported: {file_path}")
            except Exception as e:
                self.view.update_status(f"Error importing PDF: {str(e)}")

    def analyze_script(self):
        script_text = self.view.get_text()
        if not script_text:
            self.view.update_status("Error: No script text to analyze")
            return

        self.view.show_progress_bar(determinate=False)  # Use indeterminate mode
        self.view.analyze_script_button.configure(state="disabled")

        def analysis_thread():
            try:
                analysis = self.pdf_analysis_service.analyze_script(script_text)
                if analysis:
                    output_path = self.get_next_analysis_filename()
                    with open(output_path, 'w') as file:
                        json.dump(analysis, file, indent=2)
                    self.view.after(0, lambda: self.view.update_status(f"Analysis saved to: {output_path}"))
                else:
                    self.view.after(0, lambda: self.view.update_status("Error: Failed to analyze script"))
            except Exception as e:
                self.view.after(0, lambda: self.view.update_status(f"Error analyzing script: {str(e)}"))
            finally:
                self.view.after(0, self.view.hide_progress_bar)
                self.view.after(0, lambda: self.view.analyze_script_button.configure(state="normal"))

        threading.Thread(target=analysis_thread, daemon=True).start()

    def get_next_analysis_filename(self):
        scripts_dir = self.project_model.get_scripts_dir()
        index = 1
        while True:
            filename = f"script_analysis{index}.json"
            full_path = os.path.join(scripts_dir, filename)
            if not os.path.exists(full_path):
                return full_path
            index += 1

    def create_audio(self):
        analysis_file = self.get_latest_analysis_file()
        if not analysis_file:
            self.view.update_status("No analysis file found. Please analyze the script first.")
            return

        with open(analysis_file, 'r') as file:
            analysis = json.load(file)

        self.view.show_progress_bar(determinate=False)
        self.view.create_audio_button.configure(state="disabled")

        def audio_creation_thread():
            try:
                audio_clips = []
                
                # Process speech
                for speaker, sentences in analysis['speech'].items():
                    voice_char = analysis['voice_characteristics'].get(speaker, {})
                    suitable_voices = self.get_suitable_voices(voice_char)
                    chosen_voice = random.choice(suitable_voices) if suitable_voices else random.choice(self.audio_controller.speech_service.get_available_voices())
                    
                    for index, sentence in sentences.items():
                        self.audio_controller.view.user_input.delete("1.0", "end")
                        self.audio_controller.view.user_input.insert("1.0", sentence)
                        self.audio_controller.view.selected_voice.set(chosen_voice[0])
                        self.audio_controller.process_speech_request()
                        
                        # Wait for the audio to be generated
                        while self.audio_controller.view.generate_button.cget("state") == "disabled":
                            time.sleep(0.1)
                        
                        # Get the last generated audio file
                        audio_file = self.audio_controller.view.audio_file_selector.get_selected_file()
                        if audio_file:
                            audio_clips.append(('speech', speaker, int(index), audio_file))

                # Process SFX
                for index, description in analysis['sfx'].items():
                    self.audio_controller.view.user_input.delete("1.0", "end")
                    self.audio_controller.view.user_input.insert("1.0", description)
                    self.audio_controller.view.duration_var.set("0")  # Use automatic duration
                    self.audio_controller.process_sfx_request()
                    
                    # Wait for the audio to be generated
                    while self.audio_controller.view.generate_button.cget("state") == "disabled":
                        time.sleep(0.1)
                    
                    audio_file = self.audio_controller.view.audio_file_selector.get_selected_file()
                    if audio_file:
                        audio_clips.append(('sfx', 'SFX', int(index), audio_file))

                # Process music
                for index, description in analysis['music'].items():
                    self.audio_controller.view.user_input.delete("1.0", "end")
                    self.audio_controller.view.user_input.insert("1.0", description)
                    self.audio_controller.view.instrumental_var.set(False)  # Assuming we want vocals
                    self.audio_controller.process_music_request()
                    
                    # Wait for the audio to be generated
                    while self.audio_controller.view.generate_button.cget("state") == "disabled":
                        time.sleep(0.1)
                    
                    audio_file = self.audio_controller.view.audio_file_selector.get_selected_file()
                    if audio_file:
                        audio_clips.append(('music', 'Music', int(index), audio_file))

                # Sort clips by index
                audio_clips.sort(key=lambda x: x[2])

                # Add clips to timeline
                current_position = 0
                for clip_type, track_name, index, file_path in audio_clips:
                    track_index = self.timeline_controller.get_or_create_track(track_name)
                    clip_duration = self.timeline_controller.get_clip_duration(file_path)
                    self.timeline_controller.add_audio_clip(file_path, track_index, current_position)
                    current_position += clip_duration

                self.view.after(0, lambda: self.view.update_status("Audio creation completed and added to timeline."))
            except Exception as e:
                self.view.after(0, lambda: self.view.update_status(f"Error creating audio: {str(e)}"))
            finally:
                self.view.after(0, self.view.hide_progress_bar)
                self.view.after(0, lambda: self.view.create_audio_button.configure(state="normal"))

        threading.Thread(target=audio_creation_thread, daemon=True).start()

    def get_suitable_voices(self, voice_char):
        suitable_voices = []
        all_voices = self.audio_controller.speech_service.get_available_voices()
        
        for voice in all_voices:
            # This is a simplified matching. You might want to implement a more sophisticated matching system.
            if (voice_char.get('Gender', '').lower() in voice[0].lower() and
                voice_char.get('Age', '').lower() in voice[0].lower() and
                voice_char.get('Accent', '').lower() in voice[0].lower()):
                suitable_voices.append(voice)
        
        return suitable_voices if suitable_voices else all_voices

    def get_latest_analysis_file(self):
        scripts_dir = self.project_model.get_scripts_dir()
        analysis_files = [f for f in os.listdir(scripts_dir) if f.startswith("script_analysis") and f.endswith(".json")]
        if not analysis_files:
            return None
        latest_file = max(analysis_files, key=lambda f: int(f.split("script_analysis")[1].split(".json")[0]))
        return os.path.join(scripts_dir, latest_file)