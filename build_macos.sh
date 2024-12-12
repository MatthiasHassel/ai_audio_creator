#!/bin/bash

# Exit on error
set -e

echo "🚀 Building AI Audio Creator for macOS..."

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

# Clean up any existing virtual environment
echo "🧹 Cleaning up old environment..."
rm -rf venv
rm -rf build dist
rm -f "AI Audio Creator.dmg"

# Create and activate virtual environment
echo "🔧 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip and install wheel
echo "⬆️  Upgrading pip and installing wheel..."
pip install --upgrade pip wheel

# Install Python dependencies
echo "📚 Installing Python dependencies..."
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

# Build the application
echo "🏗️  Building application..."
python -m PyInstaller ai_audio_creator.spec

# Verify the build
if [ ! -d "dist/AI Audio Creator.app" ]; then
    echo "❌ Failed to build the application"
    exit 1
fi

# Test the built application
echo "🧪 Testing built application..."
if ! "dist/AI Audio Creator.app/Contents/MacOS/AI Audio Creator" --version &> /dev/null; then
    echo "⚠️  Warning: Built application may have issues. Proceeding with DMG creation anyway..."
fi

# Create temporary directory for DMG contents
echo "📦 Preparing DMG contents..."
DMG_DIR=$(mktemp -d)
cp -r "dist/AI Audio Creator.app" "$DMG_DIR/"

# Create a DMG installer with custom icon
echo "📦 Creating DMG installer..."
create-dmg \
  --volname "AI Audio Creator" \
  --window-pos 200 120 \
  --window-size 800 400 \
  --icon-size 100 \
  --icon "AI Audio Creator.app" 200 190 \
  --hide-extension "AI Audio Creator.app" \
  --app-drop-link 600 185 \
  "AI Audio Creator.dmg" \
  "$DMG_DIR" \
  || { echo "❌ Failed to create DMG"; exit 1; }

# Clean up temporary directory
rm -rf "$DMG_DIR"

# Deactivate virtual environment
deactivate

echo "✅ Build completed successfully!"
echo "📝 Build artifacts:"
echo "   • Application: dist/AI Audio Creator.app"
echo "   • Installer: AI Audio Creator.dmg"
echo ""
echo "🎯 Next steps:"
echo "1. Test the application by running:"
echo "   open 'dist/AI Audio Creator.app'"
echo ""
echo "2. If the application works correctly, distribute the DMG:"
echo "   • Open 'AI Audio Creator.dmg'"
echo "   • Drag 'AI Audio Creator.app' to your Applications folder"
echo ""
echo "If you encounter any issues:"
echo "• Check the application logs in ~/Library/Logs/AI Audio Creator/"
echo "• Run the app from terminal to see error output:"
echo "  /Applications/AI\\ Audio\\ Creator.app/Contents/MacOS/AI\\ Audio\\ Creator"
