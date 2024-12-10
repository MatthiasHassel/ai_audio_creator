import sys
import customtkinter as ctk
from pathlib import Path
from models.main_model import MainModel
from models.project_model import ProjectModel
from views.main_view import MainView
from controllers.main_controller import MainController
from views.first_run_wizard import ConfigWizard
from utils.config_manager import load_config
import logging
import os
from PySide6.QtWidgets import QApplication

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

def check_first_run():
    """Check if this is the first run of the application."""
    config_path = Path.home() / ".ai_audio_creator" / "config.yaml"
    return not config_path.exists()

def run_first_time_setup():
    """Run the first-time setup wizard."""
    app = QApplication(sys.argv)
    wizard = ConfigWizard()
    result = wizard.exec()
    app.quit()
    return result == ConfigWizard.Accepted

def main():
    # Check for first run
    if check_first_run():
        if not run_first_time_setup():
            print("First-time setup cancelled")
            sys.exit(0)
    
    # Load configuration
    config = load_config()
    if not config:
        print("Failed to load configuration")
        sys.exit(1)

    # Setup logging
    setup_logging(config)
    logging.info("Application starting")
    
    # Create main components
    root = ctk.CTk()
    root.withdraw()  # Hide the root window
    
    main_model = MainModel()
    project_model = ProjectModel(config['projects']['base_dir'])
    view = MainView(root, config, project_model)
    controller = MainController(main_model, view, config, project_model)

    # Run the application
    controller.run()

if __name__ == "__main__":
    main()
