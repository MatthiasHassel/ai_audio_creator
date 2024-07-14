import tkinter as tk
from tkinter import filedialog
import os

class ScriptEditorController:
    def __init__(self, model, view, config):
        self.model = model
        self.view = view
        self.config = config
        self.setup_view_commands()

    def setup_view_commands(self):
        self.view.bold_button.configure(command=lambda: self.format_text('bold'))
        self.view.italic_button.configure(command=lambda: self.format_text('italic'))
        self.view.underline_button.configure(command=lambda: self.format_text('underline'))
        self.view.save_button.configure(command=self.save_script)
        self.view.load_button.configure(command=self.load_script)

    def format_text(self, style):
        try:
            current_tags = self.view.text_area.tag_names("sel.first")
            if style in current_tags:
                self.view.text_area.tag_remove(style, "sel.first", "sel.last")
            else:
                self.view.text_area.tag_add(style, "sel.first", "sel.last")

            self.view.text_area.tag_configure('bold', font=('TkDefaultFont', 10, 'bold'))
            self.view.text_area.tag_configure('italic', font=('TkDefaultFont', 10, 'italic'))
            self.view.text_area.tag_configure('underline', underline=1)
        except tk.TclError:
            # No text selected
            pass

    def save_script(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".txt",
                                                 filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if file_path:
            with open(file_path, 'w') as file:
                file.write(self.view.get_text())
            self.view.update_status(f"Script saved to {file_path}")

    def load_script(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if file_path:
            with open(file_path, 'r') as file:
                self.view.set_text(file.read())
            self.view.update_status(f"Script loaded from {file_path}")

    def analyze_script(self):
        # This method will be implemented later for script analysis
        pass