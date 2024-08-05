import os
import re
import platform
import subprocess
import mutagen

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
        audio = mutagen.File(file_path, easy=True)
        if audio and 'comment' in audio:
            return audio['comment'][0]
        elif audio:
            # If 'comment' is not found, try to read the COMM frame directly
            id3 = mutagen.id3.ID3(file_path)
            comm_frame = id3.getall('COMM')
            if comm_frame:
                return comm_frame[0].text
    except Exception as e:
        print(f"Error reading audio prompt: {str(e)}")
    return None