import os
import customtkinter as ctk

class AudioFileSelector:
    def __init__(self, master, config):
        self.master = master
        self.config = config
        self.file_var = ctk.StringVar(value="Select audio file")
        self.current_directory = None
        self.file_select_command = None
        self.create_widgets()

    def create_widgets(self):
        selector_frame = ctk.CTkFrame(self.master)
        selector_frame.grid(row=9, column=0, pady=10, padx=10, sticky="ew")

        self.file_dropdown = ctk.CTkOptionMenu(
            selector_frame, 
            variable=self.file_var,
            width=290,
            command=self.on_file_select
        )
        self.file_dropdown.pack(side="left", padx=(0, 10))

        self.refresh_button = ctk.CTkButton(
            selector_frame,
            text="Refresh",
            command=self.refresh_files
        )
        self.refresh_button.pack(side="left")

    def get_output_dir(self, module):
        if module == 'music':
            return self.config['music_gen']['output_dir']
        elif module == 'sfx':
            return self.config['sfx_gen']['output_dir']
        elif module == 'speech':
            return self.config['speech_gen']['output_dir']
        else:
            raise ValueError(f"Unknown module: {module}")

    def refresh_files(self, module=None):
        if module is not None:
            self.current_directory = self.get_output_dir(module)
        elif self.current_directory is None:
            self.current_directory = self.get_output_dir('music')  # Default to music

        files = [f for f in os.listdir(self.current_directory) if f.endswith('.mp3')]
        if files:
            self.file_dropdown.configure(values=files)
            if self.file_var.get() == "Select audio file" or self.file_var.get() not in files:
                self.file_var.set("Select audio file")
        else:
            self.file_dropdown.configure(values=["No files available"])
            self.file_var.set("No files available")

    def on_file_select(self, choice):
        if choice != "No files available" and self.current_directory:
            file_path = os.path.join(self.current_directory, choice)
            if os.path.exists(file_path):
                if self.file_select_command:
                    self.file_select_command(file_path)

    def get_selected_file(self):
        if self.current_directory and self.file_var.get() not in ["Select audio file", "No files available"]:
            return os.path.join(self.current_directory, self.file_var.get())
        return None

    def clear(self):
        self.file_var.set("Select audio file")
        self.file_dropdown.configure(values=[])

    def set_file_select_command(self, command):
        self.file_select_command = command

    def update_module(self, module):
        self.refresh_files(module)