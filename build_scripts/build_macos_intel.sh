#!/bin/bash

# Exit on error
set -e

echo "🚀 Building AI Audio Creator for Intel Mac..."

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3 and try again."
    exit 1
fi

# Check pip3
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed. Please install pip3 and try again."
    exit 1
fi

# Check Homebrew
if ! command -v brew &> /dev/null; then
    echo "❌ Homebrew is not installed. Please install Homebrew first."
    echo "   Run this command to install Homebrew:"
    echo "   /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
    exit 1
fi

# Install system dependencies
echo "📦 Installing system dependencies..."
brew install portaudio create-dmg ffmpeg

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
python3 -m venv venv_intel
source venv_intel/bin/activate

# Upgrade pip and install wheel
echo "⬆️  Upgrading pip and installing wheel..."
pip install --upgrade pip wheel

# Set architecture flags for Intel
export ARCHFLAGS="-arch x86_64"

# Install Python dependencies with specific versions for Intel compatibility
echo "📚 Installing Python dependencies..."
pip install numpy==1.24.3  # Use older NumPy version for better compatibility
pip install -r requirements.txt

# Verify critical dependencies
echo "🔍 Verifying critical dependencies..."

# Verify customtkinter
echo "  • Checking customtkinter..."
if ! python3 -c "import customtkinter" &> /dev/null; then
    echo "❌ customtkinter not properly installed. Attempting to reinstall..."
    pip uninstall -y customtkinter
    pip install customtkinter
    if ! python3 -c "import customtkinter" &> /dev/null; then
        echo "❌ Failed to install customtkinter. Build cannot continue."
        exit 1
    fi
fi

# Verify tkinterdnd2
echo "  • Checking tkinterdnd2..."
if ! python3 -c "import tkinterdnd2" &> /dev/null; then
    echo "❌ tkinterdnd2 not properly installed. Attempting to reinstall..."
    pip uninstall -y tkinterdnd2
    pip install tkinterdnd2
    if ! python3 -c "import tkinterdnd2" &> /dev/null; then
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
TKINTERDND2_PATH=$(python3 -c "import tkinterdnd2; print(tkinterdnd2.__file__)")
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
    ('assets', 'assets'),
    ('config', 'config'),
    ('docs', 'docs'),
    # Add customtkinter theme files
    (os.path.join(ctk_path, 'assets'), 'customtkinter/assets'),
    # Add src directory for imports
    ('src', 'src'),
    # Add ffmpeg binaries
    (temp_binaries_dir, '.'),
    # Add reapy scripts
    (reapy_scripts, 'reapy/reascripts'),
]

# Add tkinterdnd2 data files if found
datas.extend(tkinterdnd2_paths)

a = Analysis(
    ['src/main.py'],
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
    runtime_hooks=[],
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
    icon='assets/app_icon.icns',
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
python -m PyInstaller build_scripts/ai_audio_creator_intel.spec --distpath dist_intel --workpath build_intel --clean

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
