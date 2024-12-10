# Building AI Audio Creator for macOS

This guide explains how to build the AI Audio Creator application for macOS and create a distributable DMG installer.

## System Requirements

### For Building
- macOS 10.15 (Catalina) or higher
- Python 3.8 or higher
- Homebrew (for system dependencies)
- Xcode Command Line Tools
- At least 2GB of free disk space for building

### For Running
- macOS 10.15 or higher
- 4GB RAM minimum (8GB recommended)
- 500MB free disk space
- Internet connection for API access
- Required API keys:
  - ElevenLabs API key (for text-to-speech)
  - OpenRouter API key (for AI text generation)
- Optional API keys:
  - OpenAI API key (alternative for text generation)
  - Suno Cookie (for music generation)

## Building the Application

1. **Install Prerequisites**
   ```bash
   # Install Homebrew if not already installed
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   
   # Install Xcode Command Line Tools
   xcode-select --install
   ```

2. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd ai_audio_creator
   ```

3. **Run the Build Script**
   ```bash
   # Make the build script executable
   chmod +x build_macos.sh
   
   # Run the build script
   ./build_macos.sh
   ```

   The build script will:
   - Create a virtual environment
   - Install all required dependencies
   - Build the application using PyInstaller
   - Create a DMG installer

4. **Build Artifacts**
   After successful build, you'll find:
   - The application bundle at `dist/AI Audio Creator.app`
   - The DMG installer as `AI Audio Creator.dmg`

## Distribution

The generated `AI Audio Creator.dmg` file is ready for distribution. Users can:

1. Double-click the DMG file to mount it
2. Drag the AI Audio Creator app to their Applications folder
3. Launch the app from Applications

## First Run Setup

When users first launch the application, they'll go through a configuration wizard:

1. Required API Keys (must be provided):
   - ElevenLabs API Key (get from https://elevenlabs.io)
   - OpenRouter API Key (get from https://openrouter.ai)

2. Optional API Keys (can be skipped):
   - OpenAI API Key (alternative for text generation)
   - Suno Cookie (required for music generation)

Note: If optional API keys are skipped, users can add them later through the preferences menu.

The configuration is saved in `~/.ai_audio_creator/config.yaml`

## Troubleshooting

### Build Issues

1. **Python Environment Issues**
   ```bash
   # Verify Python installation
   python3 --version
   
   # Verify pip installation
   pip3 --version
   ```

2. **Missing Dependencies**
   ```bash
   # Install system dependencies manually
   brew install portaudio create-dmg
   ```

3. **Permission Issues**
   ```bash
   # Fix build script permissions
   chmod +x build_macos.sh
   ```

### Runtime Issues

1. **Configuration Issues**
   - Check if config file exists: `~/.ai_audio_creator/config.yaml`
   - Verify API keys are correctly entered
   - Delete config file to trigger reconfiguration: `rm ~/.ai_audio_creator/config.yaml`

2. **Audio Issues**
   - Ensure PortAudio is installed: `brew install portaudio`
   - Check system audio permissions

3. **Logging**
   - Check application logs at: `~/Library/Logs/AI Audio Creator/ai_audio_creator.log`

4. **API Key Issues**
   - Verify ElevenLabs API key at https://elevenlabs.io
   - Verify OpenRouter API key at https://openrouter.ai
   - If using optional features:
     - Verify OpenAI API key at https://platform.openai.com
     - Check Suno Cookie format and validity

## Development Notes

- The application uses customtkinter for the main GUI
- PySide6 is used for the first-run configuration wizard
- PyInstaller handles the application bundling
- Configuration is stored in the user's home directory
- Logs are stored in the standard macOS application logs directory

## Support

For support or to report issues:
1. Check the logs at `~/Library/Logs/AI Audio Creator/ai_audio_creator.log`
2. Submit an issue on the project repository
3. Contact the development team

## License

This project is licensed under the MIT License - see the LICENSE file for details.
