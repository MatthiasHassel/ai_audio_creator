import numpy as np
import threading
import pyaudio
import logging

class AudioBufferManager:
    def __init__(self, timeline_model, buffer_size=2048):
        self.timeline_model = timeline_model
        self.buffer_size = buffer_size
        self.current_buffer = np.zeros((buffer_size, 2), dtype=np.float32)
        self.buffer_lock = threading.Lock()
        self.playhead_position = 0
        self.buffer_position = 0
        self.is_playing = False
        self.error_count = 0
        self.max_errors = 3

    def reset(self):
        """Reset buffer state without blocking"""
        try:
            # Create new buffer instead of waiting for lock
            new_buffer = np.zeros((self.buffer_size, 2), dtype=np.float32)
            
            # Quick swap with minimal locking
            with self.buffer_lock:
                self.current_buffer = new_buffer
                self.playhead_position = 0
                self.buffer_position = 0
                self.error_count = 0
                
        except Exception as e:
            logging.error(f"Error in buffer reset: {str(e)}")

    def get_audio_data(self, in_data, frame_count, time_info, status):
        """Get audio data for playback with minimal blocking"""
        try:
            # Quick check without lock
            if not self.is_playing:
                return (np.zeros((frame_count, 2), dtype=np.float32), pyaudio.paComplete)

            with self.buffer_lock:
                # Check if we need more data
                if self.buffer_position + frame_count > self.current_buffer.shape[0]:
                    # Prepare new data
                    self._fill_buffer()
                    self.buffer_position = 0

                # Get data and advance position
                data = self.current_buffer[self.buffer_position:self.buffer_position + frame_count].copy()
                self.buffer_position += frame_count
                self.playhead_position += frame_count / self.timeline_model.sample_rate
                self.error_count = 0

            return (data, pyaudio.paContinue)

        except Exception as e:
            logging.error(f"Error in get_audio_data: {str(e)}")
            self.error_count += 1
            
            if self.error_count >= self.max_errors:
                logging.error("Too many consecutive errors, stopping playback")
                self.is_playing = False
                return (np.zeros((frame_count, 2), dtype=np.float32), pyaudio.paComplete)
            
            # Return silence but keep playing
            return (np.zeros((frame_count, 2), dtype=np.float32), pyaudio.paContinue)

    def _fill_buffer(self):
        """Fill the current buffer with new audio data"""
        try:
            # Create new buffer
            new_buffer = np.zeros((self.buffer_size, 2), dtype=np.float32)
            end_time = self.playhead_position + self.buffer_size / self.timeline_model.sample_rate

            # Get active tracks without holding any locks
            active_tracks = self.timeline_model.get_active_tracks()
            
            # Process each track
            for track in active_tracks:
                if not self.is_playing:  # Check if we should stop
                    break
                    
                # Convert track volume from dB to amplitude multiplier
                track_volume_db = track.get("volume_db", 0.0)
                track_volume = self.timeline_model.db_to_amplitude(track_volume_db)
                
                for clip in track['clips']:
                    if not self.is_playing:  # Check if we should stop
                        break
                        
                    if clip.x < end_time and clip.x + clip.duration > self.playhead_position:
                        try:
                            clip_start = max(0, self.playhead_position - clip.x)
                            clip_end = min(clip.duration, end_time - clip.x)
                            
                            # Get clip frames without holding buffer lock
                            clip_frames = self.timeline_model.get_clip_frames(
                                clip, clip_start, clip_end - clip_start)
                            
                            if clip_frames is not None and clip_frames.size > 0:
                                buffer_start = int(max(0, (clip.x - self.playhead_position) 
                                                     * self.timeline_model.sample_rate))
                                buffer_end = min(buffer_start + clip_frames.shape[0], self.buffer_size)
                                
                                if buffer_start < buffer_end:
                                    frames_to_add = clip_frames[:buffer_end-buffer_start] * track_volume
                                    new_buffer[buffer_start:buffer_end] += frames_to_add
                        
                        except Exception as e:
                            logging.error(f"Error processing clip {clip.file_path}: {str(e)}")
                            continue

            # Normalize if needed
            max_amplitude = np.max(np.abs(new_buffer))
            if max_amplitude > 1.0:
                new_buffer = new_buffer / max_amplitude

            # Update current buffer
            self.current_buffer = new_buffer

        except Exception as e:
            logging.error(f"Error filling buffer: {str(e)}")
            self.current_buffer.fill(0)
        
    def update_playhead(self, position):
        """Update playhead position without blocking"""
        try:
            # Create new buffer instead of waiting for lock
            new_buffer = np.zeros((self.buffer_size, 2), dtype=np.float32)
            
            # Quick swap with minimal locking
            with self.buffer_lock:
                self.current_buffer = new_buffer
                self.playhead_position = position
                self.buffer_position = 0
                self.error_count = 0
                
        except Exception as e:
            logging.error(f"Error updating playhead: {str(e)}")
