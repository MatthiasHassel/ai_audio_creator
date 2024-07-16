from views.timeline_view import TimelineView
from models.timeline_model import TimelineModel

class TimelineController:
    def __init__(self, master, model, project_model):
        self.master = master
        self.model = TimelineModel()
        self.project_model = project_model
        self.view = None
        self.toggle_audio_creator_command = None

    def show(self):
        if self.view is None or not self.view.winfo_exists():
            self.view = TimelineView(self.master)
            self.setup_view_bindings()
        self.update_project_name(self.project_model.current_project)
        self.load_timeline_data()
        self.view.deiconify()

    def hide(self):
        if self.view and self.view.winfo_exists():
            self.view.withdraw()

    def setup_view_bindings(self):
        self.view.protocol("WM_DELETE_WINDOW", self.hide)
        self.view.add_track_button.configure(command=self.add_track)
        self.view.play_button.configure(command=self.play_timeline)
        self.view.stop_button.configure(command=self.stop_timeline)
        self.view.toggle_audio_creator_button.configure(command=self.toggle_audio_creator)

    def load_timeline_data(self):
        if self.view:
            self.view.clear_tracks()
            timeline_data = self.project_model.get_timeline_data()
            self.model.set_tracks(timeline_data)
            for track_data in self.model.get_tracks():
                self.view.add_track(track_data['name'])
                for clip in track_data['clips']:
                    self.view.add_clip_to_track(track_data['name'], clip)
        self.model.mark_as_saved()

    def update_project_name(self, project_name):
        if self.view and self.view.winfo_exists():
            self.view.update_title(project_name)

    def on_project_change(self):
        self.update_project_name(self.project_model.current_project)
        self.load_timeline_data()

    def save_timeline_data(self):
        if self.model.is_modified:
            self.project_model.update_timeline_data(self.model.get_tracks())
            self.model.mark_as_saved()

    def add_track(self):
        if self.view:
            track_name = f"Track {len(self.model.get_tracks()) + 1}"
            self.view.add_track(track_name)
            self.model.add_track({'name': track_name, 'clips': []})

    def add_clip_to_timeline(self, track_name, clip_data):
        if self.view:
            self.view.add_clip_to_track(track_name, clip_data)
            track_index = next((i for i, track in enumerate(self.model.get_tracks()) if track['name'] == track_name), None)
            if track_index is not None:
                self.model.add_clip_to_track(track_index, clip_data)
    def play_timeline(self):
        print("Playing timeline")
        # Implement playback logic here

    def stop_timeline(self):
        print("Stopping timeline")
        # Implement stop logic here

    def clear_timeline(self):
        if self.view:
            self.view.clear_timeline()

    def redraw_timeline(self):
        if self.view:
            self.view.redraw_timeline()

    def on_drag_start(self, event):
        # Implement drag start logic
        pass

    def on_drag_motion(self, event):
        # Implement drag motion logic
        pass

    def on_drag_release(self, event):
        # Implement drag release logic
        pass

    def toggle_visibility(self):
        if self.view and self.view.winfo_viewable():
            self.hide()
        else:
            self.show()

    def set_toggle_audio_creator_command(self, command):
        self.toggle_audio_creator_command = command
        if self.view:
            self.view.toggle_audio_creator_button.configure(command=self.toggle_audio_creator)

    def toggle_audio_creator(self):
        if self.toggle_audio_creator_command:
            self.toggle_audio_creator_command()