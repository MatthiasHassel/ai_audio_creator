import os
import re
import platform
import subprocess
from mutagen.mp3 import MP3
from mutagen.id3 import ID3

def sanitize_filename(filename):
    """
    Remove invalid characters from a filename.
    """
    # Remove invalid characters
    sanitized = re.sub(r'[\\/*?:"<>|]', "", filename)
    # Replace spaces with underscores
    sanitized = sanitized.replace(' ', '_')
    # Truncate to a reasonable length
    return sanitized[:255]  # 255 is a common maximum filename length

def ensure_dir_exists(directory):
    """
    Ensure that a directory exists, creating it if necessary.
    """
    os.makedirs(directory, exist_ok=True)

def open_file(file_path):
    """
    Open a file with the default application based on the operating system.
    """
    try:
        if platform.system() == "Darwin":  # macOS
            subprocess.run(["open", file_path], check=True)
        elif platform.system() == "Windows":
            os.startfile(file_path)
        else:  # Linux and other Unix-like
            subprocess.run(["xdg-open", file_path], check=True)
    except Exception as e:
        raise Exception(f"Error opening file: {e}")
    
def read_audio_prompt(file_path):
    try:
        audio = MP3(file_path, ID3=ID3)
        if audio.tags:
            comments = audio.tags.getall('COMM')
            for comment in comments:
                if comment.desc == 'Prompt':
                    # Return the first element if it's a list, otherwise return the whole text
                    return comment.text[0] if isinstance(comment.text, list) else comment.text
    except Exception as e:
        print(f"Error reading audio prompt: {str(e)}")
    return None