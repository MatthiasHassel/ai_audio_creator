import threading
import os
from models.audio_generator_model import AudioGeneratorModel
from services.llm_service import LLMService
from services.music_service import MusicService
from services.sfx_service import SFXService
from services.speech_service import SpeechService
from tkinter import messagebox
import logging
from utils.file_utils import read_audio_prompt

class AudioGeneratorController:
    def __init__(self, model: AudioGeneratorModel, view, config):
        self.model = model
        self.view = view
        self.config = config
        self.timeline_controller = None 
        self.add_to_timeline_callback = None
        self.add_to_new_audio_files_callback = None
        self.llama_service = None
        self.music_service = None
        self.sfx_service = None
        self.speech_service = None
        self.playhead_update_id = None
        self.current_audio_file = None
        self.setup_services()
        self.setup_view_commands()
        self.model.set_playback_finished_callback(self.on_playback_finished)
        self.current_preview_file = None
        self.setup_voice_preview_handlers()

    def setup_services(self):
        self.llm_service = LLMService(self.config, self.update_status, self.update_output)
        self.music_service = MusicService(self.config, self.update_status)
        self.sfx_service = SFXService(self.config, self.update_status)
        self.speech_service = SpeechService(self.config, self.update_status)

    def setup_view_commands(self):
        self.view.set_generate_command(self.process_input)
        self.view.set_clear_command(self.clear_input)
        self.view.set_llama_command(self.improve_prompt)
        self.view.set_play_command(self.play_audio)
        self.view.set_stop_command(self.stop_audio)
        self.view.set_restart_command(self.restart_audio)
        self.view.set_add_to_timeline_command(self.add_audio_to_timeline)
        self.view.set_file_select_command(self.on_audio_file_select)
        self.view.set_visualizer_click_command(self.seek_audio)
        self.view.audio_visualizer.set_delete_callback(self.delete_audio_file)
        self.model.set_playback_finished_callback(self.on_playback_finished)

    def set_timeline_controller(self, timeline_controller):
        self.timeline_controller = timeline_controller

    def update_output_directories(self, music_dir, sfx_dir, speech_dir):
        self.music_service.update_output_directory(music_dir)
        self.sfx_service.update_output_directory(sfx_dir)
        self.speech_service.update_output_directory(speech_dir)
        self.view.audio_file_selector.refresh_files(self.view.current_module.get().lower())

    def process_input(self):
        current_module = self.view.current_module.get()
        if current_module == "Music":
            self.process_music_request()
        elif current_module == "SFX":
            self.process_sfx_request()
        elif current_module == "Speech":
            self.process_speech_request()

    def improve_prompt(self):
        user_input = self.view.user_input.get("1.0", "end-1c").strip()
        if not user_input:
            self.view.update_output("Error: Please enter some text.")
            return

        current_module = self.view.current_module.get()
        if current_module not in ["Music", "SFX"]:
            self.view.update_output("Error: Llama input is only available for Music and SFX modules.")
            return

        # Clear the output field
        self.view.output_text.configure(state="normal")
        self.view.output_text.delete("1.0", "end")
        self.view.output_text.configure(state="disabled")

        # Show the progress bar
        self.view.show_progress_bar(determinate=False)

        # Process the Llama request
        self.llm_service.process_llm_request(user_input, current_module == "Music")

    def set_add_to_timeline_callback(self, callback):
            self.add_to_timeline_callback = callback

    def set_add_to_new_audio_files_callback(self, callback):
        self.add_to_new_audio_files_callback = callback

    def _process_request(self, service_method, args, synchronous=False):
        if not args[0]:  # Check if user input is empty
            self.view.update_output("Error: Please enter some text.")
            return None

        self.view.generate_button.configure(state="disabled")
        self.model.stop()
        self.view.clear_input()
        
        self.view.show_progress_bar(determinate=False)  # Use indeterminate mode

        try:
            if synchronous:
                result = service_method(*args)
                if result:
                    self.handle_successful_generation(result)
                return result
            else:
                def process_thread():
                    result = service_method(*args)
                    if result:
                        self.view.after(0, lambda: self.handle_successful_generation(result))
                    else:
                        self.view.after(0, lambda: self.view.update_output("Error: An error occurred during audio generation."))
                    self.view.after(0, lambda: self.view.generate_button.configure(state="normal"))
                    self.view.after(0, self.view.hide_progress_bar)

                threading.Thread(target=process_thread, daemon=True).start()
                return None
        except Exception as e:
            self.view.update_output(f"Error: {str(e)}")
            return None
        finally:
            if synchronous:
                self.view.generate_button.configure(state="normal")
                self.view.hide_progress_bar()

    def process_speech_request(self, text_prompt=None, voice_id=None, synchronous=False):
        if text_prompt is None:
            text_prompt = self.view.user_input.get("1.0", "end-1c").strip()
        if voice_id is None:
            selected_voice_name = self.view.selected_voice.get()
            user_voices = self.speech_service.get_user_voices()
            voice_id = next((voice_id for name, voice_id in user_voices if name == selected_voice_name), None)
        
        if voice_id:
            return self._process_request(self.speech_service.process_speech_request, 
                                    [text_prompt, voice_id],
                                    synchronous=synchronous)
        else:
            self.view.update_output("Error: Invalid voice selected.")
            return None

    def setup_voice_preview_handlers(self):
        """Set up handlers for voice preview functionality."""
        # Connect the view's preview handlers to controller methods
        self.view.set_generate_preview_command(self.handle_voice_preview)
        self.view.set_save_preview_command(self.save_voice_preview)
        self.view.set_discard_preview_command(self.discard_voice_preview)

    def handle_voice_preview(self, description: str, text: str):
        """Handle the generation of a voice preview."""
        try:
            preview_file = self.speech_service.generate_voice_preview(description, text)
            if preview_file:
                self.current_preview_file = preview_file
                self.model.load_audio(preview_file)
                self.view.audio_visualizer.update_waveform(preview_file)
                self.view.update_button_states(False)
                return True
            else:
                self.view.update_output("Failed to generate voice preview")
                return False
        except Exception as e:
            self.view.update_output(f"Error generating voice preview: {str(e)}")
            return False

    def save_voice_preview(self, voice_name: str):
        """Save the previewed voice to the library."""
        try:
            if self.speech_service.save_preview_voice_to_library(voice_name):
                self.load_voices()  # Refresh voice list
                self.view.update_output(f"Voice '{voice_name}' saved to library")
                return True
            else:
                self.view.update_output("Failed to save voice to library")
                return False
        except Exception as e:
            self.view.update_output(f"Error saving voice to library: {str(e)}")
            return False

    def discard_voice_preview(self):
        """Discard the current voice preview."""
        try:
            self.speech_service.discard_preview_voice()
            self.current_preview_file = None
            self.view.update_output("Voice preview discarded")
            return True
        except Exception as e:
            self.view.update_output(f"Error discarding voice preview: {str(e)}")
            return False
        
    def process_sfx_request(self, synchronous=False):
        text_prompt = self.view.user_input.get("1.0", "end-1c").strip()
        duration = self.view.duration_var.get()
        return self._process_request(self.sfx_service.process_sfx_request, 
                                     [text_prompt, duration],
                                     synchronous)

    def process_music_request(self, text_prompt=None, make_instrumental=None, synchronous=False):
        if text_prompt is None:
            text_prompt = self.view.user_input.get("1.0", "end-1c").strip()
        if make_instrumental is None:
            make_instrumental = self.view.instrumental_var.get()
        
        return self._process_request(self.music_service.process_music_request, 
                                [text_prompt, make_instrumental],
                                synchronous)
        
    def handle_successful_generation(self, result):
        self.view.update_output(f"Audio generated successfully. File saved to: {result}")
        self.view.update_status("Ready")
        self.view.audio_file_selector.refresh_files(self.view.current_module.get().lower())
        self.model.load_audio(result)
        self.view.audio_visualizer.update_waveform(result)
        self.current_audio_file = result
        self.view.update_button_states(False)
        self.on_audio_file_select(result)  # Manually trigger file selection

    def seek_audio(self, position):
        if self.model.seek(position):
            self.view.audio_visualizer.update_playhead(position)
            if self.model.is_playing:
                self.start_playhead_update()

    def play_audio(self):
        if self.current_audio_file:
            self.model.play()
            self.view.update_button_states(self.model.is_playing)
            self.start_playhead_update()
        else:
            logging.warning("No audio file loaded")
    
    def on_playback_finished(self):
        """Handle playback finished event."""
        self.view.after(0, self.view.on_playback_finished)

    def _update_ui_after_playback(self):
        self.model.seek(0)  # Reset the seek position to the start
        self.view.update_button_states(False)
        self.stop_playhead_update()
        self.view.audio_visualizer.update_playhead(0)  # Reset the visual playhead to the start
        
    def stop_audio(self):
        self.model.stop()
        self.view.update_button_states(self.model.is_playing)
        self.stop_playhead_update()

    def start_playhead_update(self):
        self.stop_playhead_update()  # Ensure no existing update is running
        self.update_playhead()

    def stop_playhead_update(self):
        if self.playhead_update_id:
            self.view.after_cancel(self.playhead_update_id)
            self.playhead_update_id = None

    def restart_audio(self):
        self.model.restart()
        self.view.update_button_states(self.model.is_playing)
        self.view.audio_visualizer.update_playhead(0)
        if self.model.is_playing:
            self.start_playhead_update()
        else:
            self.stop_playhead_update()

    def update_playhead(self):
        if self.model.is_playing:
            current_time = self.model.get_current_position()
            self.view.audio_visualizer.update_playhead(current_time)
            self.playhead_update_id = self.view.after(50, self.update_playhead)  # Update every 50ms

    def on_audio_file_select(self, file_path):
        if file_path and os.path.exists(file_path):
            self.model.load_audio(file_path)
            self.view.audio_visualizer.update_waveform(file_path)
            self.view.update_button_states(False)
            self.current_audio_file = file_path
            self.view.add_to_timeline_button.configure(state="normal")
            
            # Display the prompt used to generate the audio
            prompt = read_audio_prompt(file_path)
            if prompt:
                self.view.update_output(f"Prompt used: {prompt}")
            else:
                self.view.update_output("No prompt information available for this file.")
            
            logging.info(f"Audio file loaded: {file_path}")
        else:
            logging.warning(f"Invalid file path: {file_path}")
            self.view.add_to_timeline_button.configure(state="disabled")

    def clear_input(self):
        self.view.clear_input()

    def load_voices(self):
        voices = self.speech_service.get_user_voices()
        self.view.update_voice_dropdown(voices)

    def add_audio_to_timeline(self):
        selected_file = self.view.audio_file_selector.get_selected_file()
        if selected_file and self.add_to_timeline_callback:
            # Use the callback to add the file to new_audio_files
            if self.add_to_new_audio_files_callback:
                self.add_to_new_audio_files_callback(selected_file)

            # Use the callback to add the clip to the currently selected track
            self.add_to_timeline_callback(selected_file)
            self.view.update_status(f"Added audio to the selected track")
        else:
            self.view.update_status("No audio file selected or timeline not available")

    def update_status(self, message):
        self.view.update_status(message)

    def update_output(self, message):
        self.view.output_text.configure(state="normal")
        self.view.output_text.delete("1.0", "end")
        self.view.output_text.insert("end", message)
        self.view.output_text.configure(state="disabled")
        self.view.hide_progress_bar()
        
    def set_show_timeline_command(self, command):
        self.view.set_timeline_command(command)

    def quit(self):
        self.model.quit()

    def delete_audio_file(self, file_path):
        try:
            if os.path.exists(file_path):
                is_in_timeline = False
                
                # Check if the file is in the timeline, if timeline_controller is available
                if self.timeline_controller:
                    is_in_timeline = self.timeline_controller.is_clip_in_timeline(file_path)
                
                if is_in_timeline:
                    # Show confirmation dialog
                    confirm = messagebox.askyesno(
                        "Confirm Deletion",
                        f"The file {os.path.basename(file_path)} is used in the timeline. "
                        "Deleting it will also remove it from the timeline. Are you sure you want to proceed?",
                        icon='warning'
                    )
                    if not confirm:
                        return

                # Delete the file
                os.remove(file_path)
                logging.info(f"Deleted audio file: {file_path}")
                
                # Remove from timeline if necessary
                if is_in_timeline and self.timeline_controller:
                    self.timeline_controller.remove_clip_from_all_tracks(file_path)
                
                # Clear the audio visualizer
                self.view.audio_visualizer.clear()
                
                # Clear the current audio file
                self.current_audio_file = None
                
                # Refresh the audio file selector
                current_module = self.view.current_module.get().lower()
                self.view.audio_file_selector.refresh_files(current_module)
                
                # Update the view
                self.view.update_status(f"Deleted audio file: {os.path.basename(file_path)}")
                self.view.update_button_states(False)
                self.view.add_to_timeline_button.configure(state="disabled")
            else:
                logging.warning(f"File not found: {file_path}")
                self.view.update_status("Error: File not found")
        except Exception as e:
            logging.error(f"Error deleting file {file_path}: {str(e)}", exc_info=True)
            self.view.update_status(f"Error deleting file: {str(e)}")

