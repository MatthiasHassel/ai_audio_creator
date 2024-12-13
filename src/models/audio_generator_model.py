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
        
        # Initialize PyAudio and buffer manager
        self.audio = pyaudio.PyAudio()
        self.audio_stream = None
        self.buffer_manager = AudioBufferManager(self, buffer_size=2048)
        self.current_clip = None
        self.playback_finished_callback = None
        
        # Get configured output device
        self.device_index = self.config.get('audio', {}).get('output_device_index')
        if self.device_index is None:
            # Fall back to default device if no configuration
            default_device = self.audio.get_default_output_device_info()
            self.device_index = default_device['index']
        
        logging.info(f"AudioGeneratorModel using output device index: {self.device_index}")

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
            if self.audio_stream and self.audio_stream.is_active():
                self.audio_stream.stop_stream()
                self.audio_stream.close()
            
            def audio_callback(in_data, frame_count, time_info, status):
                if status:
                    logging.warning(f"Audio callback status: {status}")
                
                if not self.is_playing:
                    return (None, pyaudio.paComplete)
                
                try:
                    # Get audio data from the clip
                    start_sample = int(self.seek_position * self.sample_rate)
                    samples = self.current_clip.get_samples(start_sample, start_sample + frame_count)
                    
                    if len(samples) < frame_count:
                        # End of file reached
                        self.is_playing = False
                        if self.playback_finished_callback:
                            self.playback_finished_callback()
                        return (samples.tobytes(), pyaudio.paComplete)
                    
                    self.seek_position += frame_count / self.sample_rate
                    return (samples.tobytes(), pyaudio.paContinue)
                    
                except Exception as e:
                    logging.error(f"Error in audio callback: {str(e)}")
                    return (None, pyaudio.paComplete)
            
            # Create and start the stream
            self.audio_stream = self.audio.open(
                format=pyaudio.paFloat32,
                channels=self.channels,
                rate=self.sample_rate,
                output=True,
                output_device_index=self.device_index,
                stream_callback=audio_callback,
                frames_per_buffer=2048
            )
            
            self.is_playing = True
            self.start_time = time.time() - self.seek_position
            self.audio_stream.start_stream()
            
            logging.info(f"Started preview playback with device index: {self.device_index}")
            
        except Exception as e:
            logging.error(f"Error playing preview: {str(e)}")
            self.is_playing = False

    def stop_preview(self):
        """Stop playing the preview audio"""
        try:
            self.is_playing = False
            if self.audio_stream:
                self.audio_stream.stop_stream()
                self.audio_stream.close()
                self.audio_stream = None
            
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
        self.seek_position = 0
        if self.is_playing:
            self.stop_preview()
            self.play_preview()

    def seek(self, position):
        try:
            if not self.current_clip:
                return False
                
            # Ensure position is within bounds
            self.seek_position = max(0, min(position, self.duration))
            
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
    
    def quit(self):
        try:
            if self.audio_stream:
                self.audio_stream.stop_stream()
                self.audio_stream.close()
            if self.audio:
                self.audio.terminate()
        except Exception as e:
            logging.error(f"Error cleaning up AudioGeneratorModel: {str(e)}")
