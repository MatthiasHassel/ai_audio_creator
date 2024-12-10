# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path

block_cipher = None

# Gather all necessary data files
datas = [
    ('assets', 'assets'),
    ('config', 'config'),
    ('docs', 'docs'),
]

# Define the analysis configuration
a = Analysis(
    ['src/main.py'],
    pathex=[],
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
    icon=None,  # We'll create an icon later if needed
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
            'PATH': '/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin'
        },
    }
)
