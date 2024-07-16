class TimelineModel:
    def __init__(self):
        self.tracks = []
        self.is_modified = False

    def add_track(self, track_data):
        self.tracks.append(track_data)
        self.is_modified = True

    def remove_track(self, track_index):
        if 0 <= track_index < len(self.tracks):
            del self.tracks[track_index]
            self.is_modified = True

    def add_clip_to_track(self, track_index, clip_data):
        if 0 <= track_index < len(self.tracks):
            self.tracks[track_index]['clips'].append(clip_data)
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

    def is_modified(self):
        return self.is_modified