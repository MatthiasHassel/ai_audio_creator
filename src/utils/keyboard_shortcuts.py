# utils/keyboard_shortcuts.py

class KeyboardShortcuts:
    def __init__(self, timeline_view):
        self.timeline_view = timeline_view
        self.setup_shortcuts()

    def setup_shortcuts(self):
        self.timeline_view.bind("<Command-s>", self.save_project)
        self.timeline_view.bind("<Command-o>", self.open_project)
        self.timeline_view.bind("<Command-n>", self.new_project)
        self.timeline_view.bind("<space>", self.toggle_playback)
        self.timeline_view.bind("s", self.toggle_solo)
        self.timeline_view.bind("m", self.toggle_mute)
        self.timeline_view.bind("<Up>", self.select_track_up)
        self.timeline_view.bind("<Down>", self.select_track_down)
        self.timeline_view.bind("n", self.add_new_track)

    def save_project(self, event):
        if self.timeline_view.controller:
            self.timeline_view.controller.save_project()

    def open_project(self, event):
        if self.timeline_view.controller:
            self.timeline_view.controller.open_project()

    def new_project(self, event):
        if self.timeline_view.controller:
            self.timeline_view.controller.new_project()

    def toggle_playback(self, event):
        if self.timeline_view.controller:
            if self.timeline_view.controller.is_playing():
                self.timeline_view.controller.stop_timeline()
            else:
                self.timeline_view.controller.play_timeline()

    def toggle_solo(self, event):
        if self.timeline_view.controller and self.timeline_view.selected_track:
            self.timeline_view.controller.toggle_solo(self.timeline_view.selected_track)

    def toggle_mute(self, event):
        if self.timeline_view.controller and self.timeline_view.selected_track:
            self.timeline_view.controller.toggle_mute(self.timeline_view.selected_track)

    def select_track_up(self, event):
        if self.timeline_view.selected_track:
            current_index = self.timeline_view.tracks.index(self.timeline_view.selected_track)
            if current_index > 0:
                self.timeline_view.select_track(self.timeline_view.tracks[current_index - 1])

    def select_track_down(self, event):
        if self.timeline_view.selected_track:
            current_index = self.timeline_view.tracks.index(self.timeline_view.selected_track)
            if current_index < len(self.timeline_view.tracks) - 1:
                self.timeline_view.select_track(self.timeline_view.tracks[current_index + 1])

    def add_new_track(self, event):
        if self.timeline_view.controller:
            self.timeline_view.controller.add_track()