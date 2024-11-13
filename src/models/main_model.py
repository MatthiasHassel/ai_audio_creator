# main_model.py

from models.audio_generator_model import AudioGeneratorModel
from models.script_editor_model import ScriptEditorModel
from models.timeline_model import TimelineModel

class MainModel:
    def __init__(self):
        self.audio_model = AudioGeneratorModel()
        self.script_editor_model = ScriptEditorModel()
        self.timeline_model = TimelineModel()

    def get_audio_model(self):
        return self.audio_model

    def get_script_editor_model(self):
        return self.script_editor_model

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

    def play_timeline(self):
        return self.timeline_model.play_timeline()

    def stop_timeline(self):
        return self.timeline_model.stop_timeline()

    def update_playhead(self):
        return self.timeline_model.update_playhead()

    def set_playhead_position(self, position):
        return self.timeline_model.set_playhead_position(position)