import tkinter as tk
from tkinter import filedialog
import os

class ScriptEditorController:
    def __init__(self, model, view, config):
        self.model = model
        self.view = view
        self.config = config
        self.analysis_callback = None
        self.setup_view_commands()

    def setup_view_commands(self):
        self.view.bold_button.configure(command=lambda: self.format_text('bold'))
        self.view.italic_button.configure(command=lambda: self.format_text('italic'))
        self.view.underline_button.configure(command=lambda: self.format_text('underline'))
        self.view.save_button.configure(command=self.save_script)
        self.view.load_button.configure(command=self.load_script)

        # Bind the text change event to trigger analysis
        self.view.text_area.bind('<<Modified>>', self.on_text_changed)

    def set_analysis_callback(self, callback):
        self.analysis_callback = callback

    def on_text_changed(self, event):
        self.view.text_area.edit_modified(False)  # Reset the modified flag
        if self.analysis_callback:
            self.analysis_callback()

    def format_text(self, style):
        self.view.format_text(style)

    def save_script(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".txt",
                                                 filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if file_path:
            with open(file_path, 'w') as file:
                file.write(self.get_script_text())
            self.view.update_status(f"Script saved to {file_path}")

    def load_script(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if file_path:
            with open(file_path, 'r') as file:
                self.set_script_text(file.read())
            self.view.update_status(f"Script loaded from {file_path}")

    def get_script_text(self):
        return self.view.get_text()

    def set_script_text(self, text):
        self.model.set_content(text)  # Update the model
        self.view.set_text(text)  # Update the view
        if self.analysis_callback:
            self.analysis_callback()  # Trigger analysis for the new text

    def analyze_script(self):
        if self.analysis_callback:
            self.analysis_callback()