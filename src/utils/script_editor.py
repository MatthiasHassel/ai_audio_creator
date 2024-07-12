import customtkinter as ctk
import tkinter as tk
from tkinter import font as tkfont
import re

class ScriptEditor(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.master = master
        self.is_visible = False
        self.width = 400  # Default width of the editor panel
        self.min_width = 200
        self.max_width = 800

        self.create_widgets()
        self.create_formatting_buttons()

    def create_widgets(self):
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Title
        self.title_label = ctk.CTkLabel(self, text="Script Editor", font=("Arial", 16, "bold"))
        self.title_label.grid(row=0, column=0, pady=(10, 5), sticky="ew")

        # Formatting toolbar
        self.formatting_frame = ctk.CTkFrame(self)
        self.formatting_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)

        # Text editor
        self.text_editor = tk.Text(self, wrap=tk.WORD, undo=True)
        self.text_editor.grid(row=2, column=0, sticky="nsew", padx=(10, 0), pady=(5, 10))

        # Scrollbar
        self.scrollbar = ctk.CTkScrollbar(self, command=self.text_editor.yview)
        self.scrollbar.grid(row=2, column=1, sticky="ns", padx=(0, 10), pady=(5, 10))
        self.text_editor.config(yscrollcommand=self.scrollbar.set)

        # Bind key events for formatting
        self.text_editor.bind("<Control-b>", lambda event: self.toggle_format('bold'))
        self.text_editor.bind("<Control-i>", lambda event: self.toggle_format('italic'))
        self.text_editor.bind("<Control-u>", lambda event: self.toggle_format('underline'))

    def create_formatting_buttons(self):
        bold_button = ctk.CTkButton(self.formatting_frame, text="B", width=30, command=lambda: self.toggle_format('bold'))
        bold_button.pack(side=tk.LEFT, padx=2)

        italic_button = ctk.CTkButton(self.formatting_frame, text="I", width=30, command=lambda: self.toggle_format('italic'))
        italic_button.pack(side=tk.LEFT, padx=2)

        underline_button = ctk.CTkButton(self.formatting_frame, text="U", width=30, command=lambda: self.toggle_format('underline'))
        underline_button.pack(side=tk.LEFT, padx=2)

        dialogue_button = ctk.CTkButton(self.formatting_frame, text="Dialogue", width=60, command=self.mark_dialogue)
        dialogue_button.pack(side=tk.LEFT, padx=2)

        scene_break_button = ctk.CTkButton(self.formatting_frame, text="Scene Break", width=80, command=self.insert_scene_break)
        scene_break_button.pack(side=tk.LEFT, padx=2)

    def toggle_format(self, format_type):
        current_tags = self.text_editor.tag_names("sel.first")
        if format_type in current_tags:
            self.text_editor.tag_remove(format_type, "sel.first", "sel.last")
        else:
            self.text_editor.tag_add(format_type, "sel.first", "sel.last")

        if format_type == 'bold':
            self.text_editor.tag_configure('bold', font=tkfont.Font(weight='bold'))
        elif format_type == 'italic':
            self.text_editor.tag_configure('italic', font=tkfont.Font(slant='italic'))
        elif format_type == 'underline':
            self.text_editor.tag_configure('underline', underline=1)

    def mark_dialogue(self):
        self.text_editor.insert(tk.INSERT, '"')
        self.text_editor.insert(tk.INSERT, '"')
        self.text_editor.mark_set(tk.INSERT, "insert-1c")

    def insert_scene_break(self):
        self.text_editor.insert(tk.INSERT, "\n\n***\n\n")

    def toggle_visibility(self):
        self.is_visible = not self.is_visible

    def get_content(self):
        return self.text_editor.get("1.0", tk.END)

    def set_content(self, content):
        self.text_editor.delete("1.0", tk.END)
        self.text_editor.insert(tk.END, content)

    def analyze_script(self):
        content = self.get_content()
        segments = self.segment_script(content)
        return segments

    def segment_script(self, content):
        segments = []
        lines = content.split('\n')
        current_segment = {'type': 'narration', 'content': ''}

        for line in lines:
            if line.strip() == '***':
                if current_segment['content']:
                    segments.append(current_segment)
                segments.append({'type': 'scene_break', 'content': '***'})
                current_segment = {'type': 'narration', 'content': ''}
            elif line.strip().startswith('"') and line.strip().endswith('"'):
                if current_segment['content']:
                    segments.append(current_segment)
                segments.append({'type': 'dialogue', 'content': line.strip()})
                current_segment = {'type': 'narration', 'content': ''}
            else:
                current_segment['content'] += line + '\n'

        if current_segment['content']:
            segments.append(current_segment)

        return segments

    def generate_audio_for_segment(self, segment):
        # This method would integrate with your existing audio generation services
        if segment['type'] == 'dialogue':
            # Use speech generation service
            pass
        elif segment['type'] == 'narration':
            # Use speech generation service with different settings
            pass
        elif segment['type'] == 'scene_break':
            # Use music generation service
            pass

    def generate_full_audiobook(self):
        segments = self.analyze_script()
        audio_segments = []
        for segment in segments:
            audio = self.generate_audio_for_segment(segment)
            audio_segments.append(audio)
        # Combine audio segments and return final audiobook
        return audio_segments