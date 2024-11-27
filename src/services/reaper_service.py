import reapy
import logging
import os
import math
from datetime import datetime

class ReaperService:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        
    def is_reaper_running(self):
        """Check if Reaper is running and accessible"""
        try:
            import warnings
            from reapy.errors import DisabledDistAPIWarning
            
            # Catch DisabledDistAPIWarning
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                
                try:
                    reapy.connect()
                    
                    for warning in w:
                        if issubclass(warning.category, DisabledDistAPIWarning):
                            self.logger.error("Reaper not running or ReaScript not enabled")
                            return False
                            
                    return True
                    
                except AttributeError:
                    self.logger.error("ReaScript API not accessible")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Failed to connect to Reaper: {str(e)}")
            return False

    def add_audio_file(self, file_path, track_name=None):
        """
        Add an audio file to the current Reaper project
        
        Args:
            file_path (str): Path to the audio file
            track_name (str, optional): Name for the new track
            
        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            if not self.is_reaper_running():
                return False, ("Please make sure:\n"
                            "1. REAPER is running\n"
                            "2. ReaScript is enabled in REAPER:\n"
                            "   - Open REAPER\n"
                            "   - Go to Preferences -> Plug-ins -> ReaScript\n"
                            "   - Enable 'Allow Python to access REAPER via ReaScript'")

            # Convert to absolute path
            abs_file_path = os.path.abspath(file_path)
            
            self.logger.info(f"Attempting to add file: {abs_file_path}")
            
            if not os.path.exists(abs_file_path):
                self.logger.error("File not found!")
                return False, f"Audio file not found: {abs_file_path}"

            # Get the current project
            project = reapy.Project()
            
            # Add a new track at the end
            new_track = project.add_track()
            
            # Set track name
            if track_name:
                new_track.name = track_name
            else:
                new_track.name = os.path.splitext(os.path.basename(abs_file_path))[0]
            
            # Make this track the only selected track
            new_track.make_only_selected_track()
            
            # Add media to the track - mode 0 means add to current track
            reapy.reascript_api.InsertMedia(abs_file_path, 0)
            
            # Update the Reaper UI
            reapy.update_arrange()
            
            # Print to Reaper console
            reapy.show_console_message(f"Added audio file: {abs_file_path} to track: {new_track.name}\n")
            
            self.logger.info("Audio file added successfully!")
            return True, "Audio file added successfully"
            
        except Exception as e:
            error_msg = f"Error adding audio to Reaper: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg
    
    
    def sync_timeline_to_reaper(self, tracks_data):
        """
        Synchronize the timeline with the currently opened Reaper project
        
        Args:
            tracks_data (list): List of track data containing clips and their properties
            
        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            if not self.is_reaper_running():
                return False, "Reaper is not running"

            self.logger.info("Starting timeline sync with Reaper")
            
            # Get the current project
            project = reapy.Project()
            
            # Start undo block
            project.begin_undo_block()
            
            try:
                # Process each track
                for track_data in tracks_data:
                    self.logger.info(f"Processing track: {track_data['name']}")
                    
                    # Create a new track
                    track = project.add_track()
                    track.name = track_data['name']
                    self.logger.debug(f"Created track: {track_data['name']}")
                    
                    # Set track properties
                    if track_data.get('mute', False):
                        track.mute = True
                        self.logger.debug(f"Track {track_data['name']} set to mute")
                    
                    if track_data.get('solo', False):
                        track.solo = True
                        self.logger.debug(f"Track {track_data['name']} set to solo")
                    
                    # Set track volume
                    volume = track_data.get('volume', 1.0)
                    if volume > 0:
                        track.volume = volume
                        self.logger.debug(f"Track {track_data['name']} volume set to {volume}")
                    
                    # Make this track the only selected track
                    track.make_only_selected_track()
                    
                    # Add clips to track
                    for clip in track_data['clips']:
                        if os.path.exists(clip.file_path):
                            self.logger.debug(f"Adding clip: {clip.file_path} at position {clip.x}")
                            
                            try:
                                # Convert to absolute path
                                abs_file_path = os.path.abspath(clip.file_path)
                                
                                # Insert media to the track - mode 0 means add to current track
                                reapy.reascript_api.InsertMedia(abs_file_path, 0)
                                
                                # Get the newly inserted media item (should be the last item on the track)
                                media_item = track.items[-1]
                                
                                # Set the position of the media item
                                media_item.position = clip.x
                                
                                self.logger.debug(f"Successfully added clip at position {clip.x}")
                            except Exception as e:
                                self.logger.error(f"Error adding clip {clip.file_path}: {str(e)}")
                        else:
                            self.logger.warning(f"Audio file not found: {clip.file_path}")
                
                # End undo block
                project.end_undo_block("Sync Timeline to Reaper")
                
                # Update the Reaper UI
                reapy.update_arrange()
                
                self.logger.info("Timeline successfully synced to Reaper")
                return True, "Timeline successfully synced to Reaper"
                
            except Exception as e:
                project.end_undo_block("Sync Timeline to Reaper (Failed)")
                raise e
            
        except Exception as e:
            error_msg = f"Error syncing timeline to Reaper: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return False, error_msg