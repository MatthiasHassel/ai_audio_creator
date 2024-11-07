from views.timeline_view import TimelineView
import os
from utils.audio_clip import AudioClip
from tkinterdnd2 import DND_FILES
import logging 
from tkinter import messagebox, filedialog
from pydub import AudioSegment
import soundfile as sf
import numpy as np
from utils.file_utils import read_audio_prompt

class TimelineController:
    def __init__(self, master, timeline_model, project_model):
        self.master = master
        self.timeline_model = timeline_model
        self.project_model = project_model
        self.view = None
        self.update_interval = 50  # milliseconds
        self.unsaved_changes = False
        self.imported_audio_files = set()
        self.max_playhead_position = 1800  # Set a maximum playhead position in sec (e.g., 30m -> 1800s)
        self.timeline_model.on_playhead_update = self.update_playhead_view
        self.timeline_model.add_state_change_callback(self.on_playback_state_change)

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
        self.timeline_model.preload_audio_files()
        if self.view:
            self.view.update_tracks(tracks)
            for track_index, track_data in enumerate(tracks):
                for clip in track_data['clips']:
                    # Ensure each clip has the prompt information and title
                    if not hasattr(clip, 'prompt'):
                        clip.prompt = read_audio_prompt(clip.file_path)
                    if not hasattr(clip, 'title'):
                        clip.title = os.path.basename(clip.file_path)
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

    def add_audio_clip(self, file_path):
        tracks = self.timeline_model.get_tracks()
        
        # If there are no tracks, create a new one
        if not tracks:
            self.add_track()
            tracks = self.timeline_model.get_tracks()
        
        # Use the currently selected track, or the first track if none is selected
        selected_track = self.view.selected_track if self.view.selected_track else tracks[0]
        track_index = tracks.index(selected_track)
        
        # Get the current playhead position
        start_time = self.timeline_model.get_playhead_position()
        
        # Find the next available position
        for clip in selected_track['clips']:
            if clip.x <= start_time < clip.x + clip.duration:
                start_time = clip.x + clip.duration
        
        # Create the new clip
        new_clip = AudioClip(file_path, start_time)
        
        # Add the clip to the model
        self.timeline_model.add_clip_to_track(track_index, new_clip)
        
        # Update the view
        if self.view:
            self.view.add_clip(new_clip, track_index)
            self.view.redraw_timeline()
        
        self.unsaved_changes = True
        logging.info(f"Added audio clip to track {track_index} at position {start_time}")

    def add_audio_clip_to_track(self, file_path, track_name, start_time, index):
        track_index = self.get_or_create_track(track_name)
        
        # Create the new clip
        new_clip = AudioClip(file_path, start_time, index)
        
        # Add the clip to the model
        self.timeline_model.add_clip_to_track(track_index, new_clip)
        
        # Update the view
        if self.view:
            self.view.update_tracks(self.timeline_model.get_tracks())  # Ensure view is updated with new tracks
            self.view.add_clip(new_clip, track_index)
            self.view.redraw_timeline()
        
        self.unsaved_changes = True
        logging.info(f"Added audio clip to track '{track_name}' (index: {track_index}) at position {start_time}")
           
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

    def on_playback_state_change(self, is_playing, position):
        if self.view and self.view.winfo_exists():
            if is_playing:
                self.view.on_playback_started(position)
            else:
                self.view.on_playback_stopped(position)

    def play_timeline(self):
        active_tracks = self.get_active_tracks()
        self.timeline_model.play_timeline(active_tracks)
        logging.info(f"Timeline playback initiated from controller. Initial position: {self.timeline_model.playhead_position}")

    def stop_timeline(self):
        self.timeline_model.stop_timeline()
        logging.info("Timeline playback stopped from controller")

    def update_playhead_view(self, position):
        if self.view:
            self.view.update_playhead_position(position)
            
    def set_playhead_position(self, position):
        self.timeline_model.set_playhead_position(position)
        if self.view:
            self.view.update_playhead_position(position)
        logging.info(f"Playhead position set to {position}")

    def restart_timeline(self):
        if self.timeline_model.is_playing:
            self.stop_timeline()
            # Add small delay to ensure stop is processed
            self.view.after(100, lambda: self.set_playhead_position(0))
        else:
            self.set_playhead_position(0)

    def get_playhead_position(self):
        position = self.timeline_model.get_playhead_position()
        return min(position, self.max_playhead_position)
    
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
        return len(self.timeline_model.get_tracks()) - 1  # Return the index of the new track

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
    
    def export_audio(self):
        if not self.timeline_model.get_tracks():
            messagebox.showerror("Error", "No tracks to export")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".mp3",
            filetypes=[("MP3 files", "*.mp3")]
        )

        if not file_path:
            return  # User cancelled the file dialog

        try:
            self.view.show_progress_bar(determinate=True)
            self.view.update_status("Exporting audio...")

            # Get the end time of the last clip
            end_time = max(
                clip.x + clip.duration
                for track in self.timeline_model.get_tracks()
                for clip in track['clips']
            )

            # Initialize an empty numpy array for the final mix
            sample_rate = 44100
            channels = 2
            final_mix = np.zeros((int(end_time * sample_rate), channels))

            total_clips = sum(len(track['clips']) for track in self.timeline_model.get_tracks())
            processed_clips = 0

            for track in self.timeline_model.get_tracks():
                for clip in track['clips']:
                    audio_data = self.timeline_model.get_clip_frames(clip, 0, clip.duration)
                    start_sample = int(clip.x * sample_rate)
                    end_sample = start_sample + len(audio_data)
                    
                    if end_sample > len(final_mix):
                        pad_length = end_sample - len(final_mix)
                        final_mix = np.pad(final_mix, ((0, pad_length), (0, 0)))

                    final_mix[start_sample:end_sample] += audio_data * track.get("volume", 1.0)

                    processed_clips += 1
                    self.view.progress_bar.set(processed_clips / total_clips)

            # Normalize the final mix
            max_amplitude = np.max(np.abs(final_mix))
            if max_amplitude > 0:
                final_mix = final_mix / max_amplitude

            # Export as MP3
            with sf.SoundFile(file_path, 'w', samplerate=sample_rate, channels=channels, format='mp3') as f:
                f.write(final_mix)

            self.view.update_status(f"Audio exported successfully to {file_path}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export audio: {str(e)}")
        finally:
            self.view.hide_progress_bar()

    def undo_action(self):
        self.timeline_model.undo()
        self.load_timeline_data()
        self.update_status("Undo successful")

    def redo_action(self):
        self.timeline_model.redo()
        self.load_timeline_data()
        self.update_status("Redo successful")