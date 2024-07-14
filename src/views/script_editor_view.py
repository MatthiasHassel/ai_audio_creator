import customtkinter as ctk
import tkinter as tk

class ScriptEditorView(ctk.CTkFrame):
    def __init__(self, master, config):
        super().__init__(master)
        self.config = config
        self.create_widgets()

    def create_widgets(self):
        self.create_toolbar()
        self.create_text_area()
        self.create_status_bar()

    def create_toolbar(self):
        toolbar = ctk.CTkFrame(self)
        toolbar.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))

        self.bold_button = ctk.CTkButton(toolbar, text="B", width=30, command=lambda: self.format_text('bold'))
        self.bold_button.pack(side=tk.LEFT, padx=2)

        self.italic_button = ctk.CTkButton(toolbar, text="I", width=30, command=lambda: self.format_text('italic'))
        self.italic_button.pack(side=tk.LEFT, padx=2)

        self.underline_button = ctk.CTkButton(toolbar, text="U", width=30, command=lambda: self.format_text('underline'))
        self.underline_button.pack(side=tk.LEFT, padx=2)

        self.save_button = ctk.CTkButton(toolbar, text="Save", command=self.save_script)
        self.save_button.pack(side=tk.LEFT, padx=2)

        self.load_button = ctk.CTkButton(toolbar, text="Load", command=self.load_script)
        self.load_button.pack(side=tk.LEFT, padx=2)

    def create_text_area(self):
        self.text_area = tk.Text(self, wrap=tk.WORD, undo=True)
        self.text_area.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        scrollbar = ctk.CTkScrollbar(self, command=self.text_area.yview)
        scrollbar.grid(row=1, column=1, sticky="ns")
        self.text_area.configure(yscrollcommand=scrollbar.set)

    def create_status_bar(self):
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        self.status_bar = ctk.CTkLabel(self, textvariable=self.status_var, anchor="w")
        self.status_bar.grid(row=2, column=0, sticky="ew", padx=10, pady=5)

    def format_text(self, style):
        # This method will be implemented in the controller
        pass

    def save_script(self):
        # This method will be implemented in the controller
        pass

    def load_script(self):
        # This method will be implemented in the controller
        pass

    def get_text(self):
        return self.text_area.get("1.0", tk.END)

    def set_text(self, text):
        self.text_area.delete("1.0", tk.END)
        self.text_area.insert(tk.END, text)

    def update_status(self, message):
        self.status_var.set(message)