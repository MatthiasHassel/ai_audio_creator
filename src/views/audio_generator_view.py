import customtkinter as ctk
import logging
import threading
import time
from tkinter import messagebox
from utils.audio_visualizer import AudioVisualizer
from utils.audio_file_selector import AudioFileSelector
import sounddevice as sd
import numpy as np
from tkinter import filedialog
import os
import threading
import tempfile
import librosa
import io
from pydub import AudioSegment


class AudioGeneratorView(ctk.CTkFrame):
    def __init__(self, master, config, project_model):
        super().__init__(master)
        self.config = config
        self.project_model = project_model
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.controller = None  # Will be set later
        # Initialize voice settings with default values
        self.voice_settings = {
            'stability': ctk.DoubleVar(value=0.5),
            'similarity_boost': ctk.DoubleVar(value=0.75),
            'style': ctk.DoubleVar(value=0.0),
            'use_speaker_boost': ctk.BooleanVar(value=True)
        }
        self.create_widgets()

    def set_controller(self, controller):
        """Set the audio controller for this view."""
        self.controller = controller

    def create_widgets(self):
        # Create fixed top bar
        self.create_top_bar()
        
        # Create scrollable frame for main content
        self.scrollable_frame = ctk.CTkScrollableFrame(self)
        self.scrollable_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.scrollable_frame.grid_columnconfigure(0, weight=1)
        
        # Create main content container inside scrollable frame
        self.main_content = ctk.CTkFrame(self.scrollable_frame)  # Removed transparent background
        self.main_content.grid(row=0, column=0, sticky="nsew")
        self.main_content.grid_columnconfigure(0, weight=1)
        
        # Set fixed heights for components
        self.create_main_content()

    def create_top_bar(self):
        top_bar = ctk.CTkFrame(self)
        top_bar.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 0))
        top_bar.grid_columnconfigure(3, weight=1)

        self.current_module = ctk.StringVar(value="Music")
        for i, module in enumerate(["Music", "SFX", "Speech"]):
            ctk.CTkRadioButton(
                top_bar, 
                text=module, 
                variable=self.current_module, 
                value=module, 
                command=self.update_tab_widgets
            ).grid(row=0, column=i, padx=5)

        self.timeline_button = ctk.CTkButton(top_bar, text="Show Timeline", width=120)
        self.timeline_button.grid(row=0, column=4, padx=5, sticky="e")

    def create_main_content(self):
        # Create input field
        self.create_input_field(self.main_content)
        
        # Create action buttons
        self.create_action_buttons(self.main_content)
        
        # Create tab specific options
        self.create_tab_specific_options(self.main_content)
        # Create output display
        self.create_output_display(self.main_content)
        
        # Create separator
        self.create_separator(self.main_content)
        
        # Create audio file selector
        self.create_audio_file_selector(self.main_content)
        
        # Create audio visualizer with fixed height
        self.create_audio_visualizer(self.main_content)
        
        # Create audio controls
        self.create_audio_controls(self.main_content)
        
        # Create progress and status bar
        self.create_progress_and_status_bar(self.main_content)

    def create_action_buttons(self, parent):
        """Create the action buttons (Generate, Clear, Improve Prompt)"""
        action_frame = ctk.CTkFrame(parent)
        action_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        action_frame.grid_columnconfigure(3, weight=1)

        # Generate button
        self.generate_button = ctk.CTkButton(action_frame, text="Generate")
        self.generate_button.grid(row=0, column=0, padx=(0, 5))

        # Clear button
        self.clear_button = ctk.CTkButton(action_frame, text="Clear")
        self.clear_button.grid(row=0, column=1, padx=5)

        # LLM button (Improve Prompt)
        self.llm_button = ctk.CTkButton(action_frame, text="Improve Prompt")
        self.llm_button.grid(row=0, column=2, padx=5)

    def create_audio_controls(self, parent):
        """Create the audio playback controls"""
        control_frame = ctk.CTkFrame(parent)
        control_frame.grid(row=7, column=0, sticky="ew", pady=(0, 10))

        # Play button
        self.play_button = ctk.CTkButton(control_frame, text="Play", state="disabled", width=60)
        self.play_button.grid(row=0, column=0, padx=(0, 2))

        # Stop button
        self.stop_button = ctk.CTkButton(control_frame, text="Stop", state="disabled", width=60)
        self.stop_button.grid(row=0, column=1, padx=2)

        # Restart button
        self.restart_button = ctk.CTkButton(control_frame, text="Restart", state="disabled", width=60)
        self.restart_button.grid(row=0, column=2, padx=2)

        # Add to Timeline button
        self.add_to_timeline_button = ctk.CTkButton(control_frame, text="Add to Timeline", state="disabled", width=120)
        self.add_to_timeline_button.grid(row=0, column=3, padx=2)

        # Add to Reaper button
        self.add_to_reaper_button = ctk.CTkButton(control_frame, text="Add to Reaper", state="disabled", width=120)
        self.add_to_reaper_button.grid(row=0, column=4, padx=2)

    def create_output_display(self, parent):
        """Create the output display area"""
        output_frame = ctk.CTkFrame(parent)
        output_frame.grid(row=3, column=0, sticky="nsew", pady=(0, 10))
        output_frame.grid_columnconfigure(0, weight=1)
        output_frame.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(output_frame, text="Output:").grid(row=0, column=0, sticky="w")
        self.output_text = ctk.CTkTextbox(output_frame, height=100, state="disabled")
        self.output_text.grid(row=1, column=0, sticky="nsew")

    def create_separator(self, parent):
        """Create a visual separator"""
        separator = ctk.CTkFrame(parent, height=2, fg_color="gray")
        separator.grid(row=4, column=0, sticky="ew", pady=(0, 10))

    def create_audio_file_selector(self, parent):
        """Create the audio file selector"""
        self.audio_file_selector = AudioFileSelector(parent, self.config, self.project_model)
        self.audio_file_selector.grid(row=5, column=0, sticky="ew", pady=(0, 10))

    def create_audio_visualizer(self, parent):
        """Create the audio visualizer"""
        visualizer_frame = ctk.CTkFrame(parent)
        visualizer_frame.grid(row=6, column=0, sticky="nsew", pady=(0, 10))
        visualizer_frame.grid_rowconfigure(0, weight=1)
        visualizer_frame.grid_columnconfigure(0, weight=1)
        
        self.audio_visualizer = AudioVisualizer(visualizer_frame)
        self.audio_visualizer.grid(row=0, column=0, sticky="nsew")
        parent.grid_rowconfigure(6, weight=1)  # Make the visualizer expandable

    def create_progress_and_status_bar(self, parent):
        """Create the progress and status bar"""
        progress_status_frame = ctk.CTkFrame(parent)
        progress_status_frame.grid(row=8, column=0, sticky="ew")
        progress_status_frame.grid_columnconfigure(0, weight=1)

        self.progress_bar = ctk.CTkProgressBar(progress_status_frame)
        self.progress_bar.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        self.progress_bar.set(0)
        self.progress_bar.grid_remove()  # Initially hidden

        self.status_var = ctk.StringVar()
        self.status_var.set(" ")
        self.status_bar = ctk.CTkLabel(progress_status_frame, textvariable=self.status_var, anchor="w")
        self.status_bar.grid(row=1, column=0, sticky="ew")

    def create_tab_specific_options(self, parent):
        """Create the tab-specific options"""
        self.tab_widgets = {
            'Music': self.create_music_widgets(parent),
            'SFX': self.create_sfx_widgets(parent),
            'Speech': self.create_speech_widgets(parent)
        }
        self.current_tab_widget = self.tab_widgets['Music']
        self.current_tab_widget.grid(row=2, column=0, sticky="ew", pady=(0, 10))

    def create_music_widgets(self, parent):
        """Create music-specific widgets"""
        frame = ctk.CTkFrame(parent)
        self.instrumental_var = ctk.BooleanVar(value=False)
        checkbox = ctk.CTkCheckBox(frame, text="Instrumental", variable=self.instrumental_var)
        checkbox.pack()
        return frame

    def create_sfx_widgets(self, parent):
        """Create SFX-specific widgets"""
        frame = ctk.CTkFrame(parent)
        self.duration_var = ctk.StringVar(value="0")
        label = ctk.CTkLabel(frame, text="Duration (0 = automatic, 0.5-22s):")
        entry = ctk.CTkEntry(frame, textvariable=self.duration_var, width=100)
        label.pack(side="left", padx=(0, 5))
        entry.pack(side="left")
        return frame

    def create_speech_widgets(self, parent):
        """Create speech-specific widgets"""
        frame = ctk.CTkFrame(parent)
        frame.grid_columnconfigure(1, weight=1)

        # Standard voice selection
        self.selected_voice = ctk.StringVar()
        label = ctk.CTkLabel(frame, text="Select Voice:")
        self.voice_dropdown = ctk.CTkOptionMenu(frame, variable=self.selected_voice, width=120)
        label.grid(row=0, column=0, padx=(0, 5), pady=5, sticky="w")
        self.voice_dropdown.grid(row=0, column=1, pady=5, sticky="w")

        # Advanced Voice Settings
        self.show_advanced_settings = ctk.BooleanVar(value=False)
        self.advanced_settings_checkbox = ctk.CTkCheckBox(
            frame, 
            text="Advanced Voice Settings",
            variable=self.show_advanced_settings,
            command=self.toggle_advanced_settings
        )
        self.advanced_settings_checkbox.grid(row=1, column=0, columnspan=2, pady=5, sticky="w")

        # Create advanced settings frame
        self.advanced_settings_frame = ctk.CTkFrame(frame)
        self.advanced_settings_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=5)
        self.advanced_settings_frame.grid_columnconfigure(1, weight=1)
        self.advanced_settings_frame.grid_remove()  # Initially hidden

        # Create tooltips for settings
        tooltips = {
            'stability': "Adjusts the emotional range and consistency of the voice.\nLower settings result in more variation and emotion,\nwhile higher settings produce a more stable, monotone voice.",
            'similarity': "Controls how closely the AI matches the original voice.\nHigh settings may replicate artifacts from low-quality audio.",
            'style': "Enhances the speaker's style, but can affect stability.",
            'speaker_boost': "Increases the likeness to the original speaker,\nuseful for weaker voices."
        }

        # Stability slider with percentage label
        stability_frame = ctk.CTkFrame(self.advanced_settings_frame, fg_color="transparent")
        stability_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=2)
        stability_frame.grid_columnconfigure(1, weight=1)
        
        stability_label = ctk.CTkLabel(stability_frame, text="Stability:")
        stability_label.grid(row=0, column=0, sticky="w")
        self.create_tooltip(stability_label, tooltips['stability'])
        
        stability_slider = ctk.CTkSlider(
            stability_frame,
            from_=0,
            to=1,
            number_of_steps=100,
            variable=self.voice_settings['stability'],
            command=lambda value: self.update_percentage_label('stability', value)
        )
        stability_slider.grid(row=0, column=1, padx=5, sticky="ew")
        
        self.stability_percentage = ctk.CTkLabel(stability_frame, text="50%")
        self.stability_percentage.grid(row=0, column=2, padx=(0, 5))

        # Similarity Boost slider with percentage label
        similarity_frame = ctk.CTkFrame(self.advanced_settings_frame, fg_color="transparent")
        similarity_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=2)
        similarity_frame.grid_columnconfigure(1, weight=1)
        
        similarity_label = ctk.CTkLabel(similarity_frame, text="Similarity:")
        similarity_label.grid(row=0, column=0, sticky="w")
        self.create_tooltip(similarity_label, tooltips['similarity'])
        
        similarity_slider = ctk.CTkSlider(
            similarity_frame,
            from_=0,
            to=1,
            number_of_steps=100,
            variable=self.voice_settings['similarity_boost'],
            command=lambda value: self.update_percentage_label('similarity', value)
        )
        similarity_slider.grid(row=0, column=1, padx=5, sticky="ew")
        
        self.similarity_percentage = ctk.CTkLabel(similarity_frame, text="75%")
        self.similarity_percentage.grid(row=0, column=2, padx=(0, 5))

        # Style Exaggeration slider with percentage label
        style_frame = ctk.CTkFrame(self.advanced_settings_frame, fg_color="transparent")
        style_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=5, pady=2)
        style_frame.grid_columnconfigure(1, weight=1)
        
        style_label = ctk.CTkLabel(style_frame, text="Style:")
        style_label.grid(row=0, column=0, sticky="w")
        self.create_tooltip(style_label, tooltips['style'])
        
        style_slider = ctk.CTkSlider(
            style_frame,
            from_=0,
            to=1,
            number_of_steps=100,
            variable=self.voice_settings['style'],
            command=lambda value: self.update_percentage_label('style', value)
        )
        style_slider.grid(row=0, column=1, padx=5, sticky="ew")
        
        self.style_percentage = ctk.CTkLabel(style_frame, text="0%")
        self.style_percentage.grid(row=0, column=2, padx=(0, 5))

        # Speaker Boost checkbox with tooltip
        speaker_boost_frame = ctk.CTkFrame(self.advanced_settings_frame, fg_color="transparent")
        speaker_boost_frame.grid(row=3, column=0, columnspan=2, sticky="w", padx=5, pady=2)
        
        speaker_boost_checkbox = ctk.CTkCheckBox(
            speaker_boost_frame,
            text="Speaker Boost",
            variable=self.voice_settings['use_speaker_boost']
        )
        speaker_boost_checkbox.grid(row=0, column=0, sticky="w")
        self.create_tooltip(speaker_boost_checkbox, tooltips['speaker_boost'])

        # Reset button
        reset_button = ctk.CTkButton(
            self.advanced_settings_frame,
            text="Reset to Defaults",
            command=self.reset_voice_settings
        )
        reset_button.grid(row=4, column=0, columnspan=2, padx=5, pady=5)

        # Checkbox for unique voice generation
        self.use_unique_voice = ctk.BooleanVar(value=False)
        self.unique_voice_checkbox = ctk.CTkCheckBox(frame, text="Generate Unique Voice", 
                                                variable=self.use_unique_voice, 
                                                command=self.toggle_unique_voice_options)
        self.unique_voice_checkbox.grid(row=3, column=0, columnspan=2, pady=5, sticky="w")

        # Create container frame for unique voice options
        self.unique_voice_frame = ctk.CTkFrame(frame)
        self.unique_voice_frame.grid(row=4, column=0, columnspan=2, sticky="ew", pady=5)
        self.unique_voice_frame.grid_columnconfigure(1, weight=1)  # Make second column expandable
        self.unique_voice_frame.grid_remove()  # Initially hidden

        # Create voice description frame
        self.create_voice_description_frame(self.unique_voice_frame)

        # Create voice preview frame
        self.create_voice_preview_frame(frame)

        return frame

    def create_tooltip(self, widget, text):
        """Create a tooltip for a given widget"""
        def show_tooltip(event):
            tooltip = ctk.CTkToplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            
            label = ctk.CTkLabel(
                tooltip,
                text=text,
                justify="left",
                wraplength=300
            )
            label.pack(padx=5, pady=5)
            
            def hide_tooltip():
                tooltip.destroy()
            
            tooltip.bind("<Leave>", lambda e: hide_tooltip())
            widget.bind("<Leave>", lambda e: hide_tooltip())
            
            # Store tooltip reference to prevent garbage collection
            widget.tooltip = tooltip

        widget.bind("<Enter>", show_tooltip)

    def update_percentage_label(self, setting, value):
        """Update the percentage label for a slider"""
        percentage = int(float(value) * 100)
        if setting == 'stability':
            self.stability_percentage.configure(text=f"{percentage}%")
        elif setting == 'similarity':
            self.similarity_percentage.configure(text=f"{percentage}%")
        elif setting == 'style':
            self.style_percentage.configure(text=f"{percentage}%")

    def reset_voice_settings(self):
        """Reset voice settings to default values"""
        self.voice_settings['stability'].set(0.5)
        self.voice_settings['similarity_boost'].set(0.75)
        self.voice_settings['style'].set(0.0)
        self.voice_settings['use_speaker_boost'].set(True)
        
        # Update percentage labels
        self.stability_percentage.configure(text="50%")
        self.similarity_percentage.configure(text="75%")
        self.style_percentage.configure(text="0%")

    def toggle_advanced_settings(self):
        """Toggle visibility of advanced voice settings"""
        if self.show_advanced_settings.get():
            self.advanced_settings_frame.grid()
        else:
            self.advanced_settings_frame.grid_remove()

    def toggle_unique_voice_options(self):
        """Toggle between standard voice selection and unique voice generation"""
        enable = self.use_unique_voice.get()
        
        if enable:
            self.voice_dropdown.configure(state="disabled")
            self.unique_voice_frame.grid()  # Show the unique voice options
            
            # Enable all the controls
            self.voice_description.configure(state="normal")
            self.example_text.configure(state="normal")
            self.preview_button.configure(state="normal")
            
            # Reset placeholder text if needed
            if not self.voice_description.get("1.0", "end-1c").strip():
                self.voice_description.insert("1.0", self.voice_description._placeholder_text)
                self.voice_description.configure(text_color="gray60")
            if not self.example_text.get("1.0", "end-1c").strip():
                self.example_text.insert("1.0", self.example_text._placeholder_text)
                self.example_text.configure(text_color="gray60")
        else:
            self.voice_dropdown.configure(state="normal")
            self.unique_voice_frame.grid_remove()  # Hide the unique voice options
            
            # Clear and disable controls
            self.voice_description.delete("1.0", "end")
            self.example_text.delete("1.0", "end")
            self.voice_description.configure(state="disabled")
            self.example_text.configure(state="disabled")
            self.preview_button.configure(state="disabled")
            
            # Reset character counter
            self.char_counter.configure(text="0/1000", text_color="gray60")
            
            # Hide preview frame if visible
            if self.preview_frame.winfo_viewable():
                self.preview_frame.grid_remove()

    def create_input_field(self, parent):
        input_frame = ctk.CTkFrame(parent)
        input_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        input_frame.grid_columnconfigure(0, weight=1)
        input_frame.grid_rowconfigure(1, weight=1)

        # Create a header frame for label and checkbox
        header_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        header_frame.grid_columnconfigure(1, weight=1)  # Make space between label and checkbox

        # Input label
        self.input_label = ctk.CTkLabel(header_frame, text="Enter your text:")
        self.input_label.grid(row=0, column=0, sticky="w")

        # S2S checkbox (only visible in speech tab)
        self.use_s2s = ctk.BooleanVar(value=False)
        self.s2s_checkbox = ctk.CTkCheckBox(header_frame, text="Use Speech-to-Speech Mode", 
                                        variable=self.use_s2s,
                                        command=self.toggle_s2s_mode)
        self.s2s_checkbox.grid(row=0, column=1, sticky="e")
        self.s2s_checkbox.grid_remove()  # Initially hidden

        # Create container for input methods
        self.input_container = ctk.CTkFrame(input_frame, fg_color="transparent")
        self.input_container.grid(row=1, column=0, sticky="nsew")
        self.input_container.grid_columnconfigure(0, weight=1)
        self.input_container.grid_rowconfigure(0, weight=1)

        # Text input
        self.user_input = ctk.CTkTextbox(self.input_container, height=100)
        self.user_input.grid(row=0, column=0, sticky="nsew")

        # S2S controls (initially hidden)
        self.s2s_controls = ctk.CTkFrame(self.input_container)
        self.create_s2s_controls(self.s2s_controls)
        return input_frame

    def create_s2s_controls(self, parent):
        """Create the S2S control buttons"""
        parent.grid_columnconfigure(2, weight=1)  # Make space for status label

        # Record button
        self.is_recording = False
        self.record_button = ctk.CTkButton(
            parent, 
            text="Start Recording",
            command=self.toggle_recording
        )
        self.record_button.grid(row=0, column=0, padx=5, pady=10)

        # Import button
        self.import_button = ctk.CTkButton(
            parent,
            text="Import Audio File",
            command=self.import_s2s_audio
        )
        self.import_button.grid(row=0, column=1, padx=5, pady=10)

        # Add level meter canvas
        self.level_meter = ctk.CTkCanvas(parent, width=150, height=20, bg='gray20', highlightthickness=0)
        self.level_meter.grid(row=0, column=2, padx=(5, 10))
        self.level_bar = self.level_meter.create_rectangle(0, 0, 0, 20, fill='#00ff00')

        # Status label
        self.s2s_status_label = ctk.CTkLabel(parent, text="")
        self.s2s_status_label.grid(row=0, column=3, padx=(20, 5), sticky="w")

        # Preview frame
        self.s2s_preview_frame = ctk.CTkFrame(parent)
        self.s2s_preview_frame.grid(row=1, column=0, columnspan=4, sticky="nsew", padx=5, pady=5)
        self.s2s_preview_frame.grid_columnconfigure(0, weight=1)
        self.s2s_preview_frame.grid_rowconfigure(0, weight=1)
        
        # Create audio visualizer for the preview
        s2s_visualizer_frame = ctk.CTkFrame(self.s2s_preview_frame)
        s2s_visualizer_frame.grid(row=0, column=0, sticky="nsew", pady=5)
        s2s_visualizer_frame.grid_columnconfigure(0, weight=1)
        s2s_visualizer_frame.grid_rowconfigure(0, weight=1)
        
        self.s2s_visualizer = AudioVisualizer(s2s_visualizer_frame)
        self.s2s_visualizer.grid(row=0, column=0, sticky="nsew")
        self.s2s_visualizer.set_on_click_seek(self.seek_s2s_audio)
        
        # Add play controls for the recorded/imported audio
        self.s2s_preview_controls = ctk.CTkFrame(self.s2s_preview_frame)
        self.s2s_preview_controls.grid(row=1, column=0, sticky="ew", pady=5)
        self.s2s_preview_controls.grid_columnconfigure(3, weight=1)  # Adjusted for restart button
        
        # Play button
        self.s2s_preview_play_button = ctk.CTkButton(
            self.s2s_preview_controls, 
            text="Play", 
            width=60,
            command=self.play_s2s_audio,
            state="disabled"  # Initially disabled
        )
        self.s2s_preview_play_button.grid(row=0, column=0, padx=5)
        
        # Stop button
        self.s2s_preview_stop_button = ctk.CTkButton(
            self.s2s_preview_controls, 
            text="Stop", 
            width=60,
            command=self.stop_s2s_audio,
            state="disabled"  # Initially disabled
        )
        self.s2s_preview_stop_button.grid(row=0, column=1, padx=5)
        
        # Restart button (new)
        self.s2s_preview_restart_button = ctk.CTkButton(
            self.s2s_preview_controls,
            text="Restart",
            width=60,
            command=self.restart_s2s_audio,
            state="disabled"  # Initially disabled
        )
        self.s2s_preview_restart_button.grid(row=0, column=2, padx=5)
        
        # Initially hide preview frame
        self.s2s_preview_frame.grid_remove()

    def update_button_states(self, is_playing):
        """Update main player button states"""
        if is_playing:
            self.play_button.configure(state="disabled")
            self.stop_button.configure(state="normal")
            self.restart_button.configure(state="normal")
        else:
            # Only enable play if we have audio loaded
            play_state = "normal" if self.controller and self.controller.current_audio_file else "disabled"
            self.play_button.configure(state=play_state)
            self.stop_button.configure(state="disabled")
            self.restart_button.configure(state="normal")
            
    def update_s2s_button_states(self, is_playing):
        """Update s2s preview player button states"""
        if is_playing:
            self.s2s_preview_play_button.configure(state="disabled")
            self.s2s_preview_stop_button.configure(state="normal")
            self.s2s_preview_restart_button.configure(state="normal")
        else:
            # Only enable play if we have audio loaded
            play_state = "normal" if hasattr(self, 'current_s2s_audio') else "disabled"
            self.s2s_preview_play_button.configure(state=play_state)
            self.s2s_preview_stop_button.configure(state="disabled")
            self.s2s_preview_restart_button.configure(state=play_state)

    def play_s2s_audio(self):
        """Play the s2s audio and start updating playhead"""
        if self.controller and hasattr(self, 'current_s2s_audio'):
            # Stop main player if it's playing
            if self.controller.s2s_model.is_playing:  # Fixed: Check s2s_model instead of main model
                self.controller.stop_s2s_audio()
            # Load and play s2s audio using s2s_model
            self.controller.s2s_model.load_audio(self.current_s2s_audio)
            self.controller.s2s_model.play()
            self.update_s2s_button_states(True)
            self.start_s2s_playhead_update()

    def stop_s2s_audio(self):
        """Stop the s2s audio playback"""
        if self.controller:
            self.controller.s2s_model.stop()  # Use s2s_model
            self.update_s2s_button_states(False)
            self.stop_s2s_playhead_update()
            self.s2s_visualizer.update_playhead(0)  # Reset playhead position

    def restart_s2s_audio(self):
        """Restart the s2s audio from the beginning"""
        if self.controller and hasattr(self, 'current_s2s_audio'):
            self.controller.s2s_model.restart()  # Use s2s_model
            self.update_s2s_button_states(True)
            self.s2s_visualizer.update_playhead(0)
            if self.controller.s2s_model.is_playing:  # Check s2s_model state
                self.start_s2s_playhead_update()

    def seek_s2s_audio(self, position):
        """Seek to a position in the s2s audio"""
        if self.controller:
            if self.controller.s2s_model.seek(position):  # Use s2s_model
                self.s2s_visualizer.update_playhead(position)
                if self.controller.s2s_model.is_playing:  # Check s2s_model state
                    self.start_s2s_playhead_update()

    def start_s2s_playhead_update(self):
        """Start updating the s2s preview playhead position"""
        self.stop_s2s_playhead_update()  # Ensure no existing update is running
        self.update_s2s_playhead()

    def stop_s2s_playhead_update(self):
        """Stop updating the s2s preview playhead"""
        if hasattr(self, 's2s_update_id') and self.s2s_update_id is not None:
            try:
                self.after_cancel(self.s2s_update_id)
            except ValueError:
                pass  # Ignore if the id is no longer valid
            self.s2s_update_id = None

    def update_s2s_playhead(self):
        """Update the s2s preview playhead position using s2s_model"""
        if self.controller and self.controller.s2s_model.is_playing:
            current_time = self.controller.s2s_model.get_current_position()
            self.s2s_visualizer.update_playhead(current_time)
            self.s2s_update_id = self.after(50, self.update_s2s_playhead)
        else:
            self.stop_s2s_playhead_update()
            self.update_s2s_button_states(False)

    def import_s2s_audio(self):
        """Import audio file for speech-to-speech conversion"""
        try:
            file_types = (
                ('WAV files', '*.wav'),
                ('MP3 files', '*.mp3'),
                ('All files', '*.*')
            )
            
            file_path = filedialog.askopenfilename(
                title="Select Audio File",
                filetypes=file_types
            )
            
            if file_path:
                try:
                    # If it's an MP3 file, convert it to WAV
                    if file_path.lower().endswith('.mp3'):
                        # Load the audio file using librosa
                        y, sr = librosa.load(file_path, sr=44100)
                        
                        # Convert to stereo if mono
                        if len(y.shape) == 1:
                            y = np.column_stack((y, y))
                        
                        # Create a temporary WAV file
                        temp_wav = os.path.join(
                            os.path.dirname(file_path),
                            f"temp_{os.path.splitext(os.path.basename(file_path))[0]}.wav"
                        )
                        
                        # Convert to 16-bit PCM
                        audio_16bit = (y * 32767).astype(np.int16)
                        
                        # Create WAV in memory
                        wav_buffer = io.BytesIO()
                        
                        # Write WAV header
                        wav_buffer.write(b'RIFF')
                        wav_buffer.write((36 + len(audio_16bit.tobytes())).to_bytes(4, 'little'))
                        wav_buffer.write(b'WAVE')
                        wav_buffer.write(b'fmt ')
                        wav_buffer.write((16).to_bytes(4, 'little'))
                        wav_buffer.write((1).to_bytes(2, 'little'))
                        wav_buffer.write((2).to_bytes(2, 'little'))  # 2 channels
                        wav_buffer.write((sr).to_bytes(4, 'little'))
                        wav_buffer.write((sr * 2 * 2).to_bytes(4, 'little'))
                        wav_buffer.write((4).to_bytes(2, 'little'))
                        wav_buffer.write((16).to_bytes(2, 'little'))
                        wav_buffer.write(b'data')
                        wav_buffer.write(len(audio_16bit.tobytes()).to_bytes(4, 'little'))
                        wav_buffer.write(audio_16bit.tobytes())
                        
                        # Save WAV file
                        wav_buffer.seek(0)
                        with open(temp_wav, 'wb') as f:
                            f.write(wav_buffer.getvalue())
                        
                        # Update the file path to use the WAV file
                        file_path = temp_wav
                    
                    self.current_s2s_audio = file_path
                    self.s2s_preview_frame.grid()
                    
                    # Update the visualizer in a thread-safe way
                    def update_visualizer():
                        self.s2s_visualizer.update_waveform(file_path)
                        self.s2s_status_label.configure(text="Audio file loaded")
                        self.update_s2s_button_states(False)  # Initialize button states
                        self.s2s_preview_play_button.configure(state="normal")  # Enable play button
                    
                    self.after(0, update_visualizer)
                
                except Exception as e:
                    self.s2s_status_label.configure(text=f"Error loading audio: {str(e)}")
                    messagebox.showerror("Error", f"Failed to load audio file: {str(e)}")
        
        except Exception as e:
            self.s2s_status_label.configure(text=f"Error showing file dialog: {str(e)}")
            messagebox.showerror("Error", f"Failed to show file dialog: {str(e)}")

    def toggle_recording(self):
        """Toggle audio recording state"""
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()
            
    def start_recording(self):
        """Start audio recording"""
        try:
            self.is_recording = True
            self.record_button.configure(
                text="Stop Recording",
                fg_color="red",
                hover_color="dark red"
            )
            self.s2s_status_label.configure(text="Recording...")
            
            # Reset level meter
            self.level_meter.coords(self.level_bar, 0, 0, 0, 20)
            self.s2s_preview_play_button.configure(state="disabled")
            self.s2s_preview_stop_button.configure(state="disabled")
            self.s2s_preview_restart_button.configure(state="disabled")
            
            # Create temporary file for recording
            self.temp_audio_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            
            # Configure the audio stream with proper settings
            # Using default device, mono recording (1 channel), with 44.1kHz sample rate
            self.stream = sd.InputStream(
                channels=1,  # Changed from 2 to 1 for mono recording
                samplerate=44100,
                dtype=np.float32,
                callback=self.audio_callback,
                blocksize=2048
            )
            self.audio_frames = []
            self.stream.start()
            
        except Exception as e:
            self.s2s_status_label.configure(text=f"Error: {str(e)}")
            self.is_recording = False
            self.record_button.configure(
                text="Start Recording",
                fg_color=["#3B8ED0", "#1F6AA5"],
                hover_color=["#3B8ED0", "#1F6AA5"]
            )

    def stop_recording(self):
        """Stop audio recording"""
        if hasattr(self, 'stream'):
            self.stream.stop()
            self.stream.close()
            self.is_recording = False
            
            # Reset button appearance
            self.record_button.configure(
                text="Start Recording",
                fg_color=["#3B8ED0", "#1F6AA5"],
                hover_color=["#3B8ED0", "#1F6AA5"]
            )
            
            try:
                # Save the recorded audio
                audio_data = np.concatenate(self.audio_frames, axis=0)
                
                # Convert mono to stereo if needed
                if len(audio_data.shape) == 1 or audio_data.shape[1] == 1:
                    # Convert mono to stereo by duplicating the channel
                    audio_data = np.column_stack((audio_data, audio_data))
                
                # Convert to 16-bit PCM
                audio_16bit = (audio_data * 32767).astype(np.int16)
                
                # Create WAV in memory
                wav_buffer = io.BytesIO()
                
                # Write WAV header
                wav_buffer.write(b'RIFF')
                wav_buffer.write((36 + len(audio_16bit.tobytes())).to_bytes(4, 'little'))
                wav_buffer.write(b'WAVE')
                wav_buffer.write(b'fmt ')
                wav_buffer.write((16).to_bytes(4, 'little'))
                wav_buffer.write((1).to_bytes(2, 'little'))
                wav_buffer.write((2).to_bytes(2, 'little'))  # 2 channels
                wav_buffer.write((44100).to_bytes(4, 'little'))  # Sample rate
                wav_buffer.write((44100 * 2 * 2).to_bytes(4, 'little'))
                wav_buffer.write((4).to_bytes(2, 'little'))
                wav_buffer.write((16).to_bytes(2, 'little'))
                wav_buffer.write(b'data')
                wav_buffer.write(len(audio_16bit.tobytes()).to_bytes(4, 'little'))
                wav_buffer.write(audio_16bit.tobytes())
                
                # Save WAV file
                wav_buffer.seek(0)
                with open(self.temp_audio_file.name, 'wb') as f:
                    f.write(wav_buffer.getvalue())
                
                # Update the controller
                if self.controller:
                    self.controller.handle_recorded_audio(self.temp_audio_file.name)
                
                self.s2s_status_label.configure(text="Recording saved")
                
                # Clear level meter
                self.level_meter.coords(self.level_bar, 0, 0, 0, 20)
                
            except Exception as e:
                self.s2s_status_label.configure(text=f"Error saving recording: {str(e)}")

    def audio_callback(self, indata, frames, time, status):
        """Callback for audio recording"""
        if status:
            print(status)
        # Append a copy of the data to our frames list
        self.audio_frames.append(indata.copy())
        
        # Calculate RMS level
        rms = np.sqrt(np.mean(indata**2))
        # Convert to dB and normalize
        db = 20 * np.log10(max(1e-9, rms))
        normalized_level = min(1.0, max(0, (db + 60) / 60))  # Normalize between -60dB and 0dB
        
        # Update level meter (using after to ensure thread safety)
        self.after(0, lambda: self.update_level_meter(normalized_level))

    def update_level_meter(self, level):
        """Update the level meter visualization"""
        width = self.level_meter.winfo_width()
        bar_width = int(width * level)
        self.level_meter.coords(self.level_bar, 0, 0, bar_width, 20)
        
        # Change color based on level
        if level > 0.9:
            color = '#ff0000'  # Red for high levels
        elif level > 0.7:
            color = '#ffff00'  # Yellow for medium levels
        else:
            color = '#00ff00'  # Green for normal levels
        self.level_meter.itemconfig(self.level_bar, fill=color)

    def toggle_s2s_mode(self):
        """Switch between text input and Speech-to-Speech modes"""
        if self.use_s2s.get():
            self.user_input.grid_remove()
            self.s2s_controls.grid(row=0, column=0, sticky="ew")
            self.input_label.configure(text="Reference Audio:")
            # Clear output text when switching to S2S mode
            self.output_text.configure(state="normal")
            self.output_text.delete("1.0", "end")
            self.output_text.configure(state="disabled")
            # Show s2s preview if audio exists
            if hasattr(self, 'current_s2s_audio'):
                self.s2s_preview_frame.grid()
                self.update_s2s_button_states(False)
                self.preview_play_button.configure(state="normal")
        else:
            self.s2s_controls.grid_remove()
            self.user_input.grid(row=0, column=0, sticky="nsew")
            self.input_label.configure(text="Enter your text:")
            self.output_text.configure(state="normal")
            self.output_text.delete("1.0", "end")
            self.output_text.configure(state="disabled")
            # Hide s2s preview
            self.s2s_preview_frame.grid_remove()

    def on_playback_finished(self):
        """Handle playback finished event."""
        # Reset button states for both main and s2s players
        if hasattr(self, 'current_s2s_audio'):
            self.update_s2s_button_states(False)
        self.update_button_states(False)

    def update_playhead(self):
        """Update the playhead position for the main player"""
        if self.controller and self.controller.model.is_playing:
            current_time = self.controller.model.get_current_position()
            self.audio_visualizer.update_playhead(current_time)
            self.playhead_update_id = self.after(50, self.update_playhead)  # Update every 50ms
        else:
            self.stop_playhead_update()
            self.update_button_states(False)

    def start_playhead_update(self):
        """Start updating the playhead position"""
        self.stop_playhead_update()  # Ensure no existing update is running
        self.update_playhead()

    def stop_playhead_update(self):
        """Stop updating the playhead"""
        if hasattr(self, 'playhead_update_id'):
            self.after_cancel(self.playhead_update_id)
            self.playhead_update_id = None

    def cleanup_audio_state(self):
        """Clean up audio state when switching modes or closing"""
        # Stop any playing audio in both models
        if self.controller:
            self.controller.model.stop()
            self.controller.s2s_model.stop()  # Stop s2s model as well
        
        # Stop all playhead updates
        self.stop_playhead_update()
        self.stop_s2s_playhead_update()
        
        # Reset all button states
        self.update_button_states(False)
        self.update_s2s_button_states(False)
        
        # Reset all playheads
        self.audio_visualizer.update_playhead(0)
        if hasattr(self, 's2s_visualizer'):
            self.s2s_visualizer.update_playhead(0)

    def handle_error(self, error_message, title="Error"):
        """Handle errors in a consistent way"""
        logging.error(error_message)
        self.update_status(f"Error: {error_message}")
        messagebox.showerror(title, error_message)
        
        # Clean up state after error
        self.cleanup_audio_state()

    def on_tab_change(self):
        """Handle tab changes"""
        # Clean up audio state
        self.cleanup_audio_state()
        
        # Update tab widgets
        self.update_tab_widgets()

    def quit(self):
        """Clean up before quitting"""
        self.cleanup_audio_state()

    def update_tab_widgets(self):
        """Update the widgets when switching tabs."""
        current_tab = self.current_module.get()
        self.current_tab_widget.grid_remove()
        self.current_tab_widget = self.tab_widgets[current_tab]
        self.current_tab_widget.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        
        # Clear the output field when switching tabs
        self.output_text.configure(state="normal")
        self.output_text.delete("1.0", "end")
        self.output_text.configure(state="disabled")
        
        if current_tab in ["Music", "SFX"]:
            self.llm_button.grid()
            self.s2s_checkbox.grid_remove()  # Hide S2S checkbox
            self.use_s2s.set(False)  # Reset S2S mode
            # Clear any S2S related output
            if hasattr(self, 's2s_preview_frame'):
                self.s2s_preview_frame.grid_remove()
                # Stop any playing s2s audio
                if self.controller and self.controller.s2s_model.is_playing:  # Fixed: Check s2s_model instead of main model
                    self.stop_s2s_audio()
        else:
            self.llm_button.grid_remove()
            self.s2s_checkbox.grid()  # Show S2S checkbox
            # Show s2s preview if in s2s mode and audio exists
            if self.use_s2s.get() and hasattr(self, 'current_s2s_audio'):
                self.s2s_preview_frame.grid()
                self.update_s2s_button_states(False)
            
        # Update the audio file selector
        self.audio_file_selector.update_module(current_tab.lower())

    def set_generate_command(self, command):
        """Set the command for the Generate button"""
        self.generate_button.configure(command=command)

    def set_clear_command(self, command):
        """Set the command for the Clear button"""
        self.clear_button.configure(command=command)

    def set_llm_command(self, command):
        """Set the command for the Improve Prompt button"""
        self.llm_button.configure(command=command)

    def set_play_command(self, command):
        """Set the command for the Play button"""
        self.play_button.configure(command=command)

    def set_stop_command(self, command):
        """Set the command for the Stop button"""
        self.stop_button.configure(command=command)

    def set_restart_command(self, command):
        """Set the command for the Restart button"""
        self.restart_button.configure(command=command)

    def set_add_to_timeline_command(self, command):
        """Set the command for the Add to Timeline button"""
        self.add_to_timeline_button.configure(command=command)

    def set_add_to_reaper_command(self, command):
        """Set the command for the Add to Reaper button"""
        self.add_to_reaper_button.configure(command=command)

    def set_timeline_command(self, command):
        """Set the command for the Show Timeline button"""
        self.timeline_button.configure(command=command)

    def set_visualizer_click_command(self, command):
        """Set the command for visualizer click events"""
        self.audio_visualizer.set_on_click_seek(command)

    def show_progress_bar(self, determinate=True):
        """Show and start the progress bar"""
        if determinate:
            self.progress_bar.configure(mode="determinate")
            self.progress_bar.set(0)
        else:
            self.progress_bar.configure(mode="indeterminate")
        self.progress_bar.grid()
        self.progress_bar.start()

    def hide_progress_bar(self):
        """Hide and stop the progress bar"""
        self.progress_bar.stop()
        self.progress_bar.grid_remove()

    def update_status(self, message):
        """Update the status bar message"""
        self.status_var.set(message)

    def update_output(self, message):
        """Update the output text area"""
        self.output_text.configure(state="normal")
        self.output_text.delete("1.0", "end")
        self.output_text.insert("end", message)
        self.output_text.configure(state="disabled")

    def clear_input(self):
        """Clear the input text area"""
        self.user_input.delete("1.0", "end")
        self.output_text.configure(state="normal")
        self.output_text.delete("1.0", "end")
        self.output_text.configure(state="disabled")
        self.duration_var.set("0")
        self.update_status("")

    def update_voice_dropdown(self, voices):
        """Update the voice dropdown with available voices"""
        self.voice_dropdown.configure(values=[voice[0] for voice in voices])
        if voices:
            self.selected_voice.set(voices[0][0])

    def set_file_select_command(self, command):
        """Set the command for file selection"""
        self.audio_file_selector.set_file_select_command(command)

    def refresh_file_list(self, module):
        """Refresh the audio file list for the given module"""
        self.audio_file_selector.refresh_files(module)

    def get_selected_file(self):
        """Get the currently selected audio file"""
        return self.audio_file_selector.get_selected_file()

    def get_voice_settings(self):
        """Get current voice settings as a dictionary"""
        return {
            'stability': self.voice_settings['stability'].get(),
            'similarity_boost': self.voice_settings['similarity_boost'].get(),
            'style': self.voice_settings['style'].get(),
            'use_speaker_boost': self.voice_settings['use_speaker_boost'].get()
        }

    def set_generate_preview_command(self, command):
        """Set the command for generating voice previews"""
        self.generate_preview_command = command

    def set_save_preview_command(self, command):
        """Set the command for saving voice previews"""
        self.save_preview_command = command

    def set_discard_preview_command(self, command):
        """Set the command for discarding voice previews"""
        self.discard_preview_command = command

    def show_preview_controls(self):
        """Show the preview controls and initialize preview navigation"""
        self.preview_frame.grid()
        self.current_preview_index = 0
        self.update_preview_label()
        self.voice_name_entry.delete(0, 'end')
        self.voice_name_entry.insert(0, f"Custom Voice {time.strftime('%Y%m%d_%H%M%S')}")
        self.listen_button.configure(text="Listen")

    def update_preview_label(self):
        """Update the preview counter label"""
        self.preview_label.configure(text=f"Preview {self.current_preview_index + 1}/3")

    def update_preview_display(self, preview_file):
        """Update the display with the current preview"""
        self.update_preview_label()
        # Update audio player and visualizer
        if self.controller:
            self.controller.model.stop()  # Stop any playing audio
            self.listen_button.configure(text="Listen")  # Reset listen button
            self.controller.model.load_audio(preview_file)
            self.audio_visualizer.update_waveform(preview_file)
            self.update_button_states(False)

    def next_preview(self):
        """Switch to the next voice preview"""
        if self.controller:
            preview_file = self.controller.speech_service.next_preview()
            if preview_file:
                self.current_preview_index = (self.current_preview_index + 1) % 3
                self.update_preview_display(preview_file)

    def previous_preview(self):
        """Switch to the previous voice preview"""
        if self.controller:
            preview_file = self.controller.speech_service.previous_preview()
            if preview_file:
                self.current_preview_index = (self.current_preview_index - 1) % 3
                self.update_preview_display(preview_file)

    def generate_voice_preview(self):
        """Generate previews of the unique voice"""
        if not self.controller:
            messagebox.showerror("Error", "Controller not initialized")
            return

        description = self.voice_description.get("1.0", "end-1c").strip()
        text = self.example_text.get("1.0", "end-1c").strip()
        
        if not description or not text:
            messagebox.showerror("Error", "Please provide both a voice description and example text.")
            return
            
        if len(text) < 100:
            messagebox.showerror("Error", "Example text must be at least 100 characters long.")
            return
        
        # Show progress
        self.show_progress_bar(determinate=False)
        self.preview_button.configure(state="disabled")
        
        def preview_thread():
            if self.controller:
                success = self.controller.handle_voice_preview(description, text)
                if success:
                    self.after(0, self.show_preview_controls)
                else:
                    self.after(0, lambda: messagebox.showerror("Error", "Failed to generate voice previews"))
            
            self.after(0, self.hide_progress_bar)
            self.after(0, lambda: self.preview_button.configure(state="normal"))
        
        threading.Thread(target=preview_thread, daemon=True).start()

    def save_voice_to_library(self):
        """Save the current preview voice to the library"""
        if not self.controller:
            messagebox.showerror("Error", "Controller not initialized")
            return

        voice_name = self.voice_name_entry.get().strip()
        if not voice_name:
            messagebox.showerror("Error", "Please provide a name for the voice")
            return
        
        if self.controller.save_voice_preview(voice_name):
            messagebox.showinfo("Success", f"Voice '{voice_name}' added to library")
            self.preview_frame.grid_remove()
            self.selected_voice.set(voice_name)
        else:
            messagebox.showerror("Error", "Failed to save voice to library")

    def discard_voice(self):
        """Discard all preview voices"""
        if self.controller:
            self.controller.discard_voice_preview()
        self.preview_frame.grid_remove()

    def toggle_preview_playback(self):
        """Toggle play/pause for the current preview"""
        if not self.controller:
            return
            
        if self.controller.model.is_playing:
            self.controller.model.stop()
            self.listen_button.configure(text="Listen")
            self.update_button_states(False)
        else:
            self.controller.model.play()
            self.listen_button.configure(text="Stop")
            self.update_button_states(True)

    def create_voice_preview_frame(self, parent):
        """Create the voice preview frame"""
        self.preview_frame = ctk.CTkFrame(parent)
        self.preview_frame.grid(row=3, column=0, columnspan=2, pady=5, sticky="ew")
        self.preview_frame.grid_columnconfigure(0, weight=1)  # Make preview frame expandable
        self.preview_frame.grid_remove()  # Hidden by default
        
        # Preview navigation
        nav_frame = ctk.CTkFrame(self.preview_frame)
        nav_frame.grid(row=0, column=0, columnspan=2, pady=5, sticky="ew")
        nav_frame.grid_columnconfigure(2, weight=1)  # Center the preview label
        
        self.prev_preview_button = ctk.CTkButton(nav_frame, text="←", width=30,
                                            command=self.previous_preview)
        self.prev_preview_button.grid(row=0, column=0, padx=5)
        
        self.preview_label = ctk.CTkLabel(nav_frame, text="Preview 1/3")
        self.preview_label.grid(row=0, column=1, padx=20)
        
        self.next_preview_button = ctk.CTkButton(nav_frame, text="→", width=30,
                                            command=self.next_preview)
        self.next_preview_button.grid(row=0, column=2, padx=5)
        
        # Listen button
        self.listen_button = ctk.CTkButton(nav_frame, text="Listen", width=80,
                                        command=self.toggle_preview_playback)
        self.listen_button.grid(row=0, column=3, padx=20)
        
        # Voice name input
        name_label = ctk.CTkLabel(self.preview_frame, text="Voice Name:")
        name_label.grid(row=1, column=0, padx=5, pady=5)
        self.voice_name_entry = ctk.CTkEntry(self.preview_frame, width=150)
        self.voice_name_entry.grid(row=1, column=1, padx=5, pady=5)
        
        # Save/Discard buttons
        self.save_voice_button = ctk.CTkButton(self.preview_frame, text="Save to Library",
                                            command=self.save_voice_to_library)
        self.save_voice_button.grid(row=2, column=0, padx=5, pady=5)
        
        self.discard_voice_button = ctk.CTkButton(self.preview_frame, text="Discard",
                                                command=self.discard_voice)
        self.discard_voice_button.grid(row=2, column=1, padx=5, pady=5)

    def create_voice_description_frame(self, parent):
        """Create the voice description frame"""
        # Voice description
        description_label = ctk.CTkLabel(parent, text="Voice Description:")
        description_label.grid(row=0, column=0, padx=(0, 5), pady=2, sticky="w")
        
        self.voice_description = ctk.CTkTextbox(parent, height=60)
        self.voice_description.grid(row=0, column=1, pady=2, sticky="ew")
        self.voice_description._placeholder_text = "Example: A warm and friendly female voice with a slight British accent"
        self.voice_description.insert("1.0", self.voice_description._placeholder_text)
        self.voice_description.configure(text_color="gray60")

        # Example text input with character counter
        text_label = ctk.CTkLabel(parent, text="Example Text:")
        text_label.grid(row=1, column=0, padx=(0, 5), pady=2, sticky="w")
        
        text_frame = ctk.CTkFrame(parent)
        text_frame.grid(row=1, column=1, pady=2, sticky="ew")
        text_frame.grid_columnconfigure(0, weight=1)
        
        self.example_text = ctk.CTkTextbox(text_frame, height=60)
        self.example_text.grid(row=0, column=0, sticky="ew")
        self.example_text._placeholder_text = "Enter text for the voice sample (minimum 100 characters)"
        self.example_text.insert("1.0", self.example_text._placeholder_text)
        self.example_text.configure(text_color="gray60")
        
        self.char_counter = ctk.CTkLabel(text_frame, text="0/1000", text_color="gray60")
        self.char_counter.grid(row=1, column=0, pady=(2, 0), sticky="e")

        # Preview button
        self.preview_button = ctk.CTkButton(parent, text="Generate Preview", 
                                        command=self.generate_voice_preview)
        self.preview_button.grid(row=2, column=0, columnspan=2, pady=10)

        # Bind text change events
        self.example_text.bind("<FocusIn>", self.on_example_text_focus_in)
        self.example_text.bind("<FocusOut>", self.on_example_text_focus_out)
        self.example_text.bind("<KeyRelease>", self.update_char_counter)
        
        self.voice_description.bind("<FocusIn>", self.on_description_focus_in)
        self.voice_description.bind("<FocusOut>", self.on_description_focus_out)

    def on_example_text_focus_in(self, event):
        """Handle focus in event for example text"""
        if self.example_text.get("1.0", "end-1c") == self.example_text._placeholder_text:
            self.example_text.delete("1.0", "end")
            self.example_text.configure(text_color=("black", "white"))
            self.update_char_counter(None)

    def on_example_text_focus_out(self, event):
        """Handle focus out event for example text"""
        if not self.example_text.get("1.0", "end-1c").strip():
            self.example_text.insert("1.0", self.example_text._placeholder_text)
            self.example_text.configure(text_color="gray60")
            self.update_char_counter(None)

    def on_description_focus_in(self, event):
        """Handle focus in event for voice description"""
        if self.voice_description.get("1.0", "end-1c") == self.voice_description._placeholder_text:
            self.voice_description.delete("1.0", "end")
            self.voice_description.configure(text_color=("black", "white"))

    def on_description_focus_out(self, event):
        """Handle focus out event for voice description"""
        if not self.voice_description.get("1.0", "end-1c").strip():
            self.voice_description.insert("1.0", self.voice_description._placeholder_text)
            self.voice_description.configure(text_color="gray60")

    def update_char_counter(self, event):
        """Update the character counter and its appearance"""
        text = self.example_text.get("1.0", "end-1c")
        if text == self.example_text._placeholder_text:
            count = 0
        else:
            count = len(text)
        
        # Update counter text and color based on count
        self.char_counter.configure(text=f"{count}/1000")
        
        if count >= 100:
            self.char_counter.configure(text_color=("green", "light green"))
        elif count > 0:
            self.char_counter.configure(text_color=("red", "red"))
        else:
            self.char_counter.configure(text_color="gray60")
