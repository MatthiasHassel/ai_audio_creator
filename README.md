# AI Audio Creator

AI Audio Creator is a Python application that combines AI-generated audio content with a timeline interface for creating and editing audio projects. This tool is aimed for content creators, podcasters, and anyone looking to streamline their audio production workflow.

## Table of Contents
1. [Features](#features)
2. [Installation](#installation)
3. [Usage Guide](#usage-guide)
   - [Audio Generator](#audio-generator)
   - [Script Editor](#script-editor)
   - [Timeline](#timeline)
4. [Project Management](#project-management)
5. [Limitations and Future Improvements](#limitations-and-future-improvements)
6. [Attributions](#attributions)

## Features

- AI-powered audio generation for music, sound effects (SFX), and speech
- Script editor for writing and managing audio scripts
- Timeline interface for arranging and mixing audio clips
- Project management system for organizing your work
- Integration with various AI services (ElevenLabs, OpenAI, etc.)
- Waveform visualization and audio playback

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/ai-audio-creator.git
   cd ai-audio-creator
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```
4. Install llama3 via ollama: https://ollama.com/

5. Set up API keys:
   - Adjust the .env_example file:
   Add your ElevenLabs + ChatGPT API Keys:
   ```
   ELEVENLABS_API_KEY=your_elevenlabs_api_key
   OPENAI_API_KEY=your_openai_api_key
   ```

6. Add your Suno-Cookie and Session ID.
   Instructions for this: https://github.com/gcui-art/suno-api/blob/main/public/get-cookie-demo.gif

7. Rename the .env_example file to just .env and place a copy of it in the suno_api directory.
   (Temporary workaround. Should not be necessary in future versions)

   Install Suno API:
   ```
   cd /<your_project_directory_here>/suno_api
   npm install
   ```

   To check if the Suno API works, in suno_api run:
   ```
   npm run dev
   ```
   Visit http://localhost:3000/api/get_limit
   If the following result is returned:
   
   {
     "credits_left": 50,
     "period": "day",
     "monthly_limit": 50,
     "monthly_usage": 50
   }
   
   ...it means the program is running normally.


9. Configure the application:
   - Review and modify `config/config.yaml` as needed

10. Run the application:
   ```
   python src/main.py
   ```

## Usage Guide

### Audio Generator

The Audio Generator allows you to create AI-generated audio content:

1. Select the desired tab (Music, SFX, or Speech)
2. Enter a text prompt describing the audio you want to generate
3. Use the "Generate" button to create the audio
4. Preview the generated audio using the built-in player
5. Optionally, use the "Input to Llama3" button for AI-assisted prompt refinement (Music and SFX only)

### Script Editor

The Script Editor helps you write and manage scripts for your audio projects:

1. Use the text area to write or edit your script
2. Format text using the toolbar buttons (Bold, Italic, Underline)
3. Use speaker tags to denote different characters (e.g., `**Speaker 1:** "Dialogue here"`)
4. Add sound effects and music cues using tags (e.g., `[SFX: description]`, `[MUSIC: description]`)
5. Save and load scripts using the buttons at the bottom
6. Import PDF scripts and analyze them for automatic formatting

### Timeline

The Timeline interface allows you to arrange and mix your audio clips:

1. Open the Timeline window using the "Show Timeline" button
2. Drag and drop audio files from the Audio Generator to add them to the timeline
3. Arrange clips by dragging them within tracks
4. Add new tracks using the "Add Track" button
5. Use the playhead to preview your project
6. Adjust volume levels and apply solo/mute to individual tracks
7. Zoom in/out using the slider controls for precise editing

## Project Management

AI Audio Creator uses a project-based system to organize your work:

1. Create a new project using File > New Project
2. Open existing projects with File > Open Project
3. Save your progress frequently with File > Save Project
4. All project files (scripts, generated audio, timeline data) are stored in the project folder

## Limitations and Future Improvements

While AI Audio Creator offers a robust set of features, there are some limitations and areas for future improvement:

- Currently limited to specific AI services (ElevenLabs, OpenAI)
- No built-in audio effects or mixing capabilities
- Limited undo/redo functionality


Future improvements could include:

- Support for additional AI audio generation services
- Support for running generative AI models locally + replacing ChatGPT fully with Llama
- Advanced audio editing and effects processing
- Improved project version control and backup
- Export options for various audio formats and platforms

Contributions and suggestions for improving AI Audio Creator are very welcome!

## Attributions
Suno-API provided by: https://github.com/gcui-art/suno-api/tree/main

