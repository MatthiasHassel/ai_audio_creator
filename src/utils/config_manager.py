import os
import yaml
from dotenv import load_dotenv

def load_config():
    """Load configuration from YAML file and substitute environment variables."""
    load_dotenv()  # Load environment variables from .env file
    
    config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'config.yaml')
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