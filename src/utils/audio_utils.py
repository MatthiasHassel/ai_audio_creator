import customtkinter as ctk
import pygame
import threading
import time

class AudioPlayer:
    def __init__(self, master, audio_visualizer):
        self.master = master
        self.audio_visualizer = audio_visualizer
        self.current_audio_file = None
        pygame.mixer.init()
        self.create_audio_controls()
        self.is_playing = False
        self.is_paused = False
        self.play_thread = None
        self.current_position = 0

    def create_audio_controls(self):
        audio_frame = ctk.CTkFrame(self.master)
        audio_frame.grid(row=7, column=0, pady=10, padx=10, sticky="ew")

        self.play_button = ctk.CTkButton(audio_frame, text="Play", command=self.play_from_start, state="disabled")
        self.play_button.grid(row=0, column=0, padx=5)

        self.pause_resume_button = ctk.CTkButton(audio_frame, text="Pause", command=self.pause_resume_audio, state="disabled")
        self.pause_resume_button.grid(row=0, column=1, padx=5)

        self.stop_button = ctk.CTkButton(audio_frame, text="Stop", command=self.stop_audio, state="disabled")
        self.stop_button.grid(row=0, column=2, padx=5)

    def play_from_start(self):
        if self.current_audio_file:
            self.stop_audio()
            pygame.mixer.music.load(self.current_audio_file)
            pygame.mixer.music.play()
            self.is_playing = True
            self.is_paused = False
            self.current_position = 0
            self.pause_resume_button.configure(text="Pause")
            self.start_playhead_update()

    def pause_resume_audio(self):
        if self.is_playing and not self.is_paused:
            pygame.mixer.music.pause()
            self.is_paused = True
            self.is_playing = False
            self.pause_resume_button.configure(text="Resume")
        elif self.is_paused:
            pygame.mixer.music.unpause()
            self.is_paused = False
            self.is_playing = True
            self.pause_resume_button.configure(text="Pause")
            self.start_playhead_update()

    def start_playhead_update(self):
        if self.play_thread and self.play_thread.is_alive():
            return
        self.play_thread = threading.Thread(target=self.update_playhead)
        self.play_thread.start()

    def update_playhead(self):
        start_time = time.time() - self.current_position
        while self.is_playing and pygame.mixer.music.get_busy():
            self.current_position = time.time() - start_time
            self.audio_visualizer.update_playhead(self.current_position)
            time.sleep(0.05)  # Update every 50ms

    def stop_audio(self):
        pygame.mixer.music.stop()
        self.is_playing = False
        self.is_paused = False
        self.current_position = 0
        if self.play_thread:
            self.play_thread.join()
        self.pause_resume_button.configure(text="Pause")
        self.audio_visualizer.update_playhead(0)  # Move playhead to start

    def set_audio_file(self, audio_file):
        self.current_audio_file = audio_file
        self.current_position = 0
        self.play_button.configure(state="normal")
        self.pause_resume_button.configure(state="normal", text="Pause")
        self.stop_button.configure(state="normal")
        self.audio_visualizer.update_waveform(audio_file)
        self.audio_visualizer.update_playhead(0)  # Show playhead at start

    def clear(self):
        self.stop_audio()
        self.current_audio_file = None
        self.current_position = 0
        self.play_button.configure(state="disabled")
        self.pause_resume_button.configure(state="disabled", text="Pause")
        self.stop_button.configure(state="disabled")
        self.audio_visualizer.clear()