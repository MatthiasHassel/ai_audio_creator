import customtkinter as ctk
from tkinterdnd2 import TkinterDnD
from models.main_model import MainModel
from models.project_model import ProjectModel
from views.main_view import MainView
from controllers.main_controller import MainController
from utils.config_manager import load_config
import logging
import os

def setup_logging(config):
     # Get the directory of the main.py file
    src_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(src_dir)
    
    # Construct the log file path
    log_file_path = os.path.join(base_dir, 'logs', 'ai_audio_creator.log')
    
    # Ensure the logs directory exists
    os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

    try:
        logging.basicConfig(
            level=config['logging']['level'],
            format=config['logging']['format'],
            filename=log_file_path
        )
        print(f"Logging setup successful. Log file: {log_file_path}")
    except Exception as e:
        print(f"Error setting up logging: {str(e)}")
        raise

def main():
    # Load configuration
    config = load_config()

    # Setup logging
    setup_logging(config)
    logging.info("Application starting")
    
    # Create main components
    root = TkinterDnD.Tk()
    root.withdraw()  # Hide the root window
    
    main_model = MainModel()
    project_model = ProjectModel(config['projects']['base_dir'])
    view = MainView(root, config, project_model)
    controller = MainController(main_model, view, config, project_model)

    # Run the application
    controller.run()

if __name__ == "__main__":
    main()