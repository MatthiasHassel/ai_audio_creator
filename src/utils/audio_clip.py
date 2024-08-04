from pydub import AudioSegment
import logging
import os

class AudioClip:
    def __init__(self, file_path, x, index=None):
        self.file_path = file_path
        self.x = x
        self.duration = 0
        self.audio = None
        self.index = index

        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Audio file not found: {file_path}")

            # Use pydub to load the audio file
            self.audio = AudioSegment.from_file(file_path)
            
            # Ensure the audio is at 44.1kHz
            if self.audio.frame_rate != 44100:
                raise ValueError(f"Audio file {file_path} is not at 44.1kHz. It should have been converted during import.")
            
            self.duration = len(self.audio) / 1000.0  # Duration in seconds

            logging.info(f"AudioClip created: file={file_path}, x={x}, duration={self.duration}, index={index}")
        except Exception as e:
            logging.error(f"Error initializing AudioClip: {str(e)}", exc_info=True)
            raise

    def get_sample_array(self):
        if self.audio:
            return self.audio.get_array_of_samples()
        return []

    # Placeholder for actual playback implementation
    def play(self, start_time=0):
        logging.info(f"Playing {self.file_path} from {start_time}")
        # Implement actual playback here