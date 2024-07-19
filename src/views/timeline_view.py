# timeline_view.py

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD
from utils.audio_clip import AudioClip
from utils.audio_visualizer import AudioVisualizer
import logging
import os 
import time

class TimelineView(ctk.CTkToplevel, TkinterDnD.DnDWrapper):
    def __init__(self, master, project_model, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.TkdndVersion = TkinterDnD._require(self)
        
        self.project_model = project_model
        self.controller = None
        self.base_title = "Audio Timeline"
        self.current_project = "Untitled Project"
        self.update_title()
        self.geometry("1000x600")
        self.protocol("WM_DELETE_WINDOW", self.withdraw)
        
        # Initialize variables
        self.tracks = []
        self.selected_track = None
        self.base_track_height = 60
        self.track_height = self.base_track_height
        self.min_track_height = 30
        self.max_track_height = 200
        self.base_seconds_per_pixel = 0.01  # 100 pixels = 1 second at default zoom
        self.seconds_per_pixel = self.base_seconds_per_pixel
        self.x_zoom = 1.0
        self.y_zoom = 1.0
        self.min_x_zoom = 0.1
        self.max_x_zoom = 5.0
        self.option_key_pressed = False
        self.waveform_images = {}

        self.track_label_canvas = None
        self.timeline_canvas = None
        self.playhead_line = None
        self.after_id = None
        self.start_time = 0
        self.is_playing = False
        self.playhead_position = 0

        self.create_widgets()
        
        # Set up bindings
        self.bind("<Delete>", self.remove_selected_track)
        self.bind("<KeyPress-Alt_L>", self.option_key_press)
        self.bind("<KeyRelease-Alt_L>", self.option_key_release)
        self.bind_all("<MouseWheel>", self.on_mouse_scroll)
        self.bind_all("<Shift-MouseWheel>", self.on_shift_mouse_scroll)
        self.timeline_canvas.bind("<Button-1>", self.on_canvas_click)

    def set_controller(self, controller):
        self.controller = controller

    def create_widgets(self):
        self.create_toolbar()
        self.create_main_content()
        self.create_timeline()

    def create_toolbar(self):
        toolbar = ctk.CTkFrame(self)
        toolbar.pack(fill=tk.X, padx=5, pady=5)

        self.add_track_button = ctk.CTkButton(toolbar, text="Add Track", command=self.add_track)
        self.add_track_button.pack(side=tk.LEFT, padx=5)

        self.play_button = ctk.CTkButton(toolbar, text="Play", command=self.play_timeline)
        self.play_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = ctk.CTkButton(toolbar, text="Stop", command=self.stop_timeline)
        self.stop_button.pack(side=tk.LEFT, padx=5)

        self.restart_button = ctk.CTkButton(toolbar, text="Restart", command=self.restart_timeline)
        self.restart_button.pack(side=tk.LEFT, padx=5)

        self.toggle_audio_creator_button = ctk.CTkButton(toolbar, text="Show Audio Creator")
        self.toggle_audio_creator_button.pack(side=tk.RIGHT, padx=5)

        ttk.Label(toolbar, text="   ").pack(side=tk.LEFT)

        self.x_zoom_slider = ttk.Scale(toolbar, from_=self.min_x_zoom, to=self.max_x_zoom, orient=tk.HORIZONTAL, 
                                       command=self.update_x_zoom, length=100)
        self.x_zoom_slider.set(1.0)
        self.x_zoom_slider.pack(side=tk.LEFT, padx=(0, 5))

        self.y_zoom_slider = ttk.Scale(toolbar, from_=self.min_track_height/self.base_track_height, 
                                       to=self.max_track_height/self.base_track_height, 
                                       orient=tk.VERTICAL, command=self.update_y_zoom, length=50)
        self.y_zoom_slider.set(1.0)
        self.y_zoom_slider.pack(side=tk.LEFT)

    def create_main_content(self):
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)

        self.track_label_frame = ctk.CTkFrame(self.main_frame, width=200)
        self.track_label_frame.pack(side=tk.LEFT, fill=tk.Y)
        self.track_label_frame.pack_propagate(False)

        self.timeline_frame = ctk.CTkFrame(self.main_frame)
        self.timeline_frame.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

        self.track_label_canvas = tk.Canvas(self.track_label_frame, bg="gray20", highlightthickness=0)
        self.track_label_canvas.pack(expand=True, fill=tk.BOTH)
        
    def create_timeline(self):
        self.timeline_canvas = tk.Canvas(self.timeline_frame, bg="gray30", highlightthickness=0)
        self.timeline_canvas.pack(expand=True, fill=tk.BOTH)
        self.timeline_canvas.bind("<Configure>", self.on_canvas_resize)
        self.timeline_canvas.bind("<Button-1>", self.on_canvas_click)
        
        self.timeline_canvas.drop_target_register(DND_FILES)
        self.timeline_canvas.dnd_bind('<<Drop>>', self.on_drop)

        self.after(100, self.initialize_playhead)

    def initialize_playhead(self):
        if self.timeline_canvas:
            self.draw_playhead(0)
        else:
            self.after(100, self.initialize_playhead)

    def redraw_timeline(self):
        if self.timeline_canvas:
            self.timeline_canvas.delete("all")
            self.draw_grid()
            self.draw_clips()
            if self.playhead_line:
                x = self.playhead_position * self.seconds_per_pixel * self.x_zoom
                self.draw_playhead(x)
        else:
            logging.warning("Timeline canvas is not initialized.")

    def set_toggle_audio_creator_command(self, command):
        self.toggle_audio_creator_button.configure(command=command)

    def on_canvas_resize(self, event):
        self.redraw_timeline()
        self.update_track_labels()

    def draw_grid(self):
        width = self.timeline_canvas.winfo_width()
        height = self.timeline_canvas.winfo_height()
        
        # Draw vertical lines (1 second apart at default zoom)
        seconds_per_line = max(1, round(100 * self.seconds_per_pixel))
        for x in range(0, width, int(seconds_per_line / self.seconds_per_pixel)):
            self.timeline_canvas.create_line(x, 0, x, height, fill="gray50", tags="grid")
        
        # Draw horizontal lines
        for i in range(len(self.tracks) + 1):
            y = i * self.track_height
            self.timeline_canvas.create_line(0, y, width, y, fill="gray50", tags="grid")

    def update_track_labels(self):
        if not self.track_label_canvas:
            return  # Exit if track_label_canvas doesn't exist
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
        self.redraw_timeline()

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

    def remove_track(self, track):
        if track in self.tracks:
            track_index = self.tracks.index(track)
            del self.tracks[track_index]
            self.update_track_labels()
            self.redraw_timeline()
            if self.remove_track_callback:
                self.remove_track_callback(track)

    def remove_selected_track(self, event=None):
        if self.selected_track:
            self.remove_track(self.selected_track)

    def show_track_context_menu(self, event, track):
        context_menu = tk.Menu(self, tearoff=0)
        context_menu.add_command(label="Rename", command=lambda: self.start_rename_track(track))
        context_menu.add_command(label="Remove", command=lambda: self.remove_track(track))
        context_menu.tk_popup(event.x_root, event.y_root)

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

    def set_remove_track_callback(self, callback):
        self.remove_track_callback = callback

    def play_timeline(self):
        if not self.is_playing:
            self.is_playing = True
            self.start_time = time.time() - self.playhead_position
            self.update_playhead()
            logging.info("Timeline playback started in view")
        self.play_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.restart_button.configure(state="normal")

    def stop_timeline(self):
        self.is_playing = False
        if self.after_id:
            self.after_cancel(self.after_id)
            self.after_id = None
        self.play_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.restart_button.configure(state="normal")

    def restart_timeline(self):
        self.stop_timeline()
        self.playhead_position = 0
        if self.controller:
            self.controller.set_playhead_position(0)
        self.draw_playhead(0)

    def update_playhead(self):
        if self.is_playing:
            current_time = time.time() - self.start_time
            x = current_time / self.seconds_per_pixel
            self.playhead_position = current_time
            self.draw_playhead(x)
            logging.info(f"Playhead updated: time={current_time}, x={x}")
            self.after_id = self.after(50, self.update_playhead)  # Update every 50ms
        else:
            logging.info("Playhead update stopped")

    def draw_playhead(self, x):
        if self.timeline_canvas:
            if self.playhead_line:
                self.timeline_canvas.delete(self.playhead_line)
            height = self.timeline_canvas.winfo_height()
            if height > 0:
                self.playhead_line = self.timeline_canvas.create_line(x, 0, x, height, fill="red", width=2)
                # Ensure the playhead is visible by scrolling the canvas if necessary
                self.timeline_canvas.xview_moveto(max(0, (x - self.timeline_canvas.winfo_width() / 2) / self.timeline_canvas.winfo_width()))
            else:
                self.after(100, lambda: self.draw_playhead(x))
        else:
            self.after(100, lambda: self.draw_playhead(x))

    def on_canvas_click(self, event):
        if self.controller:
            x = self.timeline_canvas.canvasx(event.x)
            self.playhead_position = x * self.seconds_per_pixel
            self.controller.set_playhead_position(self.playhead_position)
            self.draw_playhead(x)
            if self.is_playing:
                self.start_time = time.time() - self.playhead_position

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
        self.seconds_per_pixel = self.base_seconds_per_pixel / self.x_zoom
        # Adjust playhead position after zooming
        if self.playhead_line:
            x = self.playhead_position / self.seconds_per_pixel
            self.draw_playhead(x)
        self.redraw_timeline()

    def update_y_zoom(self, value):
        self.y_zoom = float(value)
        self.track_height = max(self.min_track_height, min(self.base_track_height * self.y_zoom, self.max_track_height))
        self.redraw_timeline()
        if self.track_label_canvas:
            self.update_track_labels()


    def update_title(self, project_name=None):
        if project_name:
            self.current_project = project_name
        self.title(f"{self.base_title} - {self.current_project}")

    def set_toggle_audio_creator_command(self, command):
        self.toggle_audio_creator_button.configure(command=command)

    def on_drop(self, event):
        file_path = event.data
        if file_path.lower().endswith(('.mp3', '.wav')):
            try:
                # Import the audio file into the project
                new_file_path = self.project_model.import_audio_file(file_path)
                
                track_index = self.get_track_index_from_y(event.y)
                x_position = event.x / self.seconds_per_pixel
                self.add_audio_clip(new_file_path, track_index, x_position)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to import audio file: {str(e)}")
    
    def get_track_index_from_y(self, y):
        return int(y // self.track_height)

    def add_audio_clip(self, file_path, track_index, x_position):
        if track_index < len(self.tracks):
            clip = AudioClip(file_path, x_position)
            self.tracks[track_index]['clips'].append(clip)
            self.draw_clip(clip, track_index)
            if hasattr(self, 'add_clip_callback'):
                self.add_clip_callback(track_index, clip)

    def add_clip(self, clip, track_index):
            if track_index < len(self.tracks):
                self.tracks[track_index]['clips'].append(clip)
                self.draw_clip(clip, track_index)
                logging.info(f"Clip added to track {track_index} in view")
            else:
                logging.warning(f"Attempted to add clip to non-existent track {track_index}")

    def set_add_clip_callback(self, callback):
        self.add_clip_callback = callback

    def draw_clips(self):
        for i, track in enumerate(self.tracks):
            y = i * self.track_height
            for clip in track['clips']:
                self.draw_clip(clip, y)

    def draw_clip(self, clip, track_index):
        y = track_index * self.track_height
        x = clip.x * self.seconds_per_pixel * self.x_zoom
        width = clip.duration * self.seconds_per_pixel * self.x_zoom
        self.timeline_canvas.create_rectangle(x, y, x + width, y + self.track_height, fill="lightblue", outline="blue", tags="clip")
        self.timeline_canvas.create_text(x + 5, y + self.track_height // 2, text=os.path.basename(clip.file_path), anchor="w", tags="clip")
        logging.info(f"Clip drawn on track {track_index} at x={x}, y={y}, width={width}")

    def draw_waveform(self, clip, x, y, width, height):
        if clip not in self.waveform_images:
            self.waveform_images[clip] = self.audio_visualizer.create_waveform_image(clip.file_path, int(width), int(height))
        
        return self.timeline_canvas.create_image(x, y, anchor="nw", image=self.waveform_images[clip], tags=("waveform",))