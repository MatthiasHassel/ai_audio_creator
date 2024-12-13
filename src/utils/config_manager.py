import os
import sys
import yaml
from pathlib import Path
from dotenv import load_dotenv

def get_base_dir():
    """Get the base directory for the application in both development and bundled environments."""
    if getattr(sys, 'frozen', False):
        # Running in a bundle
        return os.path.join(os.path.dirname(sys.executable), '..')
    else:
        # Running in development
        return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def get_config_dir():
    """Get the configuration directory for both development and bundled environments."""
    config_dir = os.path.join(Path.home(), '.ai_audio_creator')
    os.makedirs(config_dir, exist_ok=True)
    return config_dir

def create_default_config():
    """Create default configuration file."""
    # Get base directory for relative paths
    projects_dir = os.path.join(Path.home(), 'AI Audio Creator')
    
    default_config = {
        'api': {
            'elevenlabs_api_key': '',
            'openai_api_key': '',
            'openrouter_api_key': '',
            'suno_cookie': '',
            'selected_model': 'llama'  # Default to llama (OpenRouter)
        },
        'logging': {
            'level': 'INFO',
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        },
        'projects': {
            'base_dir': projects_dir
        },
        'audio_generator_gui': {
            'window_size': '1200x800'
        },
        'music_gen': {
            'base_url': 'http://localhost:3000'
        },
        'sfx_gen': {
            'min_duration': 0.5,
            'max_duration': 22.0
        },
        'speech_gen': {},
        'audio': {
            'output_device_index': None,  # Will be set to system default
            'input_device_index': None,   # Will be set to system default
            'output_device_name': '',     # For display/persistence
            'input_device_name': ''       # For display/persistence
        }
    }
    return default_config

def load_config():
    """Load configuration from YAML file and environment variables."""
    try:
        # Get config directory
        config_dir = get_config_dir()
        
        # Load .env file from config directory
        env_path = os.path.join(config_dir, '.env')
        if os.path.exists(env_path):
            load_dotenv(env_path)
        
        # Get config file path
        config_path = os.path.join(config_dir, 'config.yaml')
        
        # Create default config if it doesn't exist
        if not os.path.exists(config_path):
            config = create_default_config()
            with open(config_path, 'w') as file:
                yaml.dump(config, file)
        else:
            # Load existing config
            with open(config_path, 'r') as file:
                config = yaml.safe_load(file)
        
        # Update API keys from environment variables if they exist
        if os.getenv('ELEVENLABS_API_KEY'):
            config['api']['elevenlabs_api_key'] = os.getenv('ELEVENLABS_API_KEY')
        if os.getenv('OPENAI_API_KEY'):
            config['api']['openai_api_key'] = os.getenv('OPENAI_API_KEY')
        if os.getenv('OPENROUTER_API_KEY'):
            config['api']['openrouter_api_key'] = os.getenv('OPENROUTER_API_KEY')
        if os.getenv('SUNO_COOKIE'):
            config['api']['suno_cookie'] = os.getenv('SUNO_COOKIE')
        
        # Ensure all required config sections exist with defaults
        default_config = create_default_config()
        for section, values in default_config.items():
            if section not in config:
                config[section] = values
            elif isinstance(values, dict):
                # Update nested configuration while preserving existing values
                for key, value in values.items():
                    if key not in config[section]:
                        config[section][key] = value
        
        # Ensure selected_model has a valid value
        if config['api'].get('selected_model') not in ['llama', 'openai']:
            config['api']['selected_model'] = 'llama'  # Default to llama if invalid
        
        # Create base projects directory
        os.makedirs(config['projects']['base_dir'], exist_ok=True)
        
        return config
        
    except Exception as e:
        print(f"Error loading configuration: {str(e)}")
        # In case of any error, return default config
        return create_default_config()
