# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path
import customtkinter
import os
import site
import tkinter
import shutil

block_cipher = None

# Get customtkinter package path
ctk_path = os.path.dirname(customtkinter.__file__)

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
]

# Add tkinterdnd2 data files if found
datas.extend(tkinterdnd2_paths)

# Define the analysis configuration
a = Analysis(
    ['src/main.py'],
    pathex=[src_path],  # Add src directory to Python path
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
        'darkdetect',  # Required by customtkinter
        'tkinterdnd2',  # Add tkinterdnd2
        # Add all local modules
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
        'utils.ffmpeg_utils',  # Add ffmpeg_utils explicitly
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

# Create the PYZ archive
pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

# Create the executable
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='AI Audio Creator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=True,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# Create the collection
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='AI Audio Creator',
)

# Create the macOS app bundle
app = BUNDLE(
    coll,
    name='AI Audio Creator.app',
    icon='assets/app_icon.icns',
    bundle_identifier='com.matthiashassel.aiaudiocreator',
    version='0.1.0',
    info_plist={
        'CFBundleShortVersionString': '0.1.0',
        'CFBundleVersion': '0.1.0',
        'NSHighResolutionCapable': True,
        'LSMinimumSystemVersion': '10.15',
        'CFBundleName': 'AI Audio Creator',
        'CFBundleDisplayName': 'AI Audio Creator',
        'CFBundleGetInfoString': 'Create AI-powered audio content',
        'NSHumanReadableCopyright': '© 2024 Matthias Hassel',
        'LSEnvironment': {
            'PATH': '/opt/homebrew/bin:@executable_path/../Resources:@executable_path/../MacOS:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin',
            'PYTHONPATH': '@executable_path/../Resources:@executable_path/../Resources/src',
            'TKINTERDND2_LIBRARY': '@executable_path/../Resources/tkinterdnd2',
        },
    }
)
