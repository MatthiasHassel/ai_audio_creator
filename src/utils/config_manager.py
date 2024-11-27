import os
import yaml
from dotenv import load_dotenv

def load_config():
    """Load configuration from YAML file and environment variables."""
    # Get base directory and load .env file
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    load_dotenv(os.path.join(base_dir, '.env'))
    
    # Load base config
    config_path = os.path.join(base_dir, 'config', 'config.yaml')
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)
    
    # Update API keys from environment variables
    config['api']['elevenlabs_api_key'] = os.getenv('ELEVENLABS_API_KEY', '')
    config['api']['openai_api_key'] = os.getenv('OPENAI_API_KEY', '')
    config['api']['openrouter_api_key'] = os.getenv('OPENROUTER_API_KEY', '')
    config['api']['suno_cookie'] = os.getenv('SUNO_COOKIE', '')

    
    return config
