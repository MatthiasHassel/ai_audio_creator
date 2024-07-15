import customtkinter as ctk
from utils.audio_visualizer import AudioVisualizer
from utils.audio_file_selector import AudioFileSelector

class AudioGeneratorView(ctk.CTkFrame):
    def __init__(self, master, config, project_model):
        super().__init__(master)
        self.config = config
        self.project_model = project_model
        self.create_widgets()

    def create_widgets(self):
        self.create_module_buttons()
        self.create_input_field()
        self.create_action_buttons()
        self.create_tab_specific_options()
        self.create_audio_components()
        self.create_progress_and_status_bar()
        self.create_separator()
        self.create_output_display()

    def create_module_buttons(self):
        self.current_module = ctk.StringVar(value="Music")
        module_frame = ctk.CTkFrame(self)
        module_frame.grid(row=0, column=0, pady=10, padx=10, sticky="ew")
        for i, module in enumerate(["Music", "SFX", "Speech"]):
            ctk.CTkRadioButton(
                module_frame, 
                text=module, 
                variable=self.current_module, 
                value=module, 
                command=self.update_tab_widgets
            ).grid(row=0, column=i, padx=5)


    def create_input_field(self):
        input_frame = ctk.CTkFrame(self)
        input_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=2)
        input_frame.grid_rowconfigure(1, weight=1)
        input_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(input_frame, text="Enter your text:").grid(row=0, column=0, sticky="w")
        self.user_input = ctk.CTkTextbox(input_frame)
        self.user_input.grid(row=1, column=0, sticky="nsew")

    def create_action_buttons(self):
        action_frame = ctk.CTkFrame(self)
        action_frame.grid(row=2, column=0, pady=10, padx=10, sticky="w")
        self.generate_button = ctk.CTkButton(action_frame, text="Generate")
        self.generate_button.pack(side="left", padx=(0, 5))
        self.clear_button = ctk.CTkButton(action_frame, text="Clear")
        self.clear_button.pack(side="left", padx=(0, 5))
        self.llama_button = ctk.CTkButton(action_frame, text="Input to Llama3")
        self.llama_button.pack(side="left")

    def create_tab_specific_options(self):
        self.tab_widgets = {
            'Music': self.create_music_widgets(),
            'SFX': self.create_sfx_widgets(),
            'Speech': self.create_speech_widgets()
        }
        self.current_tab_widget = self.tab_widgets['Music']
        self.current_tab_widget.grid(row=3, column=0, pady=5, padx=10, sticky="w")

    def create_music_widgets(self):
        frame = ctk.CTkFrame(self)
        self.instrumental_var = ctk.BooleanVar(value=False)
        checkbox = ctk.CTkCheckBox(frame, text="Instrumental", variable=self.instrumental_var)
        checkbox.pack()
        return frame

    def create_sfx_widgets(self):
        frame = ctk.CTkFrame(self)
        self.duration_var = ctk.StringVar(value="0")
        label = ctk.CTkLabel(frame, text="Duration (0 = automatic, 0.5-22s):")
        entry = ctk.CTkEntry(frame, textvariable=self.duration_var, width=100)
        label.pack(side="left", padx=(0, 5))
        entry.pack(side="left")
        return frame

    def create_speech_widgets(self):
        frame = ctk.CTkFrame(self)
        self.selected_voice = ctk.StringVar()
        label = ctk.CTkLabel(frame, text="Select Voice:")
        self.voice_dropdown = ctk.CTkOptionMenu(frame, variable=self.selected_voice, width=120)
        label.pack(side="left", padx=(0, 5))
        self.voice_dropdown.pack(side="left")
        return frame

    def create_progress_and_status_bar(self):
        progress_status_frame = ctk.CTkFrame(self)
        progress_status_frame.grid(row=4, column=0, pady=(5, 0), padx=10, sticky="ew")
        progress_status_frame.grid_columnconfigure(0, weight=1)

        self.progress_bar = ctk.CTkProgressBar(progress_status_frame)
        self.progress_bar.grid(row=0, column=0, pady=(0, 5), sticky="ew")
        self.progress_bar.set(0)
        self.progress_bar.grid_remove()  # Initially hidden

        self.status_var = ctk.StringVar()
        self.status_var.set(" ")
        self.status_bar = ctk.CTkLabel(progress_status_frame, textvariable=self.status_var, anchor="w", padx=10)
        self.status_bar.grid(row=1, column=0, sticky="ew")

    def create_separator(self):
        separator = ctk.CTkFrame(self, height=2, fg_color="gray")
        separator.grid(row=5, column=0, pady=(5, 0), padx=10, sticky="ew")

    def create_output_display(self):
        output_frame = ctk.CTkFrame(self)
        output_frame.grid(row=6, column=0, pady=(5, 5), padx=10, sticky="ew")
        output_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(output_frame, text="Output:").grid(row=0, column=0, sticky="w")
        self.output_text = ctk.CTkTextbox(output_frame, height=60, state="disabled")
        self.output_text.grid(row=1, column=0, sticky="ew")

    def create_audio_components(self):
        self.audio_visualizer = AudioVisualizer(self)
        self.audio_visualizer.canvas_widget.grid(row=7, column=0, pady=(0, 5), padx=10, sticky="ew")
        self.audio_file_selector = AudioFileSelector(self, self.config, self.project_model)
        self.audio_file_selector.refresh_files(self.current_module.get().lower())
        self.create_audio_controls()

    def create_audio_controls(self):
        audio_frame = ctk.CTkFrame(self)
        audio_frame.grid(row=8, column=0, sticky="ew", padx=5, pady=2)

        self.play_button = ctk.CTkButton(audio_frame, text="Play", state="disabled", width=60)
        self.play_button.grid(row=0, column=0, padx=(0, 2))

        self.pause_resume_button = ctk.CTkButton(audio_frame, text="Pause", state="disabled", width=60)
        self.pause_resume_button.grid(row=0, column=1, padx=2)

        self.stop_button = ctk.CTkButton(audio_frame, text="Stop", state="disabled", width=60)
        self.stop_button.grid(row=0, column=2, padx=2)

    def update_tab_widgets(self):
        current_tab = self.current_module.get()
        self.current_tab_widget.grid_remove()
        self.current_tab_widget = self.tab_widgets[current_tab]
        self.current_tab_widget.grid(row=3, column=0, pady=10, padx=11, sticky="w")
        
        if current_tab in ["Music", "SFX"]:
            self.llama_button.pack(side="left", padx=(0, 5))
        else:
            self.llama_button.pack_forget()

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

    def refresh_file_list(self, module):
        self.audio_file_selector.refresh_files(module)

    def set_visualizer_click_command(self, command):
        self.audio_visualizer.set_on_click_seek(command)