import customtkinter as ctk
import tkinter as tk
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
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

    def create_components(self):
        self.paned_window = tk.PanedWindow(self, orient=tk.HORIZONTAL, sashwidth=10, sashrelief=tk.RAISED, bg='#3E3E3E')
        self.paned_window.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        self.script_editor_view = ScriptEditorView(self.paned_window, self.config)
        self.paned_window.add(self.script_editor_view, stretch="always")

        self.audio_generator_view = AudioGeneratorView(self.paned_window, self.config)
        self.paned_window.add(self.audio_generator_view, stretch="always")

        self.paned_window.after(10, self.set_initial_sash_position)

    def set_initial_sash_position(self):
        width = self.paned_window.winfo_width()
        self.paned_window.sash_place(0, width // 2, 0)

    def get_audio_generator_view(self):
        return self.audio_generator_view

    def get_script_editor_view(self):
        return self.script_editor_view

    def set_save_analysis_callback(self, callback):
        self.script_editor_view.set_save_analysis_callback(callback)

    def set_load_analysis_callback(self, callback):
        self.script_editor_view.set_load_analysis_callback(callback)

    def update_analysis_results(self, analyzed_script, suggested_voices, element_counts, estimated_duration):
        self.script_editor_view.update_analysis_results(analyzed_script, suggested_voices, element_counts, estimated_duration)

    def update_status(self, message):
        self.script_editor_view.update_status(message)

    def run(self):
        self.mainloop()