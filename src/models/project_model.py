import os
import json
import datetime
import logging
import shutil
from models.timeline_model import TimelineModel  
from pydub import AudioSegment

class ProjectModel:
    def __init__(self, base_projects_dir):
        self.base_projects_dir = base_projects_dir
        self.current_project = None
        self.metadata = {}
        self.default_project_name = "Default Project"
        self.timeline_model = TimelineModel()  
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
        
        os.makedirs(project_dir)
        os.makedirs(os.path.join(project_dir, "output", "music"))
        os.makedirs(os.path.join(project_dir, "output", "sfx"))
        os.makedirs(os.path.join(project_dir, "output", "speech"))
        os.makedirs(os.path.join(project_dir, "scripts"))
        os.makedirs(os.path.join(project_dir, "audio_files"))

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
        project_dir = os.path.join(self.base_projects_dir, project_name)
        if not os.path.exists(project_dir):
            raise ValueError(f"Project '{project_name}' does not exist")
        
        self.current_project = project_name
        self.load_project_metadata()
        self.load_timeline_data()
        self.saved_audio_files.update(self.get_all_project_audio_files())

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
                print(f"Error parsing project metadata: {str(e)}")
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
            except json.JSONDecodeError as e:
                print(f"Error parsing timeline data: {str(e)}")
                self.timeline_model.clear_tracks()
        else:
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
        
        # Load the audio file
        audio = AudioSegment.from_file(file_path)
        
        # Check if the sample rate is either 44.1kHz or 48kHz
        if audio.frame_rate not in [44100, 48000]:
            raise ValueError(f"Unsupported sample rate: {audio.frame_rate}Hz. Only 44.1kHz and 48kHz are supported.")
        
        audio_files_dir = self.get_audio_files_dir()
        file_name = os.path.basename(file_path)
        destination = os.path.join(audio_files_dir, file_name)
        
        os.makedirs(audio_files_dir, exist_ok=True)
        
        # Resample if necessary
        if audio.frame_rate == 48000:
            print(f"Resampling {file_name} from 48kHz to 44.1kHz")
            audio = audio.set_frame_rate(44100)
            audio.export(destination, format="wav")
        else:
            # If it's already 44.1kHz, just copy the file
            shutil.copy2(file_path, destination)
        
        print(f"File imported to: {destination}")
        self.new_audio_files.add(destination)
        return destination
    
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
                    print(f"Removed unsaved audio file: {file_path}")
                except OSError as e:
                    print(f"Error removing file {file_path}: {e}")
            self.new_audio_files.remove(file_path)
            
    def get_audio_files_dir(self):
        if not self.current_project:
            raise ValueError("No project is currently active")
        return os.path.join(self.get_project_dir(), "audio_files")
    
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