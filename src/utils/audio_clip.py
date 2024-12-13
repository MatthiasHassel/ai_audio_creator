import logging
import os
import numpy as np
from utils.file_utils import read_audio_prompt
from utils.ffmpeg_utils import convert_audio_to_mp3, read_audio_file
import threading

class AudioClip:
    def __init__(self, file_path, x, index=None):
        self.file_path = file_path
        self.x = x
        self.duration = 0
        self.index = index
        self.prompt = read_audio_prompt(file_path)
        self.title = os.path.basename(file_path)
        self.sample_rate = 44100
        self.channels = 2
        self._samples = None
        self._samples_lock = threading.Lock()

        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Audio file not found: {file_path}")

            # Convert to MP3 if it's not already (this will handle WAV files too)
            if not file_path.lower().endswith('.mp3'):
                mp3_path = os.path.splitext(file_path)[0] + '.mp3'
                logging.info(f"Converting {file_path} to MP3 format")
                convert_audio_to_mp3(file_path, mp3_path)
                self.file_path = mp3_path

            # Load audio data
            samples, sample_rate, duration = read_audio_file(self.file_path)
            self.duration = duration
            
            # Ensure stereo
            if len(samples.shape) == 1:
                samples = np.column_stack((samples, samples))
            elif samples.shape[1] > 2:
                samples = samples[:, :2]
            
            # Store samples
            with self._samples_lock:
                self._samples = samples

            logging.info(f"AudioClip created: file={self.file_path}, x={x}, duration={self.duration}, index={index}")
            
        except Exception as e:
            logging.error(f"Error initializing AudioClip: {str(e)}", exc_info=True)
            raise

    def get_samples(self, start_sample=None, end_sample=None):
        """Get audio samples for the specified range"""
        with self._samples_lock:
            if self._samples is None:
                return np.zeros((0, 2), dtype=np.float32)
            
            if start_sample is None:
                start_sample = 0
            if end_sample is None:
                end_sample = len(self._samples)
            
            # Ensure bounds
            start_sample = max(0, min(start_sample, len(self._samples)))
            end_sample = max(0, min(end_sample, len(self._samples)))
            
            return self._samples[start_sample:end_sample].copy()

    def get_display_text(self):
        """Get the text to display for this clip"""
        if self.prompt:
            prompt_text = self.prompt if isinstance(self.prompt, str) else str(self.prompt)
            return prompt_text.strip("{}").strip()
        return self.title

    def __del__(self):
        """Cleanup resources"""
        try:
            with self._samples_lock:
                self._samples = None
        except Exception as e:
            logging.error(f"Error cleaning up AudioClip: {str(e)}")
