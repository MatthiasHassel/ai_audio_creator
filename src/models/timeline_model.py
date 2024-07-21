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
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=4096)
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

    def get_tracks(self):
        return self.tracks

    def set_tracks(self, tracks_data):
        self.tracks = tracks_data
        self.is_modified = True

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
        self.stop_clips()  # Stop any currently playing clips
        current_time = self.playhead_position
        for track in self.tracks:
            for clip in track['clips']:
                clip_end = clip.x + clip.duration
                if clip.x <= current_time < clip_end:
                    try:
                        sound = pygame.mixer.Sound(clip.file_path)
                        clip_start_time = current_time - clip.x
                        
                        # Calculate the start position in samples
                        sample_rate = pygame.mixer.get_init()[0]
                        start_sample = int(clip_start_time * sample_rate)
                        
                        # Create a new Sound object starting from the calculated position
                        sound_array = pygame.sndarray.array(sound)
                        cut_sound = pygame.sndarray.make_sound(sound_array[start_sample:])
                        
                        channel = cut_sound.play()
                        self.active_sounds.append((sound, channel, clip))
                    except Exception as e:
                        logging.error(f"Error playing clip {clip.file_path}: {str(e)}")

    def stop_clips(self):
        for sound, channel, _ in self.active_sounds:
            if channel is not None:
                channel.stop()
        self.active_sounds.clear()

    def update_playhead(self):
        if self.is_playing:
            current_time = time.time() - self.start_time
            self.playhead_position = current_time
            self.update_active_sounds()
            self.play_new_clips()
        return self.playhead_position

    def update_active_sounds(self):
        current_time = self.playhead_position
        for sound, channel, clip in self.active_sounds[:]:
            if current_time >= clip.x + clip.duration:
                channel.stop()
                self.active_sounds.remove((sound, channel, clip))

    def play_new_clips(self):
        current_time = self.playhead_position
        for track in self.tracks:
            for clip in track['clips']:
                if clip.x <= current_time < clip.x + clip.duration:
                    if not any(c == clip for _, _, c in self.active_sounds):
                        try:
                            sound = pygame.mixer.Sound(clip.file_path)
                            start_pos = int((current_time - clip.x) * 1000)
                            sound_array = pygame.sndarray.array(sound)
                            start_frame = int(start_pos * sound.get_length() * 1000 / len(sound_array))
                            cut_sound = pygame.sndarray.make_sound(sound_array[start_frame:])
                            channel = cut_sound.play()
                            self.active_sounds.append((sound, channel, clip))
                        except Exception as e:
                            logging.error(f"Error playing clip {clip.file_path}: {str(e)}")

    def set_playhead_position(self, position):
        self.playhead_position = max(0, position)
        if self.is_playing:
            self.start_time = time.time() - self.playhead_position
            self.stop_clips()
            self.play_clips()

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
                # Stop the clip if it's currently playing
                for sound, channel, playing_clip in self.active_sounds[:]:
                    if playing_clip == clip:
                        channel.stop()
                        self.active_sounds.remove((sound, channel, playing_clip))

    def move_clip(self, clip, new_x, old_track_index, new_track_index):
        if 0 <= old_track_index < len(self.tracks) and 0 <= new_track_index < len(self.tracks):
            if clip in self.tracks[old_track_index]['clips']:
                self.tracks[old_track_index]['clips'].remove(clip)
                self.tracks[new_track_index]['clips'].append(clip)
                clip.x = max(0, new_x)
                self.is_modified = True
                return True
        return False