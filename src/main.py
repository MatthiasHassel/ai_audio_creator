from models.main_model import MainModel
from views.main_view import MainView
from controllers.main_controller import MainController
from utils.config_manager import load_config

def main():
    # Load configuration
    config = load_config()

    # Create main components
    model = MainModel()
    view = MainView(config)
    controller = MainController(model, view, config)

    # Run the application
    controller.run()

if __name__ == "__main__":
    main()