import sys
import os
import customtkinter as ctk
from pathlib import Path
import logging

def set_working_directory():
    """Set the working directory based on how the app is launched."""
    try:
        if getattr(sys, 'frozen', False):
            # Running in a bundle
            if sys.platform == 'darwin':
                # On macOS, the bundle structure is:
                # MyApp.app/
                #   Contents/
                #     MacOS/
                #       executable
                #     Resources/
                #       ...
                bundle_dir = os.path.dirname(sys.executable)  # .../Contents/MacOS
                resources_dir = os.path.join(bundle_dir, '..', 'Resources')
                resources_dir = os.path.abspath(resources_dir)
                
                # Set working directory to Resources
                os.chdir(resources_dir)
                return resources_dir
        else:
            # Running in development
            src_dir = os.path.dirname(os.path.abspath(__file__))
            base_dir = os.path.dirname(src_dir)
            os.chdir(base_dir)
            return base_dir
    except Exception as e:
        print(f"Error setting working directory: {str(e)}")
        return None

# Set working directory before anything else
app_dir = set_working_directory()

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

# Set up basic logging as early as possible
def setup_basic_logging():
    try:
        # Get the directory for logs
        if getattr(sys, 'frozen', False):
            # Running in a bundle
            log_dir = os.path.expanduser('~/Library/Logs/AI Audio Creator')
        else:
            # Development logging
            log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
        
        # Ensure log directory exists
        os.makedirs(log_dir, exist_ok=True)
        log_file_path = os.path.join(log_dir, 'ai_audio_creator.log')

        # Set up logging with default configuration
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file_path, mode='a'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        # Log initial information
        logging.info("Application starting")
        logging.info(f"Python version: {sys.version}")
        logging.info(f"Running from bundle: {getattr(sys, 'frozen', False)}")
        logging.info(f"Application path: {os.path.dirname(os.path.abspath(sys.argv[0]))}")
        logging.info(f"Working directory: {os.getcwd()}")
        logging.info(f"App directory: {app_dir}")
        logging.info(f"Python path: {sys.path}")
        logging.info(f"Log file location: {log_file_path}")
        
        return True
    except Exception as e:
        print(f"Error setting up logging: {str(e)}")
        return False

# Set up basic logging before anything else
if not setup_basic_logging():
    print("Failed to set up logging")
    sys.exit(1)

def import_with_error_handling(module_name):
    try:
        return __import__(module_name, fromlist=['*'])
    except ImportError as e:
        logging.error(f"Error importing {module_name}: {e}")
        logging.error(f"Python path: {sys.path}")
        logging.error("This might be due to incorrect installation or missing dependencies.")
        print(f"Error importing {module_name}: {e}")
        print(f"Python path: {sys.path}")
        print("This might be due to incorrect installation or missing dependencies.")
        print("Try reinstalling the application or contact support.")
        sys.exit(1)

# Import required modules with error handling
try:
    import customtkinter as ctk
    from pathlib import Path
    
    # Import local modules
    MainModel = import_with_error_handling('models.main_model').MainModel
    ProjectModel = import_with_error_handling('models.project_model').ProjectModel
    MainView = import_with_error_handling('views.main_view').MainView
    MainController = import_with_error_handling('controllers.main_controller').MainController
    first_run_wizard = import_with_error_handling('views.first_run_wizard')
    config_manager = import_with_error_handling('utils.config_manager')
    ffmpeg_utils = import_with_error_handling('utils.ffmpeg_utils')

except ImportError as e:
    logging.error(f"Error importing required modules: {e}")
    logging.error(f"Python path: {sys.path}")
    print(f"Error importing required modules: {e}")
    print(f"Python path: {sys.path}")
    print("This might be due to incorrect installation or missing dependencies.")
    print("Try reinstalling the application or contact support.")
    sys.exit(1)

def update_logging_from_config(config):
    """Update logging configuration based on loaded config."""
    try:
        root_logger = logging.getLogger()
        root_logger.setLevel(config['logging']['level'])
        
        # Update format for all handlers
        formatter = logging.Formatter(config['logging']['format'])
        for handler in root_logger.handlers:
            handler.setFormatter(formatter)
            
        logging.info("Logging configuration updated from config file")
    except Exception as e:
        logging.error(f"Error updating logging configuration: {str(e)}")

def check_first_run():
    """Check if this is the first run of the application."""
    config_dir = config_manager.get_config_dir()
    config_path = os.path.join(config_dir, 'config.yaml')
    return not os.path.exists(config_path)

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
        # Log system information
        logging.info(f"Environment variables: {dict(os.environ)}")
        logging.info(f"Current working directory: {os.getcwd()}")
        
        # Create root window
        root = ctk.CTk()
        root.withdraw()  # Hide the root window
        
        # Configure ffmpeg before anything else
        if not ffmpeg_utils.configure_pydub():
            logging.error("Failed to configure ffmpeg")
            print("Failed to configure ffmpeg")
            sys.exit(1)
        
        # Check for first run
        if check_first_run():
            logging.info("First run detected, launching setup wizard")
            if not first_run_wizard.run_first_time_setup():
                logging.info("First-time setup cancelled")
                print("First-time setup cancelled")
                sys.exit(0)
            logging.info("First-time setup completed successfully")
        
        # Load configuration
        config = config_manager.load_config()
        if not config:
            logging.error("Failed to load configuration")
            print("Failed to load configuration")
            sys.exit(1)

        # Update logging configuration from loaded config
        update_logging_from_config(config)
        
        # Create main components with config
        main_model = MainModel(config)
        project_model = ProjectModel(config['projects']['base_dir'], config)  # Fixed: Pass base_dir and config
        view = MainView(root, config, project_model)
        controller = MainController(main_model, view, config, project_model)

        # Run the application
        logging.info("Starting main application loop")
        controller.run()
        
    except Exception as e:
        logging.error(f"Error starting application: {str(e)}", exc_info=True)
        print(f"Error starting application: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
