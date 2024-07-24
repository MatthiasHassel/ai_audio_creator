import os
import json
import datetime
import logging
import shutil
from models.timeline_model import TimelineModel  

class ProjectModel:
    def __init__(self, base_projects_dir):
        self.base_projects_dir = base_projects_dir
        self.current_project = None
        self.metadata = {}
        self.default_project_name = "Default Project"
        self.timeline_model = TimelineModel()  
        self.saved_audio_files = set()
        self.new_audio_files = set()

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

    def save_project(self):
        if not self.current_project:
            raise ValueError("No project is currently active")
        
        try:
            self.save_project_metadata()
            self.save_timeline_data()
            self.update_saved_audio_files()
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
        
        audio_files_dir = self.get_audio_files_dir()
        file_name = os.path.basename(file_path)
        destination = os.path.join(audio_files_dir, file_name)
        
        os.makedirs(audio_files_dir, exist_ok=True)
        shutil.copy2(file_path, destination)
        print(f"File copied to: {destination}")  # For debugging
        self.new_audio_files.add(destination)
        return destination
    
    def update_saved_audio_files(self):
        self.saved_audio_files.update(self.new_audio_files)
        self.new_audio_files.clear()

    def get_saved_audio_files(self):
        return self.saved_audio_files

    def get_new_audio_files(self):
        return self.new_audio_files

    def remove_unsaved_audio_files(self):
        for file_path in self.new_audio_files:
            try:
                os.remove(file_path)
                print(f"Removed unsaved audio file: {file_path}")
            except OSError as e:
                print(f"Error removing file {file_path}: {e}")
        self.new_audio_files.clear()

    def get_audio_files_dir(self):
        if not self.current_project:
            raise ValueError("No project is currently active")
        return os.path.join(self.get_project_dir(), "audio_files")