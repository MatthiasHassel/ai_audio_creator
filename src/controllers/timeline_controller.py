from views.timeline_view import TimelineView
from models.timeline_model import TimelineModel
from utils.audio_clip import AudioClip
from tkinterdnd2 import DND_FILES
import logging 

class TimelineController:
    def __init__(self, master, model, project_model):
        self.master = master
        self.model = model
        self.timeline_model = model.get_timeline_model()  # Get the TimelineModel from MainModel
        self.project_model = project_model
        self.view = None

    def show(self):
        if self.view is None or not self.view.winfo_exists():
            self.view = TimelineView(self.master, self.project_model)
            self.setup_view_bindings()
            self.load_timeline_data()
        self.view.update_title(self.project_model.current_project)
        self.view.deiconify()
    
    def hide(self):
        if self.view and self.view.winfo_exists():
            self.view.withdraw()

    def setup_view_bindings(self):
        self.view.protocol("WM_DELETE_WINDOW", self.hide)
        self.view.add_track_button.configure(command=self.add_track)
        self.view.play_button.configure(command=self.play_timeline)
        self.view.stop_button.configure(command=self.stop_timeline)
        self.view.set_toggle_audio_creator_command(self.toggle_audio_creator)
        self.view.set_rename_track_callback(self.rename_track)
        self.view.set_remove_track_callback(self.remove_track)
        self.view.timeline_canvas.drop_target_register(DND_FILES)
        self.view.timeline_canvas.dnd_bind('<<Drop>>', self.on_drop)
        self.view.set_add_clip_callback(self.add_clip_to_model)

    def load_timeline_data(self):
        if self.view:
            self.view.clear_tracks()
            timeline_data = self.project_model.get_timeline_data()
            self.timeline_model.set_tracks(timeline_data)
            for track_data in self.timeline_model.get_tracks():
                self.view.add_track(track_data['name'])
                for clip in track_data['clips']:
                    self.view.draw_clip(clip, self.timeline_model.get_tracks().index(track_data))
            self.view.redraw_timeline()

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
        track_name = f"Track {len(self.timeline_model.get_tracks()) + 1}"
        self.timeline_model.add_track({'name': track_name, 'clips': []})
        if self.view:
            self.view.add_track(track_name)

    def rename_track(self, track, new_name):
        try:
            track_index = self.model.get_track_index(track)
            self.model.rename_track(track_index, new_name)
            self.view.update_track_labels()
        except ValueError:
            logging.error(f"Track not found: {track}")
        except Exception as e:
            logging.error(f"Error renaming track: {str(e)}")

    def remove_track(self, track):
        try:
            track_index = self.timeline_model.get_track_index(track)
            self.timeline_model.remove_track(track_index)
            self.view.remove_track(track)  # Pass the track object, not the index
        except ValueError:
            logging.error(f"Track not found: {track}")
        except Exception as e:
            logging.error(f"Error removing track: {str(e)}")

    def on_drop(self, event):
        file_path = event.data
        if file_path.lower().endswith(('.mp3', '.wav')):
            track_index = self.view.get_track_index_from_y(event.y)
            x_position = event.x
            self.add_audio_clip(file_path, track_index, x_position)

    def add_audio_clip(self, file_path, track_index, start_time):
        try:
            logging.info(f"Adding audio clip: file={file_path}, track={track_index}, start_time={start_time}")
            clip = AudioClip(file_path, start_time)
            self.model.add_clip_to_track(track_index, clip)
            if self.view:
                self.view.draw_clip(clip, track_index)
                self.view.redraw_timeline()
            logging.info("Audio clip added successfully")
        except Exception as e:
            logging.error(f"Error adding audio clip: {str(e)}", exc_info=True)
            # Optionally, show an error message to the user
            if hasattr(self.view, 'show_error'):
                self.view.show_error("Error", f"Failed to add audio clip: {str(e)}")

    def move_clip(self, track_index, clip_index, new_x):
        self.model.move_clip(track_index, clip_index, new_x)
        self.view.redraw_timeline()

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

    def add_clip_to_model(self, track_index, clip):
        self.model.add_clip_to_track(track_index, {
            'file_path': clip.file_path,
            'start_time': clip.x,
            'duration': clip.duration
        })