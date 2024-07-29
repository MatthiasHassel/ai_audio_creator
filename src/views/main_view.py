import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import tkinter.simpledialog as simpledialog
from tkinterdnd2 import DND_FILES, TkinterDnD
import os
from views.audio_generator_view import AudioGeneratorView
from views.script_editor_view import ScriptEditorView

class MainView(tk.Toplevel, TkinterDnD.DnDWrapper):
    def __init__(self, master, config, project_model):
        tk.Toplevel.__init__(self, master)
        self.TkdndVersion = TkinterDnD._require(self)
        
        self.config_data = config
        self.project_model = project_model
        self.setup_audio_generator_window()
        self.setup_timeline_window()
        self.create_components()
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.timeline_controller = None

    def setup_audio_generator_window(self):
        self.base_title = "Audio Creator"
        self.update_title()
        self.geometry(self.config_data['audio_generator_gui']['window_size'])
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

    def setup_timeline_window(self):
        #Implement later
        pass

    def update_title(self, project_name=None):
        if project_name:
            self.title(f"{self.base_title} - {project_name}")
        else:
            self.title(self.base_title)

    def hide(self):
        self.withdraw()

    def show(self):
        self.deiconify()

    def on_close(self):
        self.withdraw()  # Hide the main window instead of destroying it

    def set_timeline_controller(self, timeline_controller):
        self.timeline_controller = timeline_controller
        self.audio_generator_view.set_timeline_command(self.timeline_controller.show)

    def get_audio_generator_view(self):
        return self.audio_generator_view

    def get_script_editor_view(self):
        return self.script_editor_view

    def set_new_project_callback(self, callback):
        self.new_project_callback = callback

    def set_open_project_callback(self, callback):
        self.open_project_callback = callback

    def set_save_project_callback(self, callback):
        self.save_project_callback = callback
    
    def create_project_frame(self):
        project_frame = ctk.CTkFrame(self)
        project_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        
        ctk.CTkLabel(project_frame, text="Current Project:").pack(side="left", padx=(0, 5))
        self.current_project_var = ctk.StringVar(value="No project open")
        ctk.CTkLabel(project_frame, textvariable=self.current_project_var).pack(side="left")

    def new_project(self):
        if hasattr(self, 'new_project_callback'):
            self.new_project_callback()

    def open_project(self):
        initial_dir = self.config_data['projects']['base_dir']
        project_dir = filedialog.askdirectory(
            title="Select Project Directory",
            initialdir=initial_dir
        )
        if project_dir:
            project_name = os.path.basename(project_dir)
            self.open_project_callback(project_name)

    def save_project(self):
        if hasattr(self, 'save_project_callback'):
            self.save_project_callback()

    def update_current_project(self, project_name):
        self.update_title(project_name)
        if hasattr(self, 'timeline_controller'):
            self.timeline_controller.update_project_name(project_name)
            
    def show_info(self, title, message):
        messagebox.showinfo(title, message)

    def show_error(self, title, message):
        messagebox.showerror(title, message)

    def show_warning(self, title, message):
        messagebox.showwarning(title, message)

    def import_audio(self):
        if self.import_audio_callback:
            self.import_audio_callback()

    def set_import_audio_callback(self, callback):
        self.import_audio_callback = callback
        
    def set_initial_sash_position(self):
        width = self.paned_window.winfo_width()
        self.paned_window.sash_place(0, width // 2, 0)

    def create_components(self):
        self.create_menu()
        self.create_main_content()
        self.create_status_bar()

    def create_menu(self):
        self.menu = tk.Menu(self)
        self.configure(menu=self.menu)

        file_menu = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Project", command=self.new_project)
        file_menu.add_command(label="Open Project", command=self.open_project)
        file_menu.add_command(label="Save Project", command=self.save_project)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)

        edit_menu = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Import Audio", command=self.import_audio)

        self.window_menu = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="Window", menu=self.window_menu)
        self.window_menu.add_command(label="Show/Hide Timeline", command=self.toggle_timeline)
        self.window_menu.add_command(label="Show/Hide Audio Creator", command=self.toggle_visibility)

    def create_main_content(self):
        self.paned_window = tk.PanedWindow(self, orient=tk.HORIZONTAL, sashwidth=10, sashrelief=tk.RAISED, bg='#3E3E3E')
        self.paned_window.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

        self.script_editor_view = ScriptEditorView(self.paned_window, self.config_data)
        self.paned_window.add(self.script_editor_view, stretch="always")

        self.audio_generator_view = AudioGeneratorView(self.paned_window, self.config_data, self.project_model)
        self.paned_window.add(self.audio_generator_view, stretch="always")

        self.paned_window.after(10, self.set_initial_sash_position)

    def create_status_bar(self):
        self.status_var = tk.StringVar()
        self.status_bar = ctk.CTkLabel(self, textvariable=self.status_var, anchor="w")
        self.status_bar.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
        
    def create_timeline_button(self):
        timeline_button = ctk.CTkButton(self, text="Open Timeline", command=self.open_timeline)
        timeline_button.grid(row=3, column=0, pady=10)

    def open_timeline(self):
        self.timeline_controller.show()

    def toggle_timeline(self):
        if self.timeline_controller:
            self.timeline_controller.toggle_visibility()

    def toggle_visibility(self):
        if self.winfo_viewable():
            self.hide()
        else:
            self.show()

    def update_analysis_results(self, analyzed_script, suggested_voices, element_counts, estimated_duration, categorized_sentences):
        self.script_editor_view.update_analysis_results(
            analyzed_script, suggested_voices, element_counts, estimated_duration, categorized_sentences
        )

    def update_status(self, message):
        if hasattr(self, 'status_var'):
            self.status_var.set(message)

    def run(self):
        self.mainloop()

    def ask_string(self, title, prompt):
        return simpledialog.askstring(title, prompt, parent=self)