import customtkinter as ctk
import pygame

class AudioPlayer:
    def __init__(self, master):
        self.master = master
        self.current_audio_file = None
        pygame.mixer.init()

        self.create_audio_controls()
        self.is_playing = False
        self.is_paused = False

    def create_audio_controls(self):
        audio_frame = ctk.CTkFrame(self.master)
        audio_frame.pack(pady=10)

        self.play_button = ctk.CTkButton(audio_frame, text="Play", command=self.play_audio, state="disabled")
        self.play_button.pack(side="left", padx=5)

        self.pause_button = ctk.CTkButton(audio_frame, text="Pause", command=self.pause_audio, state="disabled")
        self.pause_button.pack(side="left", padx=5)

        self.stop_button = ctk.CTkButton(audio_frame, text="Stop", command=self.stop_audio, state="disabled")
        self.stop_button.pack(side="left", padx=5)

    def play_audio(self):
        if self.current_audio_file:
            if self.is_paused:
                pygame.mixer.music.unpause()
                self.is_paused = False
            else:
                pygame.mixer.music.load(self.current_audio_file)
                pygame.mixer.music.play()
            self.is_playing = True

    def pause_audio(self):
        if self.is_playing and not self.is_paused:
            pygame.mixer.music.pause()
            self.is_paused = True
            self.is_playing = False

    def stop_audio(self):
        pygame.mixer.music.stop()
        self.is_playing = False
        self.is_paused = False

    def set_audio_file(self, audio_file):
        self.current_audio_file = audio_file
        self.play_button.configure(state="normal")
        self.pause_button.configure(state="normal")
        self.stop_button.configure(state="normal")

    def clear(self):
        self.current_audio_file = None
        self.play_button.configure(state="disabled")
        self.pause_button.configure(state="disabled")
        self.stop_button.configure(state="disabled")
        self.stop_audio()

    def quit(self):
        pygame.mixer.quit()