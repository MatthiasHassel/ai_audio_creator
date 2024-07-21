import customtkinter as ctk
import logging
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
        self.create_widgets()

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

        self.llama_button = ctk.CTkButton(action_frame, text="Input to Llama3")
        self.llama_button.grid(row=0, column=2, padx=5)

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

        self.pause_resume_button = ctk.CTkButton(control_frame, text="Pause", state="disabled", width=60)
        self.pause_resume_button.grid(row=0, column=1, padx=2)

        self.stop_button = ctk.CTkButton(control_frame, text="Stop", state="disabled", width=60)
        self.stop_button.grid(row=0, column=2, padx=2)

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
        self.selected_voice = ctk.StringVar()
        label = ctk.CTkLabel(frame, text="Select Voice:")
        self.voice_dropdown = ctk.CTkOptionMenu(frame, variable=self.selected_voice, width=120)
        label.pack(side="left", padx=(0, 5))
        self.voice_dropdown.pack(side="left")
        return frame

    def update_tab_widgets(self):
        current_tab = self.current_module.get()
        self.current_tab_widget.grid_remove()
        self.current_tab_widget = self.tab_widgets[current_tab]
        self.current_tab_widget.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        
        if current_tab in ["Music", "SFX"]:
            self.llama_button.grid()
        else:
            self.llama_button.grid_remove()

        # Update the audio file selector
        self.audio_file_selector.update_module(current_tab.lower())

    

    def update_button_states(self, is_playing, is_paused):
        if is_playing:
            self.play_button.configure(state="disabled")
            self.pause_resume_button.configure(state="normal")
            self.stop_button.configure(state="normal")
            if is_paused:
                self.pause_resume_button.configure(text="Resume")
            else:
                self.pause_resume_button.configure(text="Pause")
        else:
            self.play_button.configure(state="normal")
            self.pause_resume_button.configure(state="disabled", text="Pause")
            self.stop_button.configure(state="disabled")

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
        self.audio_visualizer.clear()
        self.audio_file_selector.clear()
        self.audio_visualizer.hide_playhead()

    def set_generate_command(self, command):
        self.generate_button.configure(command=command)

    def set_clear_command(self, command):
        self.clear_button.configure(command=command)

    def set_llama_command(self, command):
        self.llama_button.configure(command=command)

    def set_play_command(self, command):
        self.play_button.configure(command=command)

    def set_pause_resume_command(self, command):
        self.pause_resume_button.configure(command=command)

    def set_stop_command(self, command):
        self.stop_button.configure(command=command)

    def set_file_select_command(self, command):
        self.audio_file_selector.set_file_select_command(command)

    def set_timeline_command(self, command):
        self.timeline_button.configure(command=command)

    def refresh_file_list(self, module):
        self.audio_file_selector.refresh_files(module)

    def set_visualizer_click_command(self, command):
        self.audio_visualizer.set_on_click_seek(command)