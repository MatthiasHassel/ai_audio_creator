import customtkinter as ctk

class TabWidgets(ctk.CTkFrame):
    def __init__(self, master, config):
        super().__init__(master)
        self.config = config
        self.widgets = self.create_widgets()

    def create_widgets(self):
        return {
            'Music': self.create_music_widgets(),
            'SFX': self.create_sfx_widgets(),
            'Speech': self.create_speech_widgets()
        }

    def create_music_widgets(self):
        frame = ctk.CTkFrame(self)
        label = ctk.CTkLabel(frame, text="Instrumental:")
        checkbox = ctk.CTkCheckBox(frame, text="", variable=self.config['instrumental_var'])
        label.pack(side="left", padx=(0, 5))
        checkbox.pack(side="left")
        return frame

    def create_sfx_widgets(self):
        frame = ctk.CTkFrame(self)
        label = ctk.CTkLabel(frame, text="Duration (0 = automatic, 0.5-22s):")
        entry = ctk.CTkEntry(frame, textvariable=self.config['duration_var'], width=100)
        label.pack(side="left", padx=(0, 5))
        entry.pack(side="left")
        return frame

    def create_speech_widgets(self):
        frame = ctk.CTkFrame(self)
        label = ctk.CTkLabel(frame, text="Select Voice:")
        dropdown = ctk.CTkOptionMenu(frame, variable=self.config['selected_voice'], width=200)
        label.pack(side="left", padx=(0, 5))
        dropdown.pack(side="left")
        return frame

    def update_widgets(self, tab):
        for widget in self.winfo_children():
            widget.pack_forget()
        self.widgets[tab].pack(fill="x", expand=True)

    def configure_widget(self, tab, widget_name, **kwargs):
        widget = self.widgets[tab].winfo_children()[1]  # Assumes label is first child, widget is second
        widget.configure(**kwargs)