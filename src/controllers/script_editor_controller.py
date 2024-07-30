import os
import logging
import threading
import time
import json
import random 
import requests
import hashlib
from tkinter import filedialog, messagebox
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
        self.setup_view_commands()
        self.pdf_analysis_service = PDFAnalysisService(config)

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
        if self.timeline_controller is None:
            self.view.update_status("Timeline controller is not initialized. Cannot create audio.")
            messagebox.showerror("Error", "Timeline controller is not initialized. Cannot create audio.")
            return

        analysis_file = self.get_latest_analysis_file()
        if not analysis_file:
            self.view.update_status("No analysis file found. Please analyze the script first.")
            return

        with open(analysis_file, 'r') as file:
            analysis = json.load(file)

        self.view.show_progress_bar(determinate=True)
        self.view.create_audio_button.configure(state="disabled")

        def audio_creation_thread():
            try:
                script_analysis = analysis.get('script_analysis', [])
                total_elements = len(script_analysis)
                
                for i, element in enumerate(script_analysis, 1):
                    self.view.update_status(f"Processing element {i} of {total_elements}")
                    self.view.progress_bar.set(i / total_elements)
                    
                    if element['type'] == 'character_line':
                        self.process_speech_element(element)
                    elif element['type'] == 'sfx':
                        self.process_sfx_element(element)
                    elif element['type'] == 'music':
                        self.process_music_element(element)
                    
                    # Small delay to allow GUI to update
                    time.sleep(0.1)

                self.view.after(0, lambda: self.view.update_status("Audio creation completed and added to timeline."))
            except Exception as e:
                error_msg = f"Error creating audio: {str(e)}"
                logging.error(error_msg, exc_info=True)
                self.view.after(0, lambda: self.view.update_status(error_msg))
            finally:
                self.view.after(0, self.view.hide_progress_bar)
                self.view.after(0, lambda: self.view.create_audio_button.configure(state="normal"))

        threading.Thread(target=audio_creation_thread, daemon=True).start()

    def process_speech_element(self, element):
        speaker = element['character']
        sentence = element['content']
        
        self.view.update_status(f"Generating speech for {speaker}: {sentence[:30]}...")
        
        voice_char = self.get_voice_characteristics(speaker)
        chosen_voice_name, chosen_voice_id = self.get_suitable_voice(voice_char)
        
        # Ensure the chosen voice is in the user's library
        if not self.audio_controller.speech_service.ensure_voice_in_library(chosen_voice_id, chosen_voice_name):
            self.view.update_status(f"Failed to add voice '{chosen_voice_name}' to library. Using default voice.")
            chosen_voice_name, chosen_voice_id = self.get_default_voice(voice_char['Gender'])

        # Now that we've ensured the voice is in the library, generate the speech
        audio_file = self.audio_controller.process_speech_request(
            text_prompt=sentence,
            voice_id=chosen_voice_id,
            synchronous=True
        )
        
        if audio_file:
            track_name = speaker
            track_index = self.timeline_controller.get_or_create_track(track_name)
            self.add_clip_to_timeline(audio_file, track_index)

    def get_default_voice(self, gender):
        default_voices = {
            'male': ('George', 'jsCqWAovK2LkecY7zXl4'),
            'female': ('Matilda', 'XrExE9yKIg1WjnnlVkGX')
        }
        return default_voices.get(gender.lower(), default_voices['male'])

    def process_sfx_element(self, element):
        description = element['content']
        duration = element.get('duration', 0)
        
        self.view.update_status(f"Generating SFX: {description[:30]}...")
        
        self.audio_controller.view.current_module.set("SFX")
        self.audio_controller.view.user_input.delete("1.0", "end")
        self.audio_controller.view.user_input.insert("1.0", description)
        self.audio_controller.view.duration_var.set(str(duration))
        
        audio_file = self.audio_controller.process_sfx_request(synchronous=True)
        
        if audio_file:
            track_index = self.timeline_controller.get_or_create_track("SFX")
            self.add_clip_to_timeline(audio_file, track_index)

    def process_music_element(self, element):
        description = element['content']
        instrumental = element.get('instrumental', 'yes') == 'yes'
        
        self.view.update_status(f"Generating Music: {description[:30]}...")
        
        self.audio_controller.view.current_module.set("Music")
        self.audio_controller.view.user_input.delete("1.0", "end")
        self.audio_controller.view.user_input.insert("1.0", description)
        self.audio_controller.view.instrumental_var.set(instrumental)
        
        audio_file = self.audio_controller.process_music_request(synchronous=True)
        
        if audio_file:
            track_index = self.timeline_controller.get_or_create_track("Music")
            self.add_clip_to_timeline(audio_file, track_index)


    def add_clip_to_timeline(self, file_path, track_index):
        if file_path:
            start_time = self.timeline_controller.get_track_end_time(track_index)
            self.timeline_controller.add_audio_clip(file_path, track_index, start_time)
        else:
            logging.warning(f"Skipping addition of non-existent audio clip to timeline")
        
    def get_audio_duration(self, file_path):
        return self.timeline_controller.get_clip_duration(file_path)

    def get_voice_characteristics(self, speaker):
        analysis_file = self.get_latest_analysis_file()
        with open(analysis_file, 'r') as file:
            analysis = json.load(file)
        
        return analysis.get('voice_characteristics', {}).get(speaker, {})

    def get_suitable_voice(self, voice_char):
        # Get available voices from ElevenLabs API
        available_voices = self.audio_controller.speech_service.get_available_voices()

        gender = voice_char.get('Gender', '').lower()
        age = voice_char.get('Age', '').lower()
        accent = voice_char.get('Accent', '').lower()
        description = voice_char.get('Voice Description', '').lower()

        # Filter voices based on characteristics
        matching_voices = [
            voice for voice in available_voices
            if gender in voice['gender'].lower()
            and age in voice['age'].lower()
            and (accent == 'none' or accent in voice['accent'].lower())
        ]

        # Try to find a voice with matching description
        for voice in matching_voices:
            if description in voice['descriptive'].lower():
                return voice['name'], voice['voice_id']

        # If no matching description, choose a random voice with correct attributes
        if matching_voices:
            chosen_voice = random.choice(matching_voices)
            return chosen_voice['name'], chosen_voice['voice_id']

        # If no fitting voice at all, use default voices
        default_voices = {
            'male': ('George', 'jsCqWAovK2LkecY7zXl4'),
            'female': ('Matilda', 'XrExE9yKIg1WjnnlVkGX')
        }
        return default_voices.get(gender, default_voices['male'])

    def get_latest_analysis_file(self):
        scripts_dir = self.project_model.get_scripts_dir()
        analysis_files = [f for f in os.listdir(scripts_dir) if f.startswith("script_analysis") and f.endswith(".json")]
        if not analysis_files:
            return None
        latest_file = max(analysis_files, key=lambda f: int(f.split("script_analysis")[1].split(".json")[0]))
        return os.path.join(scripts_dir, latest_file)