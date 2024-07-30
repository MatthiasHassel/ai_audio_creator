from views.timeline_view import TimelineView
import os
from utils.audio_clip import AudioClip
from tkinterdnd2 import DND_FILES
import logging 
from tkinter import messagebox
from pydub import AudioSegment

class TimelineController:
    def __init__(self, master, timeline_model, project_model):
        self.master = master
        self.timeline_model = timeline_model
        self.project_model = project_model
        self.view = None
        self.update_interval = 50  # milliseconds
        self.unsaved_changes = False
        self.imported_audio_files = set()

    def show(self):
        if self.view is None or not self.view.winfo_exists():
            self.view = TimelineView(self.master, self.project_model, self.timeline_model)
            self.view.set_controller(self)
            self.setup_view_bindings()
        self.load_timeline_data()
        self.view.update_title(self.project_model.current_project)
        self.view.deiconify()
    
    def hide(self):
        if self.unsaved_changes:
            response = messagebox.askyesnocancel("Unsaved Changes", "You have unsaved changes. Do you want to save before closing?")
            if response is None:  # Cancel
                return
            elif response:  # Yes
                self.save_timeline_data()
            else:  # No
                self.discard_unsaved_changes()
        
        if self.view and self.view.winfo_exists():
            self.view.withdraw()
        
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
        tracks = self.project_model.get_timeline_data()
        self.timeline_model.set_tracks(tracks)
        if self.view:
            self.view.update_tracks(tracks)
            for track_index, track_data in enumerate(tracks):
                for clip in track_data['clips']:
                    self.view.draw_clip(clip, track_index)
            self.view.redraw_timeline()
        self.project_model.clear_timeline_clips()
        for track in tracks:
            for clip in track['clips']:
                self.project_model.add_clip_to_timeline(clip.file_path)

    def update_project_name(self, project_name):
        if self.view and self.view.winfo_exists():
            self.view.update_title(project_name)

    def on_project_change(self):
        self.update_project_name(self.project_model.current_project)
        self.load_timeline_data()

    def on_project_saved(self):
        self.unsaved_changes = False
        if self.view and self.view.winfo_exists():
            self.view.update_status("Project saved successfully")

    def update_status(self, message):
        if self.view and self.view.winfo_exists():
            self.view.update_status(message)

    def save_timeline_data(self):
        if self.timeline_model.is_modified:
            self.project_model.update_timeline_data(self.timeline_model.get_serializable_tracks())
            self.timeline_model.set_modified(False)
            self.project_model.update_saved_audio_files()
            self.unsaved_changes = False

    def add_track(self, track_name=None):
        if track_name is None:
            track_name = f"Track {len(self.timeline_model.get_tracks()) + 1}"
        self.timeline_model.add_track({'name': track_name, 'clips': []})
        if self.view:
            self.view.update_tracks(self.timeline_model.get_tracks())
            self.view.select_track(self.timeline_model.get_tracks()[-1])
        self.unsaved_changes = True

    def rename_track(self, track, new_name):
        try:
            track_index = self.model.get_track_index(track)
            self.model.rename_track(track_index, new_name)
            self.view.update_track_labels()
        except ValueError:
            logging.error(f"Track not found: {track}")
        except Exception as e:
            logging.error(f"Error renaming track: {str(e)}")
        self.unsaved_changes = True

    def remove_track(self, track):
        try:
            track_index = self.timeline_model.get_track_index(track)
            clips_to_delete = self.timeline_model.get_tracks()[track_index]['clips']
            
            # Delete audio files associated with the clips
            for clip in clips_to_delete:
                self.delete_audio_file(clip.file_path)
            
            # Remove the track from the model
            self.timeline_model.remove_track(track_index)
            
            # Determine the next track to select
            tracks = self.timeline_model.get_tracks()
            if tracks:
                if track_index > 0:
                    next_track = tracks[track_index - 1]
                elif track_index < len(tracks):
                    next_track = tracks[track_index]
                else:
                    next_track = None
            else:
                next_track = None
            
            # Update the view
            if self.view:
                self.view.update_tracks(tracks)
                self.view.redraw_timeline()
                if next_track:
                    self.view.select_track(next_track)
                else:
                    self.view.deselect_all_tracks()
            
            logging.info(f"Track and associated clips removed: {track['name']}")
        except ValueError:
            logging.error(f"Track not found: {track}")
        except Exception as e:
            logging.error(f"Error removing track: {str(e)}")
        self.unsaved_changes = True

    def add_audio_clip(self, clip, track_index, track_name):
        tracks = self.timeline_model.get_tracks()
        
        # Find the correct track by name
        target_track_index = next((i for i, track in enumerate(tracks) if track['name'] == track_name), None)
        
        if target_track_index is None:
            # If the track doesn't exist, create it
            new_track = {'name': track_name, 'clips': []}
            self.timeline_model.add_track(new_track)
            target_track_index = len(tracks)
        
        # Add the clip to the correct track
        self.timeline_model.add_clip_to_track(target_track_index, clip)
        
        if self.view:
            self.view.add_clip(clip, target_track_index)
            self.view.redraw_timeline()
        self.unsaved_changes = True
        logging.info(f"Added audio clip to track {target_track_index} ({track_name}) at position {clip.x}")
            
    def delete_clip(self, clip):
        track_index = self.timeline_model.get_track_index_for_clip(clip)
        if track_index != -1:
            self.timeline_model.remove_clip_from_track(track_index, clip)
            self.project_model.remove_clip_from_timeline(clip.file_path)
            if self.view:
                self.view.remove_clip(clip)
        self.unsaved_changes = True

    def remove_clip_from_all_tracks(self, file_path):
        tracks = self.timeline_model.get_tracks()
        for track_index, track in enumerate(tracks):
            clips_to_remove = [clip for clip in track['clips'] if clip.file_path == file_path]
            for clip in clips_to_remove:
                self.timeline_model.remove_clip_from_track(track_index, clip)
        
        # Update the view
        if self.view:
            self.view.redraw_timeline()
        
        # Update project model
        self.project_model.remove_clip_from_timeline(file_path)
        
        # Update active tracks
        self.update_active_tracks()

    def is_clip_in_timeline(self, file_path):
        tracks = self.timeline_model.get_tracks()
        return any(any(clip.file_path == file_path for clip in track['clips']) for track in tracks)

    def on_drop(self, event):
        file_path = event.data
        if file_path.lower().endswith(('.mp3', '.wav')):
            track_index = self.view.get_track_index_from_y(event.y)
            x_position = event.x / (self.view.seconds_per_pixel * self.view.x_zoom)
            self.add_audio_clip(file_path, track_index, x_position)
            logging.info(f"File dropped on track {track_index} at position {x_position}")

    def move_clip(self, clip, new_x, old_track_index, new_track_index):
        try:
            new_x = max(0, new_x)  # Ensure clip doesn't go below 0s
            tracks = self.timeline_model.get_tracks()
            
            if 0 <= old_track_index < len(tracks) and 0 <= new_track_index < len(tracks):
                old_track = tracks[old_track_index]
                new_track = tracks[new_track_index]
                
                # Remove the clip from the old track
                old_track['clips'] = [c for c in old_track['clips'] if c.file_path != clip.file_path]
                
                # Update the clip's position
                clip.x = new_x
                
                # Add the clip to the new track
                new_track['clips'].append(clip)
                
                self.timeline_model.set_modified(True)
                if self.view:
                    self.view.update_tracks(tracks)
                    self.view.redraw_timeline()
                return True
            else:
                logging.warning(f"Invalid track indices: old={old_track_index}, new={new_track_index}")
                return False
        except Exception as e:
            logging.error(f"Error moving clip: {str(e)}")
            return False

    def update_track_solo_mute(self, track):
        self.timeline_model.update_track_solo_mute(track)
        if self.view:
            self.view.update_single_track_label(track)
        active_tracks = self.get_active_tracks()
        self.timeline_model.update_playing_tracks(active_tracks)

    def update_track_volume(self, track):
        self.timeline_model.update_track_volume(track)

    def update_active_tracks(self):
        active_tracks = self.get_active_tracks()
        self.timeline_model.update_playing_tracks(active_tracks)

    def get_active_tracks(self):
        tracks = self.timeline_model.get_tracks()
        solo_tracks = [track for track in tracks if track.get("solo", False)]
        if solo_tracks:
            return solo_tracks
        return [track for track in tracks if not track.get("mute", False)]

    def play_timeline(self):
        active_tracks = self.get_active_tracks()
        self.timeline_model.play_timeline(active_tracks)
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
        position = self.timeline_model.get_playhead_position()
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

    def discard_unsaved_changes(self):
        self.project_model.remove_unsaved_audio_files()
        self.project_model.clear_timeline_clips()
        self.load_timeline_data()
        self.unsaved_changes = False

    def save_project(self):
        if self.project_model:
            success, message = self.project_model.save_project()
            if success:
                self.on_project_saved()
                if self.view:
                    self.view.update_status("Project saved successfully")
            else:
                if self.view:
                    self.view.update_status(f"Failed to save project: {message}")

    def open_project(self):
        if self.master_controller:
            self.master_controller.show_open_project_dialog()

    def new_project(self):
        if self.master_controller:
            self.master_controller.show_new_project_dialog()

    def is_playing(self):
        return self.timeline_model.is_playing

    def toggle_solo(self, track):
        track["solo"] = not track.get("solo", False)
        self.update_track_solo_mute(track)

    def toggle_mute(self, track):
        track["mute"] = not track.get("mute", False)
        self.update_track_solo_mute(track)
    
    def add_track(self, track_name=None):
        if track_name is None:
            track_name = f"Track {len(self.timeline_model.get_tracks()) + 1}"
        self.timeline_model.add_track({'name': track_name, 'clips': []})
        if self.view:
            self.view.update_tracks(self.timeline_model.get_tracks())
            self.view.select_track(self.timeline_model.get_tracks()[-1])
        self.unsaved_changes = True
    
    def add_clip(self, clip, track_index):
        self.timeline_model.add_clip_to_track(track_index, clip)
        if self.view:
            self.view.add_clip(clip, track_index)
            self.view.redraw_timeline()
        self.unsaved_changes = True

    def get_or_create_track(self, track_name):
        tracks = self.timeline_model.get_tracks()
        for index, track in enumerate(tracks):
            if track['name'] == track_name:
                return index
        
        # If the track doesn't exist, create it
        new_track = {'name': track_name, 'clips': []}
        self.timeline_model.add_track(new_track)
        if self.view:
            self.view.update_tracks(self.timeline_model.get_tracks())
        return len(tracks)  # Return the index of the new track

    def get_clip_duration(self, file_path):
        try:
            audio = AudioSegment.from_file(file_path)
            return len(audio) / 1000.0  # Convert milliseconds to seconds
        except Exception as e:
            logging.error(f"Error getting clip duration: {str(e)}")
            return 0  # Return 0 duration if there's an error

    def get_track_end_time(self, track_index):
        if 0 <= track_index < len(self.timeline_model.get_tracks()):
            track = self.timeline_model.get_tracks()[track_index]
            if track['clips']:
                last_clip = max(track['clips'], key=lambda clip: clip.x + clip.duration)
                return last_clip.x + last_clip.duration
        return 0  # Return 0 if the track is empty or doesn't exist