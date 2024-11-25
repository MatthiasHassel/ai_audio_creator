import pygame
import time
import threading

class AudioGeneratorModel:
    def __init__(self):
        self.current_audio_file = None
        self.is_playing = False
        self.start_time = 0
        self.pause_time = 0
        self.seek_position = 0
        self.duration = 0
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
        self.playback_finished_callback = None

    def load_preview_audio(self, file_path):
        """Load a preview audio file for playback"""
        self.preview_audio_file = file_path
        self.preview_sound = pygame.mixer.Sound(file_path)
        self.preview_channel = None

    def play_preview(self):
        """Play the preview audio"""
        if hasattr(self, 'preview_audio_file'):
            if self.preview_channel and self.preview_channel.get_busy():
                self.preview_channel.stop()
            self.preview_channel = self.preview_sound.play()

    def stop_preview(self):
        """Stop playing the preview audio"""
        if hasattr(self, 'preview_channel') and self.preview_channel:
            self.preview_channel.stop()

    def load_audio(self, file_path):
        self.current_audio_file = file_path
        pygame.mixer.music.load(self.current_audio_file)
        self.seek_position = 0
        sound = pygame.mixer.Sound(file_path)
        self.duration = sound.get_length()

    def play(self):
        if self.current_audio_file:
            pygame.mixer.music.play(start=self.seek_position)
            self.start_time = time.time() - self.seek_position
            self.is_playing = True
            threading.Thread(target=self._monitor_playback, daemon=True).start()

    def _monitor_playback(self):
        while self.is_playing:
            if not pygame.mixer.music.get_busy():
                self.stop()
                if self.playback_finished_callback:
                    self.playback_finished_callback()
                break
            time.sleep(0.1)

    def set_playback_finished_callback(self, callback):
        self.playback_finished_callback = callback

    def stop(self):
        pygame.mixer.music.stop()
        self.is_playing = False
        self.seek_position = self.get_current_position()

    def restart(self):
        self.seek_position = 0
        if self.is_playing:
            self.play()

    def seek(self, position):
        self.seek_position = max(0, min(position, self.duration))
        if self.is_playing:
            pygame.mixer.music.play(start=self.seek_position)
            self.start_time = time.time() - self.seek_position
        return True

    def get_current_position(self):
        if self.is_playing:
            return time.time() - self.start_time
        return self.seek_position
    
    def quit(self):
        pygame.mixer.quit()