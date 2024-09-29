# AI Audio Creator User Manual

## Table of Contents
1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Main Interface](#main-interface)
4. [Audio Generator](#audio-generator)
   - [Music Generation](#music-generation)
   - [SFX Generation](#sfx-generation)
   - [Speech Generation](#speech-generation)
   - [Audio Playback](#audio-playback)
5. [Script Editor](#script-editor)
6. [Timeline](#timeline)
7. [Project Management](#project-management)
8. [Exporting Audio](#exporting-audio)
9. [Keyboard Shortcuts](#keyboard-shortcuts)
10. [Troubleshooting](#troubleshooting)

## 1. Introduction

Welcome to AI Audio Creator, an innovative application that combines 
AI-powered audio generation with a comprehensive timeline interface for 
creating and editing audio projects. This tool is designed for content 
creators, podcasters, and anyone looking to streamline their audio 
production workflow.

## 2. Getting Started

To launch AI Audio Creator, run the main application file. Upon startup, 
you'll be presented with the main interface, which includes the Audio 
Generator and Script Editor. The Timeline interface can be accessed 
through the "Window" menu or by clicking the "Show Timeline" button in the 
Audio Generator.

## 3. Main Interface

The main interface consists of two primary sections:

- **Audio Generator**: Located on the right side, this is where you can 
generate music, sound effects (SFX), and speech using AI.
- **Script Editor**: On the left side, you can write, edit, and manage 
your audio scripts.

The top menu bar provides access to various functions such as file 
management, editing options, and window controls.

## 4. Audio Generator

The Audio Generator is divided into three tabs: Music, SFX, and Speech. 
Each tab has specific controls for generating different types of audio 
content.

### Music Generation

1. Select the "Music" tab.
2. Enter a descriptive prompt for the music you want to generate.
3. (Optional) Check the "Instrumental" box if you want instrumental music.
4. Click "Generate" to create the music.
5. Use the "Improve Prompt" button to refine your input using AI 
suggestions.

### SFX Generation

1. Select the "SFX" tab.
2. Describe the sound effect you want to create.
3. Set the duration (0 for automatic, or specify between 0.5-22 seconds).
4. Click "Generate" to create the sound effect.
5. Use the "Improve Prompt" button for AI-assisted prompt refinement.

### Speech Generation

1. Select the "Speech" tab.
2. Enter the text you want to convert to speech.
3. Choose a voice from the dropdown menu.
4. (Optional) Use the "Generate Unique Voice" option to create a custom 
voice.
5. Click "Generate" to create the speech audio.

### Audio Playback

After generating audio:
1. The waveform will appear in the visualizer at the bottom.
2. Use the play, pause, and stop buttons to control playback.
3. Click on the waveform to seek to a specific position.
4. Use the "Add to Timeline" button to include the audio in your project 
timeline.

## 5. Script Editor

The Script Editor allows you to write and format scripts for your audio 
projects:

1. Use the toolbar buttons (B, I, U) to format text.
2. The "Speaker" dropdown lets you assign dialogue to specific characters.
3. Use the "SFX" and "Music" buttons to insert sound effect and music 
cues.
4. Save and load scripts using the buttons at the bottom.
5. Use the "Import PDF" button to import scripts from PDF files.
6. The "Analyze Script" function helps break down your script into audio 
elements.
7. "Create Audio" will generate audio files based on your script analysis.

## 6. Timeline

The Timeline interface allows you to arrange and mix your audio clips:

1. Access the Timeline through the "Window" menu or the "Show Timeline" 
button.
2. Drag and drop audio files from the Audio Generator to add them to 
tracks.
3. Use the mouse to move and arrange clips on the timeline.
4. Adjust track volumes using the sliders on the left.
5. Use the solo (S) and mute (M) buttons to control track playback.
6. The playhead (red line) shows the current playback position.
7. Use the zoom controls to adjust the timeline view.

## 7. Project Management

- **New Project**: Create a new project from the "File" menu.
- **Open Project**: Load an existing project from the "File" menu.
- **Save Project**: Save your current project from the "File" menu.
- **Import Audio**: Add external audio files to your project from the 
"Edit" menu.

## 8. Exporting Audio

To export your timeline as a single audio file:

1. Go to the "Edit" menu and select "Export Audio".
2. Choose a location and filename for your exported audio.
3. Wait for the export process to complete (a progress bar will show the 
status).
4. Your exported audio will be saved as an MP3 file.

## 9. Keyboard Shortcuts

- **Ctrl+B**: Bold text in Script Editor
- **Ctrl+I**: Italic text in Script Editor
- **Ctrl+U**: Underline text in Script Editor
- **Ctrl+1-5**: Assign speaker in Script Editor
- **Ctrl+F**: Insert SFX cue in Script Editor
- **Ctrl+M**: Insert Music cue in Script Editor
- **Space**: Play/Pause timeline
- **S**: Solo selected track
- **M**: Mute selected track
- **Up/Down Arrows**: Select track in timeline
- **Ctrl+Z**: Undo in timeline
- **Ctrl+Shift+Z**: Redo in timeline

## 10. Troubleshooting

- If audio generation fails, check your internet connection and API key 
settings.
- For timeline playback issues, ensure all audio files are present in your 
project folder.
- If the application crashes, check the log file in the 'logs' directory 
for error information.

For additional support, please refer to the project's documentation or 
contact the development team.
