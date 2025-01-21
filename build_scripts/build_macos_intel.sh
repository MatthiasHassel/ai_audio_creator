#!/bin/bash

# Exit on error
set -e

echo "🚀 Building AI Audio Creator for Intel Mac..."

# Check if running on Intel Mac
if [ "$(uname -m)" = "x86_64" ]; then
    echo "✅ Running on Intel Mac"
    BREW_CMD="brew"
else
    echo "❌ This script should be run on an Intel Mac for best compatibility"
    echo "   Current architecture: $(uname -m)"
    exit 1
fi

# Install and setup x86_64 Python 3.11
echo "🔍 Setting up Intel Python 3.11..."

# Clean up existing Python installation if needed
if [ -d "/usr/local/opt/python@3.11" ] || [ -L "/usr/local/opt/python@3.11" ]; then
    echo "🧹 Cleaning up existing Python installation..."
    arch -x86_64 /usr/local/bin/brew unlink python@3.11 || true
    sudo rm -rf /usr/local/opt/python@3.11
    sudo rm -f /usr/local/bin/python3.11
    sudo rm -f /usr/local/bin/python3.11-config
    sudo rm -f /usr/local/bin/pip3.11
fi

# Install Python 3.11
echo "📦 Installing Python 3.11..."
export MACOSX_DEPLOYMENT_TARGET=10.15
$BREW_CMD install python@3.11

# Ensure proper linking and setup
echo "🔗 Setting up Python 3.11..."
arch -x86_64 /usr/local/bin/brew unlink python@3.11 || true
arch -x86_64 /usr/local/bin/brew link --overwrite python@3.11

# Verify installation and get Python path
PYTHON_CMD=$(arch -x86_64 /usr/local/bin/brew --prefix python@3.11)/bin/python3.11
if [ ! -f "$PYTHON_CMD" ]; then
    echo "❌ Failed to locate Python 3.11 executable at $PYTHON_CMD"
    exit 1
fi

# Verify Python version
if ! arch -x86_64 "$PYTHON_CMD" --version &> /dev/null; then
    echo "❌ Failed to run Python 3.11"
    exit 1
fi

echo "✅ Using Python at: $PYTHON_CMD"

# Install system dependencies
echo "📦 Installing system dependencies..."
$BREW_CMD install portaudio create-dmg ffmpeg tcl-tk

# Ensure tcl-tk is properly linked
echo "🔗 Linking tcl-tk..."
$BREW_CMD link --overwrite tcl-tk

# Set tcl-tk environment variables
export PATH="/usr/local/opt/tcl-tk/bin:$PATH"
export LDFLAGS="-L/usr/local/opt/tcl-tk/lib"
export CPPFLAGS="-I/usr/local/opt/tcl-tk/include"
export PKG_CONFIG_PATH="/usr/local/opt/tcl-tk/lib/pkgconfig"
export PYTHON_CONFIGURE_OPTS="--with-tcltk-includes='-I/usr/local/opt/tcl-tk/include' --with-tcltk-libs='-L/usr/local/opt/tcl-tk/lib'"

# Set working directory to project root
cd "$(dirname "$0")/.."

# Clean up any existing virtual environment and build artifacts
echo "🧹 Cleaning up old environment..."
if [ -d "dist_intel" ]; then
    sudo rm -rf dist_intel
fi
if [ -d "build_intel" ]; then
    sudo rm -rf build_intel
fi
if [ -d "venv_intel" ]; then
    sudo rm -rf venv_intel
fi
if [ -f "AI Audio Creator Intel.dmg" ]; then
    sudo rm -f "AI Audio Creator Intel.dmg"
fi

# Create and clean temp directories
mkdir -p temp_binaries

# Clean PyInstaller cache
echo "🧹 Cleaning PyInstaller cache..."
CACHE_DIR="$HOME/Library/Application Support/pyinstaller"
if [ -d "$CACHE_DIR" ]; then
    sudo rm -rf "$CACHE_DIR"
fi

# Create and activate virtual environment
echo "🔧 Creating virtual environment..."
$PYTHON_CMD -m venv venv_intel
source venv_intel/bin/activate

# Ensure virtual environment Python is executable
chmod +x venv_intel/bin/python3.11
export PYTHON_CMD="arch -x86_64 $(pwd)/venv_intel/bin/python3.11"

# Copy tkinter libraries to virtual environment
echo "🔧 Setting up tkinter in virtual environment..."
SYSTEM_TKINTER="/usr/local/opt/python-tk@3.11/lib/python3.11/lib-dynload/_tkinter.cpython-311-darwin.so"
VENV_TKINTER="venv_intel/lib/python3.11/lib-dynload/_tkinter.cpython-311-darwin.so"
if [ -f "$SYSTEM_TKINTER" ]; then
    mkdir -p "$(dirname "$VENV_TKINTER")"
    cp "$SYSTEM_TKINTER" "$VENV_TKINTER"
    chmod +x "$VENV_TKINTER"
fi

# Setup tcl/tk libraries
TCL_PATH="/usr/local/opt/tcl-tk/lib"
if [ -d "$TCL_PATH" ]; then
    # Find tcl/tk versions
    TCL_VERSION=$(ls "$TCL_PATH" | grep -E '^tcl[0-9]+(\.[0-9]+)?$' | head -n 1)
    TK_VERSION=$(ls "$TCL_PATH" | grep -E '^tk[0-9]+(\.[0-9]+)?$' | head -n 1)
    
    if [ -n "$TCL_VERSION" ] && [ -n "$TK_VERSION" ]; then
        echo "  • Found Tcl/Tk versions: $TCL_VERSION, $TK_VERSION"
        
        # Set environment variables
        export TCL_LIBRARY="$TCL_PATH/$TCL_VERSION"
        export TK_LIBRARY="$TCL_PATH/$TK_VERSION"
        
        # Copy libraries to virtual environment
        mkdir -p "venv_intel/lib"
        cp -R "$TCL_PATH/$TCL_VERSION" "venv_intel/lib/" || true
        cp -R "$TCL_PATH/$TK_VERSION" "venv_intel/lib/" || true
        
        # Create symbolic links with version numbers
        ln -sf "$TCL_VERSION" "venv_intel/lib/tcl"
        ln -sf "$TK_VERSION" "venv_intel/lib/tk"
    fi
fi

# Upgrade pip and install required build tools
echo "⬆️  Upgrading pip and installing build tools..."
$PYTHON_CMD -m pip install --upgrade pip wheel setuptools

# Set architecture and deployment target flags
export ARCHFLAGS="-arch x86_64"
export MACOSX_DEPLOYMENT_TARGET=10.15

# Install Python dependencies with specific versions for Intel compatibility
echo "📚 Installing Python dependencies..."

# Install and configure tkinter (required for customtkinter)
echo "  • Setting up tkinter..."
$BREW_CMD uninstall --ignore-dependencies python-tk@3.11 || true
$BREW_CMD install python-tk@3.11

# Link tkinter libraries
echo "  • Linking tkinter..."
if [ -d "/usr/local/opt/python-tk@3.11" ]; then
    TKINTER_PATH="/usr/local/opt/python-tk@3.11"
    PYTHON_FRAMEWORK="/usr/local/opt/python@3.11/Frameworks/Python.framework/Versions/3.11"
    
    # Create lib-dynload directory if it doesn't exist
    sudo mkdir -p "$PYTHON_FRAMEWORK/lib/python3.11/lib-dynload"
    
    # Link _tkinter.cpython-311-darwin.so
    if [ -f "$TKINTER_PATH/lib/python3.11/lib-dynload/_tkinter.cpython-311-darwin.so" ]; then
        sudo ln -sf "$TKINTER_PATH/lib/python3.11/lib-dynload/_tkinter.cpython-311-darwin.so" \
                   "$PYTHON_FRAMEWORK/lib/python3.11/lib-dynload/_tkinter.cpython-311-darwin.so"
    fi
fi

# Install core dependencies with specific versions
echo "  • Installing core dependencies..."
$PYTHON_CMD -m pip install numpy==1.24.3  # Use older NumPy version for better compatibility
$PYTHON_CMD -m pip install customtkinter==5.2.2  # Pin specific version
$PYTHON_CMD -m pip install tkinterdnd2==0.3.0  # Pin specific version

# Install remaining dependencies
echo "  • Installing remaining dependencies..."
$PYTHON_CMD -m pip install -r requirements.txt

# Debug Python environment
echo "🔍 Python environment info:"
$PYTHON_CMD -c "import sys; print(f'Python path: {sys.executable}')"
$PYTHON_CMD -c "import sys; print(f'Architecture: {sys.platform}')"
$PYTHON_CMD -c "import tkinter; print(f'Tkinter version: {tkinter.TkVersion}')" || echo "❌ Tkinter not available"

# Verify critical dependencies
echo "🔍 Verifying critical dependencies..."

# Verify tkinter first
echo "  • Checking tkinter..."
if ! $PYTHON_CMD -c "import tkinter; root = tkinter.Tk(); root.destroy()" 2>/dev/null; then
    echo "❌ Tkinter not working properly. Checking installation..."
    # Check if tkinter is installed
    $PYTHON_CMD -c "import tkinter" 2>/dev/null || {
        echo "   Attempting to fix tkinter..."
        arch -x86_64 /usr/local/bin/brew uninstall --ignore-dependencies python-tk@3.11
        arch -x86_64 /usr/local/bin/brew install python-tk@3.11
    }
    # Verify tkinter again
    if ! $PYTHON_CMD -c "import tkinter; root = tkinter.Tk(); root.destroy()" 2>/dev/null; then
        echo "❌ Failed to setup tkinter. Build cannot continue."
        exit 1
    fi
fi
echo "  ✓ Tkinter working properly"

# Verify customtkinter with detailed error reporting
echo "  • Checking customtkinter..."
if ! $PYTHON_CMD -c "import customtkinter" 2>/dev/null; then
    echo "❌ customtkinter not properly installed. Attempting to reinstall..."
    $PYTHON_CMD -m pip uninstall -y customtkinter
    $PYTHON_CMD -m pip install --no-cache-dir customtkinter==5.2.2
    
    # Try importing again with error output
    if ! $PYTHON_CMD -c "import customtkinter; print('customtkinter version:', customtkinter.__version__)" 2>&1; then
        echo "❌ Failed to install customtkinter. Detailed error above."
        echo "Python path: $($PYTHON_CMD -c 'import sys; print(sys.executable)')"
        echo "Site packages: $($PYTHON_CMD -c 'import site; print("\n".join(site.getsitepackages()))')"
        exit 1
    fi
fi
echo "  ✓ customtkinter working properly"

# Verify tkinterdnd2
echo "  • Checking tkinterdnd2..."
if ! $PYTHON_CMD -c "import tkinterdnd2" &> /dev/null; then
    echo "❌ tkinterdnd2 not properly installed. Attempting to reinstall..."
    $PYTHON_CMD -m pip uninstall -y tkinterdnd2
    $PYTHON_CMD -m pip install tkinterdnd2
    if ! $PYTHON_CMD -c "import tkinterdnd2" &> /dev/null; then
        echo "❌ Failed to install tkinterdnd2. Build cannot continue."
        exit 1
    fi
fi

# Verify ffmpeg
echo "  • Checking ffmpeg..."
if ! command -v ffmpeg &> /dev/null; then
    echo "❌ ffmpeg not found. Please ensure ffmpeg is installed."
    exit 1
fi

# Verify the tkinterdnd2 library location
TKINTERDND2_PATH=$($PYTHON_CMD -c "import tkinterdnd2; print(tkinterdnd2.__file__)")
if [ -z "$TKINTERDND2_PATH" ]; then
    echo "❌ Could not find tkinterdnd2 installation path"
    exit 1
fi
echo "  ✓ tkinterdnd2 found at: $TKINTERDND2_PATH"

# Create Intel-specific spec file
cat > build_scripts/ai_audio_creator_intel.spec << EOL
# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path
import customtkinter
import os
import site
import tkinter
import shutil
import reapy

block_cipher = None

# Get customtkinter package path
ctk_path = os.path.dirname(customtkinter.__file__)

# Get reapy package path and scripts
reapy_path = os.path.dirname(reapy.__file__)
reapy_scripts = os.path.join(reapy_path, 'reascripts')

# Get the absolute path to the src directory
src_path = os.path.abspath('src')

# Find tkinterdnd2 package paths
site_packages = site.getsitepackages()
tkinterdnd2_paths = []
for site_package in site_packages:
    tkinterdnd2_path = os.path.join(site_package, 'tkinterdnd2')
    if os.path.exists(tkinterdnd2_path):
        tkinterdnd2_paths.append((tkinterdnd2_path, 'tkinterdnd2'))

# Find ffmpeg and ffprobe paths
ffmpeg_path = shutil.which('ffmpeg')
ffprobe_path = shutil.which('ffprobe')

if not ffmpeg_path or not ffprobe_path:
    raise Exception("ffmpeg and ffprobe must be installed. Run 'brew install ffmpeg' to install them.")

# Create temp_binaries directory if it doesn't exist
temp_binaries_dir = 'temp_binaries'
os.makedirs(temp_binaries_dir, exist_ok=True)

# Copy ffmpeg and ffprobe to temp_binaries
temp_ffmpeg = os.path.join(temp_binaries_dir, 'ffmpeg')
temp_ffprobe = os.path.join(temp_binaries_dir, 'ffprobe')
shutil.copy2(ffmpeg_path, temp_ffmpeg)
shutil.copy2(ffprobe_path, temp_ffprobe)
os.chmod(temp_ffmpeg, 0o755)
os.chmod(temp_ffprobe, 0o755)

# Gather all necessary data files
datas = [
    ('../assets', 'assets'),
    ('../config', 'config'),
    ('../docs', 'docs'),
    # Add customtkinter theme files
    (os.path.join(ctk_path, 'assets'), 'customtkinter/assets'),
    # Add src directory for imports
    ('../src', 'src'),
    # Add ffmpeg binaries
    ('../temp_binaries', '.'),
    # Add reapy scripts
    (reapy_scripts, 'reapy/reascripts'),
]

# Add tcl/tk libraries
tcl_path = '/usr/local/opt/tcl-tk/lib'
if os.path.exists(tcl_path):
    # Find tcl/tk versions
    tcl_version = next((d for d in os.listdir(tcl_path) if d.startswith('tcl8')), None)
    tk_version = next((d for d in os.listdir(tcl_path) if d.startswith('tk8')), None)
    
    if tcl_version and tk_version:
        datas.extend([
            (os.path.join(tcl_path, tcl_version), tcl_version),
            (os.path.join(tcl_path, tk_version), tk_version),
            # Add tcl/tk scripts
            (os.path.join(tcl_path, '..', 'share', 'tcltk'), 'tcltk'),
        ])

# Add tkinterdnd2 data files if found
datas.extend(tkinterdnd2_paths)

a = Analysis(
    ['../src/main.py'],
    pathex=[src_path],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'yaml',
        'openai',
        'pydub',
        'pyaudio',
        'sounddevice',
        'numpy',
        'PyPDF2',
        'requests',
        'python_dotenv',
        'librosa',
        'librosa.util',
        'librosa.core',
        'librosa.feature',
        'librosa.effects',
        'librosa.filters',
        'librosa.onset',
        'librosa.segment',
        'librosa.sequence',
        'librosa.beat',
        'librosa.decompose',
        'librosa.display',
        'customtkinter',
        'tkinter',
        'PIL',
        'darkdetect',
        'tkinterdnd2',
        'reapy',
        'reapy.core',
        'reapy.reascript_api',
        'reapy.config',
        'models',
        'models.main_model',
        'models.project_model',
        'models.audio_generator_model',
        'models.script_editor_model',
        'models.timeline_model',
        'views',
        'views.main_view',
        'views.audio_generator_view',
        'views.script_editor_view',
        'views.timeline_view',
        'views.preferences_view',
        'views.first_run_wizard',
        'controllers',
        'controllers.main_controller',
        'controllers.audio_generator_controller',
        'controllers.script_editor_controller',
        'controllers.timeline_controller',
        'utils',
        'utils.config_manager',
        'utils.file_utils',
        'utils.audio_buffer_manager',
        'utils.audio_clip',
        'utils.audio_file_selector',
        'utils.audio_visualizer',
        'utils.keyboard_shortcuts',
        'utils.script_analyzer',
        'utils.ffmpeg_utils',
        'services',
        'services.base_service',
        'services.llm_service',
        'services.music_service',
        'services.pdf_analysis_service',
        'services.reaper_service',
        'services.sfx_service',
        'services.speech_service',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[
        # Create runtime hook for tcl/tk
        os.path.join('build_scripts', 'hook-tcl-tk.py'),
    ],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='AI Audio Creator Intel',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=True,
    target_arch='x86_64',
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='AI Audio Creator Intel',
)

app = BUNDLE(
    coll,
    name='AI Audio Creator Intel.app',
    icon='../assets/app_icon.icns',
    bundle_identifier='com.matthiashassel.aiaudiocreator.intel',
    version='0.1.0',
    info_plist={
        'CFBundleShortVersionString': '0.1.0',
        'CFBundleVersion': '0.1.0',
        'NSHighResolutionCapable': True,
        'LSMinimumSystemVersion': '10.15',
        'CFBundleName': 'AI Audio Creator Intel',
        'CFBundleDisplayName': 'AI Audio Creator Intel',
        'CFBundleGetInfoString': 'Create AI-powered audio content',
        'NSHumanReadableCopyright': '© 2024 Matthias Hassel',
        'LSEnvironment': {
            'PATH': '/usr/local/bin:@executable_path/../Resources:@executable_path/../MacOS:/usr/bin:/bin:/usr/sbin:/sbin',
            'PYTHONPATH': '@executable_path/../Resources:@executable_path/../Resources/src',
            'TKINTERDND2_LIBRARY': '@executable_path/../Resources/tkinterdnd2',
        },
    }
)
EOL

# Build the application
echo "🏗️  Building application..."
$PYTHON_CMD -m PyInstaller build_scripts/ai_audio_creator_intel.spec --distpath dist_intel --workpath build_intel --clean

# Clean up temp directories
rm -rf temp_binaries

# Verify the build
if [ ! -d "dist_intel/AI Audio Creator Intel.app" ]; then
    echo "❌ Failed to build the application"
    exit 1
fi

# Test the built application
echo "🧪 Testing built application..."
if ! "dist_intel/AI Audio Creator Intel.app/Contents/MacOS/AI Audio Creator Intel" --version &> /dev/null; then
    echo "⚠️  Warning: Built application may have issues. Proceeding with DMG creation anyway..."
fi

# Create temporary directory for DMG contents
echo "📦 Preparing DMG contents..."
DMG_DIR=$(mktemp -d)
sudo cp -r "dist_intel/AI Audio Creator Intel.app" "$DMG_DIR/"
sudo chown -R $(whoami) "$DMG_DIR"

# Create a DMG installer with custom icon
echo "📦 Creating DMG installer..."
create-dmg \
  --volname "AI Audio Creator Intel" \
  --window-pos 200 120 \
  --window-size 800 400 \
  --icon-size 100 \
  --icon "AI Audio Creator Intel.app" 200 190 \
  --hide-extension "AI Audio Creator Intel.app" \
  --app-drop-link 600 185 \
  "AI Audio Creator Intel.dmg" \
  "$DMG_DIR" \
  || { echo "❌ Failed to create DMG"; exit 1; }

# Clean up temporary directory
sudo rm -rf "$DMG_DIR"

# Deactivate virtual environment
deactivate

echo "✅ Build completed successfully!"
echo "📝 Build artifacts:"
echo "   • Application: dist_intel/AI Audio Creator Intel.app"
echo "   • Installer: AI Audio Creator Intel.dmg"
echo ""
echo "🎯 Next steps:"
echo "1. Test the application by running:"
echo "   open 'dist_intel/AI Audio Creator Intel.app'"
echo ""
echo "2. If the application works correctly, distribute the DMG:"
echo "   • Open 'AI Audio Creator Intel.dmg'"
echo "   • Drag 'AI Audio Creator Intel.app' to your Applications folder"
echo ""
echo "If you encounter any issues:"
echo "• Check the application logs in ~/Library/Logs/AI Audio Creator/"
echo "• Run the app from terminal to see error output:"
echo "  /Applications/AI\\ Audio\\ Creator\\ Intel.app/Contents/MacOS/AI\\ Audio\\ Creator\\ Intel"
