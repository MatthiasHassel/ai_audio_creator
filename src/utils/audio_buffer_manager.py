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
        self.is_playing = False

    def reset(self):
        with self.buffer_lock:
            self.playhead_position = 0
            self.current_buffer.fill(0)

    def get_audio_data(self, in_data, frame_count, time_info, status):
        if not self.is_playing:
            return (np.zeros((frame_count, 2), dtype=np.float32), pyaudio.paComplete)

        with self.buffer_lock:
            if frame_count <= self.current_buffer.shape[0]:
                data = self.current_buffer[:frame_count].copy()
                self.current_buffer = np.roll(self.current_buffer, -frame_count, axis=0)
                self.current_buffer[-frame_count:].fill(0)
                self.playhead_position += frame_count / self.timeline_model.sample_rate
            else:
                logging.warning("Buffer underrun")
                data = np.zeros((frame_count, 2), dtype=np.float32)

        self.prepare_next_buffer(frame_count)
        return (data, pyaudio.paContinue)

    def prepare_next_buffer(self, frame_count):
        next_buffer = np.zeros((frame_count, 2), dtype=np.float32)
        end_time = self.playhead_position + frame_count / self.timeline_model.sample_rate
        
        for track in self.timeline_model.get_active_tracks():
            for clip in track['clips']:
                if clip.x < end_time and clip.x + clip.duration > self.playhead_position:
                    clip_start = max(0, self.playhead_position - clip.x)
                    clip_end = min(clip.duration, end_time - clip.x)
                    clip_frames = self.timeline_model.get_clip_frames(clip, clip_start, int((clip_end - clip_start) * self.timeline_model.sample_rate))
                    
                    buffer_start = int(max(0, (clip.x - self.playhead_position) * self.timeline_model.sample_rate))
                    buffer_end = buffer_start + clip_frames.shape[0]
                    
                    next_buffer[buffer_start:buffer_end] += clip_frames * track.get("volume", 1.0)
        
        with self.buffer_lock:
            self.current_buffer[-frame_count:] += next_buffer

    def update_playhead(self, position):
        with self.buffer_lock:
            self.playhead_position = position
            self.current_buffer.fill(0)