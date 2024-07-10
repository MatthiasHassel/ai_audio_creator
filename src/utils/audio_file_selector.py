import os
import customtkinter as ctk

class AudioFileSelector(ctk.CTkFrame):
    def __init__(self, master, config, current_module, on_select):
        super().__init__(master)
        self.config = config
        self.current_module = current_module
        self.on_select = on_select
        self.initial_state = True
        self.selected_file = None
        self.create_widgets()

    def create_widgets(self):
        self.file_var = ctk.StringVar(value="Select audio file")
        self.file_dropdown = ctk.CTkOptionMenu(
            self, 
            variable=self.file_var,
            command=self.on_file_select,
            width=300
        )
        self.file_dropdown.pack(side="left", padx=(0, 10))

        self.refresh_button = ctk.CTkButton(
            self,
            text="Refresh",
            command=self.refresh_files
        )
        self.refresh_button.pack(side="left")

    def get_output_dir(self):
        module = self.current_module.get().lower()
        if module == 'music':
            return self.config['music_gen']['output_dir']
        elif module == 'sfx':
            return self.config['sfx_gen']['output_dir']
        elif module == 'speech':
            return self.config['speech_gen']['output_dir']
        else:
            raise ValueError(f"Unknown module: {module}")

    def refresh_files(self):
        directory = self.get_output_dir()
        files = [f for f in os.listdir(directory) if f.endswith('.mp3')]
        if files:
            self.file_dropdown.configure(values=files)
            if self.initial_state and not self.selected_file:
                self.file_var.set("Select audio file")
            elif self.selected_file and self.selected_file in files:
                self.file_var.set(self.selected_file)
            elif not self.initial_state:
                self.file_var.set(files[0])
                self.selected_file = files[0]
        else:
            self.file_dropdown.configure(values=["No files available"])
            self.file_var.set("No files available")
            self.selected_file = None

    def on_file_select(self, choice):
        if choice not in ["Select audio file", "No files available"]:
            directory = self.get_output_dir()
            file_path = os.path.join(directory, choice)
            self.on_select(file_path)
            self.initial_state = False
            self.selected_file = choice

    def set_latest_file(self):
        directory = self.get_output_dir()
        files = [f for f in os.listdir(directory) if f.endswith('.mp3')]
        if files:
            latest_file = max(files, key=lambda f: os.path.getmtime(os.path.join(directory, f)))
            self.file_var.set(latest_file)
            self.selected_file = latest_file
            self.on_file_select(latest_file)
        self.initial_state = False

    def reset_to_initial_state(self):
        self.initial_state = True
        self.selected_file = None
        self.file_var.set("Select audio file")