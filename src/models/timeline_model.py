# timeline_model.py

class TimelineModel:
    def __init__(self):
        self.tracks = []
        self.is_modified = False

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