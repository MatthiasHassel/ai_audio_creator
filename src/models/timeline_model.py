# timeline_model.py
import pyaudio
import numpy as np
import time
import logging
import threading
from utils.audio_clip import AudioClip
from utils.audio_buffer_manager import AudioBufferManager

class TimelineModel:
    def __init__(self):
        self.tracks = []
        self.is_playing = False
        self.playhead_position = 0
        self.start_time = 0
        self.audio_stream = None
        self.active_clips = []
        self.audio_cache = {}
        self.cache_lock = threading.Lock()
        self.stop_event = threading.Event()
        self.state_lock = threading.Lock()
        self.is_stopping = False
        self.state_change_callbacks = []
        self.sample_rate = 44100
        self.channels = 2
        self.max_playhead_position = 1800
        self.quantization_interval = 1 / 44100

        self.undo_stack = []
        self.redo_stack = []
        self.is_modified = False

        # Initialize PyAudio
        try:
            self.audio = pyaudio.PyAudio()
            # Find best output device
            self.device_index = self._find_best_output_device()
            logging.info(f"Using audio device index: {self.device_index}")
            
            # Initialize buffer manager
            self.buffer_manager = AudioBufferManager(self, buffer_size=2048)
            
        except Exception as e:
            logging.error(f"Error initializing audio: {str(e)}")
            raise

    def _find_best_output_device(self):
        """Find the best available output device"""
        try:
            default_device = self.audio.get_default_output_device_info()
            logging.info(f"Default output device: {default_device['name']}")
            return default_device['index']
        except Exception as e:
            logging.warning(f"Could not get default device: {e}")
            
            # Try to find a suitable device
            for i in range(self.audio.get_device_count()):
                try:
                    device_info = self.audio.get_device_info_by_index(i)
                    if device_info['maxOutputChannels'] >= 2:
                        logging.info(f"Using alternative device: {device_info['name']}")
                        return i
                except:
                    continue
            
            # If no suitable device found, use system default (index 0)
            logging.warning("No suitable audio device found, using system default")
            return 0

    def add_state_change_callback(self, callback):
        self.state_change_callbacks.append(callback)

    def _notify_state_change(self, is_playing, position):
        for callback in self.state_change_callbacks:
            try:
                callback(is_playing, position)
            except Exception as e:
                logging.error(f"Error in state change callback: {str(e)}")

    def preload_audio_files(self):
        """Preload all audio files in the timeline"""
        try:
            logging.info("Starting audio file preload...")
            for track in self.tracks:
                for clip in track['clips']:
                    try:
                        # Get a small portion of audio to ensure it's loaded and cached
                        self.get_clip_frames(clip, 0, 0.1)
                        logging.info(f"Preloaded audio file: {clip.file_path}")
                    except Exception as e:
                        logging.error(f"Error preloading audio file {clip.file_path}: {str(e)}")
            logging.info("Audio file preload completed")
        except Exception as e:
            logging.error(f"Error in preload_audio_files: {str(e)}")

    def play_timeline(self, active_tracks):
        logging.info("Starting timeline playback...")
        try:
            with self.state_lock:
                if self.is_playing or self.is_stopping:
                    return
                self.is_playing = True
                self.stop_event.clear()

            self._notify_state_change(True, self.playhead_position)
            self.buffer_manager.is_playing = True
            self.buffer_manager.reset()
            self.buffer_manager.playhead_position = self.playhead_position
            self.start_time = time.time() - self.playhead_position

            def audio_callback(in_data, frame_count, time_info, status):
                if status:
                    logging.warning(f"Audio callback status: {status}")
                
                if self.stop_event.is_set():
                    return (None, pyaudio.paComplete)

                try:
                    if not self.is_playing:
                        return (None, pyaudio.paComplete)
                    
                    data, status = self.buffer_manager.get_audio_data(None, frame_count, None, None)
                    self.update_playhead()
                    return (data.tobytes(), pyaudio.paContinue)
                    
                except Exception as e:
                    logging.error(f"Error in audio callback: {str(e)}")
                    return (None, pyaudio.paComplete)

            logging.info("Creating audio stream...")
            
            try:
                self.audio_stream = self.audio.open(
                    format=pyaudio.paFloat32,
                    channels=self.channels,
                    rate=self.sample_rate,
                    output=True,
                    output_device_index=self.device_index,
                    stream_callback=audio_callback,
                    frames_per_buffer=2048
                )
                
                self.audio_stream.start_stream()
                logging.info("Audio stream started successfully")
                
            except Exception as e:
                logging.error(f"Failed to open audio stream: {e}")
                self._safe_cleanup()
                raise
                
        except Exception as e:
            logging.error(f"Error starting playback: {str(e)}", exc_info=True)
            self._safe_cleanup()

    def stop_timeline(self):
        """Non-blocking stop operation"""
        logging.info("Stopping timeline playback...")
        try:
            with self.state_lock:
                if not self.is_playing or self.is_stopping:
                    return
                self.is_stopping = True
                self.is_playing = False

            # Signal stop to all components
            self.stop_event.set()
            self.buffer_manager.is_playing = False
            
            # Start cleanup in a separate thread
            threading.Thread(target=self._cleanup_audio_stream, daemon=True).start()
            
            # Notify state change immediately
            self._notify_state_change(False, self.playhead_position)
            
        except Exception as e:
            logging.error(f"Error in stop_timeline: {str(e)}")
            self._safe_cleanup()

    def _cleanup_audio_stream(self):
        """Cleanup audio stream in a separate thread"""
        try:
            if self.audio_stream is not None:
                logging.info("Stopping audio stream...")
                try:
                    if self.audio_stream.is_active():
                        self.audio_stream.stop_stream()
                    self.audio_stream.close()
                except Exception as e:
                    logging.error(f"Error stopping audio stream: {str(e)}")
                finally:
                    self.audio_stream = None

            with self.state_lock:
                self.is_stopping = False
            
            logging.info("Audio stream cleanup completed")
            
        except Exception as e:
            logging.error(f"Error in cleanup_audio_stream: {str(e)}")
            with self.state_lock:
                self.is_stopping = False

    def _safe_cleanup(self):
        """Safe cleanup that can be called from any thread"""
        try:
            self.stop_event.set()
            self.buffer_manager.is_playing = False
            
            with self.state_lock:
                self.is_playing = False
                self.is_stopping = False
            
            threading.Thread(target=self._cleanup_audio_stream, daemon=True).start()
            self._notify_state_change(False, self.playhead_position)
            
        except Exception as e:
            logging.error(f"Error in safe cleanup: {str(e)}")
        finally:
            self.stop_event.clear()

    def update_playhead(self):
        if self.is_playing:
            self.playhead_position = time.time() - self.start_time
            if hasattr(self, 'on_playhead_update'):
                self.on_playhead_update(self.playhead_position)

    def get_clip_frames(self, clip, start_time, duration):
        """Get audio frames from a clip"""
        try:
            start_sample = int(round(start_time * self.sample_rate))
            num_samples = int(round(duration * self.sample_rate))
            
            return clip.get_samples(start_sample, start_sample + num_samples)
            
        except Exception as e:
            logging.error(f"Error getting clip frames: {str(e)}")
            return np.zeros((0, 2), dtype=np.float32)

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
        if 'volume_db' not in track_data:
            track_data['volume_db'] = 0.0
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
            self.tracks.append({
                "name": f"Track {len(self.tracks) + 1}", 
                "clips": [],
                "volume_db": 0.0
            })
        
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
        for track in tracks_data:
            if 'volume_db' not in track:
                track['volume_db'] = 0.0
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
            self.tracks[track_index]["volume_db"] = track.get("volume_db", 0.0)
            self.is_modified = True

    def db_to_amplitude(self, db):
        """Convert decibels to amplitude multiplier"""
        if db <= -70:  # Mute threshold
            return 0.0
        return 10 ** (db / 20.0)

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
                'volume_db': track.get('volume_db', 0.0)
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
                'volume_db': track_data.get('volume_db', 0.0)
            })
        self.is_modified = False

    def __del__(self):
        if hasattr(self, 'audio_stream') and self.audio_stream:
            try:
                self.audio_stream.stop_stream()
                self.audio_stream.close()
            except:
                pass
        if hasattr(self, 'audio'):
            try:
                self.audio.terminate()
            except:
                pass

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
