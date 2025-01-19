import os
import sys

def runtime_hook():
    # Get the application's Resources directory
    if getattr(sys, 'frozen', False):
        bundle_dir = os.path.dirname(sys.executable)
        resources_dir = os.path.join(os.path.dirname(bundle_dir), 'Resources')
        
        # Find tcl/tk directories
        tcl_dir = None
        tk_dir = None
        for item in os.listdir(resources_dir):
            if item.startswith('tcl8'):
                tcl_dir = os.path.join(resources_dir, item)
            elif item.startswith('tk8'):
                tk_dir = os.path.join(resources_dir, item)
        
        if tcl_dir and tk_dir:
            # Set environment variables for tcl/tk
            os.environ['TCL_LIBRARY'] = tcl_dir
            os.environ['TK_LIBRARY'] = tk_dir
            # Add tcl/tk directories to PATH
            os.environ['PATH'] = os.pathsep.join([
                os.path.join(resources_dir, 'tcltk', 'bin'),
                os.environ.get('PATH', '')
            ])

runtime_hook()
