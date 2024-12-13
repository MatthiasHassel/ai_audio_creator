import numpy as np
import threading
import pyaudio
import logging
import time

class AudioBufferManager:
    def __init__(self, parent_model, buffer_size=2048):
        self.parent_model = parent_model
        self.buffer_size = buffer_size
        self.current_buffer = np.zeros((buffer_size, 2), dtype=np.float32)
        self.buffer_lock = threading.Lock()
        self.playhead_position = 0
        self.buffer_position = 0
        self.is_playing = False
        self.error_count = 0
        self.max_errors = 3
        self.last_error_time = 0
        self.error_reset_interval = 5.0  # Reset error count after 5 seconds
        self.stream = None
        
        # Get device indices from config
        config = self.parent_model.config if hasattr(self.parent_model, 'config') else {}
        self.output_device_index = config.get('audio', {}).get('output_device_index', None)
        
        logging.info(f"Initialized AudioBufferManager with output device index: {self.output_device_index}")

    def handle_error(self, error_message):
        """Handle errors in a consistent way"""
        logging.error(error_message)
        self.error_count += 1
        self.last_error_time = time.time()
        
        # Stop playback if too many errors
        if self.error_count >= self.max_errors:
            logging.error("Too many consecutive errors, stopping playback")
            self.stop_playback()

    def update_device(self, device_index, pa_instance):
        """Update the audio output device"""
        try:
            was_playing = self.is_playing
            
            # Stop current playback and close existing stream
            if self.stream is not None:
                if self.stream.is_active():
                    self.stream.stop_stream()
                self.stream.close()
                self.stream = None
            
            # Update device index
            self.output_device_index = device_index
            logging.info(f"AudioBufferManager updated device index to: {device_index}")
            
            # Reset buffer state
            self.reset()
            
            # Restart playback if it was playing
            if was_playing:
                self.start_playback(pa_instance)
                
        except Exception as e:
            error_msg = f"Error updating audio device: {str(e)}"
            logging.error(error_msg)
            self.handle_error(error_msg)

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
                self.last_error_time = 0
                
        except Exception as e:
            error_msg = f"Error in buffer reset: {str(e)}"
            logging.error(error_msg)
            self.handle_error(error_msg)

    def cleanup(self):
        """Clean up resources"""
        try:
            self.stop_playback()
            self.stream = None
            self.current_buffer = None
            self.playhead_position = 0
            self.buffer_position = 0
            self.error_count = 0
            self.last_error_time = 0
            
        except Exception as e:
            error_msg = f"Error cleaning up AudioBufferManager: {str(e)}"
            logging.error(error_msg)
            self.handle_error(error_msg)


    def get_audio_data(self, in_data, frame_count, time_info, status):
        """Get audio data for playback with minimal blocking"""
        try:
            # Quick check without lock
            if not self.is_playing:
                return (np.zeros((frame_count, 2), dtype=np.float32), pyaudio.paComplete)

            # Create output buffer
            output_buffer = np.zeros((frame_count, 2), dtype=np.float32)
            
            try:
                with self.buffer_lock:
                    # Check if we need more data
                    if self.buffer_position + frame_count > self.current_buffer.shape[0]:
                        # Prepare new data
                        self._fill_buffer()
                        self.buffer_position = 0

                    # Get data and advance position
                    data = self.current_buffer[self.buffer_position:self.buffer_position + frame_count]
                    self.buffer_position += frame_count
                    self.playhead_position += frame_count / self.parent_model.sample_rate
                    
                    # Copy data to output buffer
                    output_buffer[:len(data)] = data

                self.error_count = 0  # Reset error count on successful operation
                return (output_buffer, pyaudio.paContinue)

            except Exception as e:
                current_time = time.time()
                
                # Reset error count if enough time has passed
                if current_time - self.last_error_time > self.error_reset_interval:
                    self.error_count = 0
                
                self.error_count += 1
                self.last_error_time = current_time
                
                logging.error(f"Error in get_audio_data: {str(e)}")
                
                if self.error_count >= self.max_errors:
                    logging.error("Too many consecutive errors, stopping playback")
                    self.is_playing = False
                    return (output_buffer, pyaudio.paComplete)
                
                # Return silence but keep playing
                return (output_buffer, pyaudio.paContinue)

        except Exception as e:
            logging.error(f"Critical error in get_audio_data: {str(e)}")
            return (np.zeros((frame_count, 2), dtype=np.float32), pyaudio.paComplete)

    def _fill_buffer(self):
        """Fill the current buffer with new audio data"""
        try:
            # Create new buffer
            new_buffer = np.zeros((self.buffer_size, 2), dtype=np.float32)
            end_time = self.playhead_position + self.buffer_size / self.parent_model.sample_rate

            # Get active tracks without holding any locks
            active_tracks = self.parent_model.get_active_tracks()
            
            # Process each track
            for track in active_tracks:
                if not self.is_playing:  # Check if we should stop
                    break
                    
                # Convert track volume from dB to amplitude multiplier
                track_volume_db = track.get("volume_db", 0.0)
                track_volume = self.parent_model.db_to_amplitude(track_volume_db)
                
                for clip in track['clips']:
                    if not self.is_playing:  # Check if we should stop
                        break
                        
                    if clip.x < end_time and clip.x + clip.duration > self.playhead_position:
                        try:
                            clip_start = max(0, self.playhead_position - clip.x)
                            clip_end = min(clip.duration, end_time - clip.x)
                            
                            # Get clip frames without holding buffer lock
                            clip_frames = self.parent_model.get_clip_frames(
                                clip, clip_start, clip_end - clip_start)
                            
                            if clip_frames is not None and clip_frames.size > 0:
                                buffer_start = int(max(0, (clip.x - self.playhead_position) 
                                                     * self.parent_model.sample_rate))
                                buffer_end = min(buffer_start + clip_frames.shape[0], self.buffer_size)
                                
                                if buffer_start < buffer_end:
                                    frames_to_add = clip_frames[:buffer_end-buffer_start] * track_volume
                                    new_buffer[buffer_start:buffer_end] += frames_to_add
                        
                        except Exception as e:
                            logging.error(f"Error processing clip {clip.file_path}: {str(e)}")
                            continue

            # Normalize if needed (prevent clipping)
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
                self.last_error_time = 0
                
        except Exception as e:
            logging.error(f"Error updating playhead: {str(e)}")
            
    def start_playback(self, pa_instance):
        """Start audio playback using the configured output device"""
        try:
            # Close any existing stream
            if self.stream is not None:
                if self.stream.is_active():
                    self.stream.stop_stream()
                self.stream.close()
                self.stream = None
            
            # Create new audio stream with configured output device
            self.stream = pa_instance.open(
                format=pyaudio.paFloat32,
                channels=2,
                rate=self.parent_model.sample_rate,
                output=True,
                output_device_index=self.output_device_index,
                stream_callback=self.get_audio_data,
                frames_per_buffer=self.buffer_size
            )
            
            self.is_playing = True
            self.stream.start_stream()
            logging.info(f"Started playback with output device index: {self.output_device_index}")
            
        except Exception as e:
            logging.error(f"Error starting playback: {str(e)}")
            self.is_playing = False
            
    def stop_playback(self):
        """Stop audio playback"""
        try:
            self.is_playing = False
            if self.stream is not None:
                if self.stream.is_active():
                    self.stream.stop_stream()
                self.stream.close()
                self.stream = None
            
        except Exception as e:
            logging.error(f"Error stopping playback: {str(e)}")
            
    def __del__(self):
        """Clean up audio resources"""
        try:
            if self.stream is not None:
                if self.stream.is_active():
                    self.stream.stop_stream()
                self.stream.close()
        except Exception as e:
            logging.error(f"Error cleaning up AudioBufferManager: {str(e)}")
