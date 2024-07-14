import customtkinter as ctk
from views.audio_generator_view import AudioGeneratorView
from views.script_editor_view import ScriptEditorView

class MainView(ctk.CTk):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.setup_window()
        self.create_components()

    def setup_window(self):
        self.title(self.config['gui']['window_title'])
        self.geometry(self.config['gui']['window_size'])
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

    def create_components(self):
        self.notebook = ctk.CTkTabview(self)
        self.notebook.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # Audio Generator Tab
        self.audio_tab = self.notebook.add("Audio Generator")
        self.audio_tab.grid_columnconfigure(0, weight=1)
        self.audio_tab.grid_rowconfigure(0, weight=1)
        self.audio_generator_view = AudioGeneratorView(self.audio_tab, self.config)
        self.audio_generator_view.grid(row=0, column=0, sticky="nsew")

        # Script Editor Tab
        self.script_tab = self.notebook.add("Script Editor")
        self.script_tab.grid_columnconfigure(0, weight=1)
        self.script_tab.grid_rowconfigure(0, weight=1)
        self.script_editor_view = ScriptEditorView(self.script_tab, self.config)
        self.script_editor_view.grid(row=0, column=0, sticky="nsew")

    def get_audio_generator_view(self):
        return self.audio_generator_view

    def get_script_editor_view(self):
        return self.script_editor_view

    def run(self):
        self.mainloop()