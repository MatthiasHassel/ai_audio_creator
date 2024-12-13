import os
import shutil
import platform
import subprocess
import logging
import sys
import numpy as np
from pathlib import Path
from pydub import AudioSegment

# Get logger for this module
logger = logging.getLogger(__name__)

def check_ffmpeg_installation():
    """
    Check if ffmpeg is installed and accessible from PATH
    Returns:
        tuple: (bool, str) - (is_installed, installation_path)
    """
    # First check if ffmpeg is in PATH
    ffmpeg_path = shutil.which('ffmpeg')
    if ffmpeg_path:
        return True, ffmpeg_path

    # On macOS, check Homebrew default location
    if platform.system() == "Darwin":
        brew_ffmpeg = Path("/opt/homebrew/bin/ffmpeg")
        if brew_ffmpeg.exists():
            return True, str(brew_ffmpeg)
    
    return False, None

def get_ffmpeg_version(ffmpeg_path):
    """
    Get the version of ffmpeg installation
    Returns:
        str: Version string or None if failed
    """
    try:
        result = subprocess.run([ffmpeg_path, "-version"], 
                              capture_output=True, 
                              text=True)
        if result.returncode == 0:
            # Extract first line which contains version
            return result.stdout.split('\n')[0]
        return None
    except Exception:
        return None

def get_installation_instructions():
    """
    Get platform-specific ffmpeg installation instructions
    """
    system = platform.system()
    if system == "Darwin":
        return ("To install FFmpeg on macOS:\n\n"
                "1. Install Homebrew if not already installed:\n"
                "   /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"\n\n"
                "2. Install FFmpeg using Homebrew:\n"
                "   brew install ffmpeg\n\n"
                "After installation, click 'Check Again'")
    elif system == "Windows":
        return ("To install FFmpeg on Windows:\n\n"
                "1. Download the latest FFmpeg build from:\n"
                "   https://github.com/BtbN/FFmpeg-Builds/releases\n\n"
                "2. Extract the zip file\n\n"
                "3. Add the bin folder to your system PATH:\n"
                "   - Right-click on 'This PC' or 'My Computer'\n"
                "   - Click 'Properties'\n"
                "   - Click 'Advanced system settings'\n"
                "   - Click 'Environment Variables'\n"
                "   - Under 'System variables', find and select 'Path'\n"
                "   - Click 'Edit'\n"
                "   - Click 'New'\n"
                "   - Add the path to the bin folder\n"
                "   - Click 'OK' on all windows\n\n"
                "After installation, click 'Check Again'")
    else:  # Linux
        return ("To install FFmpeg on Linux:\n\n"
                "Ubuntu/Debian:\n"
                "sudo apt update && sudo apt install ffmpeg\n\n"
                "Fedora:\n"
                "sudo dnf install ffmpeg\n\n"
                "Arch Linux:\n"
                "sudo pacman -S ffmpeg\n\n"
                "After installation, click 'Check Again'")

def get_ffmpeg_paths():
    """
    Get the paths to ffmpeg and ffprobe binaries. This function handles both
    development and bundled environments, and sets up pydub configuration.
    Returns:
        dict: Dictionary containing ffmpeg and ffprobe paths
    """
    logger.info(f"Current working directory: {os.getcwd()}")
    logger.info(f"sys.executable: {sys.executable}")
    if hasattr(sys, '_MEIPASS'):
        logger.info(f"sys._MEIPASS: {sys._MEIPASS}")
    logger.info(f"Current PATH: {os.environ.get('PATH', '')}")

    # First try to use system ffmpeg
    is_installed, ffmpeg_path = check_ffmpeg_installation()
    if is_installed:
        ffprobe_path = str(os.path.join(os.path.dirname(ffmpeg_path), 'ffprobe'))
        logger.info(f"Using system ffmpeg: {ffmpeg_path}")
        logger.info(f"Using system ffprobe: {ffprobe_path}")
        
        # Add homebrew bin to PATH if not already there
        brew_bin = '/opt/homebrew/bin'
        if brew_bin not in os.environ.get('PATH', ''):
            new_path = f"{brew_bin}:{os.environ.get('PATH', '')}"
            os.environ['PATH'] = new_path
            logger.info(f"Updated PATH: {new_path}")
        
        return {
            'ffmpeg.binaries': ffmpeg_path,
            'ffprobe.binaries': ffprobe_path
        }

    # If system ffmpeg not found, try bundled binaries
    if getattr(sys, 'frozen', False):
        # Running in a bundle
        if sys.platform == 'darwin':  # macOS
            # Get the app bundle Resources directory
            if hasattr(sys, '_MEIPASS'):
                resources_dir = sys._MEIPASS
            else:
                # Get the path to the app bundle
                app_bundle = os.path.abspath(os.path.join(os.path.dirname(sys.executable), '..'))
                resources_dir = os.path.join(app_bundle, 'Resources')
            
            logger.info(f"Resources directory: {resources_dir}")
            
            # Look for binaries in temp_binaries directory
            temp_binaries_dir = os.path.join(resources_dir, 'temp_binaries')
            ffmpeg_path = os.path.join(temp_binaries_dir, 'ffmpeg')
            ffprobe_path = os.path.join(temp_binaries_dir, 'ffprobe')
            
            logger.info(f"Looking for ffmpeg at: {ffmpeg_path}")
            logger.info(f"Looking for ffprobe at: {ffprobe_path}")
            
            if os.path.exists(ffmpeg_path) and os.path.exists(ffprobe_path):
                # Make the binaries executable
                try:
                    os.chmod(ffmpeg_path, 0o755)
                    os.chmod(ffprobe_path, 0o755)
                    logger.info(f"Found and made executable ffmpeg at: {ffmpeg_path}")
                    logger.info(f"Found and made executable ffprobe at: {ffprobe_path}")
                    
                    # Add temp_binaries directory to PATH
                    if temp_binaries_dir not in os.environ.get('PATH', ''):
                        new_path = f"{temp_binaries_dir}:{os.environ.get('PATH', '')}"
                        os.environ['PATH'] = new_path
                        logger.info(f"Updated PATH: {new_path}")
                    
                    return {
                        'ffmpeg.binaries': ffmpeg_path,
                        'ffprobe.binaries': ffprobe_path
                    }
                except Exception as e:
                    logger.error(f"Error making binaries executable: {str(e)}")
            else:
                if not os.path.exists(ffmpeg_path):
                    logger.warning(f"ffmpeg not found at {ffmpeg_path}")
                if not os.path.exists(ffprobe_path):
                    logger.warning(f"ffprobe not found at {ffprobe_path}")
    
    # If no ffmpeg found, try system PATH
    try:
        import shutil
        system_ffmpeg = shutil.which('ffmpeg')
        system_ffprobe = shutil.which('ffprobe')
        if system_ffmpeg and system_ffprobe:
            logger.info(f"Using system binaries from PATH: {system_ffmpeg}, {system_ffprobe}")
            return {
                'ffmpeg.binaries': system_ffmpeg,
                'ffprobe.binaries': system_ffprobe
            }
    except Exception as e:
        logger.error(f"Error finding system binaries: {str(e)}")
    
    # If still no ffmpeg found, return default paths and let first run wizard handle installation
    logger.warning("No ffmpeg installation found. First run wizard will guide installation.")
    return {
        'ffmpeg.binaries': 'ffmpeg',
        'ffprobe.binaries': 'ffprobe'
    }

def configure_pydub():
    """
    Configure pydub to use the correct ffmpeg paths. This should be called
    at application startup before any audio processing is done.
    """
    try:
        ffmpeg_config = get_ffmpeg_paths()
        AudioSegment.converter = ffmpeg_config['ffmpeg.binaries']
        AudioSegment.ffmpeg = ffmpeg_config['ffmpeg.binaries']
        AudioSegment.ffprobe = ffmpeg_config['ffprobe.binaries']
        logger.info(f"Configured pydub with ffmpeg paths: {ffmpeg_config}")
        
        # Verify pydub configuration
        logger.info(f"Verifying pydub configuration:")
        logger.info(f"AudioSegment.converter: {AudioSegment.converter}")
        logger.info(f"AudioSegment.ffmpeg: {AudioSegment.ffmpeg}")
        logger.info(f"AudioSegment.ffprobe: {AudioSegment.ffprobe}")
        
        return True
    except Exception as e:
        logger.error(f"Error configuring pydub: {str(e)}")
        return False

def convert_audio_to_mp3(input_path, output_path, sample_rate=44100):
    """
    Convert any audio file to MP3 format with specified sample rate
    """
    try:
        # Ensure ffmpeg is configured
        configure_pydub()
        
        # Load the audio file
        audio = AudioSegment.from_file(input_path)
        
        # Set the sample rate if different
        if audio.frame_rate != sample_rate:
            audio = audio.set_frame_rate(sample_rate)
        
        # Export as MP3
        audio.export(output_path, format="mp3", parameters=["-q:a", "0"])  # High quality MP3
        
        logger.info(f"Successfully converted {input_path} to MP3: {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error converting audio to MP3: {str(e)}")
        return False

def read_audio_file(file_path, sample_rate=44100):
    """
    Read an audio file and return its samples as a numpy array, along with sample rate and duration
    Returns:
        tuple: (numpy.ndarray, int, float) - (samples, sample_rate, duration)
    """
    try:
        # Ensure ffmpeg is configured
        configure_pydub()
        
        # Load the audio file
        audio = AudioSegment.from_file(file_path)
        
        # Convert to the desired sample rate if needed
        if audio.frame_rate != sample_rate:
            audio = audio.set_frame_rate(sample_rate)
        
        # Get samples as numpy array
        samples = np.array(audio.get_array_of_samples(), dtype=np.float32)
        
        # Convert to float32 in range [-1, 1]
        samples = samples / 32768.0
        
        # Reshape to stereo if mono
        if audio.channels == 1:
            samples = np.column_stack((samples, samples))
        elif audio.channels > 2:
            # If more than 2 channels, keep only first two
            samples = samples.reshape((-1, audio.channels))[:, :2]
        else:
            samples = samples.reshape((-1, 2))
        
        duration = len(audio) / 1000.0  # Duration in seconds
        
        return samples, sample_rate, duration
        
    except Exception as e:
        logger.error(f"Error reading audio file: {str(e)}")
        return np.zeros((0, 2), dtype=np.float32), sample_rate, 0.0
