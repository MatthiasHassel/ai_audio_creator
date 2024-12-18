import customtkinter as ctk
import yaml
import os
from pathlib import Path
from dotenv import set_key
from tkinter import filedialog
from utils.ffmpeg_utils import check_ffmpeg_installation, get_ffmpeg_version, get_installation_instructions
from utils.configure_reaper import configure_reaper
from services.reaper_service import ReaperService

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
            FFmpegCheckPage(self),
            ReaperConfigPage(self),
            APIConfigPage(self),
            LLMProviderPage(self),
            StorageLocationPage(self),
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
            
            # Get values from pages
            api_page = self.pages[3]  # Updated index due to new Reaper page
            llm_page = self.pages[4]  # Updated index due to new Reaper page
            storage_page = self.pages[5]  # Updated index due to new Reaper page
            
            elevenlabs_key = api_page.elevenlabs_var.get().strip()
            openrouter_key = api_page.openrouter_var.get().strip()
            openai_key = api_page.openai_var.get().strip()
            suno_cookie = api_page.suno_var.get().strip()
            
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
                    'selected_model': llm_page.selected_provider.get()
                },
                'projects': {
                    'base_dir': storage_page.storage_path.get()
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
            text="This wizard will help you set up the AI Audio Creator.\n\n"
                 "You'll be asked to configure:\n"
                 "- FFmpeg Installation Check\n"
                 "- Reaper Integration\n"
                 "- API Keys (all optional, but required for specific features)\n"
                 "- Default LLM Provider\n"
                 "- Project Storage Location\n\n"
                 "You can modify all settings later in the preferences menu.\n\n"
                 "Click Next to begin the setup process.",
            wraplength=500,
            justify="left"
        )
        text.pack(fill="both", expand=True)

class FFmpegCheckPage(WizardPage):
    def __init__(self, master):
        super().__init__(master)
        
        self.title = ctk.CTkLabel(self, text="FFmpeg Installation Check", font=("", 20, "bold"))
        self.title.pack(pady=(0, 20))
        
        # Status frame
        self.status_frame = ctk.CTkFrame(self)
        self.status_frame.pack(fill="x", pady=(0, 20))
        
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="Checking FFmpeg installation...",
            font=("", 14)
        )
        self.status_label.pack(pady=10)
        
        # Version label
        self.version_label = ctk.CTkLabel(
            self.status_frame,
            text="",
            font=("", 12)
        )
        self.version_label.pack(pady=(0, 10))
        
        # Instructions text
        self.instructions_text = ctk.CTkTextbox(self, height=200)
        self.instructions_text.pack(fill="both", expand=True, pady=(0, 10))
        self.instructions_text.configure(state="disabled")
        
        # Check Again button
        self.check_button = ctk.CTkButton(
            self,
            text="Check Again",
            command=self.check_ffmpeg
        )
        self.check_button.pack(pady=(0, 10))
        
        # Initial check
        self.check_ffmpeg()
        
    def check_ffmpeg(self):
        is_installed, ffmpeg_path = check_ffmpeg_installation()
        
        if is_installed:
            self.status_label.configure(
                text="✅ FFmpeg is installed and accessible",
                text_color="green"
            )
            version = get_ffmpeg_version(ffmpeg_path)
            if version:
                self.version_label.configure(text=f"Version: {version}")
            self.instructions_text.configure(state="normal")
            self.instructions_text.delete("1.0", "end")
            self.instructions_text.configure(state="disabled")
            self.check_button.configure(state="disabled")
        else:
            self.status_label.configure(
                text="❌ FFmpeg is not installed or not accessible",
                text_color="red"
            )
            self.version_label.configure(text="")
            self.instructions_text.configure(state="normal")
            self.instructions_text.delete("1.0", "end")
            self.instructions_text.insert("1.0", get_installation_instructions())
            self.instructions_text.configure(state="disabled")
            self.check_button.configure(state="normal")
    
    def validate(self):
        is_installed, _ = check_ffmpeg_installation()
        if not is_installed:
            ctk.CTkMessagebox(
                title="FFmpeg Required",
                message="FFmpeg is required for audio processing. Please install FFmpeg before continuing."
            )
            return False
        return True

class ReaperConfigPage(WizardPage):
    def __init__(self, master):
        super().__init__(master)
        
        title = ctk.CTkLabel(self, text="Reaper Integration", font=("", 20, "bold"))
        title.pack(pady=(0, 20))
        
        info = ctk.CTkLabel(
            self,
            text="AI Audio Creator can integrate with REAPER DAW for advanced audio editing.\n"
                 "Would you like to configure REAPER integration now?",
            wraplength=500,
            justify="left"
        )
        info.pack(pady=(0, 20))
        
        # Configure option
        self.configure_var = ctk.BooleanVar(value=False)
        self.configure_checkbox = ctk.CTkCheckBox(
            self,
            text="Yes, configure REAPER integration",
            variable=self.configure_var,
            command=self.on_checkbox_change
        )
        self.configure_checkbox.pack(pady=(0, 20))
        
        # Status frame
        self.status_frame = ctk.CTkFrame(self)
        self.status_frame.pack(fill="x", pady=(0, 20))
        
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="",
            font=("", 14)
        )
        self.status_label.pack(pady=10)
        
        # Configure button
        self.configure_button = ctk.CTkButton(
            self,
            text="Configure REAPER",
            command=self.configure_reaper,
            state="disabled"
        )
        self.configure_button.pack(pady=(0, 10))
        
        # Instructions text
        self.instructions_text = ctk.CTkTextbox(self, height=150)
        self.instructions_text.pack(fill="both", expand=True, pady=(0, 10))
        self.instructions_text.configure(state="disabled")
        
        # Initialize ReaperService
        self.reaper_service = ReaperService()
    
    def on_checkbox_change(self):
        if self.configure_var.get():
            self.configure_button.configure(state="normal")
            self.instructions_text.configure(state="normal")
            self.instructions_text.delete("1.0", "end")
            self.instructions_text.insert("1.0", 
                "To configure REAPER integration:\n\n"
                "1. Open REAPER\n"
                "2. Make sure ReaScript is enabled:\n"
                "   - Go to Preferences -> Plug-ins -> ReaScript\n"
                "   - Enable 'Allow Python to access REAPER via ReaScript'\n"
                "3. Click the 'Configure REAPER' button below"
            )
            self.instructions_text.configure(state="disabled")
        else:
            self.configure_button.configure(state="disabled")
            self.instructions_text.configure(state="normal")
            self.instructions_text.delete("1.0", "end")
            self.instructions_text.configure(state="disabled")
            self.status_label.configure(text="")
    
    def configure_reaper(self):
        try:
            # First check if Reaper is running
            if not self.reaper_service.is_reaper_running():
                self.status_label.configure(
                    text="❌ REAPER is not running or ReaScript is not enabled",
                    text_color="red"
                )
                self.instructions_text.configure(state="normal")
                self.instructions_text.delete("1.0", "end")
                self.instructions_text.insert("1.0",
                    "ReaScript API is not enabled. Please:\n"
                    "1. Open REAPER\n"
                    "2. Go to Preferences -> Plug-ins -> ReaScript\n"
                    "3. Enable 'Allow Python to access REAPER via ReaScript'"
                )
                self.instructions_text.configure(state="disabled")
                return
            
            # Run configuration script
            success, message = configure_reaper()
            
            if success:
                self.status_label.configure(
                    text="✅ REAPER configuration successful!",
                    text_color="green"
                )
                self.configure_button.configure(state="disabled")
                self.configure_checkbox.configure(state="disabled")
                self.instructions_text.configure(state="normal")
                self.instructions_text.delete("1.0", "end")
                self.instructions_text.insert("1.0", 
                    "REAPER has been successfully configured!\n\n"
                    "You can now use AI Audio Creator with REAPER for advanced audio editing."
                )
                self.instructions_text.configure(state="disabled")
            else:
                self.status_label.configure(
                    text="❌ Configuration failed",
                    text_color="red"
                )
                self.instructions_text.configure(state="normal")
                self.instructions_text.delete("1.0", "end")
                self.instructions_text.insert("1.0", message)
                self.instructions_text.configure(state="disabled")
                
        except Exception as e:
            self.status_label.configure(
                text=f"❌ Configuration failed: {str(e)}",
                text_color="red"
            )
    
    def validate(self):
        if self.configure_var.get():
            # If user wanted to configure but it failed
            if not self.reaper_service.is_reaper_running():
                if not ctk.CTkMessagebox(
                    title="REAPER Configuration Failed",
                    message="REAPER configuration was not successful. Do you want to continue anyway?",
                    icon="warning",
                    option_1="Yes",
                    option_2="No"
                ).get() == "Yes":
                    return False
        return True

class APIConfigPage(WizardPage):
    def __init__(self, master):
        super().__init__(master)
        
        title = ctk.CTkLabel(self, text="API Configuration", font=("", 20, "bold"))
        title.pack(pady=(0, 20))
        
        # Create scrollable frame for the content
        self.scrollable_frame = ctk.CTkScrollableFrame(self, width=500, height=300)
        self.scrollable_frame.pack(fill="both", expand=True)
        
        warning = ctk.CTkLabel(
            self.scrollable_frame,
            text="⚠️ Warning: While all API keys are optional, they are necessary for the app to work properly:\n"
                 "• ElevenLabs - Required for text-to-speech and text-to-sfx\n"
                 "• OpenRouter/OpenAI - Required for AI text generation\n"
                 "• Suno Cookie - Required for music generation",
            wraplength=460,
            justify="left",
            text_color="orange"
        )
        warning.pack(pady=(0, 20))
        
        info = ctk.CTkLabel(
            self.scrollable_frame,
            text="You can get the API keys from:\n"
                 "• ElevenLabs: https://elevenlabs.io\n"
                 "• OpenRouter: https://openrouter.ai\n"
                 "• OpenAI: https://platform.openai.com\n"
                 "• Suno: https://suno.ai",
            wraplength=460,
            justify="left"
        )
        info.pack(pady=(0, 20))
        
        # ElevenLabs
        elevenlabs_label = ctk.CTkLabel(self.scrollable_frame, text="ElevenLabs API Key:")
        elevenlabs_label.pack(anchor="w")
        self.elevenlabs_var = ctk.StringVar()
        self.elevenlabs_entry = ctk.CTkEntry(self.scrollable_frame, show="*", width=400, textvariable=self.elevenlabs_var)
        self.elevenlabs_entry.pack(pady=(0, 10))
        
        # OpenRouter
        openrouter_label = ctk.CTkLabel(self.scrollable_frame, text="OpenRouter API Key:")
        openrouter_label.pack(anchor="w")
        self.openrouter_var = ctk.StringVar()
        self.openrouter_entry = ctk.CTkEntry(self.scrollable_frame, show="*", width=400, textvariable=self.openrouter_var)
        self.openrouter_entry.pack(pady=(0, 10))
        
        # OpenAI
        openai_label = ctk.CTkLabel(self.scrollable_frame, text="OpenAI API Key:")
        openai_label.pack(anchor="w")
        self.openai_var = ctk.StringVar()
        self.openai_entry = ctk.CTkEntry(self.scrollable_frame, show="*", width=400, textvariable=self.openai_var)
        self.openai_entry.pack(pady=(0, 10))
        
        # Suno
        suno_label = ctk.CTkLabel(self.scrollable_frame, text="Suno Cookie:")
        suno_label.pack(anchor="w")
        self.suno_var = ctk.StringVar()
        self.suno_entry = ctk.CTkEntry(self.scrollable_frame, show="*", width=400, textvariable=self.suno_var)
        self.suno_entry.pack(pady=(0, 10))

class LLMProviderPage(WizardPage):
    def __init__(self, master):
        super().__init__(master)
        
        title = ctk.CTkLabel(self, text="Default LLM Provider", font=("", 20, "bold"))
        title.pack(pady=(0, 20))
        
        info = ctk.CTkLabel(
            self,
            text="Choose your default Large Language Model (LLM) provider.\n"
                 "This will be used for AI text generation.\n\n"
                 "Note: You need to have configured the corresponding API key.",
            wraplength=500,
            justify="left"
        )
        info.pack(pady=(0, 20))
        
        self.selected_provider = ctk.StringVar(value="openai")
        
        openai_radio = ctk.CTkRadioButton(
            self, 
            text="OpenAI (ChatGPT 4o mini)",
            variable=self.selected_provider,
            value="openai"
        )
        openai_radio.pack(pady=(0, 10), anchor="w")
        
        openrouter_radio = ctk.CTkRadioButton(
            self,
            text="OpenRouter (Llama 3, recommended and no costs)",
            variable=self.selected_provider,
            value="openrouter"
        )
        openrouter_radio.pack(anchor="w")

class StorageLocationPage(WizardPage):
    def __init__(self, master):
        super().__init__(master)
        
        title = ctk.CTkLabel(self, text="Project Storage Location", font=("", 20, "bold"))
        title.pack(pady=(0, 20))
        
        info = ctk.CTkLabel(
            self,
            text="Choose where your AI Audio Creator projects will be stored.\n"
                 "This is where all your project files, audio files, and other assets will be saved.",
            wraplength=500,
            justify="left"
        )
        info.pack(pady=(0, 20))
        
        # Default path
        default_path = str(Path.home() / "AI Audio Creator")
        self.storage_path = ctk.StringVar(value=default_path)
        
        path_frame = ctk.CTkFrame(self)
        path_frame.pack(fill="x", pady=(0, 20))
        
        self.path_entry = ctk.CTkEntry(
            path_frame,
            textvariable=self.storage_path,
            width=350
        )
        self.path_entry.pack(side="left", padx=(0, 10))
        
        browse_button = ctk.CTkButton(
            path_frame,
            text="Browse",
            command=self.browse_location
        )
        browse_button.pack(side="left")
    
    def browse_location(self):
        path = filedialog.askdirectory(
            initialdir=self.storage_path.get(),
            title="Select Project Storage Location"
        )
        if path:
            self.storage_path.set(path)
    
    def validate(self):
        path = Path(self.storage_path.get())
        try:
            path.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            ctk.CTkMessagebox(
                title="Error",
                message=f"Failed to create storage directory: {str(e)}\nPlease choose a different location."
            )
            return False

class CompletionPage(WizardPage):
    def __init__(self, master):
        super().__init__(master)
        
        title = ctk.CTkLabel(self, text="Setup Complete", font=("", 20, "bold"))
        title.pack(pady=(0, 20))
        
        text = ctk.CTkLabel(
            self,
            text="Configuration is complete!\n\n"
                 "The application will now start with your configuration.\n\n"
                 "You can modify all settings later through the application's "
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
