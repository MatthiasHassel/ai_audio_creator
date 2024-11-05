import customtkinter as ctk
import os
from tkinter import messagebox
from dotenv import load_dotenv, set_key, find_dotenv

class PreferencesWindow(ctk.CTkToplevel):
    def __init__(self, master, config):
        super().__init__(master)
        self.config = config
        
        # Window setup
        self.title("Preferences")
        self.geometry("700x400")
        self.resizable(False, False)
        
        # Initialize variables
        self.api_vars = {
            'elevenlabs': ctk.StringVar(),
            'openai': ctk.StringVar(),
            'suno_cookie': ctk.StringVar(),
            'suno_session': ctk.StringVar()
        }
        
        self.create_widgets()
        self.load_preferences()
        
        # Make window modal
        self.transient(master)
        self.grab_set()

    def create_widgets(self):
        # Main frame
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(main_frame, text="API Keys", font=("Arial", 18, "bold"))
        title_label.pack(pady=(0, 20))
        
        # API Key inputs
        self.create_api_entry(main_frame, "ElevenLabs API Key:", 'elevenlabs')
        self.create_api_entry(main_frame, "OpenAI API Key:", 'openai')
        self.create_api_entry(main_frame, "Suno Cookie:", 'suno_cookie')
        self.create_api_entry(main_frame, "Suno Session ID:", 'suno_session')
        
        # Buttons
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill="x", pady=(20, 0))
        
        save_button = ctk.CTkButton(button_frame, text="Save", command=self.save_preferences)
        save_button.pack(side="right", padx=5)
        
        cancel_button = ctk.CTkButton(button_frame, text="Cancel", command=self.destroy)
        cancel_button.pack(side="right", padx=5)

    def create_api_entry(self, parent, label_text, key):
        frame = ctk.CTkFrame(parent)
        frame.pack(fill="x", pady=5)
        frame.grid_columnconfigure(1, weight=1)  # Make the entry field expand
        
        label = ctk.CTkLabel(frame, text=label_text, width=120, anchor="w")  # Set anchor="w" for left alignment
        label.grid(row=0, column=0, padx=(10, 10), sticky="w")  # Use grid and sticky="w" for left alignment
        
        entry = ctk.CTkEntry(frame, textvariable=self.api_vars[key], show="*", width=300)
        entry.grid(row=0, column=1, sticky="ew", padx=(0, 5))  # Make entry expand horizontally
        
        def toggle_visibility():
            current = entry.cget("show")
            entry.configure(show="" if current == "*" else "*")
            
        toggle_button = ctk.CTkButton(frame, text="👁", width=30, command=toggle_visibility)
        toggle_button.grid(row=0, column=2, padx=5)

    def get_env_files(self):
        # Get the directory paths
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        main_env_path = os.path.join(base_dir, '.env')
        suno_env_path = os.path.join(base_dir, 'suno_api', '.env')
        
        # Create main .env file if it doesn't exist
        if not os.path.exists(main_env_path):
            with open(main_env_path, 'w') as f:
                f.write('# API Keys\n')
        
        # Create suno_api .env file if it doesn't exist
        os.makedirs(os.path.dirname(suno_env_path), exist_ok=True)
        if not os.path.exists(suno_env_path):
            with open(suno_env_path, 'w') as f:
                f.write('# Suno API Keys\n')
        
        return main_env_path, suno_env_path

    def load_preferences(self):
        try:
            main_env_path, suno_env_path = self.get_env_files()
            
            # Load both .env files
            load_dotenv(main_env_path)
            load_dotenv(suno_env_path)
            
            # Load values from environment variables
            self.api_vars['elevenlabs'].set(os.getenv('ELEVENLABS_API_KEY', ''))
            self.api_vars['openai'].set(os.getenv('OPENAI_API_KEY', ''))
            self.api_vars['suno_cookie'].set(os.getenv('SUNO_COOKIE', ''))
            self.api_vars['suno_session'].set(os.getenv('SUNO_SESSION_ID', ''))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load preferences: {str(e)}")

    def save_preferences(self):
        try:
            # Validate that required keys are not empty
            if not self.api_vars['elevenlabs'].get() or not self.api_vars['openai'].get():
                messagebox.showerror("Error", "ElevenLabs and OpenAI API keys are required.")
                return
            
            main_env_path, suno_env_path = self.get_env_files()
            
            # Update main .env file
            set_key(main_env_path, 'ELEVENLABS_API_KEY', self.api_vars['elevenlabs'].get())
            set_key(main_env_path, 'OPENAI_API_KEY', self.api_vars['openai'].get())
            set_key(main_env_path, 'SUNO_COOKIE', self.api_vars['suno_cookie'].get())
            set_key(main_env_path, 'SUNO_SESSION_ID', self.api_vars['suno_session'].get())
            
            # Update suno_api .env file
            set_key(suno_env_path, 'SUNO_COOKIE', self.api_vars['suno_cookie'].get())
            set_key(suno_env_path, 'SUNO_SESSION_ID', self.api_vars['suno_session'].get())
            
            # Reload environment variables
            load_dotenv(main_env_path)
            load_dotenv(suno_env_path)
            
            messagebox.showinfo("Success", "API keys saved successfully!")
            self.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save API keys: {str(e)}")

    def on_closing(self):
        self.destroy()