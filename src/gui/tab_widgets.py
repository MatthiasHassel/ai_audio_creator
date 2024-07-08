import customtkinter as ctk

class TabWidgets:
    def __init__(self, master, config):
        self.master = master
        self.config = config
        self.widgets = self.create_widgets()

    def create_widgets(self):
        return {
            'Music': self.create_music_widgets(),
            'SFX': self.create_sfx_widgets(),
            'Speech': self.create_speech_widgets()
        }

    def create_music_widgets(self):
        return {
            'instrumental_label': ctk.CTkLabel(self.master, text="Instrumental:"),
            'instrumental_checkbox': ctk.CTkCheckBox(self.master, text="", variable=self.config['instrumental_var'])
        }

    def create_sfx_widgets(self):
        return {
            'duration_label': ctk.CTkLabel(self.master, text="Duration (0 = automatic, 0.5-22s):"),
            'duration_entry': ctk.CTkEntry(self.master, textvariable=self.config['duration_var'], width=100)
        }

    def create_speech_widgets(self):
        return {
            'voice_label': ctk.CTkLabel(self.master, text="Select Voice:"),
            'voice_dropdown': ctk.CTkOptionMenu(self.master, variable=self.config['selected_voice'], width=200)
        }

    def grid_widgets(self, tab):
        widgets = self.widgets[tab]
        if tab == "Music":
            widgets['instrumental_label'].grid(row=2, column=0, pady=5, sticky="e", padx=(0, 10))
            widgets['instrumental_checkbox'].grid(row=2, column=1, pady=5, sticky="e")
        elif tab == "SFX":
            widgets['duration_label'].grid(row=2, column=0, pady=5, sticky="e", padx=(0, 10))
            widgets['duration_entry'].grid(row=2, column=1, pady=5, sticky="e")
        elif tab == "Speech":
            widgets['voice_label'].grid(row=2, column=0, pady=5, sticky="e", padx=(0, 10))
            widgets['voice_dropdown'].grid(row=2, column=1, pady=5, sticky="e")
        
        # Add padding to the right
        ctk.CTkLabel(self.master, text="").grid(row=2, column=2, padx=(0, 10))

    def hide_all_widgets(self):
        for widgets in self.widgets.values():
            for widget in widgets.values():
                widget.grid_remove()

    def get_widget(self, tab, widget_name):
        return self.widgets[tab][widget_name]

    def configure_widget(self, tab, widget_name, **kwargs):
        widget = self.get_widget(tab, widget_name)
        widget.configure(**kwargs)