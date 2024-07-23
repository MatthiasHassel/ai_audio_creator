# timeline_model.py
import pyaudio
import numpy as np
import time
import logging
from pydub import AudioSegment
from utils.audio_clip import AudioClip

class TimelineModel:
    def __init__(self):
        self.tracks = []
        self.is_modified = False
        self.is_playing = False
        self.playhead_position = 0
        self.start_time = 0
        self.p = pyaudio.PyAudio()
        self.stream = None
        self.active_clips = []
        self.audio_cache = {}
        self.sample_rate = 44100
        self.channels = 2

    def play_timeline(self, active_tracks):
        if not self.is_playing:
            self.is_playing = True
            self.start_time = time.time() - self.playhead_position
            self.active_clips = self.get_active_clips(active_tracks)
            self.stream = self.p.open(format=pyaudio.paFloat32,
                                      channels=self.channels,
                                      rate=self.sample_rate,
                                      output=True,
                                      frames_per_buffer=1024,
                                      stream_callback=self.audio_callback)
            self.stream.start_stream()
            logging.info("Timeline model: playback started")

    def stop_timeline(self):
        if self.is_playing:
            self.is_playing = False
            self.playhead_position = time.time() - self.start_time
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
            self.stream = None
            logging.info("Timeline model: playback stopped")

    def audio_callback(self, in_data, frame_count, time_info, status):
        current_time = time.time() - self.start_time
        output = np.zeros((frame_count, self.channels), dtype=np.float32)

        for clip, track in self.active_clips:
            if clip.x <= current_time < clip.x + clip.duration:
                clip_time = current_time - clip.x
                clip_frames = self.get_clip_frames(clip, clip_time, frame_count)
                volume = track.get("volume", 1.0)
                
                # Ensure clip_frames match the output shape
                if clip_frames.shape[0] < frame_count:
                    pad_length = frame_count - clip_frames.shape[0]
                    clip_frames = np.pad(clip_frames, ((0, pad_length), (0, 0)))
                elif clip_frames.shape[0] > frame_count:
                    clip_frames = clip_frames[:frame_count, :]

                output += clip_frames * volume

        return (output, pyaudio.paContinue)

    def get_clip_frames(self, clip, start_time, frame_count):
        if clip.file_path not in self.audio_cache:
            audio = AudioSegment.from_file(clip.file_path)
            audio = audio.set_channels(self.channels)
            audio = audio.set_frame_rate(self.sample_rate)
            self.audio_cache[clip.file_path] = audio

        audio = self.audio_cache[clip.file_path]
        start_sample = int(start_time * self.sample_rate)
        end_sample = start_sample + frame_count
        
        clip_segment = audio[start_sample * 1000 / self.sample_rate : end_sample * 1000 / self.sample_rate]
        samples = np.array(clip_segment.get_array_of_samples())

        if clip_segment.channels == 2:
            samples = samples.reshape((-1, 2))
        else:
            samples = np.column_stack((samples, samples))

        return samples.astype(np.float32) / 32768.0

    def get_active_clips(self, active_tracks):
        active_clips = []
        for track in active_tracks:
            for clip in track['clips']:
                active_clips.append((clip, track))
        return active_clips
        
    def add_track(self, track_data):
        self.tracks.append(track_data)
        self.is_modified = True

    def get_track_index(self, track):
        return self.tracks.index(track)

    def rename_track(self, track_index, new_name):
        if 0 <= track_index < len(self.tracks):
            self.tracks[track_index]['name'] = new_name
            self.is_modified = True

    def remove_track(self, track_index):
        if 0 <= track_index < len(self.tracks):
            del self.tracks[track_index]
            self.is_modified = True

    def add_clip_to_track(self, track_index, clip):
        if track_index >= len(self.tracks):
            # Add new tracks if necessary
            for _ in range(track_index - len(self.tracks) + 1):
                self.tracks.append({"name": f"Track {len(self.tracks) + 1}", "clips": []})
        
        self.tracks[track_index]['clips'].append(clip)
        self.is_modified = True

    def remove_clip_from_track(self, track_index, clip_index):
        if 0 <= track_index < len(self.tracks):
            if 0 <= clip_index < len(self.tracks[track_index]['clips']):
                del self.tracks[track_index]['clips'][clip_index]
                self.is_modified = True

    def clear_tracks(self):
        self.tracks.clear()
        self.is_modified = True

    def get_tracks(self):
        return self.tracks

    def set_tracks(self, tracks_data):
        self.tracks = tracks_data
        self.is_modified = True

    def mark_as_saved(self):
        self.is_modified = False

    def update_track_solo_mute(self, track):
        track_index = self.get_track_index(track)
        if 0 <= track_index < len(self.tracks):
            self.tracks[track_index]["solo"] = track.get("solo", False)
            self.tracks[track_index]["mute"] = track.get("mute", False)
            self.is_modified = True
        if self.is_playing:
            self.active_clips = self.get_active_clips(self.get_active_tracks())

    def update_track_volume(self, track):
        track_index = self.get_track_index(track)
        if 0 <= track_index < len(self.tracks):
            self.tracks[track_index]["volume"] = track.get("volume", 1.0)
            self.is_modified = True

    def update_playhead(self):
        if self.is_playing:
            current_time = time.time() - self.start_time
            self.playhead_position = current_time
            self.update_active_sounds()
            self.play_new_clips(self.get_active_tracks())
        return self.playhead_position

    def set_playhead_position(self, position):
        self.playhead_position = max(0, position)
        if self.is_playing:
            self.start_time = time.time() - self.playhead_position
            self.stop_timeline()
            active_tracks = self.get_active_tracks()
            self.play_timeline(active_tracks)

    def get_playhead_position(self):
        if self.is_playing:
            return time.time() - self.start_time
        return self.playhead_position
            
    def get_track_index_for_clip(self, clip):
        for i, track in enumerate(self.tracks):
            if clip in track['clips']:
                return i
        return -1

    def remove_clip_from_track(self, track_index, clip):
        if 0 <= track_index < len(self.tracks):
            if clip in self.tracks[track_index]['clips']:
                self.tracks[track_index]['clips'].remove(clip)
                self.is_modified = True
                # Remove the clip from active_clips if it's there
                self.active_clips = [(c, t) for c, t in self.active_clips if c != clip]

    def move_clip(self, clip, new_x, old_track_index, new_track_index):
        if 0 <= old_track_index < len(self.tracks) and 0 <= new_track_index < len(self.tracks):
            if clip in self.tracks[old_track_index]['clips']:
                self.tracks[old_track_index]['clips'].remove(clip)
                self.tracks[new_track_index]['clips'].append(clip)
                clip.x = max(0, new_x)
                self.is_modified = True
                return True
        return False
    
    def get_active_tracks(self):
        solo_tracks = [track for track in self.tracks if track.get("solo", False)]
        if solo_tracks:
            return solo_tracks
        return [track for track in self.tracks if not track.get("mute", False)]
    
    def get_serializable_tracks(self):
        serializable_tracks = []
        for track in self.tracks:
            serializable_clips = []
            for clip in track['clips']:
                serializable_clips.append({
                    'file_path': clip.file_path,
                    'x': clip.x,
                    'duration': clip.duration
                })
            serializable_tracks.append({
                'name': track['name'],
                'clips': serializable_clips,
                'solo': track.get('solo', False),
                'mute': track.get('mute', False),
                'volume': track.get('volume', 1.0)
            })
        return serializable_tracks

    def load_from_serializable(self, serializable_tracks):
        self.tracks = []
        for track_data in serializable_tracks:
            clips = []
            for clip_data in track_data['clips']:
                clips.append(AudioClip(clip_data['file_path'], clip_data['x']))
            self.tracks.append({
                'name': track_data['name'],
                'clips': clips,
                'solo': track_data.get('solo', False),
                'mute': track_data.get('mute', False),
                'volume': track_data.get('volume', 1.0)
            })
        self.is_modified = False

    def __del__(self):
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.p.terminate()