import customtkinter as ctk
import tkinter as tk
from tkinter import font as tkfont

import customtkinter as ctk

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
        self.create_widgets()
        self.create_tags()
        self.bind_shortcuts()
        self.bind_text_protection()

    def create_widgets(self):
        self.create_toolbar()
        self.create_main_content()
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

        self.save_button = ctk.CTkButton(toolbar, text="Save", command=self.save_script)
        self.save_button.grid(row=0, column=6, padx=2)

        self.load_button = ctk.CTkButton(toolbar, text="Load", command=self.load_script)
        self.load_button.grid(row=0, column=7, padx=2)

    def create_main_content(self):
        self.paned_window = tk.PanedWindow(self, orient=tk.VERTICAL, sashwidth=10, sashrelief=tk.RAISED, bg='#3E3E3E')
        self.paned_window.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        self.create_text_area()
        self.create_analysis_area()

        # Set initial position of the sash
        self.paned_window.after(10, self.set_initial_sash_position)

    def create_text_area(self):
        text_frame = ctk.CTkFrame(self.paned_window)
        self.text_area = tk.Text(text_frame, wrap=tk.WORD, undo=True)
        self.text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ctk.CTkScrollbar(text_frame, command=self.text_area.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_area.configure(yscrollcommand=scrollbar.set)

        self.paned_window.add(text_frame)

    def create_analysis_area(self):
        analysis_frame = ctk.CTkFrame(self.paned_window)
        analysis_frame.grid_columnconfigure(0, weight=1)
        analysis_frame.grid_rowconfigure(1, weight=1)

        button_frame = ctk.CTkFrame(analysis_frame)
        button_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        button_frame.grid_columnconfigure((0, 1), weight=1)

        self.save_analysis_button = ctk.CTkButton(button_frame, text="Save Analysis")
        self.save_analysis_button.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        self.load_analysis_button = ctk.CTkButton(button_frame, text="Load Analysis")
        self.load_analysis_button.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        self.analysis_text = ctk.CTkTextbox(analysis_frame, state="disabled")
        self.analysis_text.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        self.paned_window.add(analysis_frame)

    def create_status_bar(self):
        self.status_var = tk.StringVar()
        self.status_var.set("")
        self.status_bar = ctk.CTkLabel(self, textvariable=self.status_var, anchor="w")
        self.status_bar.grid(row=2, column=0, sticky="ew", padx=5, pady=2)

    def set_initial_sash_position(self):
        height = self.paned_window.winfo_height()
        self.paned_window.sash_place(0, 0, int(height * 0.7))  # 70% for text area, 30% for analysis
        
    def set_save_analysis_callback(self, callback):
        self.save_analysis_button.configure(command=callback)

    def set_load_analysis_callback(self, callback):
        self.load_analysis_button.configure(command=callback)

    def update_analysis_results(self, analyzed_script, suggested_voices, element_counts, estimated_duration):
        self.analysis_text.configure(state="normal")
        self.analysis_text.delete("1.0", tk.END)
        
        self.analysis_text.insert(tk.END, "Script Analysis Results:\n\n")
        
        self.analysis_text.insert(tk.END, f"Estimated Duration: {estimated_duration:.2f} minutes\n\n")
        
        self.analysis_text.insert(tk.END, "Element Counts:\n")
        for element_type, count in element_counts.items():
            self.analysis_text.insert(tk.END, f"{element_type.capitalize()}: {count}\n")
        
        self.analysis_text.insert(tk.END, "\nSuggested Voices:\n")
        for voice in suggested_voices:
            self.analysis_text.insert(tk.END, f"- {voice}\n")
        
        self.analysis_text.insert(tk.END, "\nScript Overview:\n")
        for element in analyzed_script[:10]:  # Show first 10 elements as an overview
            if element['type'] == 'speech':
                self.analysis_text.insert(tk.END, f"Speech ({element['speaker']}): {element['text'][:30]}...\n")
            elif element['type'] in ['sfx', 'music']:
                self.analysis_text.insert(tk.END, f"{element['type'].upper()}: {element['description'][:30]}...\n")
            else:
                self.analysis_text.insert(tk.END, f"Narration: {element['text'][:30]}...\n")
        
        if len(analyzed_script) > 10:
            self.analysis_text.insert(tk.END, "...\n")
        
        self.analysis_text.configure(state="disabled")

    def create_tags(self):
        bold_font = tkfont.Font(self.text_area, self.text_area.cget("font"))
        bold_font.configure(weight="bold")
        self.text_area.tag_configure("bold", font=bold_font)

        italic_font = tkfont.Font(self.text_area, self.text_area.cget("font"))
        italic_font.configure(slant="italic")
        self.text_area.tag_configure("italic", font=italic_font)
        self.text_area.tag_configure("underline", underline=1)

    def bind_shortcuts(self):
        self.text_area.bind("<Control-b>", lambda e: self.format_text('bold'))
        self.text_area.bind("<Control-i>", lambda e: self.format_text('italic'))
        self.text_area.bind("<Control-u>", lambda e: self.format_text('underline'))
        for i in range(5):
            self.text_area.bind(f"<Control-{i+1}>", lambda e, i=i: self.format_as_speaker(f"Speaker {i+1}"))
        self.text_area.bind("<Control-f>", lambda e: self.format_text('sfx'))
        self.text_area.bind("<Control-m>", lambda e: self.format_text('music'))

    def format_text(self, tag):
        if tag.startswith("speaker"):
            speaker = f"Speaker {tag[-1]}"
            self.format_as_speaker(speaker)
        elif tag in ['sfx', 'music']:
            self.format_as_sfx_or_music(tag)
        elif self.text_area.tag_ranges("sel"):
            start, end = self.text_area.tag_ranges("sel")
            current_tags = self.text_area.tag_names(start)
            
            if tag in current_tags:
                self.text_area.tag_remove(tag, start, end)
            else:
                self.text_area.tag_add(tag, start, end)

            self.update_button_states(tag)
        else:
            self.status_var.set("Please select text to format")

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

    def update_status(self, message):
        self.status_var.set(message)