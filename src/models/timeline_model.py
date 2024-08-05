# timeline_model.py
import pyaudio
import numpy as np
import time
import logging
import threading
import sounddevice as sd
from pydub import AudioSegment
from utils.audio_clip import AudioClip
from utils.audio_buffer_manager import AudioBufferManager

class TimelineModel:
    def __init__(self):
        self.tracks = []
        self.is_playing = False
        self.playhead_position = 0
        self.start_time = 0
        self.p = pyaudio.PyAudio()
        self.stream = None
        self.audio_stream = None
        self.active_clips = []
        self.audio_cache = {}
        self.cache_lock = threading.Lock()
        self.sample_rate = 44100
        self.target_sample_rate = 44100
        self.channels = 2
        self.max_playhead_position = 1800  # Set a maximum playhead position in sec (e.g., 30min -> 1800s)
        self.quantization_interval = 1 / 44100  # Quantize to sample rate


        self.undo_stack = []
        self.redo_stack = []
        self.is_modified = False

        self.buffer_manager = AudioBufferManager(self, buffer_size=2048)

    def play_timeline(self, active_tracks):
        if not self.is_playing:
            self.is_playing = True
            self.buffer_manager.is_playing = True
            self.buffer_manager.reset()
            self.buffer_manager.playhead_position = self.playhead_position
            self.start_time = time.time() - self.playhead_position

            def audio_callback(outdata, frames, time, status):
                if status:
                    print(status)
                data, _ = self.buffer_manager.get_audio_data(None, frames, None, None)
                outdata[:] = data
                self.update_playhead()

            self.audio_stream = sd.OutputStream(
                samplerate=self.sample_rate,
                channels=2,
                callback=audio_callback,
                blocksize=2048
            )
            self.audio_stream.start()

    def stop_timeline(self):
        if self.is_playing:
            self.is_playing = False
            self.buffer_manager.is_playing = False
            if self.audio_stream:
                self.audio_stream.stop()
                self.audio_stream.close()
                self.audio_stream = None

    def preload_audio_files(self):
        threading.Thread(target=self._preload_audio_files_thread, daemon=True).start()

    def _preload_audio_files_thread(self):
        for track in self.tracks:
            for clip in track['clips']:
                self._cache_audio_file(clip.file_path)

    def _cache_audio_file(self, file_path):
        if file_path not in self.audio_cache:
            try:
                audio = AudioSegment.from_file(file_path)
                if audio.frame_rate != self.target_sample_rate:
                    logging.info(f"Converting {file_path} from {audio.frame_rate}Hz to {self.target_sample_rate}Hz")
                    audio = audio.set_frame_rate(self.target_sample_rate)
                    audio.export(file_path, format="wav")
                    audio = AudioSegment.from_file(file_path)  # Reload the converted file
                
                samples = np.array(audio.get_array_of_samples(), dtype=np.float32)
                samples = samples.reshape((-1, 2)) if audio.channels == 2 else np.column_stack((samples, samples))
                
                with self.cache_lock:
                    self.audio_cache[file_path] = {
                        'samples': samples / 32768.0,
                        'duration': len(audio) / 1000.0
                    }
                logging.info(f"Cached audio file: {file_path}")
            except Exception as e:
                logging.error(f"Error caching audio file {file_path}: {str(e)}")

    def get_clip_frames(self, clip, start_time, duration):
        with self.cache_lock:
            if clip.file_path not in self.audio_cache:
                self._cache_audio_file(clip.file_path)
            
            cached_data = self.audio_cache[clip.file_path]

        start_sample = int(round(start_time * self.sample_rate))
        end_sample = int(round((start_time + duration) * self.sample_rate))

        if end_sample > len(cached_data['samples']):
            samples = np.zeros((end_sample - start_sample, 2), dtype=np.float32)
            available_samples = len(cached_data['samples']) - start_sample
            if available_samples > 0:
                samples[:available_samples] = cached_data['samples'][start_sample:start_sample + available_samples]
        else:
            samples = cached_data['samples'][start_sample:end_sample]

        return samples

    def get_active_clips(self, active_tracks):
        active_clips = []
        for track in active_tracks:
            for clip in track['clips']:
                active_clips.append((clip, track))
        return active_clips
        
    def update_playing_tracks(self, active_tracks):
        if self.is_playing:
            self.active_clips = self.get_active_clips(active_tracks)

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
            # This shouldn't happen now, but keep it as a safeguard
            self.tracks.append({"name": f"Track {len(self.tracks) + 1}", "clips": []})
        
        # Insert the clip at the correct position in the track
        track = self.tracks[track_index]
        insert_position = next((i for i, existing_clip in enumerate(track['clips']) 
                                if getattr(existing_clip, 'index', float('inf')) > clip.index), 
                            len(track['clips']))
        track['clips'].insert(insert_position, clip)
        self.buffer_manager.reset()
        self.set_modified(True)

    def remove_clip_from_track(self, track_index, clip_index):
        if 0 <= track_index < len(self.tracks):
            if 0 <= clip_index < len(self.tracks[track_index]['clips']):
                del self.tracks[track_index]['clips'][clip_index]
                self.is_modified = True
        self.buffer_manager.reset()

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

    def update_track_volume(self, track):
        track_index = self.get_track_index(track)
        if 0 <= track_index < len(self.tracks):
            self.tracks[track_index]["volume"] = track.get("volume", 1.0)
            self.is_modified = True

    def update_playhead(self):
        if self.is_playing:
            self.playhead_position = time.time() - self.start_time
            # Notify the view to update the playhead position
            if hasattr(self, 'on_playhead_update'):
                self.on_playhead_update(self.playhead_position)

    def quantize_position(self, position):
        return round(position / self.quantization_interval) * self.quantization_interval

    def get_playhead_position(self):
        if self.is_playing:
            return time.time() - self.start_time
        return self.playhead_position

    def set_playhead_position(self, position):
        self.playhead_position = min(max(0, position), self.max_playhead_position)
        self.buffer_manager.update_playhead(self.playhead_position)
        if self.is_playing:
            self.start_time = time.time() - self.playhead_position
            
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

    def set_modified(self, value):
        self.is_modified = value

    def save_state(self):
        state = {
            'tracks': self.get_serializable_tracks(),
            'playhead_position': self.playhead_position
        }
        self.undo_stack.append(state)
        self.redo_stack.clear()

    def undo(self):
        if self.undo_stack:
            current_state = {
                'tracks': self.get_serializable_tracks(),
                'playhead_position': self.playhead_position
            }
            self.redo_stack.append(current_state)
            previous_state = self.undo_stack.pop()
            self.load_from_serializable(previous_state['tracks'])
            self.set_playhead_position(previous_state['playhead_position'])

    def redo(self):
        if self.redo_stack:
            current_state = {
                'tracks': self.get_serializable_tracks(),
                'playhead_position': self.playhead_position
            }
            self.undo_stack.append(current_state)
            next_state = self.redo_stack.pop()
            self.load_from_serializable(next_state['tracks'])
            self.set_playhead_position(next_state['playhead_position'])