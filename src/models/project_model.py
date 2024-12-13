import os
import json
import datetime
import logging
import shutil
from models.timeline_model import TimelineModel  
from pydub import AudioSegment
from tkinter import messagebox

class ProjectModel:
    def __init__(self, base_projects_dir, config=None):
        self.base_projects_dir = base_projects_dir
        self.current_project = None
        self.metadata = {}
        self.default_project_name = "Default Project"
        self.timeline_model = TimelineModel(config)  # Pass config to TimelineModel
        self.saved_audio_files = set()
        self.new_audio_files = set()
        self.timeline_clips = set()

    def ensure_default_project(self):
        default_project_path = os.path.join(self.base_projects_dir, self.default_project_name)
        if not os.path.exists(default_project_path):
            self.create_project(self.default_project_name)
        self.load_project(self.default_project_name)

    def create_project(self, project_name):
        project_dir = os.path.join(self.base_projects_dir, project_name)
        if os.path.exists(project_dir):
            raise ValueError(f"Project '{project_name}' already exists")
        
        # Create main project directory
        os.makedirs(project_dir)
        
        # Create imported audio files directory for imported audio
        os.makedirs(os.path.join(project_dir, "imported_audio_files"))
        
        # Create output directory with subdirectories
        output_dir = os.path.join(project_dir, "output")
        os.makedirs(output_dir)
        os.makedirs(os.path.join(output_dir, "music"))
        os.makedirs(os.path.join(output_dir, "sfx"))
        os.makedirs(os.path.join(output_dir, "speech"))
        
        # Create scripts directory
        os.makedirs(os.path.join(project_dir, "scripts"))

        self.current_project = project_name
        self.metadata = {
            "name": project_name,
            "created_at": datetime.datetime.now().isoformat(),
            "last_modified": datetime.datetime.now().isoformat(),
            "last_opened_script": None
        }
        self.timeline_model.clear_tracks()  # Clear tracks for new project
        self.save_project_metadata()
        self.save_timeline_data()

    def load_project(self, project_name):
        try:
            project_dir = os.path.join(self.base_projects_dir, project_name)
            if not os.path.exists(project_dir):
                raise ValueError(f"Project '{project_name}' does not exist")
            
            self.current_project = project_name
            self.load_project_metadata()
            self.load_timeline_data()
            
            # Preload audio files after loading timeline data
            try:
                self.timeline_model.preload_audio_files()
            except Exception as e:
                logging.error(f"Error preloading audio files: {str(e)}")
            
            self.saved_audio_files.update(self.get_all_project_audio_files())
            logging.info(f"Project '{project_name}' loaded successfully")
            
        except Exception as e:
            logging.error(f"Error loading project '{project_name}': {str(e)}")
            raise

    def save_project(self):
        if not self.current_project:
            raise ValueError("No project is currently active")
        
        try:
            self.save_project_metadata()
            self.save_timeline_data()
            self.update_saved_audio_files()
            self.saved_audio_files.update(self.get_all_project_audio_files())
            logging.info(f"Project '{self.current_project}' saved successfully.")
            return True, "Project saved successfully."
        except Exception as e:
            error_msg = f"Failed to save project: {str(e)}"
            logging.error(error_msg)
            return False, error_msg

    def save_project_metadata(self):
        self.metadata["last_modified"] = datetime.datetime.now().isoformat()
        
        metadata_file = os.path.join(self.get_project_dir(), "project_metadata.json")
        with open(metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)
    
    def load_project_metadata(self):
        metadata_file = os.path.join(self.get_project_dir(), "project_metadata.json")
        if os.path.exists(metadata_file):
            try:
                with open(metadata_file, 'r') as f:
                    self.metadata = json.load(f)
            except json.JSONDecodeError as e:
                logging.error(f"Error parsing project metadata: {str(e)}")
                self.metadata = {}
        else:
            self.metadata = {}

    def save_timeline_data(self):
        timeline_file = os.path.join(self.get_project_dir(), "timeline_data.json")
        serializable_tracks = self.timeline_model.get_serializable_tracks()
        with open(timeline_file, 'w') as f:
            json.dump(serializable_tracks, f, indent=2)

    def load_timeline_data(self):
        timeline_file = os.path.join(self.get_project_dir(), "timeline_data.json")
        if os.path.exists(timeline_file):
            try:
                with open(timeline_file, 'r') as f:
                    serializable_tracks = json.load(f)
                self.timeline_model.load_from_serializable(serializable_tracks)
                logging.info("Timeline data loaded successfully")
            except json.JSONDecodeError as e:
                logging.error(f"Error parsing timeline data: {str(e)}")
                self.timeline_model.clear_tracks()
        else:
            logging.info("No timeline data found, starting with empty timeline")
            self.timeline_model.clear_tracks()

    def is_file_in_output_directory(self, file_path):
        output_dirs = [
            os.path.join(self.get_project_dir(), "output", dir_name)
            for dir_name in ['music', 'sfx', 'speech']
        ]
        return any(file_path.startswith(dir_path) for dir_path in output_dirs)
    
    def get_all_project_audio_files(self):
        audio_files = []
        for directory in ['music', 'sfx', 'speech']:
            dir_path = os.path.join(self.get_project_dir(), "output", directory)
            if os.path.exists(dir_path):
                for file in os.listdir(dir_path):
                    if file.endswith(('.mp3', '.wav')):
                        audio_files.append(os.path.join(dir_path, file))
        return audio_files
    
    def get_timeline_model(self):
        return self.timeline_model

    def get_timeline_data(self):
        return self.timeline_model.get_tracks()

    def update_timeline_data(self, new_timeline_data):
        self.timeline_model.load_from_serializable(new_timeline_data)
        self.save_timeline_data()

    def get_last_opened_script(self):
        return self.metadata.get('last_opened_script')

    def set_last_opened_script(self, script_path):
        self.metadata['last_opened_script'] = script_path
        self.save_project_metadata()

    def get_scripts_dir(self):
        if not self.current_project:
            raise ValueError("No project is currently active")
        return os.path.join(self.get_project_dir(), "scripts")

    def get_output_dir(self, category):
        if not self.current_project:
            raise ValueError("No project is currently active")
        return os.path.join(self.get_project_dir(), "output", category)

    def get_project_dir(self):
        if not self.current_project:
            raise ValueError("No project is currently active")
        return os.path.join(self.base_projects_dir, self.current_project)
    
    def import_audio_file(self, file_path):
        if not self.current_project:
            raise ValueError("No project is currently active")
        
        if self.is_file_in_output_directory(file_path):
            return file_path
        
        try:
            # Load the audio file
            audio = AudioSegment.from_file(file_path)
            
            # Check if the sample rate is either 44.1kHz or 48kHz
            if audio.frame_rate not in [44100, 48000]:
                raise ValueError(f"Unsupported sample rate: {audio.frame_rate}Hz. Only 44.1kHz and 48kHz are supported.")
            
            audio_files_dir = self.get_audio_files_dir()
            file_name = os.path.basename(file_path)
            destination = os.path.join(audio_files_dir, file_name)
            
            os.makedirs(audio_files_dir, exist_ok=True)
            
            # Convert to MP3 if not already
            if not file_path.lower().endswith('.mp3'):
                logging.info(f"Converting {file_name} to MP3 format")
                # If sample rate is 48kHz, resample to 44.1kHz during conversion
                if audio.frame_rate == 48000:
                    logging.info(f"Resampling {file_name} from 48kHz to 44.1kHz")
                    audio = audio.set_frame_rate(44100)
                # Export as MP3
                destination = os.path.splitext(destination)[0] + '.mp3'
                audio.export(destination, format="mp3", parameters=["-q:a", "0"])  # High quality MP3
            else:
                # If it's already MP3, just resample if needed
                if audio.frame_rate == 48000:
                    logging.info(f"Resampling {file_name} from 48kHz to 44.1kHz")
                    audio = audio.set_frame_rate(44100)
                    audio.export(destination, format="mp3", parameters=["-q:a", "0"])
                else:
                    shutil.copy2(file_path, destination)
            
            logging.info(f"File imported to: {destination}")
            self.new_audio_files.add(destination)
            return destination
            
        except Exception as e:
            logging.error(f"Error importing audio file: {str(e)}")
            raise
    
    def update_saved_audio_files(self):
        self.saved_audio_files.update(self.new_audio_files)
        self.new_audio_files.clear()

    def get_saved_audio_files(self):
        return self.saved_audio_files

    def get_new_audio_files(self):
        return self.new_audio_files

    def add_clip_to_timeline(self, file_path):
        self.timeline_clips.add(file_path)

    def remove_clip_from_timeline(self, file_path):
        self.timeline_clips.discard(file_path)
        # Only handle deletion for imported audio files
        if not self.is_clip_in_timeline(file_path) and self.is_imported_audio_file(file_path):
            # Show warning before deleting
            if messagebox.askyesno("Delete Audio File", 
                                 "This was the last instance of this imported audio clip. Delete the imported audio file as well?"):
                try:
                    os.remove(file_path)
                    logging.info(f"Deleted unused imported audio file: {file_path}")
                except OSError as e:
                    logging.error(f"Error deleting file {file_path}: {e}")

    def is_imported_audio_file(self, file_path):
        """Check if the file is in the imported_audio_files directory"""
        imported_audio_dir = self.get_audio_files_dir()
        return os.path.commonpath([imported_audio_dir]) == os.path.commonpath([imported_audio_dir, file_path])

    def clear_timeline_clips(self):
        self.timeline_clips.clear()

    def is_clip_in_timeline(self, file_path):
        return file_path in self.timeline_clips

    def remove_unsaved_audio_files(self):
        audio_files_dir = self.get_audio_files_dir()
        for file_path in list(self.new_audio_files):
            if file_path.startswith(audio_files_dir) and file_path not in self.timeline_clips:
                try:
                    os.remove(file_path)
                    logging.info(f"Removed unsaved audio file: {file_path}")
                except OSError as e:
                    logging.error(f"Error removing file {file_path}: {e}")
            self.new_audio_files.remove(file_path)
            
    def get_audio_files_dir(self):
        if not self.current_project:
            raise ValueError("No project is currently active")
        return os.path.join(self.get_project_dir(), "imported_audio_files")
    
    def rename_project(self, new_name):
        if not self.current_project:
            raise ValueError("No project is currently active")
        
        old_path = self.get_project_dir()
        new_path = os.path.join(self.base_projects_dir, new_name)
        
        if os.path.exists(new_path):
            raise ValueError("A project with this name already exists")
        
        os.rename(old_path, new_path)
        self.current_project = new_name
        self.metadata["name"] = new_name
        self.save_project_metadata()

    def delete_project(self):
        if not self.current_project:
            raise ValueError("No project is currently active")
        
        project_path = self.get_project_dir()
        shutil.rmtree(project_path)
        self.current_project = None
        self.metadata = {}
        self.timeline_model.clear_tracks()
        self.saved_audio_files.clear()
        self.new_audio_files.clear()
