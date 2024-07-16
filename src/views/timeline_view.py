import customtkinter as ctk
import tkinter as tk

class TimelineView(ctk.CTkToplevel):
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.base_title = "Audio Timeline"
        self.current_project = "Untitled Project"
        self.update_title()
        self.geometry("1000x600")
        self.protocol("WM_DELETE_WINDOW", self.withdraw)
        self.tracks = []
        self.selected_track = None
        self.track_height = 60
        self.seconds_per_pixel = 0.1
        self.create_widgets()
        self.bind("<Delete>", self.delete_selected_track)

    def update_title(self, project_name=None):
        if project_name:
            self.current_project = project_name
        self.title(f"{self.base_title} - {self.current_project}")

    def create_widgets(self):
        self.create_toolbar()
        self.create_main_content()

    def create_toolbar(self):
        toolbar = ctk.CTkFrame(self)
        toolbar.pack(fill=tk.X, padx=5, pady=5)

        self.add_track_button = ctk.CTkButton(toolbar, text="Add Track", command=self.add_track)
        self.add_track_button.pack(side=tk.LEFT, padx=5)

        self.play_button = ctk.CTkButton(toolbar, text="Play", command=self.play_timeline)
        self.play_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = ctk.CTkButton(toolbar, text="Stop", command=self.stop_timeline)
        self.stop_button.pack(side=tk.LEFT, padx=5)

        self.toggle_audio_creator_button = ctk.CTkButton(toolbar, text="Show Audio Creator")
        self.toggle_audio_creator_button.pack(side=tk.RIGHT, padx=5)

    def create_main_content(self):
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)

        self.track_label_frame = ctk.CTkFrame(self.main_frame, fg_color="gray20", width=200)
        self.track_label_frame.pack(side=tk.LEFT, fill=tk.Y)
        self.track_label_frame.pack_propagate(False)

        self.timeline_frame = ctk.CTkFrame(self.main_frame)
        self.timeline_frame.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

        self.create_track_labels()
        self.create_timeline()

    def create_track_labels(self):
        self.track_label_canvas = tk.Canvas(self.track_label_frame, bg="gray20", highlightthickness=0)
        self.track_label_canvas.pack(expand=True, fill=tk.BOTH)

    def create_timeline(self):
        self.timeline_canvas = tk.Canvas(self.timeline_frame, bg="gray30", highlightthickness=0)
        self.timeline_canvas.pack(expand=True, fill=tk.BOTH)
        self.timeline_canvas.bind("<Configure>", self.on_canvas_resize)

    def on_canvas_resize(self, event):
        self.draw_grid()
        self.update_track_labels()

    def draw_grid(self):
        self.timeline_canvas.delete("grid")
        width = self.timeline_canvas.winfo_width()
        height = self.timeline_canvas.winfo_height()
        
        # Draw vertical lines for seconds
        for x in range(0, width, int(1 / self.seconds_per_pixel)):
            self.timeline_canvas.create_line(x, 0, x, height, fill="gray50", tags="grid")
        
        # Draw horizontal lines for tracks
        for i in range(len(self.tracks) + 1):
            y = i * self.track_height
            self.timeline_canvas.create_line(0, y, width, y, fill="gray50", tags="grid")

    def update_track_labels(self):
        self.track_label_canvas.delete("all")
        for i, track in enumerate(self.tracks):
            y = i * self.track_height
            fill_color = "gray35" if track == self.selected_track else "gray25"
            self.track_label_canvas.create_rectangle(0, y, 200, y + self.track_height, fill=fill_color, tags=f"track_{i}")
            self.track_label_canvas.create_text(10, y + self.track_height // 2, text=track["name"], anchor="w", fill="white", tags=f"track_{i}")
            
            # Bind events to the track label area
            self.track_label_canvas.tag_bind(f"track_{i}", "<Button-1>", lambda e, t=track: self.select_track(t))
            self.track_label_canvas.tag_bind(f"track_{i}", "<Double-Button-1>", lambda e, t=track: self.start_rename_track(t))
            self.track_label_canvas.tag_bind(f"track_{i}", "<Button-3>", lambda e, t=track: self.show_track_context_menu(e, t))

    def add_track(self, track_name=None):
        if track_name is None:
            track_name = f"Track {len(self.tracks) + 1}"
        track_data = {"name": track_name, "clips": []}
        self.tracks.append(track_data)
        self.update_track_labels()
        self.draw_grid()

    def select_track(self, track):
        if self.selected_track:
            self.timeline_canvas.delete("track_highlight")
        self.selected_track = track
        self.update_track_labels()  # This will update the label colors
        
        # Highlight the entire row in the timeline
        track_index = self.tracks.index(track)
        y1 = track_index * self.track_height
        y2 = y1 + self.track_height
        width = self.timeline_canvas.winfo_width()
        self.timeline_canvas.create_rectangle(0, y1, width, y2, fill="gray40", outline="", tags="track_highlight")
        self.timeline_canvas.tag_lower("track_highlight", "grid")

    def create_track(self, name):
        track_frame = ctk.CTkFrame(self.track_list, fg_color="gray25", height=30)
        track_frame.pack(fill=tk.X, padx=2, pady=(0, 2))
        track_frame.pack_propagate(False)

        track_label = ctk.CTkLabel(track_frame, text=name, anchor="w", fg_color="gray25")
        track_label.pack(side=tk.LEFT, padx=5)

        track_data = {"name": name, "frame": track_frame, "label": track_label, "clips": []}
        self.tracks.append(track_data)

        track_frame.bind("<Button-1>", lambda e, t=track_data: self.select_track(t))
        track_label.bind("<Double-Button-1>", lambda e, t=track_data: self.start_rename_track(t))
        track_frame.bind("<Button-3>", lambda e, t=track_data: self.show_track_context_menu(e, t))

    def start_rename_track(self, track):
        track_index = self.tracks.index(track)
        y = track_index * self.track_height
        entry = ctk.CTkEntry(self.track_label_canvas, fg_color="gray35", text_color="white", border_width=0)
        entry.insert(0, track["name"])
        entry_window = self.track_label_canvas.create_window(10, y + self.track_height // 2, anchor="w", window=entry, width=180)
        entry.focus_set()
        entry.bind("<Return>", lambda e, t=track, ew=entry_window: self.finish_rename_track(t, e.widget, ew))
        entry.bind("<FocusOut>", lambda e, t=track, ew=entry_window: self.finish_rename_track(t, e.widget, ew))

    def finish_rename_track(self, track, entry, entry_window):
        new_name = entry.get()
        self.track_label_canvas.delete(entry_window)
        if new_name != track["name"]:
            track["name"] = new_name
            self.update_track_labels()
            if self.rename_track_callback:
                self.rename_track_callback(track, new_name)


    def show_track_context_menu(self, event, track):
        context_menu = tk.Menu(self, tearoff=0)
        context_menu.add_command(label="Rename", command=lambda: self.start_rename_track(track))
        context_menu.add_command(label="Delete", command=lambda: self.delete_track(track))
        context_menu.tk_popup(event.x_root, event.y_root)

    def delete_track(self, track):
        if track in self.tracks:
            self.tracks.remove(track)
            if self.selected_track == track:
                self.selected_track = None
            self.update_track_labels()
            self.draw_grid()
            if self.delete_track_callback:
                self.delete_track_callback(track)

    def delete_selected_track(self, event=None):
        if self.selected_track:
            self.delete_track(self.selected_track)

    def clear_tracks(self):
        self.tracks.clear()
        self.selected_track = None
        self.update_track_labels()
        self.draw_grid()

    def set_rename_track_callback(self, callback):
        self.rename_track_callback = callback

    def set_delete_track_callback(self, callback):
        self.delete_track_callback = callback

    def play_timeline(self):
        print("Playing timeline")
        # Implement playback logic here

    def stop_timeline(self):
        print("Stopping timeline")
        # Implement stop logic here