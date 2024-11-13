import customtkinter as ctk
import logging
import threading
import time
from tkinter import messagebox
from utils.audio_visualizer import AudioVisualizer
from utils.audio_file_selector import AudioFileSelector


class AudioGeneratorView(ctk.CTkFrame):
    def __init__(self, master, config, project_model):
        super().__init__(master)
        self.config = config
        self.project_model = project_model
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.controller = None  # Will be set later
        self.create_widgets()

    def set_controller(self, controller):
        """Set the audio controller for this view."""
        self.controller = controller

    def create_widgets(self):
        self.create_top_bar()
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
        main_content = ctk.CTkFrame(self)
        main_content.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        main_content.grid_columnconfigure(0, weight=1)
        main_content.grid_rowconfigure(4, weight=1)  # Make output field expandable

        self.create_input_field(main_content)
        self.create_action_buttons(main_content)
        self.create_tab_specific_options(main_content)
        self.create_output_display(main_content)
        self.create_separator(main_content)
        self.create_audio_file_selector(main_content)
        self.create_audio_visualizer(main_content)
        self.create_audio_controls(main_content)
        self.create_progress_and_status_bar(main_content)

    def create_input_field(self, parent):
        input_frame = ctk.CTkFrame(parent)
        input_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        input_frame.grid_columnconfigure(0, weight=1)
        input_frame.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(input_frame, text="Enter your text:").grid(row=0, column=0, sticky="w")
        self.user_input = ctk.CTkTextbox(input_frame, height=100)
        self.user_input.grid(row=1, column=0, sticky="nsew")

    def create_action_buttons(self, parent):
        action_frame = ctk.CTkFrame(parent)
        action_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        action_frame.grid_columnconfigure(3, weight=1)

        self.generate_button = ctk.CTkButton(action_frame, text="Generate")
        self.generate_button.grid(row=0, column=0, padx=(0, 5))

        self.clear_button = ctk.CTkButton(action_frame, text="Clear")
        self.clear_button.grid(row=0, column=1, padx=5)

        self.llm_button = ctk.CTkButton(action_frame, text="Improve Prompt")
        self.llm_button.grid(row=0, column=2, padx=5)

    def create_tab_specific_options(self, parent):
        self.tab_widgets = {
            'Music': self.create_music_widgets(parent),
            'SFX': self.create_sfx_widgets(parent),
            'Speech': self.create_speech_widgets(parent)
        }
        self.current_tab_widget = self.tab_widgets['Music']
        self.current_tab_widget.grid(row=2, column=0, sticky="ew", pady=(0, 10))

    def create_output_display(self, parent):
        output_frame = ctk.CTkFrame(parent)
        output_frame.grid(row=3, column=0, sticky="nsew", pady=(0, 10))
        output_frame.grid_columnconfigure(0, weight=1)
        output_frame.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(output_frame, text="Output:").grid(row=0, column=0, sticky="w")
        self.output_text = ctk.CTkTextbox(output_frame, height=100, state="disabled")
        self.output_text.grid(row=1, column=0, sticky="nsew")

    def create_separator(self, parent):
        separator = ctk.CTkFrame(parent, height=2, fg_color="gray")
        separator.grid(row=4, column=0, sticky="ew", pady=(0, 10))

    def create_audio_file_selector(self, parent):
        self.audio_file_selector = AudioFileSelector(parent, self.config, self.project_model)
        self.audio_file_selector.grid(row=5, column=0, sticky="ew", pady=(0, 10))

    def create_audio_visualizer(self, parent):
        visualizer_frame = ctk.CTkFrame(parent)
        visualizer_frame.grid(row=6, column=0, sticky="nsew", pady=(0, 10))
        visualizer_frame.grid_rowconfigure(0, weight=1)
        visualizer_frame.grid_columnconfigure(0, weight=1)
        
        self.audio_visualizer = AudioVisualizer(visualizer_frame)
        self.audio_visualizer.pack(fill=ctk.BOTH, expand=True)
        parent.grid_rowconfigure(6, weight=1)  # Make the visualizer expandable

    def create_audio_controls(self, parent):
        control_frame = ctk.CTkFrame(parent)
        control_frame.grid(row=7, column=0, sticky="ew", pady=(0, 10))

        self.play_button = ctk.CTkButton(control_frame, text="Play", state="disabled", width=60)
        self.play_button.grid(row=0, column=0, padx=(0, 2))

        self.stop_button = ctk.CTkButton(control_frame, text="Stop", state="disabled", width=60)
        self.stop_button.grid(row=0, column=1, padx=2)

        self.restart_button = ctk.CTkButton(control_frame, text="Restart", state="disabled", width=60)
        self.restart_button.grid(row=0, column=2, padx=2)

        self.add_to_timeline_button = ctk.CTkButton(control_frame, text="Add to Timeline", state="disabled", width=120)
        self.add_to_timeline_button.grid(row=0, column=3, padx=2)

        self.add_to_reaper_button = ctk.CTkButton(control_frame, text="Add to Reaper", state="disabled", width=120)
        self.add_to_reaper_button.grid(row=0, column=4, padx=2)

    def create_progress_and_status_bar(self, parent):
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

    def create_music_widgets(self, parent):
        frame = ctk.CTkFrame(parent)
        self.instrumental_var = ctk.BooleanVar(value=False)
        checkbox = ctk.CTkCheckBox(frame, text="Instrumental", variable=self.instrumental_var)
        checkbox.pack()
        return frame

    def create_sfx_widgets(self, parent):
        frame = ctk.CTkFrame(parent)
        self.duration_var = ctk.StringVar(value="0")
        label = ctk.CTkLabel(frame, text="Duration (0 = automatic, 0.5-22s):")
        entry = ctk.CTkEntry(frame, textvariable=self.duration_var, width=100)
        label.pack(side="left", padx=(0, 5))
        entry.pack(side="left")
        return frame

    def create_speech_widgets(self, parent):
        frame = ctk.CTkFrame(parent)
        frame.grid_columnconfigure(1, weight=1)  # Make the second column expandable

        # Standard voice selection
        self.selected_voice = ctk.StringVar()
        label = ctk.CTkLabel(frame, text="Select Voice:")
        self.voice_dropdown = ctk.CTkOptionMenu(frame, variable=self.selected_voice, width=120)
        label.grid(row=0, column=0, padx=(0, 5), pady=5, sticky="w")
        self.voice_dropdown.grid(row=0, column=1, pady=5, sticky="w")

        # Checkbox for unique voice generation
        self.use_unique_voice = ctk.BooleanVar(value=False)
        self.unique_voice_checkbox = ctk.CTkCheckBox(frame, text="Generate Unique Voice", 
                                                variable=self.use_unique_voice, 
                                                command=self.toggle_unique_voice_options)
        self.unique_voice_checkbox.grid(row=1, column=0, columnspan=2, pady=5, sticky="w")

        # Create container frame for unique voice options
        self.unique_voice_frame = ctk.CTkFrame(frame)
        self.unique_voice_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=5)
        self.unique_voice_frame.grid_columnconfigure(1, weight=1)  # Make second column expandable
        self.unique_voice_frame.grid_remove()  # Initially hidden

        # Voice description
        description_label = ctk.CTkLabel(self.unique_voice_frame, text="Voice Description:")
        description_label.grid(row=0, column=0, padx=(0, 5), pady=2, sticky="w")
        
        self.voice_description = ctk.CTkTextbox(self.unique_voice_frame, height=60)
        self.voice_description.grid(row=0, column=1, pady=2, sticky="ew")
        self.voice_description._placeholder_text = "Example: A warm and friendly female voice with a slight British accent"
        self.voice_description.insert("1.0", self.voice_description._placeholder_text)
        self.voice_description.configure(text_color="gray60")

        # Example text input with character counter
        text_label = ctk.CTkLabel(self.unique_voice_frame, text="Example Text:")
        text_label.grid(row=1, column=0, padx=(0, 5), pady=2, sticky="w")
        
        text_frame = ctk.CTkFrame(self.unique_voice_frame)
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
        self.preview_button = ctk.CTkButton(self.unique_voice_frame, text="Generate Preview", 
                                        command=self.generate_voice_preview)
        self.preview_button.grid(row=2, column=0, columnspan=2, pady=10)

        # Preview controls frame (initially hidden)
        self.preview_frame = ctk.CTkFrame(frame)
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

        # Bind text change events
        self.example_text.bind("<FocusIn>", self.on_example_text_focus_in)
        self.example_text.bind("<FocusOut>", self.on_example_text_focus_out)
        self.example_text.bind("<KeyRelease>", self.update_char_counter)
        
        self.voice_description.bind("<FocusIn>", self.on_description_focus_in)
        self.voice_description.bind("<FocusOut>", self.on_description_focus_out)

        # Set initial state for text inputs
        self.toggle_unique_voice_options()
        
        return frame

    def on_example_text_focus_in(self, event):
        """Handle focus in event for example text."""
        if self.example_text.get("1.0", "end-1c") == self.example_text._placeholder_text:
            self.example_text.delete("1.0", "end")
            self.example_text.configure(text_color=("black", "white"))
            self.update_char_counter(None)

    def on_example_text_focus_out(self, event):
        """Handle focus out event for example text."""
        if not self.example_text.get("1.0", "end-1c").strip():
            self.example_text.insert("1.0", self.example_text._placeholder_text)
            self.example_text.configure(text_color="gray60")
            self.update_char_counter(None)

    def on_description_focus_in(self, event):
        """Handle focus in event for voice description."""
        if self.voice_description.get("1.0", "end-1c") == self.voice_description._placeholder_text:
            self.voice_description.delete("1.0", "end")
            self.voice_description.configure(text_color=("black", "white"))

    def on_description_focus_out(self, event):
        """Handle focus out event for voice description."""
        if not self.voice_description.get("1.0", "end-1c").strip():
            self.voice_description.insert("1.0", self.voice_description._placeholder_text)
            self.voice_description.configure(text_color="gray60")

    def update_char_counter(self, event):
        """Update the character counter and its appearance."""
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

    def toggle_unique_voice_options(self):
        """Toggle between standard voice selection and unique voice generation."""
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

    def toggle_preview_playback(self):
        """Toggle play/pause for the current preview."""
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

    def update_preview_display(self, preview_file):
        """Update the display with the current preview."""
        self.update_preview_label()
        # Update audio player and visualizer
        if self.controller:
            self.controller.model.stop()  # Stop any playing audio
            self.listen_button.configure(text="Listen")  # Reset listen button
            self.controller.model.load_audio(preview_file)
            self.audio_visualizer.update_waveform(preview_file)
            self.update_button_states(False)

    def on_playback_finished(self):
        """Handle playback finished event."""
        self.listen_button.configure(text="Listen")
        self.update_button_states(False)

    def show_preview_controls(self):
        """Show the preview controls and initialize preview navigation."""
        self.preview_frame.grid()
        self.current_preview_index = 0
        self.update_preview_label()
        self.voice_name_entry.delete(0, 'end')
        self.voice_name_entry.insert(0, f"Custom Voice {time.strftime('%Y%m%d_%H%M%S')}")
        self.listen_button.configure(text="Listen")  # Reset listen button state

    def set_generate_preview_command(self, command):
        """Set the command for generating voice previews."""
        self.generate_preview_command = command

    def set_save_preview_command(self, command):
        """Set the command for saving voice previews."""
        self.save_preview_command = command

    def set_discard_preview_command(self, command):
        """Set the command for discarding voice previews."""
        self.discard_preview_command = command

    def show_preview_controls(self):
        """Show the preview controls and initialize preview navigation."""
        self.preview_frame.grid()
        self.current_preview_index = 0
        self.update_preview_label()
        self.voice_name_entry.delete(0, 'end')
        self.voice_name_entry.insert(0, f"Custom Voice {time.strftime('%Y%m%d_%H%M%S')}")

    def update_preview_label(self):
        """Update the preview counter label."""
        self.preview_label.configure(text=f"Preview {self.current_preview_index + 1}/3")

    def generate_voice_preview(self):
        """Generate previews of the unique voice."""
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

    def next_preview(self):
        """Switch to the next voice preview."""
        if self.controller:
            preview_file = self.controller.speech_service.next_preview()
            if preview_file:
                self.current_preview_index = (self.current_preview_index + 1) % 3
                self.update_preview_display(preview_file)

    def previous_preview(self):
        """Switch to the previous voice preview."""
        if self.controller:
            preview_file = self.controller.speech_service.previous_preview()
            if preview_file:
                self.current_preview_index = (self.current_preview_index - 1) % 3
                self.update_preview_display(preview_file)

    def update_preview_display(self, preview_file):
        """Update the display with the current preview."""
        self.update_preview_label()
        # Update audio player and visualizer
        if self.controller:
            self.controller.model.load_audio(preview_file)
            self.audio_visualizer.update_waveform(preview_file)
            self.update_button_states(False)

    def save_voice_to_library(self):
        """Save the current preview voice to the library."""
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
        """Discard all preview voices."""
        if self.controller:
            self.controller.discard_voice_preview()
        self.preview_frame.grid_remove()

    def update_tab_widgets(self):
        current_tab = self.current_module.get()
        self.current_tab_widget.grid_remove()
        self.current_tab_widget = self.tab_widgets[current_tab]
        self.current_tab_widget.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        
        if current_tab in ["Music", "SFX"]:
            self.llm_button.grid()
        else:
            self.llm_button.grid_remove()

        # Update the audio file selector
        self.audio_file_selector.update_module(current_tab.lower())

    def update_button_states(self, is_playing):
        if is_playing:
            self.play_button.configure(state="disabled")
            self.stop_button.configure(state="normal")
            self.restart_button.configure(state="normal")
        else:
            self.play_button.configure(state="normal")
            self.stop_button.configure(state="disabled")
            self.restart_button.configure(state="normal")

    def update_output(self, message):
        self.output_text.configure(state="normal")
        self.output_text.insert("end", message + "\n")
        self.output_text.see("end")
        self.output_text.configure(state="disabled")

    def update_status(self, message):
        self.status_var.set(message)

    def show_progress_bar(self, determinate=True):
        if determinate:
            self.progress_bar.configure(mode="determinate")
            self.progress_bar.set(0)
        else:
            self.progress_bar.configure(mode="indeterminate")
        self.progress_bar.grid()
        self.progress_bar.start()

    def hide_progress_bar(self):
        self.progress_bar.stop()
        self.progress_bar.grid_remove()

    def set_add_to_timeline_command(self, command):
        self.add_to_timeline_button.configure(command=command)

    def on_drag_start(self, event):
        if self.audio_file_selector.file_var.get() != "No files available":
            self.drag_data = {'x': event.x, 'y': event.y, 'item': self.audio_file_selector.file_var.get()}
            self.drag_icon = ctk.CTkLabel(self, text=self.drag_data['item'])
            self.drag_icon.place(x=event.x_root - self.winfo_rootx(), y=event.y_root - self.winfo_rooty())

    def on_drag_motion(self, event):
        if hasattr(self, 'drag_icon'):
            x = event.x_root - self.winfo_rootx()
            y = event.y_root - self.winfo_rooty()
            self.drag_icon.place(x=x, y=y)

    def on_drag_release(self, event):
        if hasattr(self, 'drag_icon'):
            self.drag_icon.destroy()
            del self.drag_icon

            # Check if the release happened over the timeline window
            timeline_view = self.master.timeline_controller.view
            if timeline_view.winfo_containing(event.x_root, event.y_root) == timeline_view:
                file_path = self.audio_file_selector.get_selected_file()
                if file_path:
                    # Determine which track to add the clip to based on the current module
                    track_index = {"music": 1, "sfx": 2, "speech": 0}.get(self.current_module.get().lower(), 0)
                    
                    # Calculate the x position relative to the timeline canvas
                    x_position = timeline_view.timeline_canvas.winfo_pointerx() - timeline_view.timeline_canvas.winfo_rootx()
                    start_time = x_position / (timeline_view.seconds_per_pixel * timeline_view.x_zoom)
                    
                    # Add the clip to the timeline
                    self.master.timeline_controller.add_audio_clip(file_path, track_index, start_time)
                    logging.info(f"Clip added to timeline: track={track_index}, start_time={start_time}")
                else:
                    logging.warning("No file selected for drag and drop.")
            else:
                logging.info("File dropped outside the timeline window.")

    def clear_input(self):
        self.user_input.delete("1.0", "end")
        self.output_text.configure(state="normal")
        self.output_text.delete("1.0", "end")
        self.output_text.configure(state="disabled")
        self.duration_var.set("0")
        self.update_status("")

    def set_generate_command(self, command):
        self.generate_button.configure(command=command)

    def set_clear_command(self, command):
        self.clear_button.configure(command=command)

    def set_llm_command(self, command):
        self.llm_button.configure(command=command)

    def set_play_command(self, command):
        self.play_button.configure(command=command)

    def set_stop_command(self, command):
        self.stop_button.configure(command=command)

    def set_restart_command(self, command):
        self.restart_button.configure(command=command)

    def set_file_select_command(self, command):
        self.audio_file_selector.set_file_select_command(command)

    def set_timeline_command(self, command):
        self.timeline_button.configure(command=command)

    def refresh_file_list(self, module):
        self.audio_file_selector.refresh_files(module)

    def set_visualizer_click_command(self, command):
        self.audio_visualizer.set_on_click_seek(command)

    def update_voice_dropdown(self, voices):
        self.voice_dropdown.configure(values=[voice[0] for voice in voices])
        if voices:
            self.selected_voice.set(voices[0][0])
    
    def set_add_to_reaper_command(self, command):
        self.add_to_reaper_button.configure(command=command)