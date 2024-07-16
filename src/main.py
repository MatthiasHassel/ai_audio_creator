# src/main.py

from models.main_model import MainModel
from models.project_model import ProjectModel
from views.main_view import MainView
from controllers.main_controller import MainController
from utils.config_manager import load_config
import logging

def setup_logging(config):
    logging.basicConfig(
        level=config['logging']['level'],
        format=config['logging']['format'],
        filename=config['logging']['file']
    )

def main():
    # Load configuration
    config = load_config()

    # Setup logging
    setup_logging(config)

    # Create main components
    main_model = MainModel()
    project_model = ProjectModel(config['projects']['base_dir'])
    view = MainView(config, project_model)
    controller = MainController(main_model, view, config, project_model)
    controller.timeline_controller.set_toggle_audio_creator_command(controller.view.toggle_visibility)

    # Run the application
    controller.run()

if __name__ == "__main__":
    main()