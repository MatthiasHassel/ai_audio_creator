from pydub import AudioSegment
import logging
import os
from utils.file_utils import read_audio_prompt
import numpy as np
import soundfile as sf

class AudioClip:
    def __init__(self, file_path, x, index=None):
        self.file_path = file_path
        self.x = x
        self.duration = 0
        self.audio = None
        self.index = index
        self.prompt = read_audio_prompt(file_path)
        self.title = os.path.basename(file_path)
        self.sample_rate = 44100
        self.channels = 2

        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Audio file not found: {file_path}")

            # Try to load with soundfile first (more efficient for WAV files)
            try:
                with sf.SoundFile(file_path) as sf_file:
                    if sf_file.samplerate != self.sample_rate:
                        logging.info(f"Converting {file_path} from {sf_file.samplerate}Hz to {self.sample_rate}Hz")
                        # Load the audio data
                        audio_data = sf_file.read()
                        # Convert sample rate using scipy's resample
                        from scipy import signal
                        num_samples = int(len(audio_data) * self.sample_rate / sf_file.samplerate)
                        audio_data = signal.resample(audio_data, num_samples)
                        # Save with new sample rate
                        sf.write(file_path, audio_data, self.sample_rate)
                    self.duration = len(sf_file) / sf_file.samplerate
                    
            except Exception as sf_error:
                logging.info(f"Could not load with soundfile, trying pydub: {str(sf_error)}")
                # Fallback to pydub for other formats
                self.audio = AudioSegment.from_file(file_path)
                
                if self.audio.frame_rate != self.sample_rate:
                    logging.info(f"Converting {file_path} from {self.audio.frame_rate}Hz to {self.sample_rate}Hz")
                    self.audio = self.audio.set_frame_rate(self.sample_rate)
                    # Export as WAV for better performance
                    wav_path = os.path.splitext(file_path)[0] + '.wav'
                    self.audio.export(wav_path, format="wav")
                    self.file_path = wav_path  # Update file path to point to WAV file
                    self.audio = AudioSegment.from_file(self.file_path)  # Reload the converted file
                
                if self.audio.channels != self.channels:
                    logging.info(f"Converting {file_path} from {self.audio.channels} to {self.channels} channels")
                    if self.audio.channels == 1:
                        self.audio = self.audio.set_channels(2)
                    else:
                        self.audio = self.audio.set_channels(2)
                
                self.duration = len(self.audio) / 1000.0  # Duration in seconds

            logging.info(f"AudioClip created: file={file_path}, x={x}, duration={self.duration}, index={index}")
            
        except Exception as e:
            logging.error(f"Error initializing AudioClip: {str(e)}", exc_info=True)
            raise

    def get_sample_array(self):
        """Get the audio samples as a numpy array"""
        try:
            # Try soundfile first
            try:
                with sf.SoundFile(self.file_path) as sf_file:
                    audio_data = sf_file.read()
                    if audio_data.ndim == 1:  # Mono
                        audio_data = np.column_stack((audio_data, audio_data))
                    return audio_data
            except Exception:
                # Fallback to pydub
                if self.audio is None:
                    self.audio = AudioSegment.from_file(self.file_path)
                
                samples = np.array(self.audio.get_array_of_samples(), dtype=np.float32)
                
                # Reshape based on number of channels
                if self.audio.channels == 1:
                    samples = np.column_stack((samples, samples))
                else:
                    samples = samples.reshape((-1, 2))
                
                # Normalize to float32 range [-1, 1]
                return samples / 32768.0
                
        except Exception as e:
            logging.error(f"Error getting sample array: {str(e)}")
            return np.zeros((0, 2), dtype=np.float32)

    def get_display_text(self):
        """Get the text to display for this clip"""
        if self.prompt:
            # Ensure prompt is a string and remove curly braces
            prompt_text = self.prompt if isinstance(self.prompt, str) else str(self.prompt)
            return prompt_text.strip("{}").strip()
        return self.title

    def __del__(self):
        """Cleanup resources"""
        try:
            if hasattr(self, 'audio') and self.audio is not None:
                del self.audio
        except Exception as e:
            logging.error(f"Error cleaning up AudioClip: {str(e)}")
