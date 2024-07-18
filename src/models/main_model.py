# main_model.py

from models.audio_model import AudioModel
from models.script_model import ScriptModel
from models.timeline_model import TimelineModel

class MainModel:
    def __init__(self):
        self.audio_model = AudioModel()
        self.script_model = ScriptModel()
        self.timeline_model = TimelineModel()

    def get_audio_model(self):
        return self.audio_model

    def get_script_model(self):
        return self.script_model

    def get_timeline_model(self):
        return self.timeline_model

    def get_tracks(self):
        return self.timeline_model.get_tracks()

    def set_tracks(self, new_tracks):
        self.timeline_model.set_tracks(new_tracks)

    def add_track(self, track_data):
        self.timeline_model.add_track(track_data)

    def get_tracks(self):
        return self.timeline_model.get_tracks()
    
    def get_track_index(self, track):
        return self.timeline_model.get_track_index(track)
    
    def set_tracks(self, tracks):
        self.timeline_model.set_tracks(tracks)

    def rename_track(self, track_index, new_name):
        self.timeline_model.rename_track(track_index, new_name)

    def remove_track(self, track_index):
        self.timeline_model.remove_track(track_index)

    def add_clip_to_track(self, track_index, clip_data):
        self.timeline_model.add_clip_to_track(track_index, clip_data)

    def remove_clip_from_track(self, track_index, clip_index):
        self.timeline_model.remove_clip_from_track(track_index, clip_index)

    def clear_tracks(self):
        self.timeline_model.clear_tracks()

    def is_modified(self):
        return self.timeline_model.is_modified

    def mark_as_saved(self):
        self.timeline_model.mark_as_saved()