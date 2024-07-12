import customtkinter as ctk
from utils.audio_visualizer import AudioVisualizer
from utils.audio_file_selector import AudioFileSelector

class AudioView:
    def __init__(self, master, config):
        self.master = master
        self.config = config
        self.create_audio_visualizer()
        self.create_audio_file_selector()
        self.create_audio_controls()
        self.seek_command = None

    def create_audio_visualizer(self):
        self.audio_visualizer = AudioVisualizer(self.master, self.on_visualizer_click)
        self.audio_visualizer.canvas_widget.grid(row=6, column=0, pady=(0, 10), padx=10, sticky="ew")

    def on_visualizer_click(self, click_time):
        if self.seek_command:
            self.seek_command(click_time)

    def set_seek_command(self, command):
        self.seek_command = command

    def create_audio_file_selector(self):
        self.audio_file_selector = AudioFileSelector(self.master, self.config)

    def create_audio_controls(self):
        audio_frame = ctk.CTkFrame(self.master)
        audio_frame.grid(row=8, column=0, pady=10, padx=10, sticky="ew")

        self.play_button = ctk.CTkButton(audio_frame, text="Play", state="disabled")
        self.play_button.grid(row=0, column=0)

        self.pause_resume_button = ctk.CTkButton(audio_frame, text="Pause", state="disabled")
        self.pause_resume_button.grid(row=0, column=1, padx=10)

        self.stop_button = ctk.CTkButton(audio_frame, text="Stop", state="disabled")
        self.stop_button.grid(row=0, column=2)

    def update_button_states(self, is_playing, is_paused):
        if is_playing:
            self.play_button.configure(state="disabled")
            self.pause_resume_button.configure(state="normal")
            self.stop_button.configure(state="normal")
            if is_paused:
                self.pause_resume_button.configure(text="Resume")
            else:
                self.pause_resume_button.configure(text="Pause")
        else:
            self.play_button.configure(state="normal")
            self.pause_resume_button.configure(state="disabled", text="Pause")
            self.stop_button.configure(state="normal")

    def set_play_command(self, command):
        self.play_button.configure(command=command)

    def set_pause_resume_command(self, command):
        self.pause_resume_button.configure(command=command)

    def set_stop_command(self, command):
        self.stop_button.configure(command=command)

    def update_waveform(self, file_path):
        self.audio_visualizer.update_waveform(file_path)

    def update_playhead(self, position):
        self.audio_visualizer.update_playhead(position)

    def clear_visualizer(self, hide_playhead=False):
        self.audio_visualizer.clear(hide_playhead)

    def quit(self):
        self.audio_visualizer.quit()

    def get_selected_file(self):
        return self.audio_file_selector.get_selected_file()
    
    def set_file_select_command(self, command):
        self.audio_file_selector.file_dropdown.configure(command=command)

    def refresh_file_list(self, module):
        self.audio_file_selector.refresh_files(module)

    def clear(self):
        self.audio_file_selector.clear()
        self.audio_visualizer.clear()
        self.update_button_states(False, False)