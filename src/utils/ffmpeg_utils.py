import subprocess
import shutil
from pathlib import Path
import platform

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
