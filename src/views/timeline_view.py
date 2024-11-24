# timeline_view.py

import customtkinter as ctk
import tkinter as tk
import logging
import os 
import textwrap
from tkinter import messagebox
from utils.audio_clip import AudioClip
from utils.audio_visualizer import AudioVisualizer
from utils.keyboard_shortcuts import KeyboardShortcuts


class TimelineView(ctk.CTkToplevel):
    def __init__(self, master, project_model, timeline_model):
        super().__init__(master)
        self.project_model = project_model
        self.timeline_model = timeline_model
        self.controller = None
        self.base_title = "Audio Timeline"
        self.current_project = "Untitled Project"
        self.update_title()
        self.geometry("1200x600")
        self.protocol("WM_DELETE_WINDOW", self.withdraw)
        self.keyboard_shortcuts = KeyboardShortcuts(self)
        self.audio_visualizer = AudioVisualizer(self)
        self.is_renaming = False  # Flag to track renaming state
        
        self.initialize_variables()

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.create_widgets()
        
        self.setup_scrolling()

        self.setup_bindings()
        self.after(100, self.initial_update)
    
    def initialize_variables(self):
        # Initialize variables
        self.tracks = []
        self.selected_track = None
        self.base_track_height = 60
        self.track_height = self.base_track_height
        self.min_track_height = 30
        self.max_track_height = 200
        self.min_track_height_for_slider = 50  # Minimum height to show volume slider
        self.topbar_height = 30  # Define the height of the topbar
        self.base_seconds_per_pixel = 0.01  # 100 pixels = 1 second at default zoom
        self.seconds_per_pixel = self.base_seconds_per_pixel
        self.x_zoom = 1.0
        self.y_zoom = 1.0
        self.min_x_zoom = 0.01
        self.max_x_zoom = 4.0
        self.option_key_pressed = False
        self.waveform_images = {}
        self.waveform_cache = {}
        self.timeline_width = 10000  # Initial width, will be adjusted based on clips
        self.playhead_line = None
        self.playhead_position = 0
        self.after_id = None
        self.after_ids = []
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
        self.y_scrollbar = None
        self.scroll_offset = 0;
        self.timeline_canvas = None
        self.track_label_canvas = None
        self.timeline_duration = 300  # Default timeline duration in seconds
        self.max_timeline_duration = 1800  # Set a maximum timeline duration in sec (e.g. 30min -> 1800s )

    def format_db(self, db_value):
        """Format decibel value for display"""
        if db_value <= -70:
            return "-∞ dB"
        return f"{db_value:+.1f} dB"
    
    def parse_db_input(self, input_str):
        """Parse dB input string and return valid dB value"""
        try:
            # Remove 'dB' suffix and any whitespace
            value_str = input_str.replace('dB', '').strip()
            # Handle infinity case
            if value_str in ['-∞', '-inf']:
                return -70.0
            # Convert to float and clamp to valid range
            value = float(value_str)
            return max(-70.0, min(3.0, value))
        except ValueError:
            return None
    
    def setup_scrolling(self):
        self.timeline_canvas.configure(xscrollcommand=self.x_scrollbar.set, 
                                   yscrollcommand=self.y_scrollbar.set)
        self.track_label_canvas.configure(yscrollcommand=self.y_scrollbar.set)
        self.x_scrollbar.configure(command=self.on_horizontal_scroll)
        self.y_scrollbar.configure(command=self.on_vertical_scroll)
        
    def setup_bindings(self):
        # Set up bindings
        self.timeline_canvas.bind("<Configure>", self.on_canvas_resize)
        self.timeline_canvas.bind("<ButtonPress-1>", self.on_canvas_click)
        self.timeline_canvas.bind("<B1-Motion>", self.on_drag)
        self.timeline_canvas.bind("<ButtonRelease-1>", self.on_drag_release)
        self.timeline_canvas.bind("<Button-2>", self.show_clip_context_menu)
        
        self.track_label_canvas.bind("<Button-2>", self.show_track_context_menu)
        self.track_label_canvas.bind("<Button-1>", self.on_track_label_click)
        
        self.bind("<Delete>", self.handle_delete)
        self.bind("<KeyPress-Alt_L>", self.option_key_press)
        self.bind("<KeyRelease-Alt_L>", self.option_key_release)

        # Scrolling - For Windows + MacOS compatibility:
        self.bind("<MouseWheel>", self.on_mousewheel)
        self.bind("<Shift-MouseWheel>", self.on_shift_mousewheel)

        # Scrolling - For Linux compatibility
        # self.bind("<Button-4>", self.on_mousewheel)
        # self.bind("<Button-5>", self.on_mousewheel)
        # self.bind("<Shift-Button-4>", self.on_shift_mousewheel)
        # self.bind("<Shift-Button-5>", self.on_shift_mousewheel)

    def create_widgets(self):
        self.create_toolbar()
        self.create_main_content()
        self.create_status_bar()
         # Create progress bar
        self.progress_bar = ctk.CTkProgressBar(self)
        self.progress_bar.grid(row=2, column=1, sticky="ew", padx=5, pady=5)
        self.progress_bar.grid_remove()  # Initially hidden

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

    def initial_update(self):
        self.update_scrollregion()
        self.update_grid_and_topbar()

    def create_main_content(self):
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.main_frame.grid_columnconfigure(1, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)

        self.create_track_label_frame()
        self.create_timeline_frame()

    def create_track_label_frame(self):
        self.track_label_frame = ctk.CTkFrame(self.main_frame, width=200)
        self.track_label_frame.grid(row=0, column=0, sticky="ns")
        self.track_label_frame.grid_propagate(False)
        self.track_label_frame.grid_rowconfigure(1, weight=1)
        self.track_label_frame.grid_columnconfigure(0, weight=1)

        self.track_label_topbar = ctk.CTkFrame(self.track_label_frame, height=self.topbar_height)
        self.track_label_topbar.grid(row=0, column=0, sticky="ew")

        self.track_label_canvas = tk.Canvas(self.track_label_frame, bg="gray20", highlightthickness=0)
        self.track_label_canvas.grid(row=1, column=0, sticky="nsew")

    def create_timeline_frame(self):
        self.timeline_frame = ctk.CTkFrame(self.main_frame)
        self.timeline_frame.grid(row=0, column=1, sticky="nsew")
        self.timeline_frame.grid_rowconfigure(1, weight=1)
        self.timeline_frame.grid_columnconfigure(0, weight=1)

        self.create_topbar()
        self.create_timeline_canvas()

    def create_topbar(self):
        self.topbar = tk.Canvas(self.timeline_frame, bg="gray40", height=self.topbar_height, highlightthickness=0)
        self.topbar.grid(row=0, column=0, sticky="ew")
        self.topbar.bind("<Button-1>", self.on_topbar_click)

    def create_timeline_canvas(self):
        self.timeline_canvas = tk.Canvas(self.timeline_frame, bg="gray30", highlightthickness=0)
        self.timeline_canvas.grid(row=1, column=0, sticky="nsew")

        self.x_scrollbar = ctk.CTkScrollbar(self.timeline_frame, orientation="horizontal", command=self.on_horizontal_scroll)
        self.x_scrollbar.grid(row=2, column=0, sticky="ew")

        self.y_scrollbar = ctk.CTkScrollbar(self.main_frame, orientation="vertical", command=self.on_vertical_scroll)
        self.y_scrollbar.grid(row=0, column=2, sticky="ns")

    def create_status_bar(self):
        self.status_var = tk.StringVar()
        self.status_bar = ctk.CTkLabel(self, textvariable=self.status_var, anchor="w")
        self.status_bar.grid(row=2, column=0, sticky="ew", padx=5, pady=2)

    def format_time_label(self, seconds):
        minutes, seconds = divmod(int(seconds), 60)
        hours, minutes = divmod(minutes, 60)
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"
    
    def update_grid_and_topbar(self):
        self.redraw_timeline()
        self.update_topbar()

    def update_topbar(self):
        self.topbar.delete("all")
        visible_start = self.timeline_canvas.canvasx(0)
        visible_end = self.timeline_canvas.canvasx(self.timeline_canvas.winfo_width())

        start_time = visible_start * self.seconds_per_pixel
        end_time = visible_end * self.seconds_per_pixel

        seconds_per_label = max(1, int((end_time - start_time) / 10))  # Adjust label density

        for i in range(int(start_time), int(end_time) + 1, seconds_per_label):
            x = (i / self.seconds_per_pixel)
            formatted_time = self.format_time_label(i)
            self.topbar.create_text(x, 15, text=formatted_time, fill="white", anchor="center")

    def draw_grid(self):
        self.timeline_canvas.delete("grid")
        
        width = self.timeline_width
        height = len(self.tracks) * self.track_height
        visible_start_x = self.timeline_canvas.canvasx(0)
        visible_end_x = self.timeline_canvas.canvasx(self.timeline_canvas.winfo_width())
        visible_start_y = self.timeline_canvas.canvasy(0)
        visible_end_y = self.timeline_canvas.canvasy(self.timeline_canvas.winfo_height())
        
        # Draw vertical lines (1 second apart at default zoom)
        seconds_per_line = max(1, round(100 * self.seconds_per_pixel))
        start_second = int(visible_start_x * self.seconds_per_pixel / seconds_per_line) * seconds_per_line
        for x in range(start_second, int(visible_end_x * self.seconds_per_pixel) + seconds_per_line, seconds_per_line):
            canvas_x = x / self.seconds_per_pixel
            self.timeline_canvas.create_line(canvas_x, visible_start_y, canvas_x, visible_end_y, fill="gray50", tags="grid")
        
        # Draw horizontal lines
        start_track = max(0, int(visible_start_y // self.track_height))
        end_track = min(len(self.tracks), int(visible_end_y // self.track_height) + 1)
        for i in range(start_track, end_track + 1):
            y = i * self.track_height - self.scroll_offset
            self.timeline_canvas.create_line(visible_start_x, y, visible_end_x, y, fill="gray50", tags="grid")

    def create_status_bar(self):
        self.status_var = tk.StringVar()
        self.status_bar = ctk.CTkLabel(self, textvariable=self.status_var, anchor="w")
        self.status_bar.grid(row=2, column=0, sticky="ew", padx=5, pady=2)

    def set_controller(self, controller):
        self.controller = controller

    def redraw_timeline(self):
        self.timeline_canvas.delete("all")
        self.draw_grid()
        for track_index, track in enumerate(self.tracks):
            y = track_index * self.track_height - self.scroll_offset
            for clip in track['clips']:
                self.draw_clip(clip, y)
        self.draw_playhead(self.playhead_position / self.seconds_per_pixel)

    def update_status(self, message):
        self.status_var.set(message)

    def initialize_playhead(self):
        self.draw_playhead(0)

    def set_toggle_audio_creator_command(self, command):
        self.toggle_audio_creator_button.configure(command=command)

    def on_canvas_resize(self, event):
        self.update_scrollregion()
        self.redraw_timeline()
        self.update_track_labels()

    def on_mousewheel(self, event):
        if self.option_key_pressed:
            self.handle_zoom(event, 'y')
        else:
            self.handle_scroll(event, 'vertical')
        return "break"

    def on_shift_mousewheel(self, event):
        if self.option_key_pressed:
            self.handle_zoom(event, 'x')
        else:
            self.handle_scroll(event, 'horizontal')
        return "break"

    def handle_scroll(self, event, direction):
        if event.num == 5 or event.delta < 0:
            scroll_amount = 1
        else:
            scroll_amount = -1

        if direction == 'vertical':
            self.timeline_canvas.yview_scroll(scroll_amount, "units")
            self.track_label_canvas.yview_scroll(scroll_amount, "units")
        else:
            self.timeline_canvas.xview_scroll(scroll_amount, "units")
            self.topbar.xview_scroll(scroll_amount, "units")

        self.update_grid_and_topbar()

    def handle_zoom(self, event, axis):
        delta = event.delta if event.num not in (4, 5) else (120 if event.num == 4 else -120)
        zoom_factor = 0.9 if delta < 0 else 1.1
        if axis == 'x':
            self.zoom_x(zoom_factor)
            self.update_x_zoom_slider()
            self.update_topbar()
        else:
            self.zoom_y(zoom_factor)
            self.update_y_zoom_slider()

    def update_x_zoom_slider(self):
        self.x_zoom_slider.set(self.x_zoom)

    def update_y_zoom_slider(self):
        self.y_zoom_slider.set(self.y_zoom)

    def on_vertical_scroll(self, *args):
        if args[0] == 'moveto':
            self.timeline_canvas.yview_moveto(args[1])
            self.track_label_canvas.yview_moveto(args[1])
        elif args[0] == 'scroll':
            self.timeline_canvas.yview_scroll(int(args[1]), args[2])
            self.track_label_canvas.yview_scroll(int(args[1]), args[2])
        
        self.scroll_offset = self.timeline_canvas.canvasy(0)
        self.update_track_labels()
        self.redraw_timeline()

    def on_horizontal_scroll(self, *args):
        if args[0] == 'moveto':
            self.timeline_canvas.xview_moveto(args[1])
            self.topbar.xview_moveto(args[1])
        elif args[0] == 'scroll':
            self.timeline_canvas.xview_scroll(int(args[1]), args[2])
            self.topbar.xview_scroll(int(args[1]), args[2])
        
        self.update_grid_and_topbar()
        
    def update_scrollregion(self):
        total_height = max(len(self.tracks) * self.track_height, self.timeline_canvas.winfo_height())
        self.timeline_width = max(self.timeline_canvas.winfo_width(), self.timeline_duration / self.seconds_per_pixel)
        
        logging.info(f"Updating scroll region. Timeline width: {self.timeline_width}, Timeline duration: {self.timeline_duration}")
        
        self.timeline_canvas.configure(scrollregion=(0, 0, self.timeline_width, total_height))
        self.topbar.configure(scrollregion=(0, 0, self.timeline_width, self.topbar_height))
        self.track_label_canvas.configure(scrollregion=(0, 0, self.track_label_canvas.winfo_width(), total_height))

        # Show or hide vertical scrollbar based on content height
        if total_height <= self.timeline_canvas.winfo_height():
            self.y_scrollbar.grid_remove()
        else:
            self.y_scrollbar.grid()

        # Show or hide horizontal scrollbar based on content width
        if self.timeline_width <= self.timeline_canvas.winfo_width():
            self.x_scrollbar.grid_remove()
        else:
            self.x_scrollbar.grid()

    def on_topbar_click(self, event):
        x = self.topbar.canvasx(event.x)
        new_position = x * self.seconds_per_pixel
        if self.controller:
            self.controller.set_playhead_position(new_position)

    def update_track_labels(self):
        self.track_label_canvas.delete("all")
        visible_start = int(self.track_label_canvas.canvasy(0))
        visible_end = int(self.track_label_canvas.canvasy(self.track_label_canvas.winfo_height()))
        
        start_index = max(0, int(visible_start / self.track_height))
        end_index = min(len(self.tracks), int(visible_end / self.track_height) + 1)

        for i in range(start_index, end_index):
            track = self.tracks[i]
            y = i * self.track_height - self.scroll_offset
            fill_color = "gray35" if track == self.selected_track else "gray25"
            self.track_label_canvas.create_rectangle(0, y, 200, y + self.track_height, fill=fill_color, tags=f"track_{i}")
            
            # Create track name slightly higher
            self.track_label_canvas.create_text(10, y + (self.track_height // 2) - 10, 
                                              text=track["name"], anchor="w", fill="white", 
                                              tags=f"track_{i}")
            
            # Add Solo button
            solo_button = ctk.CTkButton(self.track_label_canvas, text="S", width=20, height=20, 
                                        fg_color="green" if track.get("solo", False) else "gray50",
                                        command=lambda t=track: self.toggle_solo(t))
            solo_button_window = self.track_label_canvas.create_window(140, y + self.track_height // 2 - 10, window=solo_button)
            self.solo_buttons[i] = solo_button
            
            # Add Mute button
            mute_button = ctk.CTkButton(self.track_label_canvas, text="M", width=20, height=20, 
                                        fg_color="red" if track.get("mute", False) else "gray50",
                                        command=lambda t=track: self.toggle_mute(t))
            mute_button_window = self.track_label_canvas.create_window(170, y + self.track_height // 2 - 10, window=mute_button)
            self.mute_buttons[i] = mute_button
            
            # Add volume slider and label if track height is sufficient
            if self.track_height >= self.min_track_height_for_slider:
                # Create volume entry
                volume_db = track.get("volume_db", 0.0)
                volume_entry = ctk.CTkEntry(self.track_label_canvas, 
                                          width=70,
                                          height=20,
                                          fg_color="gray35",
                                          text_color="white")
                volume_entry.insert(0, self.format_db(volume_db))
                volume_entry_window = self.track_label_canvas.create_window(
                    40, y + self.track_height - 15, window=volume_entry)
                
                # Create volume slider
                volume_slider = ctk.CTkSlider(self.track_label_canvas, 
                                            from_=-70, to=3,
                                            width=100,
                                            number_of_steps=730)  # 0.1 dB steps
                volume_slider.set(volume_db)
                volume_slider_window = self.track_label_canvas.create_window(
                    140, y + self.track_height - 15, window=volume_slider)
                
                # Store references to the widgets
                self.track_volume_vars[i] = {
                    'slider': volume_slider,
                    'entry': volume_entry
                }
                
                # Bind the volume slider to update function and double-click
                volume_slider.configure(command=lambda value, t=track: self.update_volume(t, value))
                volume_slider.bind('<Double-Button-1>', lambda e, t=track: self.reset_volume(t))
                
                # Bind entry events
                volume_entry.bind('<Return>', lambda e, t=track: self.handle_volume_entry(e, t))
                volume_entry.bind('<FocusOut>', lambda e, t=track: self.handle_volume_entry(e, t))

    def handle_volume_entry(self, event, track):
        """Handle volume entry events"""
        entry = event.widget
        value = self.parse_db_input(entry.get())
        if value is not None:
            self.update_volume(track, value)
            track_index = self.tracks.index(track)
            if track_index in self.track_volume_vars:
                self.track_volume_vars[track_index]['slider'].set(value)
        else:
            # Reset to current value if input was invalid
            track_index = self.tracks.index(track)
            if track_index in self.track_volume_vars:
                current_db = track.get("volume_db", 0.0)
                entry.delete(0, tk.END)
                entry.insert(0, self.format_db(current_db))

    def reset_volume(self, track):
        """Reset volume to 0dB on double-click"""
        self.update_volume(track, 0.0)
        track_index = self.tracks.index(track)
        if track_index in self.track_volume_vars:
            self.track_volume_vars[track_index]['slider'].set(0.0)
            self.track_volume_vars[track_index]['entry'].delete(0, tk.END)
            self.track_volume_vars[track_index]['entry'].insert(0, self.format_db(0.0))

    def update_volume(self, track, value):
        """Update track volume with decibel value"""
        # Round to 0.1 dB precision
        db_value = round(float(value), 1)
        track["volume_db"] = db_value
        
        # Update the volume entry if it exists
        track_index = self.tracks.index(track)
        if track_index in self.track_volume_vars:
            entry = self.track_volume_vars[track_index]['entry']
            entry.delete(0, tk.END)
            entry.insert(0, self.format_db(db_value))
        
        if self.controller:
            self.controller.update_track_volume(track)

    def update_single_track_label(self, track):
        track_index = self.tracks.index(track)
        
        # Update solo button
        if track_index in self.solo_buttons:
            self.solo_buttons[track_index].configure(
                fg_color="green" if track.get("solo", False) else "gray50")
        
        # Update mute button
        if track_index in self.mute_buttons:
            self.mute_buttons[track_index].configure(
                fg_color="red" if track.get("mute", False) else "gray50")
        
        # Update volume slider and entry
        if track_index in self.track_volume_vars:
            widgets = self.track_volume_vars[track_index]
            db_value = track.get("volume_db", 0.0)
            widgets['slider'].set(db_value)
            widgets['entry'].delete(0, tk.END)
            widgets['entry'].insert(0, self.format_db(db_value))

    def toggle_solo(self, track):
        if not self.is_renaming and self.controller:
            self.controller.toggle_solo(track)
            self.update_single_track_label(track)

    def toggle_mute(self, track):
        if not self.is_renaming and self.controller:
            self.controller.toggle_mute(track)
            self.update_single_track_label(track)
                    
    def add_track(self, track_name=None):
        if not self.is_renaming and self.controller:
            self.controller.add_track(track_name)
        self.update_scrollregion()
        # The view will be updated via update_tracks method

    def update_tracks(self, new_tracks):
        self.tracks = new_tracks
        self.update_track_labels()
        self.redraw_timeline()
        self.update_scrollregion()
        if self.tracks and not self.selected_track:
            self.select_track(self.tracks[0])

    def on_track_label_click(self, event):
        track_index = int(event.y // self.track_height)
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
        """Start track renaming"""
        try:
            track_index = self.tracks.index(track)
            y = track_index * self.track_height - self.scroll_offset
            
            # Create and configure entry widget
            entry = ctk.CTkEntry(self.track_label_canvas, fg_color="gray35", text_color="white", border_width=0)
            entry.insert(0, track["name"])
            
            # Create entry window
            entry_window = self.track_label_canvas.create_window(
                10, 
                y + (self.track_height // 2) - 10,
                anchor="w", 
                window=entry, 
                width=180
            )
            
            # Store references to current rename widgets
            self.current_rename_data = {
                'track': track,
                'entry': entry,
                'window': entry_window
            }
            
            # Set focus and bind events
            entry.focus_set()
            
            # Bind events with specific tags for easy cleanup
            entry.bind("<Return>", self._handle_rename_return, add="+")
            entry.bind("<FocusOut>", self._handle_rename_focus_out, add="+")
            entry.bind("<Escape>", self._handle_rename_escape, add="+")
            
        except Exception as e:
            logging.error(f"Error starting rename: {str(e)}")
            self.cancel_rename_track()

    def _handle_rename_return(self, event):
        """Handle Return key press during rename"""
        if hasattr(self, 'current_rename_data'):
            self.finish_rename_track()
        return "break"

    def _handle_rename_focus_out(self, event):
        """Handle focus loss during rename"""
        if hasattr(self, 'current_rename_data'):
            self.finish_rename_track()
        return "break"

    def _handle_rename_escape(self, event):
        """Handle Escape key press during rename"""
        if hasattr(self, 'current_rename_data'):
            self.cancel_rename_track()
        return "break"

    def finish_rename_track(self):
        """Finish track renaming"""
        try:
            if hasattr(self, 'current_rename_data'):
                track = self.current_rename_data['track']
                entry = self.current_rename_data['entry']
                entry_window = self.current_rename_data['window']
                
                new_name = entry.get()
                
                # Clean up entry widget and bindings
                self.track_label_canvas.delete(entry_window)
                entry.destroy()
                
                # Update track name if changed
                if new_name and new_name != track["name"]:
                    track["name"] = new_name
                    if hasattr(self, 'rename_track_callback'):
                        self.rename_track_callback(track, new_name)
                
                # Clean up rename data
                delattr(self, 'current_rename_data')
                
                # Reset state and update view
                self.is_renaming = False
                self.set_keyboard_shortcuts_enabled(True)
                self.update_track_labels()
                
        except Exception as e:
            logging.error(f"Error finishing rename: {str(e)}")
            self.cancel_rename_track()

    def cancel_rename_track(self):
        """Cancel renaming without saving changes"""
        try:
            if hasattr(self, 'current_rename_data'):
                entry_window = self.current_rename_data['window']
                entry = self.current_rename_data['entry']
                
                # Clean up entry widget and bindings
                self.track_label_canvas.delete(entry_window)
                entry.destroy()
                
                # Clean up rename data
                delattr(self, 'current_rename_data')
            
            # Reset state and update view
            self.is_renaming = False
            self.set_keyboard_shortcuts_enabled(True)
            self.update_track_labels()
            
        except Exception as e:
            logging.error(f"Error canceling rename: {str(e)}")
        
        return "break"

    def handle_rename_context_menu(self, track):
        """Handle rename selection from context menu"""
        if not self.is_renaming:  # Only start new rename if not already renaming
            self.is_renaming = True
            self.set_keyboard_shortcuts_enabled(False)
            self.start_rename_track(track)

    def deselect_all_tracks(self):
        self.selected_track = None
        self.update_track_labels()
        self.redraw_timeline()

    def handle_delete(self, event):
        if not self.is_renaming:
            if self.selected_clip and self.controller:
                self.controller.delete_clip(self.selected_clip)
            elif self.selected_track:
                self.remove_track(self.selected_track)

    def remove_track(self, track):
        if not self.is_renaming and track in self.tracks:
            if self.remove_track_callback:
                self.remove_track_callback(track)
        self.update_scrollregion()

    def show_track_context_menu(self, event):
        if not self.is_renaming:
            track_index = int(event.y // self.track_height)
            if 0 <= track_index < len(self.tracks):
                track = self.tracks[track_index]
                context_menu = tk.Menu(self, tearoff=0)
                context_menu.add_command(label="Rename", 
                                       command=lambda t=track: self.handle_rename_context_menu(t))
                context_menu.add_command(label="Remove", 
                                       command=lambda: self.remove_track(track))
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
        """Called when user clicks play button"""
        if not self.is_renaming and self.controller:
            self.controller.play_timeline()

    def stop_timeline(self):
        """Called when user clicks stop button"""
        if not self.is_renaming and self.controller:
            self.controller.stop_timeline()

    def restart_timeline(self):
        """Called when user clicks restart button"""
        if not self.is_renaming and self.controller:
            self.controller.restart_timeline()

    def on_playback_started(self, position):
        self.play_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.restart_button.configure(state="normal")
        self.update_playhead_position(position)
        logging.info("Timeline playback started in view")

    def on_playback_stopped(self, position):
        """Called by the controller when playback stops"""
        self.play_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.restart_button.configure(state="normal")
        self.update_playhead_position(position)
        # Cancel any pending playhead updates
        while self.after_ids:
            try:
                self.after_cancel(self.after_ids.pop())
            except Exception as e:
                logging.error(f"Error cancelling after event: {str(e)}")

    def restart_timeline(self):
        if self.controller:
            self.controller.restart_timeline()

    def update_playhead_position(self, position):
        self.playhead_position = min(position, self.timeline_duration)
        x = self.playhead_position / self.seconds_per_pixel
        self.draw_playhead(x)
        
        # Check if playhead is near the edge of the view
        canvas_width = self.timeline_canvas.winfo_width()
        visible_start = self.timeline_canvas.canvasx(0)
        visible_end = self.timeline_canvas.canvasx(canvas_width)
        
        # Define a margin (e.g., 20% of the canvas width)
        margin = canvas_width * 0.2
        
        if x < visible_start + margin or x > visible_end - margin:
            # Calculate new scroll position
            new_start = max(0, x - canvas_width / 2)
            self.timeline_canvas.xview_moveto(new_start / self.timeline_width)
            self.topbar.xview_moveto(new_start / self.timeline_width)
            self.update_grid_and_topbar()
        
        # Extend timeline if nearing the end
        if position > self.timeline_duration - 60:
            self.timeline_duration += 300
            self.update_scrollregion()
            self.update_grid_and_topbar()

    def update_timeline_duration(self):
        max_duration = 0
        for track in self.tracks:
            for clip in track['clips']:
                clip_end = clip.x + clip.duration
                if clip_end > max_duration:
                    max_duration = clip_end
        self.timeline_duration = min(max(300, max_duration + 60), self.max_timeline_duration)
        self.update_scrollregion()

    def draw_playhead(self, x):
        if self.timeline_canvas:
            if self.playhead_line:
                self.timeline_canvas.delete(self.playhead_line)
            height = self.timeline_canvas.winfo_height()
            self.playhead_line = self.timeline_canvas.create_line(x, 0, x, height, fill="red", width=2)

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
    
    def zoom_x(self, factor):
        new_zoom = self.x_zoom * factor
        new_zoom = max(self.min_x_zoom, min(new_zoom, self.max_x_zoom))
        self.update_x_zoom(new_zoom)
        self.update_x_zoom_slider()

    def zoom_y(self, factor):
        new_zoom = self.y_zoom * factor
        new_track_height = self.base_track_height * new_zoom
        if self.min_track_height <= new_track_height <= self.max_track_height:
            self.update_y_zoom(new_zoom)
            self.update_y_zoom_slider()

    def update_x_zoom(self, value):
        self.x_zoom = float(value)
        self.seconds_per_pixel = self.base_seconds_per_pixel / self.x_zoom
        self.update_scrollregion()
        self.redraw_timeline()
        self.draw_playhead(self.playhead_position / self.seconds_per_pixel)
        self.update_topbar()

    def update_y_zoom(self, value):
        self.y_zoom = float(value)
        self.track_height = max(self.min_track_height, min(self.base_track_height * self.y_zoom, self.max_track_height))
        
        self.update_scrollregion()
        self.redraw_timeline()
        self.update_track_labels()

        # Adjust scroll position to keep the view centered
        visible_start = self.timeline_canvas.canvasy(0)
        visible_center = visible_start + self.timeline_canvas.winfo_height() / 2
        center_track = visible_center / self.track_height
        new_visible_start = center_track * self.track_height - self.timeline_canvas.winfo_height() / 2
        
        if new_visible_start >= 0:
            self.timeline_canvas.yview_moveto(new_visible_start / (len(self.tracks) * self.track_height))
            self.track_label_canvas.yview_moveto(new_visible_start / (len(self.tracks) * self.track_height))

    def update_title(self, project_name=None):
        if project_name:
            self.current_project = project_name
        self.title(f"{self.base_title} - {self.current_project}")

    def find_next_available_position(self, track_index, x_position):
        if track_index < len(self.tracks):
            for clip in self.tracks[track_index]['clips']:
                if clip.x <= x_position < clip.x + clip.duration:
                    x_position = clip.x + clip.duration
        return x_position

    def get_track_index_from_y(self, y):
        return int(y // self.track_height)

    def add_clip(self, clip, track_index):
        if track_index < len(self.tracks):
            self.tracks[track_index]['clips'].append(clip)
            self.draw_clip(clip, track_index)
            self.redraw_timeline()
            self.update_timeline_duration()
            self.update_scrollregion()
            self.timeline_model.set_modified(True)  # Mark project as modified
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
        visible_start_y = self.timeline_canvas.canvasy(0)
        visible_end_y = self.timeline_canvas.canvasy(self.timeline_canvas.winfo_height())
        start_track = max(0, int(visible_start_y // self.track_height))
        end_track = min(len(self.tracks), int(visible_end_y // self.track_height) + 1)

        for i in range(start_track, end_track):
            track = self.tracks[i]
            y = i * self.track_height - self.scroll_offset
            for clip in track['clips']:
                self.draw_clip(clip, y)

    def draw_clip(self, clip, y):
        x = clip.x / self.seconds_per_pixel
        width = clip.duration / self.seconds_per_pixel
        fill_color = "blue" if clip == self.selected_clip else "lightblue"
        
        self.timeline_canvas.create_rectangle(x, y, x + width, y + self.track_height, 
                                            fill=fill_color, outline="blue", tags="clip")
        
        # Get display text (prompt or title)
        display_text = clip.get_display_text()
        
        # Calculate available width for text
        available_width = width - 10  # 5 pixels padding on each side
        
        # Create a temporary text item to measure text width
        temp_text = self.timeline_canvas.create_text(0, 0, text=display_text, anchor="w")
        text_bbox = self.timeline_canvas.bbox(temp_text)
        self.timeline_canvas.delete(temp_text)
        
        if text_bbox:
            text_width = text_bbox[2] - text_bbox[0]
            
            if text_width <= available_width:
                # If the full text fits, display it all
                final_text = display_text
            else:
                # If it doesn't fit, calculate how many characters we can display
                char_width = text_width / len(display_text)
                max_chars = int(available_width / char_width)
                
                # Only display text if we can fit at least 4 characters (3 for "..." and 1 for content)
                if max_chars >= 4:
                    final_text = display_text[:max_chars-3] + "..."
                else:
                    return  # Don't display any text if there's not enough space
            
            self.timeline_canvas.create_text(x + 5, y + self.track_height/2, 
                                            text=final_text, 
                                            anchor="w",
                                            tags="clip")
            
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
        self.update_timeline_duration()
        self.update_scrollregion()
                
    def draw_dragged_clip(self, clip, new_x, new_track_index):
        self.redraw_timeline()  # Redraw to clear the old position
        x = new_x / self.seconds_per_pixel
        y = new_track_index * self.track_height
        width = clip.duration / self.seconds_per_pixel
        self.timeline_canvas.create_rectangle(x, y, x + width, y + self.track_height, 
                                            fill="red", outline="red", tags="dragged_clip")
        
        # Get display text (prompt or title)
        display_text = clip.get_display_text()
        
        # Calculate available width for text
        available_width = width - 10  # 5 pixels padding on each side
        
        # Create a temporary text item to measure text width
        temp_text = self.timeline_canvas.create_text(0, 0, text=display_text, anchor="w")
        text_bbox = self.timeline_canvas.bbox(temp_text)
        self.timeline_canvas.delete(temp_text)
        
        if text_bbox:
            text_width = text_bbox[2] - text_bbox[0]
            
            if text_width <= available_width:
                # If the full text fits, display it all
                final_text = display_text
            else:
                # If it doesn't fit, calculate how many characters we can display
                char_width = text_width / len(display_text)
                max_chars = int(available_width / char_width)
                
                # Only display text if we can fit at least 4 characters (3 for "..." and 1 for content)
                if max_chars >= 4:
                    final_text = display_text[:max_chars-3] + "..."
                else:
                    return  # Don't display any text if there's not enough space
            
            self.timeline_canvas.create_text(x + 5, y + self.track_height/2, 
                                            text=final_text, 
                                            anchor="w",
                                            tags="clip")
        
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
            context_menu.add_command(label="Regenerate", command=self.delete_selected_clip)
            context_menu.tk_popup(event.x_root, event.y_root)

    def remove_clip(self, clip):
        for track in self.tracks:
            if clip in track['clips']:
                track['clips'].remove(clip)
                break
        self.redraw_timeline()
        self.update_timeline_duration()
        self.update_scrollregion()

    def on_scroll(self, *args):
        self.timeline_canvas.xview(*args)
        self.topbar.xview(*args)
        self.update_grid_and_topbar()

    def show_error(self, title, message):
        messagebox.showerror(title, message)

    def show_progress_bar(self, determinate=True):
        if determinate:
            self.progress_bar.configure(mode="determinate")
            self.progress_bar.set(0)
        else:
            self.progress_bar.configure(mode="indeterminate")
        self.progress_bar.grid()
        self.progress_bar.start()

    def hide_progress_bar(self):
        self.progress_bar.stop()
        self.progress_bar.grid_remove()
 
    def select_multiple_clips(self, event):
        x = self.timeline_canvas.canvasx(event.x)
        y = self.timeline_canvas.canvasy(event.y)
        clicked_clip = self.find_clip_at_position(x, y)
        if clicked_clip:
            if clicked_clip not in self.selected_clips:
                self.selected_clips.append(clicked_clip)
            else:
                self.selected_clips.remove(clicked_clip)
            self.redraw_timeline()

    def set_keyboard_shortcuts_enabled(self, enabled):
        """Enable or disable keyboard shortcuts"""
        if enabled:
            # Re-bind keyboard shortcuts
            self.keyboard_shortcuts = KeyboardShortcuts(self)
        else:
            # Unbind keyboard shortcuts
            if self.keyboard_shortcuts:
                for key, callback in self.keyboard_shortcuts.__dict__.items():
                    if isinstance(callback, str) and callback.startswith('<'):
                        self.unbind(callback)
            self.keyboard_shortcuts = None