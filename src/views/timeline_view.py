import customtkinter as ctk
import tkinter as tk
from tkinter import ttk

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
        self.base_track_height = 60
        self.track_height = self.base_track_height
        self.min_track_height = 30  # Adjust this value to set the minimum track height
        self.max_track_height = 200  # Adjust this value to set the maximum track height
        self.seconds_per_pixel = 0.1
        self.x_zoom = 1.0
        self.y_zoom = 1.0
        self.min_x_zoom = 0.1  # Adjust this value to change the minimum x-axis zoom
        self.max_x_zoom = 5.0  # Adjust this value to change the maximum x-axis zoom
        
        self.option_key_pressed = False
        
        self.create_widgets()
        self.bind("<Delete>", self.delete_selected_track)
        self.bind("<KeyPress-Alt_L>", self.option_key_press)
        self.bind("<KeyRelease-Alt_L>", self.option_key_release)
        self.bind_all("<MouseWheel>", self.on_mouse_scroll)
        self.bind_all("<Shift-MouseWheel>", self.on_shift_mouse_scroll)

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

        ttk.Label(toolbar, text="   ").pack(side=tk.LEFT)

        self.x_zoom_slider = ttk.Scale(toolbar, from_=self.min_x_zoom, to=self.max_x_zoom, orient=tk.HORIZONTAL, 
                                       command=self.update_x_zoom, length=100)
        self.x_zoom_slider.set(1.0)
        self.x_zoom_slider.pack(side=tk.LEFT, padx=(0, 5))

        min_y_zoom = self.min_track_height / self.base_track_height
        max_y_zoom = self.max_track_height / self.base_track_height
        self.y_zoom_slider = ttk.Scale(toolbar, from_=min_y_zoom, to=max_y_zoom, orient=tk.VERTICAL, 
                                       command=self.update_y_zoom, length=50)
        self.y_zoom_slider.set(1.0)
        self.y_zoom_slider.pack(side=tk.LEFT)
        self.toggle_audio_creator_button = ctk.CTkButton(toolbar, text="Toggle Audio Creator")
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

    def redraw_timeline(self):
        if hasattr(self, 'track_label_canvas'):
            self.update_track_labels()
            self.draw_grid()

    def on_canvas_resize(self, event):
        self.draw_grid()
        self.update_track_labels()

    def draw_grid(self):
        self.timeline_canvas.delete("grid")
        width = self.timeline_canvas.winfo_width()
        height = self.timeline_canvas.winfo_height()
        
        for x in range(0, width, int(1 / (self.seconds_per_pixel * self.x_zoom))):
            self.timeline_canvas.create_line(x, 0, x, height, fill="gray50", tags="grid")
        
        for i in range(len(self.tracks) + 1):
            y = i * self.track_height
            self.timeline_canvas.create_line(0, y, width, y, fill="gray50", tags="grid")

    def update_track_labels(self):
        if hasattr(self, 'track_label_canvas'):
            self.track_label_canvas.delete("all")
            for i, track in enumerate(self.tracks):
                y = i * self.track_height
                fill_color = "gray35" if track == self.selected_track else "gray25"
                self.track_label_canvas.create_rectangle(0, y, 200, y + self.track_height, fill=fill_color, tags=f"track_{i}")
                self.track_label_canvas.create_text(10, y + self.track_height // 2, text=track["name"], anchor="w", fill="white", tags=f"track_{i}")
                
                self.track_label_canvas.tag_bind(f"track_{i}", "<Button-1>", lambda e, t=track: self.select_track(t))
                self.track_label_canvas.tag_bind(f"track_{i}", "<Double-Button-1>", lambda e, t=track: self.start_rename_track(t))
                self.track_label_canvas.tag_bind(f"track_{i}", "<Button-2>", lambda e, t=track: self.show_track_context_menu(e, t))

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
        self.update_track_labels()
        
        track_index = self.tracks.index(track)
        y1 = track_index * self.track_height
        y2 = y1 + self.track_height
        width = self.timeline_canvas.winfo_width()
        self.timeline_canvas.create_rectangle(0, y1, width, y2, fill="gray40", outline="", tags="track_highlight")
        self.timeline_canvas.tag_lower("track_highlight", "grid")

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
            if hasattr(self, 'rename_track_callback'):
                self.rename_track_callback(track, new_name)
            self.update_track_labels()

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
            if hasattr(self, 'delete_track_callback'):
                self.delete_track_callback(track)

    def delete_selected_track(self, event=None):
        if self.selected_track:
            self.delete_track(self.selected_track)

    def update_tracks(self, new_tracks):
        self.tracks = new_tracks
        self.update_track_labels()
        self.draw_grid()

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

    def stop_timeline(self):
        print("Stopping timeline")

    def option_key_press(self, event):
        self.option_key_pressed = True

    def option_key_release(self, event):
        self.option_key_pressed = False
    
    def on_mouse_scroll(self, event):
        if self.option_key_pressed:
            if event.delta > 0:
                self.zoom_y(1.1)
            else:
                self.zoom_y(0.9)

    def on_shift_mouse_scroll(self, event):
        if self.option_key_pressed:
            if event.delta > 0:
                self.zoom_x(1.1)
            else:
                self.zoom_x(0.9)

    def zoom_x(self, factor):
        new_zoom = self.x_zoom * factor
        new_zoom = max(self.min_x_zoom, min(new_zoom, self.max_x_zoom))
        self.x_zoom_slider.set(new_zoom)

    def zoom_y(self, factor):
        new_zoom = self.y_zoom * factor
        new_track_height = self.base_track_height * new_zoom
        if self.min_track_height <= new_track_height <= self.max_track_height:
            self.y_zoom_slider.set(new_zoom)

    def update_x_zoom(self, value):
        self.x_zoom = float(value)
        self.seconds_per_pixel = 0.1 / self.x_zoom
        self.redraw_timeline()

    def update_y_zoom(self, value):
        self.y_zoom = float(value)
        self.track_height = self.base_track_height * self.y_zoom
        self.redraw_timeline()

    def update_title(self, project_name=None):
        if project_name:
            self.current_project = project_name
        self.title(f"{self.base_title} - {self.current_project}")

    def set_toggle_audio_creator_command(self, command):
        self.toggle_audio_creator_button.configure(command=command)