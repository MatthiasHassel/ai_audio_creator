import threading
import os
from models.audio_model import AudioModel
from services.llama_service import LlamaService
from services.music_service import MusicService
from services.sfx_service import SFXService
from services.speech_service import SpeechService

class AudioController:
    def __init__(self, model: AudioModel, view, config):
        self.model = model
        self.view = view
        self.config = config
        self.llama_service = None
        self.music_service = None
        self.sfx_service = None
        self.speech_service = None
        self.playhead_update_id = None
        self.setup_services()
        self.setup_view_commands()

    def setup_services(self):
        self.llama_service = LlamaService(self.config, self.update_status)
        self.music_service = MusicService(self.config, self.update_status)
        self.sfx_service = SFXService(self.config, self.update_status)
        self.speech_service = SpeechService(self.config, self.update_status)

    def setup_view_commands(self):
        self.view.set_generate_command(self.process_input)
        self.view.set_clear_command(self.clear_input)
        self.view.set_llama_command(self.process_llama_input)
        self.view.set_play_command(self.play_audio)
        self.view.set_pause_resume_command(self.pause_resume_audio)
        self.view.set_stop_command(self.stop_audio)
        self.view.set_file_select_command(self.on_audio_file_select)
        self.view.set_visualizer_click_command(self.seek_audio)

    def process_input(self):
        current_module = self.view.current_module.get()
        if current_module == "Music":
            self.process_music_request()
        elif current_module == "SFX":
            self.process_sfx_request()
        elif current_module == "Speech":
            self.process_speech_request()

    def process_llama_input(self):
        user_input = self.view.user_input.get("1.0", "end-1c").strip()
        if not user_input:
            self.view.update_output("Error: Please enter some text.")
            return

        current_module = self.view.current_module.get()
        if current_module == "Music":
            result = self.llama_service.get_llama_musicprompt(user_input)
        elif current_module == "SFX":
            result = self.llama_service.get_llama_sfx(user_input)
        else:
            self.view.update_output("Error: Llama3 input is only available for Music and SFX modules.")
            return

        if result:
            self.view.user_input.delete("1.0", "end")
            self.view.user_input.insert("1.0", result)
        else:
            self.view.update_output("Error: Failed to process input with Llama3.")

    def process_music_request(self):
        self._process_request(self.music_service.process_music_request, 
                              [self.view.user_input.get("1.0", "end-1c").strip(), self.view.instrumental_var.get()])

    def process_sfx_request(self):
        self._process_request(self.sfx_service.process_sfx_request, 
                              [self.view.user_input.get("1.0", "end-1c").strip(), self.view.duration_var.get()])

    def process_speech_request(self):
        selected_voice_name = self.view.selected_voice.get()
        voice_id = next((voice[1] for voice in self.speech_service.get_available_voices() if voice[0] == selected_voice_name), None)
        if voice_id:
            self._process_request(self.speech_service.process_speech_request, 
                                  [self.view.user_input.get("1.0", "end-1c").strip(), voice_id])
        else:
            self.view.update_output("Error: Invalid voice selected.")

    def _process_request(self, service_method, args):
        if not args[0]:  # Check if user input is empty
            self.view.update_output("Error: Please enter some text.")
            return

        self.view.generate_button.configure(state="disabled")
        self.model.stop()
        self.view.clear_input()
        
        self.view.show_progress_bar(determinate=False)  # Use indeterminate mode for unknown duration

        def process_thread():
            result = service_method(*args)
            if result:
                self.view.update_output(f"Audio generated successfully. File saved to: {result}")
                self.view.update_status("Ready")
                self.view.audio_file_selector.refresh_files(self.view.current_module.get().lower())
                self.model.load_audio(result)
                self.view.audio_visualizer.update_waveform(result)
            else:
                self.view.update_output("Error: An error occurred during audio generation.")
            self.view.generate_button.configure(state="normal")
            self.view.hide_progress_bar()

        threading.Thread(target=process_thread, daemon=True).start()

    def seek_audio(self, position):
        if self.model.seek(position):
            self.stop_playhead_update()  # Stop any existing playhead updates
            self.view.audio_visualizer.update_playhead(position)
            if self.model.is_playing:
                self.start_playhead_update()
            else:
                self.play_audio()

    def play_audio(self):
        if self.model.current_audio_file:
            self.model.play()
            self.view.update_button_states(self.model.is_playing, self.model.is_paused)
            self.start_playhead_update()
        else:
            print("No audio file loaded")  # For debugging

    def pause_resume_audio(self):
        if self.model.is_playing and not self.model.is_paused:
            self.model.pause()
            self.stop_playhead_update()
        elif self.model.is_paused:
            self.model.resume()
            self.start_playhead_update()
        self.view.update_button_states(self.model.is_playing, self.model.is_paused)

    def stop_audio(self):
        self.model.stop()
        self.view.update_button_states(self.model.is_playing, self.model.is_paused)
        self.stop_playhead_update()
        self.view.audio_visualizer.update_playhead(0)

    def start_playhead_update(self):
        self.stop_playhead_update()  # Ensure no existing update is running
        self.update_playhead()

    def stop_playhead_update(self):
        if self.playhead_update_id:
            self.view.after_cancel(self.playhead_update_id)
            self.playhead_update_id = None

    def update_playhead(self):
        if self.model.is_playing and not self.model.is_paused:
            current_time = self.model.get_current_position()
            self.view.audio_visualizer.update_playhead(current_time)
            self.playhead_update_id = self.view.after(50, self.update_playhead)  # Update every 50ms

    def on_audio_file_select(self, file_path):
        if file_path and os.path.exists(file_path):
            self.model.load_audio(file_path)
            self.view.audio_visualizer.update_waveform(file_path)
            self.view.update_button_states(False, False)  # Enable play button
            print(f"Loaded audio file: {file_path}")  # For debugging
        else:
            print(f"Invalid file path: {file_path}")  # For debugging

    def clear_input(self):
        self.view.clear_input()
        self.model.stop()
        self.view.audio_visualizer.clear()
        self.view.audio_file_selector.refresh_files(self.view.current_module.get().lower())

    def load_voices(self):
        try:
            voices = self.speech_service.get_available_voices()
            if voices:
                voice_names = [voice[0] for voice in voices]
                self.view.selected_voice.set(voice_names[0])
                self.view.voice_dropdown.configure(values=voice_names)
            else:
                self.view.update_output("Warning: No voices available.")
        except Exception as e:
            self.view.update_output(f"Error: Failed to load voices: {str(e)}")

    def update_status(self, message):
        self.view.update_status(message)

    def quit(self):
        self.model.quit()