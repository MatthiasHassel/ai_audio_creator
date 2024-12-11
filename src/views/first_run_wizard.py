import customtkinter as ctk
import yaml
import os
from pathlib import Path
from dotenv import set_key

class ConfigWizard(ctk.CTkToplevel):
    def __init__(self):
        super().__init__()
        
        self.title("AI Audio Creator Setup")
        self.geometry("600x500")
        
        # Initialize variables
        self.current_page = 0
        self.result = False
        
        # Create navigation buttons first
        self.button_frame = ctk.CTkFrame(self)
        self.button_frame.pack(side="bottom", fill="x", padx=20, pady=20)
        
        self.back_button = ctk.CTkButton(self.button_frame, text="Back", command=self.back_clicked)
        self.back_button.pack(side="left", padx=5)
        
        self.next_button = ctk.CTkButton(self.button_frame, text="Next", command=self.next_clicked)
        self.next_button.pack(side="right", padx=5)
        
        # Create pages
        self.pages = [
            WelcomePage(self),
            RequiredAPIConfigPage(self),
            OptionalAPIConfigPage(self),
            CompletionPage(self)
        ]
        
        # Show first page
        self.show_page(0)
        
        # Center window
        self.center_window()
        
        # Make modal
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
    def center_window(self):
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
    
    def show_page(self, index):
        # Hide all pages
        for page in self.pages:
            page.pack_forget()
        
        # Show requested page
        self.pages[index].pack(fill="both", expand=True, padx=20, pady=20)
        self.current_page = index
        
        # Update button states
        self.back_button.configure(state="normal" if index > 0 else "disabled")
        self.next_button.configure(text="Finish" if index == len(self.pages)-1 else "Next")
    
    def back_clicked(self):
        if self.current_page > 0:
            self.show_page(self.current_page - 1)
    
    def next_clicked(self):
        current_page = self.pages[self.current_page]
        
        if not current_page.validate():
            return
        
        if self.current_page < len(self.pages) - 1:
            self.show_page(self.current_page + 1)
        else:
            self.finish()
    
    def finish(self):
        try:
            # Create config directory
            config_dir = Path.home() / ".ai_audio_creator"
            config_dir.mkdir(exist_ok=True)
            
            # Create base directory
            projects_dir = Path.home() / "AI Audio Creator"
            projects_dir.mkdir(parents=True, exist_ok=True)
            
            # Get values from pages
            required_page = self.pages[1]
            optional_page = self.pages[2]
            
            elevenlabs_key = required_page.elevenlabs_var.get()
            openrouter_key = required_page.openrouter_var.get()
            skip_optional = optional_page.skip_var.get()
            openai_key = "" if skip_optional else optional_page.openai_var.get()
            suno_cookie = "" if skip_optional else optional_page.suno_var.get()
            
            # Create or update .env file
            env_path = config_dir / ".env"
            set_key(str(env_path), "ELEVENLABS_API_KEY", elevenlabs_key)
            set_key(str(env_path), "OPENROUTER_API_KEY", openrouter_key)
            set_key(str(env_path), "OPENAI_API_KEY", openai_key)
            set_key(str(env_path), "SUNO_COOKIE", suno_cookie)
            
            # Create config.yaml
            config = {
                'api': {
                    'elevenlabs_api_key': elevenlabs_key,
                    'openai_api_key': openai_key,
                    'openrouter_api_key': openrouter_key,
                    'suno_cookie': suno_cookie,
                    'selected_model': 'openai'
                },
                'projects': {
                    'base_dir': str(projects_dir)
                },
                'logging': {
                    'level': 'INFO',
                    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                },
                'audio_generator_gui': {
                    'window_size': '1200x800'
                }
            }
            
            with open(config_dir / "config.yaml", 'w') as f:
                yaml.dump(config, f)
            
            self.result = True
            self.destroy()
            
        except Exception as e:
            ctk.CTkMessagebox(title="Error", message=f"Failed to save configuration: {str(e)}")
    
    def on_close(self):
        self.result = False
        self.destroy()

class WizardPage(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.configure(fg_color="transparent")
    
    def validate(self):
        return True

class WelcomePage(WizardPage):
    def __init__(self, master):
        super().__init__(master)
        
        title = ctk.CTkLabel(self, text="Welcome to AI Audio Creator", font=("", 20, "bold"))
        title.pack(pady=(0, 20))
        
        text = ctk.CTkLabel(
            self,
            text="This wizard will help you set up the necessary API keys "
                 "for the application to work properly.\n\n"
                 "Required API Keys:\n"
                 "- ElevenLabs (for text-to-speech)\n"
                 "- OpenRouter (for AI text generation)\n\n"
                 "Optional API Keys:\n"
                 "- OpenAI (alternative for text generation)\n"
                 "- Suno Cookie (for music generation)\n\n"
                 "You can skip the optional API keys setup, but some features "
                 "won't be available until you configure them in the preferences menu.\n\n"
                 "Click Next to begin the setup process.",
            wraplength=500,
            justify="left"
        )
        text.pack(fill="both", expand=True)

class RequiredAPIConfigPage(WizardPage):
    def __init__(self, master):
        super().__init__(master)
        
        title = ctk.CTkLabel(self, text="Required API Configuration", font=("", 20, "bold"))
        title.pack(pady=(0, 20))
        
        info = ctk.CTkLabel(
            self,
            text="These API keys are required for the application to function properly.\n"
                 "You can get them from:\n"
                 "- ElevenLabs: https://elevenlabs.io\n"
                 "- OpenRouter: https://openrouter.ai",
            wraplength=500,
            justify="left"
        )
        info.pack(pady=(0, 20))
        
        # ElevenLabs
        elevenlabs_label = ctk.CTkLabel(self, text="ElevenLabs API Key:")
        elevenlabs_label.pack(anchor="w")
        self.elevenlabs_var = ctk.StringVar()
        self.elevenlabs_entry = ctk.CTkEntry(self, show="*", width=400, textvariable=self.elevenlabs_var)
        self.elevenlabs_entry.pack(pady=(0, 20))
        
        # OpenRouter
        openrouter_label = ctk.CTkLabel(self, text="OpenRouter API Key:")
        openrouter_label.pack(anchor="w")
        self.openrouter_var = ctk.StringVar()
        self.openrouter_entry = ctk.CTkEntry(self, show="*", width=400, textvariable=self.openrouter_var)
        self.openrouter_entry.pack()
    
    def validate(self):
        if not self.elevenlabs_var.get().strip():
            ctk.CTkMessagebox(title="Error", message="ElevenLabs API Key is required")
            return False
        if not self.openrouter_var.get().strip():
            ctk.CTkMessagebox(title="Error", message="OpenRouter API Key is required")
            return False
        return True

class OptionalAPIConfigPage(WizardPage):
    def __init__(self, master):
        super().__init__(master)
        
        title = ctk.CTkLabel(self, text="Optional API Configuration", font=("", 20, "bold"))
        title.pack(pady=(0, 20))
        
        info = ctk.CTkLabel(
            self,
            text="These API keys are optional but enable additional features:\n"
                 "- OpenAI API Key: Alternative for text generation\n"
                 "- Suno Cookie: Required for music generation\n\n"
                 "You can skip this step and configure these later in the preferences menu.",
            wraplength=500,
            justify="left"
        )
        info.pack(pady=(0, 20))
        
        # Skip checkbox
        self.skip_var = ctk.BooleanVar()
        skip_check = ctk.CTkCheckBox(self, text="Skip optional API configuration", 
                                   variable=self.skip_var, command=self.toggle_inputs)
        skip_check.pack(pady=(0, 20))
        
        # OpenAI
        openai_label = ctk.CTkLabel(self, text="OpenAI API Key:")
        openai_label.pack(anchor="w")
        self.openai_var = ctk.StringVar()
        self.openai_entry = ctk.CTkEntry(self, show="*", width=400, textvariable=self.openai_var)
        self.openai_entry.pack(pady=(0, 20))
        
        # Suno
        suno_label = ctk.CTkLabel(self, text="Suno Cookie:")
        suno_label.pack(anchor="w")
        self.suno_var = ctk.StringVar()
        self.suno_entry = ctk.CTkEntry(self, show="*", width=400, textvariable=self.suno_var)
        self.suno_entry.pack()
    
    def toggle_inputs(self):
        state = "disabled" if self.skip_var.get() else "normal"
        self.openai_entry.configure(state=state)
        self.suno_entry.configure(state=state)

class CompletionPage(WizardPage):
    def __init__(self, master):
        super().__init__(master)
        
        title = ctk.CTkLabel(self, text="Setup Complete", font=("", 20, "bold"))
        title.pack(pady=(0, 20))
        
        text = ctk.CTkLabel(
            self,
            text="Configuration is complete!\n\n"
                 "The application will now start with your configuration.\n\n"
                 "You can modify these settings later through the application's "
                 "preferences menu.",
            wraplength=500,
            justify="left"
        )
        text.pack(fill="both", expand=True)

def run_first_time_setup():
    """Run the first-time setup wizard."""
    wizard = ConfigWizard()
    wizard.wait_window()
    return wizard.result
