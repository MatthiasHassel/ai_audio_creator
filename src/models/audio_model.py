import pygame
import time

class AudioModel:
    def __init__(self):
        self.current_audio_file = None
        self.is_playing = False
        self.is_paused = False
        self.start_time = 0
        self.pause_time = 0
        self.seek_position = 0
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)

    def load_audio(self, file_path):
        self.current_audio_file = file_path
        pygame.mixer.music.load(self.current_audio_file)
        self.seek_position = 0
        print(f"Loaded audio file in model: {file_path}")  # For debugging

    def play(self):
        if self.current_audio_file:
            if self.is_paused:
                pygame.mixer.music.unpause()
                self.start_time = time.time() - self.pause_time
            else:
                pygame.mixer.music.play(start=self.seek_position)
                self.start_time = time.time() - self.seek_position
            self.is_playing = True
            self.is_paused = False
            print(f"Playing audio from position: {self.seek_position}")  # For debugging

    def pause(self):
        if self.is_playing and not self.is_paused:
            pygame.mixer.music.pause()
            self.is_paused = True
            self.pause_time = time.time() - self.start_time
            print("Paused audio")  # For debugging

    def resume(self):
        if self.is_paused:
            pygame.mixer.music.unpause()
            self.is_paused = False
            self.start_time = time.time() - self.pause_time
            print("Resumed audio")  # For debugging

    def stop(self):
        pygame.mixer.music.stop()
        self.is_playing = False
        self.is_paused = False
        self.start_time = 0
        self.pause_time = 0
        self.seek_position = 0
        print("Stopped audio")  # For debugging

    def seek(self, position):
        if self.current_audio_file:
            self.seek_position = position
            if self.is_playing:
                pygame.mixer.music.play(start=position)
                self.start_time = time.time() - position
            return True
        return False
    
    def get_current_position(self):
        if self.is_playing:
            if self.is_paused:
                return self.pause_time
            else:
                return time.time() - self.start_time
        return self.seek_position

    def quit(self):
        pygame.mixer.quit()