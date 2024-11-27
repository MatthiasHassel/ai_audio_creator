import customtkinter as ctk
import os
import json
from tkinter import messagebox
from dotenv import load_dotenv, set_key
import yaml
import logging

class PreferencesWindow(ctk.CTkToplevel):
    def __init__(self, master, config):
        super().__init__(master)
        self.config = config
        self.prompts_config = self.load_prompts_config()

        # Initialize variables
        self.api_vars = {
            'elevenlabs': ctk.StringVar(),
            'openai': ctk.StringVar(),
            'openrouter': ctk.StringVar(),
            'suno_cookie': ctk.StringVar(),
        }
        
        # Initialize model selection variable
        self.selected_model = ctk.StringVar()
        
        self.title("Preferences")
        self.geometry("700x400")
        self.resizable(False, False)
        
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

        # Models tab
        models_tab = self.notebook.add("Models")
        self.create_models_tab(models_tab)
        
        # Buttons
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill="x", pady=(20, 0))
        
        save_button = ctk.CTkButton(button_frame, text="Save", command=self.save_preferences)
        save_button.pack(side="right", padx=5)
        
        cancel_button = ctk.CTkButton(button_frame, text="Cancel", command=self.destroy)
        cancel_button.pack(side="right", padx=5)

    def create_models_tab(self, parent):
        """Create the Models tab content."""
        scrollable_frame = ctk.CTkScrollableFrame(parent)
        scrollable_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        description = ctk.CTkLabel(
            scrollable_frame,
            text="Select the AI model to use for script analysis and prompt improvement:",
            wraplength=600
        )
        description.pack(pady=(10, 20), padx=10)
        
        # Model selection frame
        models_frame = ctk.CTkFrame(scrollable_frame, fg_color="transparent")
        models_frame.pack(fill="x", pady=5, padx=5)
        
        # OpenAI option
        openai_frame = ctk.CTkFrame(models_frame, fg_color="transparent")
        openai_frame.pack(fill="x", pady=5)
        
        openai_radio = ctk.CTkRadioButton(
            openai_frame,
            text="OpenAI GPT-4o-mini",
            variable=self.selected_model,
            value="openai"
        )
        openai_radio.pack(pady=5, padx=20, anchor="w")
        
        openai_desc = ctk.CTkLabel(
            openai_frame,
            text="OpenAI's model offers high accuracy and reliability for text analysis and generation.",
            wraplength=500,
            text_color="gray60"
        )
        openai_desc.pack(pady=(0, 10), padx=40, anchor="w")
        
        # Llama option
        llama_frame = ctk.CTkFrame(models_frame, fg_color="transparent")
        llama_frame.pack(fill="x", pady=5)
        
        llama_radio = ctk.CTkRadioButton(
            llama_frame,
            text="Meta Llama 3.2 3B Instruct (via OpenRouter)",
            variable=self.selected_model,
            value="llama"
        )
        llama_radio.pack(pady=5, padx=20, anchor="w")
        
        llama_desc = ctk.CTkLabel(
            llama_frame,
            text="Meta's Llama model provides a good balance of performance and efficiency. Available through OpenRouter.",
            wraplength=500,
            text_color="gray60"
        )
        llama_desc.pack(pady=(0, 10), padx=40, anchor="w")

    def create_api_tab(self, parent):
        """Create the API Keys tab content."""
        api_frame = ctk.CTkFrame(parent)
        api_frame.pack(fill="x", pady=5, padx=5)
        
        # Add description
        description = ctk.CTkLabel(
            api_frame,
            text="Required API Keys:\n• ElevenLabs API Key and Suno Cookie are always required\n• Either OpenAI API Key or OpenRouter API Key must be provided",
            wraplength=600,
            justify="left"
        )
        description.pack(pady=(10, 20), padx=10)

        # Create API entries
        self.create_api_entry(api_frame, "ElevenLabs API Key:", 'elevenlabs')
        self.create_api_entry(api_frame, "Suno Cookie:", 'suno_cookie')
        self.create_api_entry(api_frame, "OpenAI API Key:", 'openai')
        self.create_api_entry(api_frame, "OpenRouter API Key:", 'openrouter')

    def validate_api_keys(self):
        """Validate that required API keys are provided"""
        # Check mandatory keys
        if not self.api_vars['elevenlabs'].get().strip():
            messagebox.showerror("Error", "ElevenLabs API Key is required")
            return False
            
        if not self.api_vars['suno_cookie'].get().strip():
            messagebox.showerror("Error", "Suno Cookie is required")
            return False
            
        # Check that at least one of OpenAI or OpenRouter API keys is provided
        if not (self.api_vars['openai'].get().strip() or self.api_vars['openrouter'].get().strip()):
            messagebox.showerror("Error", "Either OpenAI API Key or OpenRouter API Key must be provided")
            return False
            
        return True

    def create_api_entry(self, parent, label_text, key):
        frame = ctk.CTkFrame(parent)
        frame.pack(fill="x", pady=5)
        frame.grid_columnconfigure(1, weight=1)
        
        label = ctk.CTkLabel(frame, text=label_text, width=120, anchor="w")
        label.grid(row=0, column=0, padx=(10, 10), sticky="w")
        
        entry = ctk.CTkEntry(frame, textvariable=self.api_vars[key], show="*", width=300)
        entry.grid(row=0, column=1, sticky="ew", padx=(0, 5))
        
        def toggle_visibility():
            current = entry.cget("show")
            if current == "*":
                entry.configure(show="")
                toggle_button.configure(fg_color="#1f538d")  # Highlighted when visible
            else:
                entry.configure(show="*")
                toggle_button.configure(fg_color="gray40")  # Not highlighted when hidden
        
        toggle_button = ctk.CTkButton(frame, text="👁", width=30, command=toggle_visibility, fg_color="gray40")
        toggle_button.grid(row=0, column=2, padx=5)

    def update_api_entries_visibility(self, *args):
        """Update visibility of API entries based on selected model"""
        selected = self.selected_model.get()
        
        # Show/hide OpenAI API Key entry
        if 'openai' in self.api_frames:
            if selected == 'openai':
                self.api_frames['openai'].pack(fill="x", pady=5)
            else:
                self.api_frames['openai'].pack_forget()
        
        # Show/hide OpenRouter API Key entry
        if 'openrouter' in self.api_frames:
            if selected == 'llama':
                self.api_frames['openrouter'].pack(fill="x", pady=5)
            else:
                self.api_frames['openrouter'].pack_forget()

    def get_env_files(self):
        """Get and ensure existence of environment files"""
        try:
            # Get the directory paths
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            main_env_path = os.path.join(base_dir, '.env')
            suno_env_path = os.path.join(base_dir, 'suno_api', '.env')
            
            # Create main .env file if it doesn't exist
            if not os.path.exists(main_env_path):
                with open(main_env_path, 'w') as f:
                    f.write('# API Keys\n')
            
            # Create suno_api directory and .env file if they don't exist
            os.makedirs(os.path.dirname(suno_env_path), exist_ok=True)
            if not os.path.exists(suno_env_path):
                with open(suno_env_path, 'w') as f:
                    f.write('# Suno API Keys\n')
            
            return main_env_path, suno_env_path
        except Exception as e:
            logging.error(f"Error getting env files: {str(e)}", exc_info=True)
            raise
    
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

    def load_preferences(self):
        try:
            main_env_path, suno_env_path = self.get_env_files()
            
            # Load both .env files
            load_dotenv(main_env_path)
            load_dotenv(suno_env_path)
            
            # Load API keys from environment variables and config
            self.api_vars['elevenlabs'].set(self.config['api'].get('elevenlabs_api_key', ''))
            self.api_vars['openai'].set(self.config['api'].get('openai_api_key', ''))
            self.api_vars['openrouter'].set(self.config['api'].get('openrouter_api_key', ''))
            self.api_vars['suno_cookie'].set(self.config['api'].get('suno_cookie', ''))
            
            # Load selected model from config
            model = self.config.get('api', {}).get('selected_model', 'openai')
            self.selected_model.set(model)
            
            # Log loaded values for debugging
            logging.info(f"Loaded preferences - Model: {model}")
            logging.info(f"Loaded API Keys:")
            for key, var in self.api_vars.items():
                # Mask the key value for security in logs
                value = var.get()
                masked_value = '*' * (len(value) if value else 0)
                logging.info(f"  {key}: {masked_value}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load preferences: {str(e)}")
            logging.error(f"Error loading preferences: {str(e)}", exc_info=True)

    def save_preferences(self):
        try:
            # Validate API keys first
            if not self.validate_api_keys():
                return
                
            # Save API keys
            main_env_path, suno_env_path = self.get_env_files()
            
            # Update main .env file with stripped values
            env_keys = {
                'elevenlabs': 'ELEVENLABS_API_KEY',
                'openai': 'OPENAI_API_KEY',
                'openrouter': 'OPENROUTER_API_KEY',
                'suno_cookie': 'SUNO_COOKIE'
            }
            
            for key, var in self.api_vars.items():
                cleaned_value = var.get().strip()
                env_key = env_keys[key]
                
                # Set key in main .env
                set_key(main_env_path, env_key, cleaned_value)
                
                # Also set suno_cookie in suno_api .env
                if key == 'suno_cookie':
                    set_key(suno_env_path, env_key, cleaned_value)
            
            # Save prompts
            self.save_prompts_config()
            
            # Save selected model to config
            config_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            config_file = os.path.join(config_dir, 'config', 'config.yaml')
            
            with open(config_file, 'r') as f:
                config_data = yaml.safe_load(f)
            
            if 'api' not in config_data:
                config_data['api'] = {}
            
            config_data['api']['selected_model'] = self.selected_model.get()
            
            with open(config_file, 'w') as f:
                yaml.dump(config_data, f, default_flow_style=False)
            
            # Update the config in memory
            self.config['api']['selected_model'] = self.selected_model.get()
            
            # Update the config with the new API keys
            self.config['api']['elevenlabs_api_key'] = self.api_vars['elevenlabs'].get().strip()
            self.config['api']['openai_api_key'] = self.api_vars['openai'].get().strip()
            self.config['api']['openrouter_api_key'] = self.api_vars['openrouter'].get().strip()
            self.config['api']['suno_cookie'] = self.api_vars['suno_cookie'].get().strip()
            
            # Reload environment variables to ensure they're up to date
            load_dotenv(main_env_path)
            load_dotenv(suno_env_path)
            
            logging.info("Preferences saved successfully")
            messagebox.showinfo("Success", "Settings saved successfully!")
            self.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {str(e)}")
            logging.error(f"Error saving preferences: {str(e)}", exc_info=True)
        
    def on_closing(self):
        self.destroy()
