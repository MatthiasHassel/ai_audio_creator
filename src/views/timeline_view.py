import customtkinter as ctk
import tkinter as tk

class TimelineView(ctk.CTkToplevel):
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.base_title = "Audio Timeline"
        self.update_title()
        self.geometry("800x600")
        self.protocol("WM_DELETE_WINDOW", self.withdraw)  # Hide instead of destroy on close
        self.tracks = []
        self.create_widgets()

    def update_title(self, project_name=None):
        if project_name:
            self.title(f"{self.base_title} - {project_name}")
        else:
            self.title(self.base_title)

    def create_widgets(self):
        self.create_toolbar()
        self.create_track_list()
        self.create_timeline()

    def create_toolbar(self):
        toolbar = ctk.CTkFrame(self)
        toolbar.pack(fill=tk.X, padx=5, pady=5)

        self.add_track_button = ctk.CTkButton(toolbar, text="Add Track")
        self.add_track_button.pack(side=tk.LEFT, padx=5)

        self.play_button = ctk.CTkButton(toolbar, text="Play")
        self.play_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = ctk.CTkButton(toolbar, text="Stop")
        self.stop_button.pack(side=tk.LEFT, padx=5)

        self.toggle_audio_creator_button = ctk.CTkButton(toolbar, text="Show Audio Creator")
        self.toggle_audio_creator_button.pack(side=tk.RIGHT, padx=5)

    def create_track_list(self):
        self.track_list = ctk.CTkFrame(self)
        self.track_list.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)

    def create_timeline(self):
        self.timeline = ctk.CTkCanvas(self)
        self.timeline.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.timeline.bind("<Button-1>", self.on_timeline_click)
        self.timeline.bind("<B1-Motion>", self.on_timeline_drag)

    def add_track(self, name):
        track_frame = ctk.CTkFrame(self.track_list)
        track_frame.pack(fill=tk.X, padx=5, pady=2)

        track_label = ctk.CTkLabel(track_frame, text=name)
        track_label.pack(side=tk.LEFT)

        self.tracks.append({"name": name, "frame": track_frame, "clips": []})

    def add_clip_to_track(self, track_name, clip_data):
        for track in self.tracks:
            if track["name"] == track_name:
                track["clips"].append(clip_data)
                self.draw_clip(track, clip_data)
                break

    def draw_clip(self, track, clip_data):
        x1 = clip_data["start_time"] * 10  # Scale factor for visualization
        x2 = clip_data["end_time"] * 10
        y1 = self.tracks.index(track) * 50  # Adjust based on your track height
        y2 = y1 + 40

        self.timeline.create_rectangle(x1, y1, x2, y2, fill=clip_data["color"], tags="clip")
        self.timeline.create_text((x1 + x2) / 2, (y1 + y2) / 2, text=clip_data["name"], tags="clip")

    def clear_tracks(self):
        for track in self.tracks:
            track["frame"].destroy()
        self.tracks.clear()
        self.clear_timeline()

    def redraw_timeline(self):
        self.clear_timeline()
        for track_index, track in enumerate(self.tracks):
            for clip in track["clips"]:
                self.draw_clip(track_index, clip)
                
    def clear_timeline(self):
        self.timeline.delete("all")

    def on_timeline_click(self, event):
        print(f"Timeline clicked at {event.x}, {event.y}")
        # Implement click handling (e.g., selecting a clip)

    def on_timeline_drag(self, event):
        print(f"Timeline dragged to {event.x}, {event.y}")
        # Implement drag handling (e.g., moving a clip)

    def play_timeline(self):
        print("Playing timeline")
        # Implement playback logic here

    def stop_timeline(self):
        print("Stopping timeline")
        # Implement stop logic here

    def set_toggle_audio_creator_command(self, command):
        self.toggle_audio_creator_button.configure(command=command)