import os
import json
import datetime

class ProjectModel:
    def __init__(self, base_projects_dir):
        self.base_projects_dir = base_projects_dir
        self.current_project = None
        self.metadata = {}
        self.default_project_name = "Default Project"
        self.timeline_data = []

    def create_project(self, project_name):
        project_dir = os.path.join(self.base_projects_dir, project_name)
        if os.path.exists(project_dir):
            raise ValueError(f"Project '{project_name}' already exists")
        
        os.makedirs(project_dir)
        os.makedirs(os.path.join(project_dir, "output", "music"))
        os.makedirs(os.path.join(project_dir, "output", "sfx"))
        os.makedirs(os.path.join(project_dir, "output", "speech"))
        os.makedirs(os.path.join(project_dir, "scripts"))

        self.current_project = project_name
        self.metadata = {
            "name": project_name,
            "created_at": datetime.datetime.now().isoformat(),
            "last_modified": datetime.datetime.now().isoformat(),
            "last_opened_script": None
        }
        self.timeline_data = []
        self.save_project_metadata()
        self.save_timeline_data()

    def load_project(self, project_name):
        project_dir = os.path.join(self.base_projects_dir, project_name)
        if not os.path.exists(project_dir):
            raise ValueError(f"Project '{project_name}' does not exist")
        
        self.current_project = project_name
        self.load_project_metadata()
        self.load_timeline_data()

    def ensure_default_project(self):
        if not os.path.exists(os.path.join(self.base_projects_dir, self.default_project_name)):
            self.create_project(self.default_project_name)
        self.load_project(self.default_project_name)

    def save_project_metadata(self):
        if not self.current_project:
            raise ValueError("No project is currently active")
        
        self.metadata["last_modified"] = datetime.datetime.now().isoformat()
        
        metadata_file = os.path.join(self.get_project_dir(), "project_metadata.json")
        with open(metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)

    def load_project_metadata(self):
        metadata_file = os.path.join(self.get_project_dir(), "project_metadata.json")
        if os.path.exists(metadata_file):
            with open(metadata_file, 'r') as f:
                self.metadata = json.load(f)
        else:
            self.metadata = {}

    def save_timeline_data(self):
        if not self.current_project:
            raise ValueError("No project is currently active")
        
        timeline_file = os.path.join(self.get_project_dir(), "timeline_data.json")
        with open(timeline_file, 'w') as f:
            json.dump(self.timeline_data, f, indent=2)

    def load_timeline_data(self):
        timeline_file = os.path.join(self.get_project_dir(), "timeline_data.json")
        if os.path.exists(timeline_file):
            with open(timeline_file, 'r') as f:
                self.timeline_data = json.load(f)
        else:
            self.timeline_data = []

    def get_timeline_data(self):
        return self.timeline_data

    def update_timeline_data(self, new_timeline_data):
        self.timeline_data = new_timeline_data
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