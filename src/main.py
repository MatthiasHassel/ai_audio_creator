import os
import logging
import yaml
from dotenv import load_dotenv
from gui.application import Application
from utils import ensure_dir_exists

def load_config():
    """Load configuration from YAML file and substitute environment variables."""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.yaml')
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)
    
    # Substitute environment variables
    def replace_env_vars(config):
        if isinstance(config, dict):
            return {key: replace_env_vars(value) for key, value in config.items()}
        elif isinstance(config, list):
            return [replace_env_vars(item) for item in config]
        elif isinstance(config, str) and config.startswith("${") and config.endswith("}"):
            env_var = config[2:-1]
            return os.getenv(env_var, config)
        else:
            return config

    return replace_env_vars(config)

def setup_logging(config):
    """Set up logging based on configuration."""
    log_config = config['logging']
    ensure_dir_exists(os.path.dirname(log_config['file']))
    logging.basicConfig(
        level=log_config['level'],
        format=log_config['format'],
        filename=log_config['file']
    )

def main():
    """Main entry point of the application."""
    # Load environment variables
    load_dotenv()

    # Load configuration
    config = load_config()

    # Debug: Print the API key (Be careful not to log this in production!)
    print(f"Config API Key: {config['api']['elevenlabs_api_key'][:5]}...")

    # Setup logging
    setup_logging(config)

    # Create output directories
    ensure_dir_exists(config['music_gen']['output_dir'])
    ensure_dir_exists(config['sfx_gen']['output_dir'])
    ensure_dir_exists(config['speech_gen']['output_dir'])

    # Initialize and run the application
    app = Application(config)
    app.mainloop()

if __name__ == "__main__":
    main()