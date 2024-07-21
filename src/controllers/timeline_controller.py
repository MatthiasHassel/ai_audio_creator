from views.timeline_view import TimelineView
import os
from utils.audio_clip import AudioClip
from tkinterdnd2 import DND_FILES
import logging 

class TimelineController:
    def __init__(self, master, model, project_model):
        self.master = master
        self.model = model
        self.timeline_model = model.get_timeline_model()
        self.project_model = project_model
        self.view = None
        self.update_interval = 50  # milliseconds
        self.ensure_one_track()

    def show(self):
        if self.view is None or not self.view.winfo_exists():
            self.view = TimelineView(self.master, self.project_model)
            self.view.set_controller(self)  # Set the controller
            self.setup_view_bindings()
            self.load_timeline_data()
        self.view.update_title(self.project_model.current_project)
        self.view.deiconify()
    
    def hide(self):
        if self.view and self.view.winfo_exists():
            self.view.withdraw()

    def ensure_one_track(self):
        if not self.timeline_model.get_tracks():
            self.add_track("Track 1")

    def select_first_track(self):
        if self.view and self.timeline_model.get_tracks():
            first_track = self.timeline_model.get_tracks()[0]
            self.view.select_track(first_track)

    def setup_view_bindings(self):
        if self.view:
            self.view.protocol("WM_DELETE_WINDOW", self.hide)
            self.view.add_track_button.configure(command=self.add_track)
            self.view.play_button.configure(command=self.play_timeline)
            self.view.stop_button.configure(command=self.stop_timeline)
            self.view.set_toggle_audio_creator_command(self.toggle_audio_creator)
            self.view.set_rename_track_callback(self.rename_track)
            self.view.set_remove_track_callback(self.remove_track)
            self.view.set_add_clip_callback(self.add_clip_to_model)

    def load_timeline_data(self):
        if self.view:
            timeline_data = self.project_model.get_timeline_data()
            self.timeline_model.set_tracks(timeline_data)
            self.ensure_one_track()
            self.view.update_tracks(self.timeline_model.get_tracks())
            for track_data in self.timeline_model.get_tracks():
                for clip in track_data['clips']:
                    self.view.draw_clip(clip, self.timeline_model.get_tracks().index(track_data))
            self.view.redraw_timeline()
            self.select_first_track()

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

    def add_track(self, track_name=None):
        if track_name is None:
            track_name = f"Track {len(self.timeline_model.get_tracks()) + 1}"
        self.timeline_model.add_track({'name': track_name, 'clips': []})
        if self.view:
            self.view.update_tracks(self.timeline_model.get_tracks())

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
            clips_to_delete = self.timeline_model.get_tracks()[track_index]['clips']
            
            # Delete audio files associated with the clips
            for clip in clips_to_delete:
                self.delete_audio_file(clip.file_path)
            
            # Remove the track from the model
            self.timeline_model.remove_track(track_index)
            
            # Update the view
            if self.view:
                self.view.update_tracks(self.timeline_model.get_tracks())
                self.view.redraw_timeline()
            
            logging.info(f"Track and associated clips removed: {track['name']}")
        except ValueError:
            logging.error(f"Track not found: {track}")
        except Exception as e:
            logging.error(f"Error removing track: {str(e)}")

    def add_audio_clip(self, file_path):
        if self.timeline_model.is_playing:
            self.view.show_error("Playback in Progress", "Cannot import audio while playback is running. Stop playback and try again.")
            return

        selected_track = self.view.selected_track
        if selected_track is None:
            self.view.show_error("No Track Selected", "Please select a track before importing audio.")
            return

        track_index = self.timeline_model.get_track_index(selected_track)
        start_time = self.timeline_model.get_playhead_position()

        try:
            clip = AudioClip(file_path, start_time)
            self.timeline_model.add_clip_to_track(track_index, clip)
            self.view.add_clip(clip, track_index)
            self.view.redraw_timeline()
        except Exception as e:
            self.view.show_error("Import Error", f"Failed to import audio clip: {str(e)}")

    def delete_clip(self, clip):
        track_index = self.timeline_model.get_track_index_for_clip(clip)
        if track_index != -1:
            self.timeline_model.remove_clip_from_track(track_index, clip)
            if self.view:
                self.view.remove_clip(clip)
            self.delete_audio_file(clip.file_path)

    def delete_audio_file(self, file_path):
        try:
            os.remove(file_path)
            logging.info(f"Deleted audio file: {file_path}")
        except Exception as e:
            logging.error(f"Failed to delete audio file {file_path}: {str(e)}")

    def on_drop(self, event):
        file_path = event.data
        if file_path.lower().endswith(('.mp3', '.wav')):
            track_index = self.view.get_track_index_from_y(event.y)
            x_position = event.x / (self.view.seconds_per_pixel * self.view.x_zoom)
            self.add_audio_clip(file_path, track_index, x_position)
            logging.info(f"File dropped on track {track_index} at position {x_position}")

    def move_clip(self, clip, new_x, old_track_index, new_track_index):
        try:
            self.timeline_model.move_clip(clip, new_x, old_track_index, new_track_index)
            if self.view:
                self.view.update_tracks(self.timeline_model.get_tracks())
                self.view.redraw_timeline()
            return True
        except Exception as e:
            logging.error(f"Error moving clip: {str(e)}")
            return False

    def update_track_solo_mute(self, track):
        self.timeline_model.update_track_solo_mute(track)
        self.redraw_timeline()

    def get_active_tracks(self):
        solo_tracks = [track for track in self.timeline_model.get_tracks() if track.get("solo", False)]
        if solo_tracks:
            return solo_tracks
        return [track for track in self.timeline_model.get_tracks() if not track.get("mute", False)]
    
    def play_timeline(self):
        self.timeline_model.play_timeline(self.get_active_tracks())
        if self.view:
            self.view.play_timeline()
        self._schedule_playhead_update()
        logging.info("Timeline playback initiated from controller")

    def stop_timeline(self):
        self.timeline_model.stop_timeline()
        if self.view:
            self.view.stop_timeline()
        if hasattr(self, '_update_id'):
            self.master.after_cancel(self._update_id)
        logging.info("Timeline playback stopped from controller")

    def _schedule_playhead_update(self):
        self._update_playhead()
        if self.timeline_model.is_playing:
            self._update_id = self.master.after(self.update_interval, self._schedule_playhead_update)

    def _update_playhead(self):
        position = self.timeline_model.update_playhead()
        if self.view:
            self.view.update_playhead_position(position)

    def set_playhead_position(self, position):
        self.timeline_model.set_playhead_position(position)
        if self.view:
            self.view.update_playhead_position(position)

    def restart_timeline(self):
        self.stop_timeline()
        self.set_playhead_position(0)
        if self.view:
            self.view.restart_button.configure(state="normal")

    def get_playhead_position(self):
        return self.timeline_model.get_playhead_position()
    
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

