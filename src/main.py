import sys
import os
import customtkinter as ctk
from pathlib import Path
from PySide6.QtWidgets import QApplication

# Add the src directory to Python path if we're running from source
if getattr(sys, 'frozen', False):
    # Running in a bundle
    bundle_dir = os.path.dirname(sys.executable)
    # Add the Resources directory to Python path for bundled modules
    sys.path.append(os.path.join(bundle_dir, '..', 'Resources'))
    sys.path.append(os.path.join(bundle_dir, '..', 'Resources', 'src'))
else:
    # Running in development
    src_dir = os.path.dirname(os.path.abspath(__file__))
    if src_dir not in sys.path:
        sys.path.insert(0, os.path.dirname(src_dir))

# Version check flag
if len(sys.argv) > 1 and sys.argv[1] == '--version':
    print("AI Audio Creator v0.1.0")
    sys.exit(0)

def import_with_error_handling(module_name):
    try:
        return __import__(module_name, fromlist=['*'])
    except ImportError as e:
        print(f"Error importing {module_name}: {e}")
        print(f"Python path: {sys.path}")
        print("This might be due to incorrect installation or missing dependencies.")
        print("Try reinstalling the application or contact support.")
        sys.exit(1)

# Import required modules with error handling
try:
    import customtkinter as ctk
    from pathlib import Path
    from PySide6.QtWidgets import QApplication
    
    # Import local modules
    MainModel = import_with_error_handling('models.main_model').MainModel
    ProjectModel = import_with_error_handling('models.project_model').ProjectModel
    MainView = import_with_error_handling('views.main_view').MainView
    MainController = import_with_error_handling('controllers.main_controller').MainController
    ConfigWizard = import_with_error_handling('views.first_run_wizard').ConfigWizard
    config_manager = import_with_error_handling('utils.config_manager')
    
    import logging

except ImportError as e:
    print(f"Error importing required modules: {e}")
    print(f"Python path: {sys.path}")
    print("This might be due to incorrect installation or missing dependencies.")
    print("Try reinstalling the application or contact support.")
    sys.exit(1)

def setup_logging(config):
    try:
        # Get the directory for logs
        if getattr(sys, 'frozen', False):
            # Running in a bundle
            log_dir = os.path.expanduser('~/Library/Logs/AI Audio Creator')
        else:
            # Development logging
            log_dir = os.path.join(config_manager.get_base_dir(), 'logs')
        
        # Ensure log directory exists
        os.makedirs(log_dir, exist_ok=True)
        log_file_path = os.path.join(log_dir, 'ai_audio_creator.log')

        logging.basicConfig(
            level=config['logging']['level'],
            format=config['logging']['format'],
            filename=log_file_path
        )
        print(f"Logging setup successful. Log file: {log_file_path}")
        
        # Log system information
        logging.info("Application starting")
        logging.info(f"Python version: {sys.version}")
        logging.info(f"Running from bundle: {getattr(sys, 'frozen', False)}")
        logging.info(f"Application path: {os.path.dirname(os.path.abspath(sys.argv[0]))}")
        logging.info(f"Python path: {sys.path}")
        
    except Exception as e:
        print(f"Error setting up logging: {str(e)}")
        raise

def check_first_run():
    """Check if this is the first run of the application."""
    config_dir = config_manager.get_config_dir()
    config_path = os.path.join(config_dir, 'config.yaml')
    return not os.path.exists(config_path)

def run_first_time_setup():
    """Run the first-time setup wizard."""
    app = QApplication.instance() or QApplication(sys.argv)
    wizard = ConfigWizard()
    result = wizard.exec()
    if not QApplication.instance():
        app.quit()
    return result == ConfigWizard.Accepted

def get_user_manual_path():
    """Get the path to the user manual based on the environment."""
    if getattr(sys, 'frozen', False):
        # Running in a bundle
        base_dir = os.path.join(os.path.dirname(sys.executable), '..')
        return os.path.join(base_dir, 'Resources', 'docs', 'AI_Audio_Creator_User_Manual.md')
    else:
        # Running in development
        base_dir = config_manager.get_base_dir()
        return os.path.join(base_dir, 'docs', 'AI_Audio_Creator_User_Manual.md')

def main():
    try:
        # Check for first run
        if check_first_run():
            if not run_first_time_setup():
                print("First-time setup cancelled")
                sys.exit(0)
        
        # Load configuration
        config = config_manager.load_config()
        if not config:
            print("Failed to load configuration")
            sys.exit(1)

        # Setup logging
        setup_logging(config)
        
        # Create main components
        root = ctk.CTk()
        root.withdraw()  # Hide the root window
        
        main_model = MainModel()
        project_model = ProjectModel(config['projects']['base_dir'])
        view = MainView(root, config, project_model)
        controller = MainController(main_model, view, config, project_model)

        # Run the application
        controller.run()
        
    except Exception as e:
        print(f"Error starting application: {str(e)}")
        if 'logging' in sys.modules:
            logging.error(f"Error starting application: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
