import time
import logging
import pyaudio
import numpy as np
from utils.audio_clip import AudioClip
from utils.audio_buffer_manager import AudioBufferManager

class AudioGeneratorModel:
    def __init__(self, config=None):
        self.current_audio_file = None
        self.is_playing = False
        self.start_time = 0
        self.seek_position = 0
        self.duration = 0
        self.config = config or {}
        self.sample_rate = 44100
        self.channels = 2
        
        # Initialize PyAudio
        self.audio = pyaudio.PyAudio()
        self.current_clip = None
        self.playback_finished_callback = None
        
        # Get configured output device
        self.device_index = self.config.get('audio', {}).get('output_device_index')
        if self.device_index is None:
            # Fall back to default device if no configuration
            default_device = self.audio.get_default_output_device_info()
            self.device_index = default_device['index']
        
        # Initialize buffer manager
        self.buffer_manager = AudioBufferManager(self, buffer_size=2048)
        
        logging.info(f"AudioGeneratorModel using output device index: {self.device_index}")

    def update_audio_device(self, device_index):
        """Update the audio output device"""
        was_playing = self.is_playing
        current_position = self.seek_position
        
        # Stop current playback
        self.stop_preview()
        
        # Update device index
        self.device_index = device_index
        self.buffer_manager.update_device(device_index, self.audio)
        logging.info(f"Updated audio device to index: {device_index}")
        
        # Restart playback if it was playing
        if was_playing and self.current_clip:
            self.seek_position = current_position
            self.play_preview()

    def load_preview_audio(self, file_path):
        """Load a preview audio file for playback"""
        try:
            self.current_audio_file = file_path
            self.current_clip = AudioClip(file_path, 0)  # x position is 0 for preview
            self.duration = self.current_clip.duration
            self.seek_position = 0
            logging.info(f"Loaded preview audio: {file_path}")
            
        except Exception as e:
            logging.error(f"Error loading preview audio: {str(e)}")
            self.current_clip = None

    def play_preview(self):
        """Play the preview audio"""
        if not self.current_clip:
            logging.error("No preview audio loaded")
            return
            
        try:
            # Reset buffer manager state
            self.buffer_manager.reset()
            self.buffer_manager.playhead_position = self.seek_position
            
            self.is_playing = True
            self.start_time = time.time() - self.seek_position
            self.buffer_manager.is_playing = True
            self.buffer_manager.start_playback(self.audio)
            
            logging.info(f"Started preview playback with device index: {self.device_index}")
            
        except Exception as e:
            logging.error(f"Error playing preview: {str(e)}")
            self.is_playing = False

    def stop_preview(self):
        """Stop playing the preview audio"""
        try:
            self.is_playing = False
            self.buffer_manager.stop_playback()
            
        except Exception as e:
            logging.error(f"Error stopping preview: {str(e)}")

    def load_audio(self, file_path):
        self.load_preview_audio(file_path)

    def play(self):
        if self.current_audio_file:
            self.play_preview()

    def stop(self):
        self.stop_preview()

    def restart(self):
        """Restart playback from the beginning"""
        try:
            was_playing = self.is_playing
            
            # Stop current playback
            if was_playing:
                self.stop_preview()
            
            # Reset positions
            self.seek_position = 0
            self.buffer_manager.playhead_position = 0
            self.buffer_manager.buffer_position = 0
            
            # Restart if it was playing
            if was_playing:
                self.play_preview()
                
        except Exception as e:
            logging.error(f"Error restarting playback: {str(e)}")

    def seek(self, position):
        try:
            if not self.current_clip:
                return False
                
            # Ensure position is within bounds
            self.seek_position = max(0, min(position, self.duration))
            
            # Update buffer manager position
            self.buffer_manager.playhead_position = self.seek_position
            self.buffer_manager.buffer_position = 0
            
            # If currently playing, restart from new position
            if self.is_playing:
                self.stop_preview()
                self.play_preview()
                
            return True
            
        except Exception as e:
            logging.error(f"Error seeking: {str(e)}")
            return False

    def get_current_position(self):
        if self.is_playing:
            return time.time() - self.start_time
        return self.seek_position

    def set_playback_finished_callback(self, callback):
        self.playback_finished_callback = callback
    
    def get_clip_frames(self, clip, start_time, duration):
        """Get audio frames from a clip"""
        try:
            start_sample = int(round(start_time * self.sample_rate))
            num_samples = int(round(duration * self.sample_rate))
            
            return clip.get_samples(start_sample, start_sample + num_samples)
            
        except Exception as e:
            logging.error(f"Error getting clip frames: {str(e)}")
            return np.zeros((0, 2), dtype=np.float32)
    
    def get_active_tracks(self):
        """Return current clip as a track for buffer manager"""
        if self.current_clip:
            return [{
                'clips': [self.current_clip],
                'volume_db': 0.0
            }]
        return []
    
    def db_to_amplitude(self, db):
        """Convert decibels to amplitude multiplier"""
        if db <= -70:  # Mute threshold
            return 0.0
        return 10 ** (db / 20.0)
    
    def quit(self):
        try:
            self.stop_preview()
            if self.audio:
                self.audio.terminate()
        except Exception as e:
            logging.error(f"Error cleaning up AudioGeneratorModel: {str(e)}")
