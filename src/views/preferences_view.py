import customtkinter as ctk
import os
import json
from tkinter import messagebox
from dotenv import load_dotenv, set_key, find_dotenv

class PreferencesWindow(ctk.CTkToplevel):
    def __init__(self, master, config):
        super().__init__(master)
        self.config = config
        self.prompts_config = self.load_prompts_config()

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
        
        # Create notebook for tabs
        self.notebook = ctk.CTkTabview(main_frame)
        self.notebook.pack(fill="both", expand=True, pady=(0, 20))
        
        # API Keys tab
        api_tab = self.notebook.add("API Keys")
        self.create_api_tab(api_tab)
        
        # Prompts tab
        prompts_tab = self.notebook.add("Prompts")
        self.create_prompts_tab(prompts_tab)
        
        # Buttons
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill="x", pady=(20, 0))
        
        save_button = ctk.CTkButton(button_frame, text="Save", command=self.save_preferences)
        save_button.pack(side="right", padx=5)
        
        cancel_button = ctk.CTkButton(button_frame, text="Cancel", command=self.destroy)
        cancel_button.pack(side="right", padx=5)

    def create_prompts_tab(self, parent):
        # Create variables
        self.sfx_prompt_var = ctk.StringVar(value=self.prompts_config.get('sfx_improvement', ''))
        self.music_prompt_var = ctk.StringVar(value=self.prompts_config.get('music_improvement', ''))
        self.script_analysis_pre_var = ctk.StringVar(value=self.prompts_config.get('script_analysis_pre', ''))

        # Create scrollable frame
        scrollable_frame = ctk.CTkScrollableFrame(parent)
        scrollable_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Store references to text boxes
        self.prompt_text_boxes = {}
        
        # SFX Prompt (90 height for ~4 lines)
        self.prompt_text_boxes['sfx'] = self.create_prompt_entry(
            scrollable_frame, 
            "SFX Improvement Pre-Prompt:", 
            self.sfx_prompt_var,
            "Pre-prompt used when improving SFX descriptions",
            """Generate a good prompt for a generative AI Model which creates Sound Effects based on this sound effect description:""",
            height=90
        )
        
        # Music Prompt (90 height for ~4 lines)
        self.prompt_text_boxes['music'] = self.create_prompt_entry(
            scrollable_frame, 
            "Music Improvement Pre-Prompt:", 
            self.music_prompt_var,
            "Pre-prompt used when improving music descriptions",
            """Generate a good prompt for a generative AI Model which creates Music based on this music piece description:""",
            height=90
        )
        
        # Script Analysis Pre-Prompt (300 height for ~15-20 lines)
        self.prompt_text_boxes['script'] = self.create_prompt_entry(
            scrollable_frame, 
            "Script Analysis Pre-Prompt:", 
            self.script_analysis_pre_var,
            "Pre-prompt used for initial script analysis instruction",
            """I have a script for an audio play that I would like to analyze and categorize. Please analyze each line in the script and categorize it as follows:

1. Determine if the line is a spoken sentence by a character, a description of a sound effect (SFX), or a description of music. If the estimated length of a music piece is below 22s categorize it as SFX
2. If it is a spoken sentence by a character, identify the character's name.
3. If it is an SFX, estimate the duration of the sound (between 0.5 and 22 seconds).
4. If it is music, specify whether it is instrumental or with vocals. Use "instrumental": "yes" for instrumental music and "instrumental": "no" for music with vocals.
5. Maintain the order of the lines as they appear in the script, and assign an index to each line.
6. Include two additional parts in the JSON:
    - Needed Speaker Tracks: List all the characternames in the script. 
    - Voice Characteristics: Analyze the emotional content of the sentence and describe the voice characteristics of each speaker.""",
            height=300
        )

        # Add Restore All Defaults button at the bottom
        restore_all_frame = ctk.CTkFrame(scrollable_frame)
        restore_all_frame.pack(fill="x", pady=(20, 5))
        
        restore_all_button = ctk.CTkButton(
            restore_all_frame, 
            text="Restore All Defaults", 
            command=self.restore_all_defaults,
            fg_color="red",
            hover_color="darkred"
        )
        restore_all_button.pack(pady=10)
    
    def create_prompt_entry(self, parent, label_text, variable, description, default_value, height=60):
        frame = ctk.CTkFrame(parent)
        frame.pack(fill="x", pady=5, padx=5)
        
        # Header frame with label and restore button
        header_frame = ctk.CTkFrame(frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(5, 0))
        
        label = ctk.CTkLabel(header_frame, text=label_text)
        label.pack(side="left", pady=(5, 0))
        
        restore_button = ctk.CTkButton(
            header_frame, 
            text="Restore Default", 
            command=lambda: self.restore_default(text_box, variable, default_value),
            width=100,
            height=25,
            fg_color="gray40",
            hover_color="gray30"
        )
        restore_button.pack(side="right", padx=5)
        
        text_box = ctk.CTkTextbox(frame, height=height)  # Use the height parameter
        text_box.pack(fill="x", pady=(5, 0))
        text_box.insert("1.0", variable.get())
        
        # Update variable when text changes
        def update_var(*args):
            variable.set(text_box.get("1.0", "end-1c"))
        text_box.bind('<KeyRelease>', update_var)
        
        description_label = ctk.CTkLabel(frame, text=description, text_color="gray60")
        description_label.pack(anchor="w", pady=(5, 10))
        
        return text_box  # Return the text_box for reference


    def restore_default(self, text_box, variable, default_value):
        """Restore default value for a single prompt"""
        text_box.delete("1.0", "end")
        text_box.insert("1.0", default_value)
        variable.set(default_value)

    def restore_all_defaults(self):
        """Restore all prompts to their default values"""
        default_prompts = {
            'sfx_improvement': "Generate a good prompt for a generative AI Model which creates Sound Effects based on this sound effect description:",
            'music_improvement': "Generate a good prompt for a generative AI Model which creates Music based on this music piece description:",
            'script_analysis_pre': """I have a script for an audio play that I would like to analyze and categorize. Please analyze each line in the script and categorize it as follows:

1. Determine if the line is a spoken sentence by a character, a description of a sound effect (SFX), or a description of music. If the estimated length of a music piece is below 22s categorize it as SFX
2. If it is a spoken sentence by a character, identify the character's name.
3. If it is an SFX, estimate the duration of the sound (between 0.5 and 22 seconds).
4. If it is music, specify whether it is instrumental or with vocals. Use "instrumental": "yes" for instrumental music and "instrumental": "no" for music with vocals.
5. Maintain the order of the lines as they appear in the script, and assign an index to each line.
6. Include two additional parts in the JSON:
    - Needed Speaker Tracks: List all the characternames in the script. 
    - Voice Characteristics: Analyze the emotional content of the sentence and describe the voice characteristics of each speaker."""
        }
        
        # Update variables with default values
        self.sfx_prompt_var.set(default_prompts['sfx_improvement'])
        self.music_prompt_var.set(default_prompts['music_improvement'])
        self.script_analysis_pre_var.set(default_prompts['script_analysis_pre'])
        
        # Update all text boxes using our stored references
        self.prompt_text_boxes['sfx'].delete("1.0", "end")
        self.prompt_text_boxes['sfx'].insert("1.0", default_prompts['sfx_improvement'])
        
        self.prompt_text_boxes['music'].delete("1.0", "end")
        self.prompt_text_boxes['music'].insert("1.0", default_prompts['music_improvement'])
        
        self.prompt_text_boxes['script'].delete("1.0", "end")
        self.prompt_text_boxes['script'].insert("1.0", default_prompts['script_analysis_pre'])
    
    def create_api_tab(self, parent):
        """Create the API Keys tab content."""
        # Create API Key entries
        self.create_api_entry(parent, "ElevenLabs API Key:", 'elevenlabs')
        self.create_api_entry(parent, "OpenAI API Key:", 'openai')
        self.create_api_entry(parent, "Suno Cookie:", 'suno_cookie')
        self.create_api_entry(parent, "Suno Session ID:", 'suno_session')

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
            # Save API keys
            main_env_path, suno_env_path = self.get_env_files()
            
            # Update main .env file
            set_key(main_env_path, 'ELEVENLABS_API_KEY', self.api_vars['elevenlabs'].get())
            set_key(main_env_path, 'OPENAI_API_KEY', self.api_vars['openai'].get())
            set_key(main_env_path, 'SUNO_COOKIE', self.api_vars['suno_cookie'].get())
            set_key(main_env_path, 'SUNO_SESSION_ID', self.api_vars['suno_session'].get())
            
            # Update suno_api .env file
            set_key(suno_env_path, 'SUNO_COOKIE', self.api_vars['suno_cookie'].get())
            set_key(suno_env_path, 'SUNO_SESSION_ID', self.api_vars['suno_session'].get())
            
            # Save prompts
            self.save_prompts_config()
            
            # Reload environment variables
            load_dotenv(main_env_path)
            load_dotenv(suno_env_path)
            
            messagebox.showinfo("Success", "Settings saved successfully!")
            self.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {str(e)}")

    def load_prompts_config(self):
        try:
            # Get the src directory path
            src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            # Go up one more level to reach the project root
            base_dir = os.path.dirname(src_dir)
            prompts_file = os.path.join(base_dir, 'config', 'prompts.json')
            
            if os.path.exists(prompts_file):
                with open(prompts_file, 'r') as f:
                    return json.load(f)
            else:
                # Default prompts
                default_prompts = {
                    'sfx_improvement': "Generate a good prompt for a generative AI Model which creates Sound Effects based on this sound effect description:",
                    'music_improvement': "Generate a good prompt for a generative AI Model which creates Music based on this music piece description:",
                    'script_analysis_pre': """I have a script for an audio play that I would like to analyze and categorize. Please analyze each line in the script and categorize it as follows:

    1. Determine if the line is a spoken sentence by a character, a description of a sound effect (SFX), or a description of music. If the estimated length of a music piece is below 22s categorize it as SFX
    2. If it is a spoken sentence by a character, identify the character's name.
    3. If it is an SFX, estimate the duration of the sound (between 0.5 and 22 seconds).
    4. If it is music, specify whether it is instrumental or with vocals. Use "instrumental": "yes" for instrumental music and "instrumental": "no" for music with vocals.
    5. Maintain the order of the lines as they appear in the script, and assign an index to each line.
    6. Include two additional parts in the JSON:
        - Needed Speaker Tracks: List all the characternames in the script. 
        - Voice Characteristics: Analyze the emotional content of the sentence and describe the voice characteristics of each speaker."""
                }
                os.makedirs(os.path.dirname(prompts_file), exist_ok=True)
                with open(prompts_file, 'w') as f:
                    json.dump(default_prompts, f, indent=2)
                return default_prompts
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load prompts config: {str(e)}")
            return {}

    def save_prompts_config(self):
        try:
            src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            base_dir = os.path.dirname(src_dir)
            prompts_file = os.path.join(base_dir, 'config', 'prompts.json')
            
            prompts = {
                'sfx_improvement': self.sfx_prompt_var.get(),
                'music_improvement': self.music_prompt_var.get(),
                'script_analysis_pre': self.script_analysis_pre_var.get()
            }
            
            os.makedirs(os.path.dirname(prompts_file), exist_ok=True)
            with open(prompts_file, 'w') as f:
                json.dump(prompts, f, indent=2)
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save prompts config: {str(e)}")

    def on_closing(self):
        self.destroy()

