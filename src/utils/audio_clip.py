# src/utils/audio_clip.py
import logging
from pydub import AudioSegment

class AudioClip:
    def __init__(self, file_path, x):
        self.file_path = file_path
        self.x = x
        try:
            self.audio = AudioSegment.from_file(file_path)
            self.duration = self.audio.duration_seconds
            if self.duration == 0:
                logging.warning(f"Audio file {file_path} has zero duration, setting to 1 second")
                self.duration = 1
        except Exception as e:
            logging.error(f"Error initializing AudioClip: {str(e)}", exc_info=True)
            # Set a default duration if we can't read the file
            self.duration = 1
        logging.info(f"AudioClip created: file={file_path}, x={x}, duration={self.duration}")