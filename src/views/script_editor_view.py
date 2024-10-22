import customtkinter as ctk
import tkinter as tk
import tkinter.font as tkfont
from tkinter import font
import customtkinter as ctk
from utils.keyboard_shortcuts import KeyboardShortcuts
import logging


class SplitButton(ctk.CTkFrame):
    def __init__(self, master, options, command, **kwargs):
        super().__init__(master, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)

        self.current_option = ctk.StringVar(value=options[0])
        self.command = command
        self.options = options

        # Remove 'text' from kwargs if it exists, as we're using self.current_option.get()
        kwargs.pop('text', None)
        
        self.main_button = ctk.CTkButton(self, text=self.current_option.get(), command=self.on_main_button_click, **kwargs)
        self.main_button.grid(row=0, column=0, sticky="ew")

        self.dropdown_button = ctk.CTkButton(self, text="▼", width=20, command=self.toggle_dropdown)
        self.dropdown_button.grid(row=0, column=1)

        self.dropdown_window = None

        # Bind click event to close dropdown when clicking outside
        self.master.bind("<Button-1>", self.close_dropdown_on_click_outside, add="+")

    def on_main_button_click(self):
        self.command(self.current_option.get())

    def toggle_dropdown(self):
        if self.dropdown_window and self.dropdown_window.winfo_exists():
            self.dropdown_window.destroy()
        else:
            self.show_dropdown()

    def show_dropdown(self):
        self.dropdown_window = tk.Toplevel(self)
        self.dropdown_window.overrideredirect(True)
        self.dropdown_window.attributes('-topmost', 'true')

        # Position the dropdown below the button
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height()
        self.dropdown_window.geometry(f"+{x}+{y}")

        # Create a frame inside the Toplevel for styling
        dropdown_frame = ctk.CTkFrame(self.dropdown_window)
        dropdown_frame.pack(expand=True, fill="both")

        for option in self.options:
            btn = ctk.CTkButton(dropdown_frame, text=option, command=lambda o=option: self.on_option_select(o))
            btn.pack(fill="x", expand=True)

    def on_option_select(self, choice):
        self.current_option.set(choice)
        self.main_button.configure(text=choice)
        if self.dropdown_window:
            self.dropdown_window.destroy()
        self.command(choice)

    def close_dropdown_on_click_outside(self, event):
        if self.dropdown_window and self.dropdown_window.winfo_exists():
            if not (self.dropdown_window.winfo_containing(event.x_root, event.y_root) in 
                    [self.dropdown_window] + self.dropdown_window.winfo_children()):
                self.dropdown_window.destroy()

    def set_active(self, is_active):
        if is_active:
            self.main_button.configure(fg_color="darkblue")
        else:
            self.main_button.configure(fg_color=["#3B8ED0", "#1F6AA5"])

class ScriptEditorView(ctk.CTkFrame):
    def __init__(self, master, config):
        super().__init__(master)
        self.config = config
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.current_speaker = ctk.StringVar(value="Speaker 1")
        self.current_font = tkfont.Font(family="TkDefaultFont", size=12)
        self.format_states = {'bold': False, 'italic': False, 'underline': False}
        self.keyboard_shortcuts = None
        self.create_widgets()
        self.create_tags()
        self.text_area.tag_add("base_font", "1.0", "end")
        self.bind_text_protection()

    def setup_keyboard_shortcuts(self, controller):
        logging.info("Setting up keyboard shortcuts for ScriptEditorView")
        self.keyboard_shortcuts = KeyboardShortcuts(self, controller)

    def create_widgets(self):
        self.create_toolbar()
        self.create_main_content()
        self.create_bottom_toolbar()
        self.create_status_bar()

    def create_toolbar(self):
        toolbar = ctk.CTkFrame(self)
        toolbar.grid(row=0, column=0, sticky="ew", padx=5, pady=(5, 2))
        toolbar.grid_columnconfigure(7, weight=1)  # Push buttons to the left

        self.bold_button = ctk.CTkButton(toolbar, text="B", width=30, command=lambda: self.format_text('bold'))
        self.bold_button.grid(row=0, column=0, padx=2)

        self.italic_button = ctk.CTkButton(toolbar, text="I", width=30, command=lambda: self.format_text('italic'))
        self.italic_button.grid(row=0, column=1, padx=2)

        self.underline_button = ctk.CTkButton(toolbar, text="U", width=30, command=lambda: self.format_text('underline'))
        self.underline_button.grid(row=0, column=2, padx=2)

        self.create_font_controls(toolbar)

        # Speaker split button
        speaker_options = [f"Speaker {i+1}" for i in range(5)]
        self.speaker_button = SplitButton(toolbar, options=speaker_options, 
                                          command=self.format_as_speaker,
                                          width=120)
        self.speaker_button.grid(row=0, column=3, padx=2)

        self.sfx_button = ctk.CTkButton(toolbar, text="SFX", width=50, command=lambda: self.format_text('sfx'))
        self.sfx_button.grid(row=0, column=4, padx=2)

        self.music_button = ctk.CTkButton(toolbar, text="Music", width=50, command=lambda: self.format_text('music'))
        self.music_button.grid(row=0, column=5, padx=2)

    def create_main_content(self):
        self.text_area = tk.Text(self, wrap=tk.WORD, undo=True, font=self.current_font)
        self.text_area.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.text_area.bind("<Key>", self.apply_current_formatting)

        scrollbar = ctk.CTkScrollbar(self, command=self.text_area.yview)
        scrollbar.grid(row=1, column=1, sticky="ns", pady=5)
        self.text_area.configure(yscrollcommand=scrollbar.set)

    def create_bottom_toolbar(self):
        bottom_toolbar = ctk.CTkFrame(self)
        bottom_toolbar.grid(row=2, column=0, columnspan=2, sticky="ew", padx=5, pady=(2, 5))
        bottom_toolbar.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.save_button = ctk.CTkButton(bottom_toolbar, text="Save Script", command=self.save_script)
        self.save_button.grid(row=0, column=0, padx=2, pady=2, sticky="ew")

        self.load_button = ctk.CTkButton(bottom_toolbar, text="Load Script", command=self.load_script)
        self.load_button.grid(row=0, column=1, padx=2, pady=2, sticky="ew")

        self.import_pdf_button = ctk.CTkButton(bottom_toolbar, text="Import PDF", command=self.import_pdf)
        self.import_pdf_button.grid(row=0, column=2, padx=2, pady=2, sticky="ew")

        self.analyze_script_button = ctk.CTkButton(bottom_toolbar, text="Analyze Script", command=self.analyze_script)
        self.analyze_script_button.grid(row=0, column=3, padx=2, pady=2, sticky="ew")

        self.create_audio_button = ctk.CTkButton(bottom_toolbar, text="Create Audio", command=self.create_audio)
        self.create_audio_button.grid(row=0, column=4, padx=2, pady=2, sticky="ew")

    def create_status_bar(self):
        status_frame = ctk.CTkFrame(self)
        status_frame.grid(row=3, column=0, columnspan=2, sticky="ew", padx=5, pady=(2, 5))
        status_frame.grid_columnconfigure(0, weight=1)

        self.progress_bar = ctk.CTkProgressBar(status_frame)
        self.progress_bar.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        self.progress_bar.set(0)
        self.progress_bar.grid_remove()  # Initially hidden

        self.status_var = tk.StringVar()
        self.status_var.set("")
        self.status_bar = ctk.CTkLabel(status_frame, textvariable=self.status_var, anchor="w")
        self.status_bar.grid(row=1, column=0, sticky="ew")

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

    def update_status(self, message):
        self.status_var.set(message)
                                           
    def create_tags(self):
        self.text_area.tag_configure("base_font", font=self.current_font)
        self.text_area.tag_configure("bold", font=(self.current_font.actual()['family'], self.current_font.actual()['size'], "bold"))
        self.text_area.tag_configure("italic", font=(self.current_font.actual()['family'], self.current_font.actual()['size'], "italic"))
        self.text_area.tag_configure("underline", underline=1)

    def format_text(self, tag):
        if tag in ['bold', 'italic', 'underline']:
            if self.text_area.tag_ranges("sel"):
                start, end = self.text_area.tag_ranges("sel")
                if tag in self.text_area.tag_names(start):
                    self.text_area.tag_remove(tag, start, end)
                    self.format_states[tag] = False
                else:
                    self.text_area.tag_add(tag, start, end)
                    self.format_states[tag] = True
            else:
                self.format_states[tag] = not self.format_states[tag]
            
            self.update_button_states(tag)
        elif tag.startswith("speaker"):
            self.format_as_speaker(f"Speaker {tag[-1]}")
        elif tag in ['sfx', 'music']:
            self.format_as_sfx_or_music(tag)
        
        # Ensure the base font is applied
        self.text_area.tag_add("base_font", "1.0", "end")

    def create_font_controls(self, parent):
        font_frame = ctk.CTkFrame(parent)
        font_frame.grid(row=0, column=6, padx=5, sticky="e")

        self.font_family_var = ctk.StringVar(value=self.current_font.actual()['family'])
        self.font_size_var = ctk.StringVar(value=str(self.current_font.actual()['size']))

        font_family_menu = ctk.CTkOptionMenu(font_frame, variable=self.font_family_var, values=font.families(), command=self.update_font)
        font_family_menu.grid(row=0, column=0, padx=5)

        font_size_menu = ctk.CTkOptionMenu(font_frame, variable=self.font_size_var, values=[str(i) for i in range(8, 25)], command=self.update_font)
        font_size_menu.grid(row=0, column=1, padx=5)

    def update_font(self, *args):
        family = self.font_family_var.get()
        size = int(self.font_size_var.get())
        self.current_font.configure(family=family, size=size)
        self.text_area.configure(font=self.current_font)
        
        # Update tags
        self.text_area.tag_configure("base_font", font=self.current_font)
        self.text_area.tag_configure("bold", font=(family, size, "bold"))
        self.text_area.tag_configure("italic", font=(family, size, "italic"))
        
        # Reapply base_font tag to all text
        self.text_area.tag_add("base_font", "1.0", "end")
        
        # Notify the controller to save preferences
        if hasattr(self, 'on_font_change'):
            self.on_font_change()

    def format_as_speaker(self, speaker):
        start_index = self.text_area.index(tk.INSERT + " linestart")
        end_index = self.text_area.index(tk.INSERT + " lineend")
        line_content = self.text_area.get(start_index, end_index).strip()

        if self.text_area.tag_ranges("sel"):
            # If text is selected
            start_sel, end_sel = self.text_area.tag_ranges("sel")
            selected_text = self.text_area.get(start_sel, end_sel)
            formatted_text = f'**{speaker}:** "{selected_text}"'
            self.text_area.delete(start_sel, end_sel)
            self.text_area.insert(start_sel, formatted_text)
        elif line_content.startswith("**") and ":**" in line_content:
            # If the line already has speaker formatting, update the speaker
            colon_index = line_content.index(":**")
            new_line = f"**{speaker}:{line_content[colon_index:]}"
            self.text_area.delete(start_index, end_index)
            self.text_area.insert(start_index, new_line)
        else:
            # If no text is selected and line doesn't have speaker formatting
            cursor_position = self.text_area.index(tk.INSERT)
            formatted_text = f'**{speaker}:** ""'
            self.text_area.insert(cursor_position, formatted_text)
            new_cursor_position = self.text_area.index(f"{cursor_position}+{len(formatted_text)-1}c")
            self.text_area.mark_set(tk.INSERT, new_cursor_position)

        self.speaker_button.current_option.set(speaker)
        self.speaker_button.main_button.configure(text=speaker)

    def format_as_sfx_or_music(self, tag):
        start_index = self.text_area.index(tk.INSERT + " linestart")
        end_index = self.text_area.index(tk.INSERT + " lineend")
        line_content = self.text_area.get(start_index, end_index).strip()

        tag_upper = tag.upper()
        if self.text_area.tag_ranges("sel"):
            start_sel, end_sel = self.text_area.tag_ranges("sel")
            selected_text = self.text_area.get(start_sel, end_sel)
            formatted_text = f'[{tag_upper}: {selected_text}]'
            self.text_area.delete(start_sel, end_sel)
            self.text_area.insert(start_sel, formatted_text)
        elif line_content.startswith(f"[{tag_upper}:") and line_content.endswith("]"):
            # If the line already has SFX or Music formatting, don't modify it
            pass
        else:
            # If no text is selected and line doesn't have formatting
            cursor_position = self.text_area.index(tk.INSERT)
            formatted_text = f'[{tag_upper}: ]'
            self.text_area.insert(cursor_position, formatted_text)
            new_cursor_position = self.text_area.index(f"{cursor_position}+{len(formatted_text)-1}c")
            self.text_area.mark_set(tk.INSERT, new_cursor_position)

    def bind_text_protection(self):
        self.text_area.bind("<KeyPress>", self.handle_keypress)
        self.text_area.bind("<KeyRelease>", self.handle_keyrelease)

    def handle_keypress(self, event):
        if event.keysym in ['Return', 'Left', 'Right', 'BackSpace', 'Delete']:
            cursor_index = self.text_area.index(tk.INSERT)
            line_start = self.text_area.index(f"{cursor_index} linestart")
            line_end = self.text_area.index(f"{cursor_index} lineend")
            line_content = self.text_area.get(line_start, line_end)

            if ('**' in line_content and ':**' in line_content) or \
               ('[SFX:' in line_content and line_content.endswith(']')) or \
               ('[MUSIC:' in line_content and line_content.endswith(']')):
                if event.keysym == 'Return':
                    if event.state & 0x1:  # Check if Shift key is pressed
                        return self.handle_shift_return(event)
                    else:
                        return self.handle_return(event)
                elif event.keysym == 'Left':
                    return self.handle_left_arrow(event)
                elif event.keysym == 'Right':
                    return self.handle_right_arrow(event)
                elif event.keysym == 'BackSpace':
                    return self.handle_backspace(event)
                elif event.keysym == 'Delete':
                    return self.handle_delete(event)
        return None

    def handle_keyrelease(self, event):
        # Trigger analysis on key release
        if hasattr(self, 'on_text_changed'):
            self.on_text_changed(event)

    def handle_return(self, event):
        cursor_index = self.text_area.index(tk.INSERT)
        line_start = self.text_area.index(f"{cursor_index} linestart")
        line_end = self.text_area.index(f"{cursor_index} lineend")
        line_content = self.text_area.get(line_start, line_end)

        if ('**' in line_content and ':**' in line_content) or \
           ('[SFX:' in line_content and line_content.endswith(']')) or \
           ('[MUSIC:' in line_content and line_content.endswith(']')):
            # Move cursor to end of line and insert new line
            self.text_area.mark_set(tk.INSERT, line_end)
            self.text_area.insert(tk.INSERT, "\n")
            return "break"  # Prevent default behavior

        return None  # Allow default behavior

    def handle_shift_return(self, event):
        cursor_index = self.text_area.index(tk.INSERT)
        line_start = self.text_area.index(f"{cursor_index} linestart")
        line_end = self.text_area.index(f"{cursor_index} lineend")
        line_content = self.text_area.get(line_start, line_end)

        if ('**' in line_content and ':**' in line_content) or \
           ('[SFX:' in line_content and line_content.endswith(']')) or \
           ('[MUSIC:' in line_content and line_content.endswith(']')):
            # Insert a line break at the current cursor position
            self.text_area.insert(tk.INSERT, "\n")
            return "break"  # Prevent default behavior

        return None  # Allow default behavior for non-formatted lines

    def handle_left_arrow(self, event):
        cursor_index = self.text_area.index(tk.INSERT)
        line_start = self.text_area.index(f"{cursor_index} linestart")
        line_content = self.text_area.get(line_start, cursor_index)

        if '**' in line_content and ':**' in line_content and '"' in line_content:
            quote_index = line_content.rfind('"')
            if quote_index != -1 and self.text_area.compare(cursor_index, "==", f"{line_start}+{quote_index+1}c"):
                return "break"  # Prevent moving left of the opening quote
        elif ('[SFX:' in line_content or '[MUSIC:' in line_content) and ':' in line_content:
            colon_index = line_content.find(':')
            if self.text_area.compare(cursor_index, "==", f"{line_start}+{colon_index+1}c"):
                return "break"  # Prevent moving left of the colon

        return None  # Allow default behavior

    def handle_right_arrow(self, event):
        cursor_index = self.text_area.index(tk.INSERT)
        line_end = self.text_area.index(f"{cursor_index} lineend")
        line_content = self.text_area.get(cursor_index, line_end)

        if '"' in line_content:
            quote_index = line_content.find('"')
            if quote_index != -1 and self.text_area.compare(cursor_index, "==", f"{cursor_index}+{quote_index}c"):
                return "break"  # Prevent moving right of the closing quote
        elif ']' in line_content:
            bracket_index = line_content.find(']')
            if bracket_index != -1 and self.text_area.compare(cursor_index, "==", f"{cursor_index}+{bracket_index}c"):
                return "break"  # Prevent moving right of the closing bracket

        return None  # Allow default behavior

    def handle_backspace(self, event):
        cursor_index = self.text_area.index(tk.INSERT)
        line_start = self.text_area.index(f"{cursor_index} linestart")
        line_content = self.text_area.get(line_start, cursor_index)

        if '**' in line_content and ':**' in line_content:
            colon_index = line_content.find(':**')
            if self.text_area.compare(cursor_index, "<=", f"{line_start}+{colon_index+3}c"):
                return "break"  # Prevent deleting the speaker format
        elif ('[SFX:' in line_content or '[MUSIC:' in line_content) and ':' in line_content:
            colon_index = line_content.find(':')
            if self.text_area.compare(cursor_index, "<=", f"{line_start}+{colon_index+1}c"):
                return "break"  # Prevent deleting the SFX or Music format

        return None  # Allow default behavior

    def handle_delete(self, event):
        cursor_index = self.text_area.index(tk.INSERT)
        line_end = self.text_area.index(f"{cursor_index} lineend")
        line_content = self.text_area.get(cursor_index, line_end)

        if '**' in line_content and ':**' in line_content:
            if line_content.startswith('**'):
                colon_index = line_content.find(':**')
                if self.text_area.compare(cursor_index, "<", f"{cursor_index}+{colon_index+3}c"):
                    return "break"  # Prevent deleting the speaker format
        elif line_content.startswith('[SFX:') or line_content.startswith('[MUSIC:'):
            colon_index = line_content.find(':')
            if self.text_area.compare(cursor_index, "<", f"{cursor_index}+{colon_index+1}c"):
                return "break"  # Prevent deleting the SFX or Music format
        
        if line_content.endswith(']'):
            if self.text_area.compare(cursor_index, "==", f"{line_end}-1c"):
                return "break"  # Prevent deleting the closing bracket

        return None  # Allow default behavior

    def update_button_states(self, active_tag):
        self.bold_button.configure(fg_color="darkblue" if active_tag == "bold" else ["#3B8ED0", "#1F6AA5"])
        self.italic_button.configure(fg_color="darkblue" if active_tag == "italic" else ["#3B8ED0", "#1F6AA5"])
        self.underline_button.configure(fg_color="darkblue" if active_tag == "underline" else ["#3B8ED0", "#1F6AA5"])
        self.speaker_button.set_active(active_tag.startswith("speaker"))
        self.sfx_button.configure(fg_color="darkblue" if active_tag == "sfx" else ["#3B8ED0", "#1F6AA5"])
        self.music_button.configure(fg_color="darkblue" if active_tag == "music" else ["#3B8ED0", "#1F6AA5"])

    def save_script(self):
        # Implementation for saving the script
        pass

    def load_script(self):
        # Implementation for loading the script
        pass

    def get_text(self):
        return self.text_area.get("1.0", tk.END)

    def set_text(self, text):
        self.text_area.delete("1.0", tk.END)
        self.text_area.insert(tk.END, text)
        self.text_area.tag_add("base_font", "1.0", "end")

    def update_button_states(self, active_tag):
        self.bold_button.configure(fg_color="darkblue" if self.format_states['bold'] else ["#3B8ED0", "#1F6AA5"])
        self.italic_button.configure(fg_color="darkblue" if self.format_states['italic'] else ["#3B8ED0", "#1F6AA5"])
        self.underline_button.configure(fg_color="darkblue" if self.format_states['underline'] else ["#3B8ED0", "#1F6AA5"])
        self.speaker_button.set_active(active_tag.startswith("speaker"))
        self.sfx_button.configure(fg_color="darkblue" if active_tag == "sfx" else ["#3B8ED0", "#1F6AA5"])
        self.music_button.configure(fg_color="darkblue" if active_tag == "music" else ["#3B8ED0", "#1F6AA5"])

    def apply_current_formatting(self, event):
        index = self.text_area.index("insert")
        for tag, state in self.format_states.items():
            if state:
                self.text_area.tag_add(tag, index)

    def import_pdf(self):
        if self.import_pdf_callback:
            self.import_pdf_callback()

    def analyze_script(self):
        if self.analyze_script_callback:
            self.analyze_script_callback()

    def set_import_pdf_callback(self, callback):
        self.import_pdf_callback = callback

    def set_analyze_script_callback(self, callback):
        self.analyze_script_callback = callback

    def create_audio(self):
        if self.create_audio_callback:
            self.create_audio_callback()

    def set_create_audio_callback(self, callback):
        self.create_audio_callback = callback