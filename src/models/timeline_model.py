# timeline_model.py
import pygame
import pygame.sndarray
import time
import logging

class TimelineModel:
    def __init__(self):
        self.tracks = []
        self.is_modified = False
        self.is_playing = False
        self.playhead_position = 0
        self.start_time = 0
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
        self.active_sounds = []

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

    def set_tracks(self, tracks_data):
        self.tracks = tracks_data
        self.is_modified = True

    def get_tracks(self):
        return self.tracks

    def mark_as_saved(self):
        self.is_modified = False

    def play_timeline(self):
        if not self.is_playing:
            self.is_playing = True
            self.start_time = time.time() - self.playhead_position
            self.play_clips()
            logging.info("Timeline model: playback started")

    def stop_timeline(self):
        if self.is_playing:
            self.is_playing = False
            self.playhead_position = time.time() - self.start_time
            self.stop_clips()
            logging.info("Timeline model: playback stopped")

    def play_clips(self):
        current_time = self.playhead_position
        for track in self.tracks:
            for clip in track['clips']:
                if clip.x <= current_time < clip.x + clip.duration:
                    try:
                        sound = pygame.mixer.Sound(clip.file_path)
                        start_pos = int((current_time - clip.x) * 1000)  # Calculate start position in milliseconds
                        
                        # Cut the sound to start from the correct position
                        sound_array = pygame.sndarray.array(sound)
                        start_frame = int(start_pos * sound.get_length() * 1000 / len(sound_array))
                        cut_sound = pygame.sndarray.make_sound(sound_array[start_frame:])
                        
                        channel = cut_sound.play()
                        self.active_sounds.append((sound, channel))
                    except Exception as e:
                        logging.error(f"Error playing clip {clip.file_path}: {str(e)}")

    def stop_clips(self):
        for sound, channel in self.active_sounds:
            if channel is not None:
                channel.stop()
        self.active_sounds.clear()

    def update_playhead(self):
        if self.is_playing:
            current_time = time.time() - self.start_time
            self.playhead_position = current_time
            self.play_clips()  # Check for new clips to play
        return self.playhead_position

    def get_playhead_position(self):
        if self.is_playing:
            return time.time() - self.start_time
        return self.playhead_position

    def set_playhead_position(self, position):
        self.playhead_position = position
        if self.is_playing:
            self.start_time = time.time() - position