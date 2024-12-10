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
brew install portaudio create-dmg

# Create and activate virtual environment
echo "🔧 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
echo "📚 Installing Python dependencies..."
pip install -r requirements.txt

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf build dist
rm -f "AI Audio Creator.dmg"

# Build the application
echo "🏗️  Building application..."
python -m PyInstaller ai_audio_creator.spec

# Check if the app was built successfully
if [ ! -d "dist/AI Audio Creator.app" ]; then
    echo "❌ Failed to build the application"
    exit 1
fi

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
  "dist/AI Audio Creator.app" \
  || { echo "❌ Failed to create DMG"; exit 1; }

# Deactivate virtual environment
deactivate

echo "✅ Build completed successfully!"
echo "📝 Build artifacts:"
echo "   • Application: dist/AI Audio Creator.app"
echo "   • Installer: AI Audio Creator.dmg"
echo ""
echo "🎉 To install the application:"
echo "1. Open 'AI Audio Creator.dmg'"
echo "2. Drag 'AI Audio Creator.app' to your Applications folder"
echo "3. Launch the app from Applications"
echo ""
echo "Note: On first launch, you'll need to enter your API keys in the configuration wizard."
