import reapy
import logging
import os

class ReaperService:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        
    def is_reaper_running(self):
        """Check if Reaper is running and accessible"""
        try:
            reapy.connect()
            return True
        except:
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
                return False, "Reaper is not running"

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