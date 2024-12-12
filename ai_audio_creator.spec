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

# Create a temporary directory for ffmpeg binaries
os.makedirs('temp_binaries', exist_ok=True)
ffmpeg_temp = os.path.join('temp_binaries', 'ffmpeg')
ffprobe_temp = os.path.join('temp_binaries', 'ffprobe')

# Copy ffmpeg and ffprobe to temp directory
shutil.copy2(ffmpeg_path, ffmpeg_temp)
shutil.copy2(ffprobe_path, ffprobe_temp)

# Make them executable
os.chmod(ffmpeg_temp, 0o755)
os.chmod(ffprobe_temp, 0o755)

# Gather all necessary data files
datas = [
    ('assets', 'assets'),
    ('config', 'config'),
    ('docs', 'docs'),
    # Add customtkinter theme files
    (os.path.join(ctk_path, 'assets'), 'customtkinter/assets'),
    # Add all Python modules from src directory
    ('src', 'src'),
    # Add ffmpeg binaries to temp_binaries directory in Resources
    ('temp_binaries', 'temp_binaries'),
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
        'soundfile',
        'pygame',
        'pyaudio',
        'sounddevice',
        'numpy',
        'PyPDF2',
        'requests',
        'python-dotenv',
        'librosa',
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
            'PATH': '@executable_path/../Resources:@executable_path/../Resources/temp_binaries:@executable_path/../MacOS:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin',
            'PYTHONPATH': '@executable_path/../Resources:@executable_path/../Resources/src',
            'TKINTERDND2_LIBRARY': '@executable_path/../Resources/tkinterdnd2',
        },
    }
)
