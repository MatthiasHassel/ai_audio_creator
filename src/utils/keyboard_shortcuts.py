# utils/keyboard_shortcuts.py

import logging

class KeyboardShortcuts:
    def __init__(self, view, controller=None):
        self.view = view
        self.controller = controller
        self.view_type = self._determine_view_type()
        logging.info(f"Initializing keyboard shortcuts for view type: {self.view_type}")
        self.setup_shortcuts()

    def _determine_view_type(self):
        """Determine the type of view we're working with."""
        # Use the class name for more reliable type checking
        view_class_name = self.view.__class__.__name__
        logging.info(f"View class name: {view_class_name}")
        
        if view_class_name == "TimelineView":
            return "timeline"
        elif view_class_name == "ScriptEditorView":
            return "script_editor"
        else:
            logging.warning(f"Unknown view type: {view_class_name}")
            return "unknown"

    def setup_shortcuts(self):
        """Set up shortcuts based on view type."""
        if self.view_type == "timeline":
            self.setup_timeline_shortcuts()
        elif self.view_type == "script_editor":
            self.setup_script_editor_shortcuts()

    def setup_timeline_shortcuts(self):
        """Set up shortcuts for timeline view."""
        try:
            # Use platform-agnostic modifier key
            mod_key = "Command" if hasattr(self.view, "tk") and self.view.tk.call("tk", "windowingsystem") == "aqua" else "Control"
            
            shortcuts = {
                f"<{mod_key}-s>": self.save_project,
                f"<{mod_key}-o>": self.open_project,
                f"<{mod_key}-n>": self.new_project,
                "<space>": self.toggle_playback,
                "s": self.toggle_solo,
                "m": self.toggle_mute,
                "<Up>": self.select_track_up,
                "<Down>": self.select_track_down,
                "n": self.add_new_track,
                f"<{mod_key}-z>": self.undo,
                f"<{mod_key}-Z>": self.redo
            }

            for key, handler in shortcuts.items():
                self.view.bind(key, handler)
                logging.info(f"Bound timeline shortcut: {key}")

        except Exception as e:
            logging.error(f"Error setting up timeline shortcuts: {str(e)}")

    def setup_script_editor_shortcuts(self):
        """Set up shortcuts for script editor view."""
        try:
            # Ensure text_area exists
            if not hasattr(self.view, "text_area"):
                logging.error("text_area not found in script editor view")
                return

            # Use platform-agnostic modifier key
            mod_key = "Command" if hasattr(self.view, "tk") and self.view.tk.call("tk", "windowingsystem") == "aqua" else "Control"

            shortcuts = {
                f"<{mod_key}-b>": self.bold,
                f"<{mod_key}-i>": self.italic,
                f"<{mod_key}-u>": self.underline,
                f"<{mod_key}-f>": self.sfx,
                f"<{mod_key}-m>": self.music
            }

            # Bind speaker shortcuts
            for i in range(5):
                self.view.text_area.bind(
                    f"<{mod_key}-{i+1}>",
                    lambda e, i=i: self.format_as_speaker(f"Speaker {i+1}")
                )
                logging.info(f"Bound speaker shortcut: Control-{i+1}")

            # Bind other shortcuts
            for key, handler in shortcuts.items():
                self.view.text_area.bind(key, handler)
                logging.info(f"Bound script editor shortcut: {key}")

        except Exception as e:
            logging.error(f"Error setting up script editor shortcuts: {str(e)}")

    # Timeline shortcut handlers
    def save_project(self, event):
        logging.debug("Save project shortcut triggered")
        if hasattr(self.view, "controller") and self.view.controller:
            self.view.controller.save_project()
        return "break"

    def open_project(self, event):
        logging.debug("Open project shortcut triggered")
        if hasattr(self.view, "controller") and self.view.controller:
            self.view.controller.open_project()
        return "break"

    def new_project(self, event):
        logging.debug("New project shortcut triggered")
        if hasattr(self.view, "controller") and self.view.controller:
            self.view.controller.new_project()
        return "break"

    def toggle_playback(self, event):
        logging.debug("Toggle playback shortcut triggered")
        if hasattr(self.view, "controller") and self.view.controller:
            if self.view.controller.is_playing():
                self.view.controller.stop_timeline()
            else:
                self.view.controller.play_timeline()
        return "break"

    def toggle_solo(self, event):
        logging.debug("Toggle solo shortcut triggered")
        if hasattr(self.view, "controller") and self.view.controller and self.view.selected_track:
            self.view.controller.toggle_solo(self.view.selected_track)
        return "break"

    def toggle_mute(self, event):
        logging.debug("Toggle mute shortcut triggered")
        if hasattr(self.view, "controller") and self.view.controller and self.view.selected_track:
            self.view.controller.toggle_mute(self.view.selected_track)
        return "break"

    def select_track_up(self, event):
        logging.debug("Select track up shortcut triggered")
        if self.view.selected_track:
            current_index = self.view.tracks.index(self.view.selected_track)
            if current_index > 0:
                self.view.select_track(self.view.tracks[current_index - 1])
        return "break"

    def select_track_down(self, event):
        logging.debug("Select track down shortcut triggered")
        if self.view.selected_track:
            current_index = self.view.tracks.index(self.view.selected_track)
            if current_index < len(self.view.tracks) - 1:
                self.view.select_track(self.view.tracks[current_index + 1])
        return "break"

    def add_new_track(self, event):
        logging.debug("Add new track shortcut triggered")
        if hasattr(self.view, "controller") and self.view.controller:
            self.view.controller.add_track()
        return "break"

    def undo(self, event):
        logging.debug("Undo shortcut triggered")
        if hasattr(self.view, "controller") and self.view.controller:
            self.view.controller.undo_action()
        return "break"

    def redo(self, event):
        logging.debug("Redo shortcut triggered")
        if hasattr(self.view, "controller") and self.view.controller:
            self.view.controller.redo_action()
        return "break"

    # Script Editor shortcut handlers
    def bold(self, event):
        logging.debug("Bold shortcut triggered")
        if self.controller:
            self.controller.format_text('bold')
        return "break"

    def italic(self, event):
        logging.debug("Italic shortcut triggered")
        if self.controller:
            self.controller.format_text('italic')
        return "break"

    def underline(self, event):
        logging.debug("Underline shortcut triggered")
        if self.controller:
            self.controller.format_text('underline')
        return "break"

    def format_as_speaker(self, speaker):
        logging.debug(f"Format as speaker shortcut triggered: {speaker}")
        if self.controller:
            self.controller.format_as_speaker(speaker)
        return "break"

    def sfx(self, event):
        logging.debug("SFX shortcut triggered")
        if self.controller:
            self.controller.format_text('sfx')
        return "break"

    def music(self, event):
        logging.debug("Music shortcut triggered")
        if self.controller:
            self.controller.format_text('music')
        return "break"