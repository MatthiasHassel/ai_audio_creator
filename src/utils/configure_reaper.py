import reapy
import os
import sys
from pathlib import Path
import site

def get_reapy_scripts_path():
    """Get the path to the reapy scripts directory"""
    try:
        # First try to get it from the reapy package
        import reapy
        reapy_path = Path(reapy.__file__).parent
        scripts_path = reapy_path / "reascripts"
        if scripts_path.exists():
            return scripts_path
        
        # If not found, try site-packages
        for site_dir in site.getsitepackages():
            scripts_path = Path(site_dir) / "reapy" / "reascripts"
            if scripts_path.exists():
                return scripts_path
        
        # If still not found and running in a bundle
        if getattr(sys, 'frozen', False):
            base_path = Path(sys._MEIPASS) if hasattr(sys, '_MEIPASS') else Path(sys.executable).parent
            scripts_path = base_path / "reapy" / "reascripts"
            if scripts_path.exists():
                return scripts_path
            
            # Try one level up in the app bundle
            scripts_path = base_path.parent / "reapy" / "reascripts"
            if scripts_path.exists():
                return scripts_path
            
            # Try Resources directory
            resources_path = base_path.parent / "Resources"
            scripts_path = resources_path / "reapy" / "reascripts"
            if scripts_path.exists():
                return scripts_path
        
        raise FileNotFoundError("Could not find reapy scripts directory")
        
    except Exception as e:
        raise FileNotFoundError(f"Error locating reapy scripts: {str(e)}")

def configure_reaper():
    """
    Configure Reaper for use with AI Audio Creator.
    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        # First try to connect to verify Reaper is running and ReaScript is enabled
        try:
            reapy.connect()
        except:
            return False, ("ReaScript API is not enabled. Please:\n"
                         "1. Open REAPER\n"
                         "2. Go to Preferences -> Plug-ins -> ReaScript\n"
                         "3. Enable 'Allow Python to access REAPER via ReaScript'")
        
        # Configure Reaper
        try:
            scripts_path = get_reapy_scripts_path()
            print(f"Found reapy scripts at: {scripts_path}")  # Debug print
            reapy.config.configure_reaper()
        except Exception as e:
            if "activate_reapy_server.py" in str(e):
                # Handle the case where the script can't be found
                try:
                    scripts_path = get_reapy_scripts_path()
                    return False, (f"Found reapy scripts at {scripts_path} but failed to configure:\n{str(e)}\n"
                                 "This might be due to permission issues or incorrect installation.")
                except FileNotFoundError as fe:
                    return False, str(fe)
            else:
                return False, f"Error configuring REAPER: {str(e)}"
        
        # Connect again to verify configuration
        reapy.connect()
        
        # Show success message in Reaper's console
        reapy.show_console_message("ReaScript configuration successful!\nAI Audio Creator can now connect to Reaper.\n")
        
        return True, "REAPER configuration successful!"
        
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"
