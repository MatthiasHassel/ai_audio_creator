# timeline_view.py

import customtkinter as ctk
import tkinter as tk
import logging
import os 
import time
from tkinter import messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD
from utils.audio_clip import AudioClip
from utils.audio_visualizer import AudioVisualizer
from utils.keyboard_shortcuts import KeyboardShortcuts


class TimelineView(ctk.CTkToplevel, TkinterDnD.DnDWrapper):
    def __init__(self, master, project_model):
        super().__init__(master)
        self.TkdndVersion = TkinterDnD._require(self)
        self.project_model = project_model
        self.controller = None
        self.base_title = "Audio Timeline"
        self.current_project = "Untitled Project"
        self.update_title()
        self.geometry("1200x600")
        self.protocol("WM_DELETE_WINDOW", self.withdraw)
        self.keyboard_shortcuts = KeyboardShortcuts(self)
        
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
        self.min_x_zoom = 0.01
        self.max_x_zoom = 4.0
        self.option_key_pressed = False
        self.waveform_images = {}
        self.timeline_width = 10000  # Initial width, will be adjusted based on clips
        self.playhead_line = None
        self.playhead_position = 0
        self.is_playing = False
        self.after_id = None
        self.start_time = 0
        self.selected_clip = None
        self.dragging = False
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.drag_threshold = 5  # pixels
        self.drag_offset = 0  # Store the click position relative to clip start
        self.track_volume_vars = {}
        self.solo_buttons = {}  # Initialize solo_buttons
        self.mute_buttons = {}  # Initialize mute_buttons

        self.audio_visualizer = AudioVisualizer(self)
        self.waveform_cache = {}

        self.timeline_canvas = None
        self.track_label_canvas = None
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.create_widgets()
        self.create_status_bar()
        
        # Set up bindings
        self.bind("<Delete>", self.handle_delete)
        self.bind("<KeyPress-Alt_L>", self.option_key_press)
        self.bind("<KeyRelease-Alt_L>", self.option_key_release)
        self.bind_all("<MouseWheel>", self.on_mouse_scroll)
        self.bind_all("<Shift-MouseWheel>", self.on_shift_mouse_scroll)

    def set_controller(self, controller):
        self.controller = controller

    def create_widgets(self):
        self.create_toolbar()
        self.create_main_content()

    def create_toolbar(self):
        toolbar = ctk.CTkFrame(self)
        toolbar.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        toolbar.grid_columnconfigure(7, weight=1)  # Push buttons to the left

        self.add_track_button = ctk.CTkButton(toolbar, text="Add Track", command=self.add_track, width=100)
        self.add_track_button.grid(row=0, column=0, padx=2)

        self.play_button = ctk.CTkButton(toolbar, text="Play", command=self.play_timeline, width=80)
        self.play_button.grid(row=0, column=1, padx=2)

        self.stop_button = ctk.CTkButton(toolbar, text="Stop", command=self.stop_timeline, width=80)
        self.stop_button.grid(row=0, column=2, padx=2)

        self.restart_button = ctk.CTkButton(toolbar, text="Restart", command=self.restart_timeline, width=80)
        self.restart_button.grid(row=0, column=3, padx=2)

        self.toggle_audio_creator_button = ctk.CTkButton(toolbar, text="Show Audio Creator", width=140)
        self.toggle_audio_creator_button.grid(row=0, column=4, padx=2)

        # Add zoom controls to the toolbar
        ctk.CTkLabel(toolbar, text="X Zoom:").grid(row=0, column=5, padx=(20, 5))
        self.x_zoom_slider = ctk.CTkSlider(toolbar, from_=self.min_x_zoom, to=self.max_x_zoom, command=self.update_x_zoom, width=100)
        self.x_zoom_slider.set(self.x_zoom)
        self.x_zoom_slider.grid(row=0, column=6, padx=5)

        ctk.CTkLabel(toolbar, text="Y Zoom:").grid(row=0, column=7, padx=(20, 5))
        self.y_zoom_slider = ctk.CTkSlider(toolbar, from_=0.5, to=3, command=self.update_y_zoom, width=100)
        self.y_zoom_slider.set(self.y_zoom)
        self.y_zoom_slider.grid(row=0, column=8, padx=5)

    def create_topbar(self):
        self.topbar = tk.Canvas(self.timeline_frame, bg="gray40", height=30, highlightthickness=0)
        self.topbar.grid(row=0, column=0, sticky="ew")
        self.topbar.bind("<Button-1>", self.on_topbar_click)

    def create_main_content(self):
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.main_frame.grid_columnconfigure(1, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)

        self.create_track_label_frame()
        self.create_timeline_frame()

    def create_track_label_frame(self):
        self.track_label_frame = ctk.CTkFrame(self.main_frame, width=200)
        self.track_label_frame.grid(row=0, column=0, rowspan=2, sticky="ns")
        self.track_label_frame.grid_propagate(False)
        self.track_label_frame.grid_rowconfigure(0, weight=1)
        self.track_label_frame.grid_columnconfigure(0, weight=1)

        self.track_label_canvas = tk.Canvas(self.track_label_frame, bg="gray20", highlightthickness=0)
        self.track_label_canvas.grid(row=0, column=0, sticky="nsew")
        self.track_label_canvas.bind("<Button-2>", self.show_track_context_menu)
        self.track_label_canvas.bind("<Button-1>", self.on_track_label_click)

    def create_timeline_frame(self):
        self.timeline_frame = ctk.CTkFrame(self.main_frame)
        self.timeline_frame.grid(row=0, column=1, rowspan=2, sticky="nsew")
        self.timeline_frame.grid_rowconfigure(1, weight=1)
        self.timeline_frame.grid_columnconfigure(0, weight=1)

        self.create_topbar()
        self.create_timeline_canvas()
        
    def create_timeline_canvas(self):
        self.timeline_canvas = tk.Canvas(self.timeline_frame, bg="gray30", highlightthickness=0)
        self.timeline_canvas.grid(row=1, column=0, sticky="nsew")

        self.x_scrollbar = ctk.CTkScrollbar(self.timeline_frame, orientation="horizontal", command=self.on_scroll)
        self.x_scrollbar.grid(row=2, column=0, sticky="ew")

        self.timeline_canvas.configure(xscrollcommand=self.x_scrollbar.set)
        self.timeline_canvas.bind("<Configure>", self.on_canvas_resize)
        self.timeline_canvas.bind("<ButtonPress-1>", self.on_canvas_click)
        self.timeline_canvas.bind("<B1-Motion>", self.on_drag)
        self.timeline_canvas.bind("<ButtonRelease-1>", self.on_drag_release)
        self.timeline_canvas.bind("<Button-2>", self.show_clip_context_menu)

        self.timeline_canvas.drop_target_register(DND_FILES)
        self.timeline_canvas.dnd_bind('<<Drop>>', self.on_drop)

    def create_status_bar(self):
        self.status_var = tk.StringVar()
        self.status_bar = ctk.CTkLabel(self, textvariable=self.status_var, anchor="w")
        self.status_bar.grid(row=2, column=0, sticky="ew", padx=5, pady=2)

    def update_status(self, message):
        self.status_var.set(message)

    def initialize_playhead(self):
        self.draw_playhead(0)

    def redraw_timeline(self):
        self.timeline_canvas.delete("all")
        self.draw_grid()
        self.draw_clips()
        if self.playhead_line:
            self.draw_playhead(self.playhead_position / self.seconds_per_pixel)

    def set_toggle_audio_creator_command(self, command):
        self.toggle_audio_creator_button.configure(command=command)

    def on_canvas_resize(self, event):
        self.update_scrollregion()
        self.redraw_timeline()
        self.update_track_labels()

    def update_scrollregion(self):
        if self.tracks and any(track['clips'] for track in self.tracks):
            max_width = max(
                (clip.x + clip.duration) / self.seconds_per_pixel 
                for track in self.tracks 
                for clip in track['clips']
            )
            self.timeline_width = max(self.timeline_canvas.winfo_width(), max_width)
        else:
            self.timeline_width = self.timeline_canvas.winfo_width()
        
        self.timeline_canvas.configure(scrollregion=(0, 0, self.timeline_width, len(self.tracks) * self.track_height))
    
    def draw_grid(self):
        self.timeline_canvas.delete("grid")
        self.topbar.delete("all")
        
        width = self.timeline_canvas.winfo_width()
        height = self.timeline_canvas.winfo_height()
        
        # Draw vertical lines (1 second apart at default zoom)
        seconds_per_line = max(1, round(100 * self.seconds_per_pixel))
        for x in range(0, width, int(seconds_per_line / self.seconds_per_pixel)):
            self.timeline_canvas.create_line(x, 0, x, height, fill="gray50", tags="grid")
            time_text = f"{x * self.seconds_per_pixel:.1f}s"
            self.topbar.create_text(x, 15, text=time_text, fill="white", anchor="center")
        
        # Draw horizontal lines
        for i in range(len(self.tracks) + 1):
            y = i * self.track_height
            self.timeline_canvas.create_line(0, y, width, y, fill="gray50", tags="grid")

    def on_topbar_click(self, event):
        x = self.topbar.canvasx(event.x)
        new_position = x * self.seconds_per_pixel
        if self.controller:
            self.controller.set_playhead_position(new_position)

    def update_track_labels(self):
        self.track_label_canvas.delete("all")
        for i, track in enumerate(self.tracks):
            y = i * self.track_height + self.topbar.winfo_height()
            fill_color = "gray35" if track == self.selected_track else "gray25"
            self.track_label_canvas.create_rectangle(0, y, 200, y + self.track_height, fill=fill_color, tags=f"track_{i}")
            self.track_label_canvas.create_text(10, y + 15, text=track["name"], anchor="w", fill="white", tags=f"track_{i}")
            
            # Add Solo button
            solo_button = ctk.CTkButton(self.track_label_canvas, text="S", width=20, height=20, 
                                        fg_color="gray50", hover_color="green",
                                        command=lambda t=track: self.toggle_solo(t))
            solo_button_window = self.track_label_canvas.create_window(140, y + 15, window=solo_button)
            self.solo_buttons[i] = solo_button
            
            # Add Mute button
            mute_button = ctk.CTkButton(self.track_label_canvas, text="M", width=20, height=20, 
                                        fg_color="gray50", hover_color="red",
                                        command=lambda t=track: self.toggle_mute(t))
            mute_button_window = self.track_label_canvas.create_window(170, y + 15, window=mute_button)
            self.mute_buttons[i] = mute_button
            
            # Add volume slider
            volume_var = tk.DoubleVar(value=track.get("volume", 1.0))
            volume_slider = ctk.CTkSlider(self.track_label_canvas, from_=0, to=1, variable=volume_var, width=180)
            volume_slider_window = self.track_label_canvas.create_window(100, y + 45, window=volume_slider)
            
            # Store references to the variables
            self.track_volume_vars[i] = volume_var
            
            # Bind the volume slider to update function
            volume_slider.configure(command=lambda value, t=track: self.update_volume(t, value))
            
            # Update button colors based on current state
            self.update_button_colors(track)

    def toggle_solo(self, track):
        track["solo"] = not track.get("solo", False)
        if self.controller:
            self.controller.update_track_solo_mute(track)
        self.update_button_colors(track)

    def toggle_mute(self, track):
        track["mute"] = not track.get("mute", False)
        if self.controller:
            self.controller.update_track_solo_mute(track)
        self.update_button_colors(track)

    def update_button_colors(self, track):
        track_index = self.tracks.index(track)
        solo_button = self.solo_buttons.get(track_index)
        mute_button = self.mute_buttons.get(track_index)
        
        if solo_button:
            solo_button.configure(fg_color="green" if track.get("solo", False) else "gray50")
        
        if mute_button:
            mute_button.configure(fg_color="red" if track.get("mute", False) else "gray50")

    def update_volume(self, track, value):
        track["volume"] = value
        if self.controller:
            self.controller.update_track_volume(track)
                    
    def add_track(self, track_name=None):
        if self.controller:
            self.controller.add_track(track_name)
        # The view will be updated via update_tracks method

    def update_tracks(self, new_tracks):
        self.tracks = new_tracks
        self.update_track_labels()
        self.redraw_timeline()
        if self.tracks and not self.selected_track:
            self.select_track(self.tracks[0])

    def on_track_label_click(self, event):
        track_index = event.y // self.track_height
        if 0 <= track_index < len(self.tracks):
            self.select_track(self.tracks[track_index])

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

    def handle_delete(self, event):
        if self.selected_clip and self.controller:
            self.controller.delete_clip(self.selected_clip)
        elif self.selected_track:
            self.remove_track(self.selected_track)

    def remove_track(self, track):
        if track in self.tracks:
            if self.remove_track_callback:
                self.remove_track_callback(track)

    def show_track_context_menu(self, event):
        track_index = event.y // self.track_height
        if 0 <= track_index < len(self.tracks):
            track = self.tracks[track_index]
            context_menu = tk.Menu(self, tearoff=0)
            context_menu.add_command(label="Rename", command=lambda: self.start_rename_track(track))
            context_menu.add_command(label="Remove", command=lambda: self.remove_track(track))
            context_menu.tk_popup(event.x_root, event.y_root)

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
            self.play_button.configure(state="disabled")
            self.stop_button.configure(state="normal")
            self.restart_button.configure(state="normal")
            logging.info("Timeline playback started in view")

    def stop_timeline(self):
        self.is_playing = False
        self.play_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.restart_button.configure(state="normal")

    def restart_timeline(self):
        self.stop_timeline()
        self.playhead_position = 0
        if self.controller:
            self.controller.set_playhead_position(0)
        self.draw_playhead(0)
        self.stop_button.configure(state="normal")

    def update_playhead(self):
        if self.is_playing:
            current_time = time.time() - self.start_time
            self.playhead_position = current_time
            self.draw_playhead(self.playhead_position / self.seconds_per_pixel)
            self.after(50, self.update_playhead)  # Update every 50ms

    def update_playhead_position(self, position):
        self.playhead_position = position
        self.draw_playhead(position / self.seconds_per_pixel)

    def draw_playhead(self, x):
        if self.timeline_canvas:
            if self.playhead_line:
                self.timeline_canvas.delete(self.playhead_line)
            height = self.timeline_canvas.winfo_height()
            if height > 0:
                self.playhead_line = self.timeline_canvas.create_line(x, 0, x, height, fill="red", width=2)
                # Ensure the playhead is visible by scrolling the canvas if necessary
                self.timeline_canvas.xview_moveto(max(0, (x - self.timeline_canvas.winfo_width() / 2) / self.timeline_width))
            else:
                self.after(100, lambda: self.draw_playhead(x))
        else:
            self.after(100, lambda: self.draw_playhead(x))

    def on_canvas_click(self, event):
        x = self.timeline_canvas.canvasx(event.x)
        y = self.timeline_canvas.canvasy(event.y)
        
        clicked_clip = self.find_clip_at_position(x, y)
        if clicked_clip:
            self.select_clip(clicked_clip)
            self.drag_start_x = x
            self.drag_start_y = y
            # Calculate and store the offset
            self.drag_offset = x - (clicked_clip.x / self.seconds_per_pixel)
        else:
            self.deselect_clip()

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
        self.update_scrollregion()
        self.redraw_timeline()

    def update_y_zoom(self, value):
        self.y_zoom = float(value)
        self.track_height = max(self.min_track_height, min(self.base_track_height * self.y_zoom, self.max_track_height))
        self.redraw_timeline()
        self.update_track_labels()

    def update_title(self, project_name=None):
        if project_name:
            self.current_project = project_name
        self.title(f"{self.base_title} - {self.current_project}")

    def on_drop(self, event):
        file_path = event.data
        if file_path.lower().endswith(('.mp3', '.wav')):
            try:
                new_file_path = self.project_model.import_audio_file(file_path)
                track_index = self.get_track_index_from_y(event.y)
                x_position = event.x * self.seconds_per_pixel
                clip = AudioClip(new_file_path, x_position)
                self.add_clip(clip, track_index)
            except Exception as e:
                error_msg = f"Failed to import audio file: {str(e)}"
                logging.error(error_msg, exc_info=True)
                self.show_error("Error", error_msg)
    
    def get_track_index_from_y(self, y):
        return int(y // self.track_height)

    def add_clip(self, clip, track_index):
        if track_index < len(self.tracks):
            self.tracks[track_index]['clips'].append(clip)
            self.after(0, lambda: self._process_clip(clip, track_index))
        else:
            logging.warning(f"Attempted to add clip to non-existent track {track_index}")

    def _process_clip(self, clip, track_index):
        try:
            waveform_image = self.audio_visualizer.create_waveform_image(
                clip.file_path, 
                int(clip.duration / self.seconds_per_pixel), 
                int(self.track_height)
            )
            if waveform_image:
                self.waveform_cache[clip.file_path] = waveform_image
                self.draw_clip(clip, track_index)
                self.redraw_timeline()
            else:
                logging.warning(f"Failed to create waveform for {clip.file_path}")
        except Exception as e:
            logging.error(f"Error processing clip: {str(e)}", exc_info=True)

    def _draw_clip_on_gui(self, clip, track_index):
        try:
            self.draw_clip(clip, track_index)
            self.redraw_timeline()
        except Exception as e:
            logging.error(f"Error drawing clip on GUI: {str(e)}", exc_info=True)

    def set_add_clip_callback(self, callback):
        self.add_clip_callback = callback

    def draw_clips(self):
        for i, track in enumerate(self.tracks):
            y = i * self.track_height
            for clip in track['clips']:
                self.draw_clip(clip, y)

    def draw_clip(self, clip, y):
        x = clip.x / self.seconds_per_pixel
        width = clip.duration / self.seconds_per_pixel
        fill_color = "blue" if clip == self.selected_clip else "lightblue"
        self.timeline_canvas.create_rectangle(x, y, x + width, y + self.track_height, 
                                              fill=fill_color, outline="blue", tags="clip")
        self.timeline_canvas.create_text(x + 5, y + 5, text=os.path.basename(clip.file_path), 
                                         anchor="nw", tags="clip")
    
    def on_drag(self, event):
        if self.selected_clip:
            x = self.timeline_canvas.canvasx(event.x)
            y = self.timeline_canvas.canvasy(event.y)
            
            if not self.dragging:
                # Check if we've moved far enough to start dragging
                if (abs(x - self.drag_start_x) > self.drag_threshold or
                    abs(y - self.drag_start_y) > self.drag_threshold):
                    self.dragging = True
            
            if self.dragging:
                # Calculate new position using the offset
                new_x = max(0, (x - self.drag_offset) * self.seconds_per_pixel)
                new_track_index = int(y / self.track_height)
                
                if 0 <= new_track_index < len(self.tracks):
                    self.draw_dragged_clip(self.selected_clip, new_x, new_track_index)

    def on_drag_release(self, event):
        if self.dragging and self.selected_clip:
            x = self.timeline_canvas.canvasx(event.x)
            y = self.timeline_canvas.canvasy(event.y)
            new_x = max(0, (x - self.drag_offset) * self.seconds_per_pixel)
            new_track_index = int(y / self.track_height)
            
            if 0 <= new_track_index < len(self.tracks):
                old_track_index = self.find_clip_track_index(self.selected_clip)
                if old_track_index != -1:
                    success = self.controller.move_clip(self.selected_clip, new_x, old_track_index, new_track_index)
                    if success:
                        # Let the controller handle the clip movement
                        pass
                    else:
                        print("Failed to move clip")
        
        self.dragging = False
        self.drag_offset = 0  # Reset the offset
        self.redraw_timeline()
                
    def draw_dragged_clip(self, clip, new_x, new_track_index):
        self.redraw_timeline()  # Redraw to clear the old position
        x = new_x / self.seconds_per_pixel
        y = new_track_index * self.track_height
        width = clip.duration / self.seconds_per_pixel
        self.timeline_canvas.create_rectangle(x, y, x + width, y + self.track_height, 
                                              fill="red", outline="red", tags="dragged_clip")
        self.timeline_canvas.create_text(x + 5, y + 5, text=os.path.basename(clip.file_path), 
                                         anchor="nw", tags="dragged_clip")
        
    def find_clip_at_position(self, x, y):
        for track_index, track in enumerate(self.tracks):
            for clip in track['clips']:
                clip_x = clip.x / self.seconds_per_pixel
                clip_width = clip.duration / self.seconds_per_pixel
                clip_y = track_index * self.track_height
                if clip_x <= x <= clip_x + clip_width and clip_y <= y < clip_y + self.track_height:
                    return clip
        return None

    def select_clip(self, clip):
        self.deselect_clip()
        self.selected_clip = clip
        self.redraw_timeline()

    def deselect_clip(self):
        self.selected_clip = None
        self.redraw_timeline()

    def delete_selected_clip(self, event=None):
        if self.selected_clip and self.controller:
            self.controller.delete_clip(self.selected_clip)

    def find_clip_track_index(self, clip):
        for i, track in enumerate(self.tracks):
            if clip in track['clips']:
                return i
        return -1

    def show_clip_context_menu(self, event):
        x = self.timeline_canvas.canvasx(event.x)
        y = self.timeline_canvas.canvasy(event.y)
        
        clicked_clip = self.find_clip_at_position(x, y)
        if clicked_clip:
            self.select_clip(clicked_clip)
            context_menu = tk.Menu(self, tearoff=0)
            context_menu.add_command(label="Delete clip", command=self.delete_selected_clip)
            context_menu.tk_popup(event.x_root, event.y_root)

    def remove_clip(self, clip):
        for track in self.tracks:
            if clip in track['clips']:
                track['clips'].remove(clip)
                break
        self.redraw_timeline()

    def on_scroll(self, *args):
        self.timeline_canvas.xview(*args)
        self.topbar.xview(*args)

    def show_error(self, title, message):
        messagebox.showerror(title, message)