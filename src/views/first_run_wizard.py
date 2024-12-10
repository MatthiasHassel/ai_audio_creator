from PySide6.QtWidgets import (QWizard, QWizardPage, QLineEdit, 
                              QVBoxLayout, QLabel, QMessageBox, QCheckBox)
from PySide6.QtCore import Qt
import yaml
import os
from pathlib import Path

class ConfigWizard(QWizard):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AI Audio Creator Setup")
        self.setWizardStyle(QWizard.ModernStyle)
        
        # Add pages
        self.addPage(WelcomePage())
        self.addPage(RequiredAPIConfigPage())
        self.addPage(OptionalAPIConfigPage())
        self.addPage(CompletionPage())
        
        # Set window size
        self.resize(600, 500)
        
        # Connect finished signal
        self.finished.connect(self.on_finish)
        
    def on_finish(self):
        if self.result() == QWizard.Accepted:
            # Get the values
            elevenlabs_key = self.field("elevenlabs_key")
            openrouter_key = self.field("openrouter_key")
            openai_key = self.field("openai_key") if not self.field("skip_optional") else ""
            suno_cookie = self.field("suno_cookie") if not self.field("skip_optional") else ""
            
            # Create config directory if it doesn't exist
            config_dir = Path.home() / ".ai_audio_creator"
            config_dir.mkdir(exist_ok=True)
            
            # Write config file
            config = {
                "api_keys": {
                    "elevenlabs": elevenlabs_key,
                    "openrouter": openrouter_key,
                    "openai": openai_key,
                    "suno_cookie": suno_cookie
                }
            }
            
            with open(config_dir / "config.yaml", "w") as f:
                yaml.dump(config, f)

class WelcomePage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Welcome to AI Audio Creator")
        
        layout = QVBoxLayout()
        label = QLabel(
            "Welcome to AI Audio Creator!\n\n"
            "This wizard will help you set up the necessary API keys "
            "for the application to work properly.\n\n"
            "Required API Keys:\n"
            "- ElevenLabs (for text-to-speech)\n"
            "- OpenRouter (for AI text generation)\n\n"
            "Optional API Keys:\n"
            "- OpenAI (alternative for text generation)\n"
            "- Suno Cookie (for music generation)\n\n"
            "You can skip the optional API keys setup, but some features "
            "won't be available until you configure them in the preferences menu.\n\n"
            "Click Next to begin the setup process."
        )
        label.setWordWrap(True)
        layout.addWidget(label)
        self.setLayout(layout)

class RequiredAPIConfigPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Required API Configuration")
        self.setSubTitle("Please enter your required API keys")
        
        layout = QVBoxLayout()
        
        # ElevenLabs API Key
        elevenlabs_label = QLabel("ElevenLabs API Key:")
        self.elevenlabs_input = QLineEdit()
        self.elevenlabs_input.setEchoMode(QLineEdit.Password)
        self.registerField("elevenlabs_key*", self.elevenlabs_input)
        
        # OpenRouter API Key
        openrouter_label = QLabel("OpenRouter API Key:")
        self.openrouter_input = QLineEdit()
        self.openrouter_input.setEchoMode(QLineEdit.Password)
        self.registerField("openrouter_key*", self.openrouter_input)
        
        # Add widgets to layout
        layout.addWidget(QLabel(
            "These API keys are required for the application to function properly.\n"
            "You can get them from:\n"
            "- ElevenLabs: https://elevenlabs.io\n"
            "- OpenRouter: https://openrouter.ai"
        ))
        layout.addSpacing(10)
        layout.addWidget(elevenlabs_label)
        layout.addWidget(self.elevenlabs_input)
        layout.addSpacing(10)
        layout.addWidget(openrouter_label)
        layout.addWidget(self.openrouter_input)
        layout.addStretch()
        
        self.setLayout(layout)

class OptionalAPIConfigPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Optional API Configuration")
        self.setSubTitle("Configure additional API keys or skip")
        
        layout = QVBoxLayout()
        
        # Skip checkbox
        self.skip_checkbox = QCheckBox("Skip optional API configuration")
        self.registerField("skip_optional", self.skip_checkbox)
        self.skip_checkbox.stateChanged.connect(self.toggle_inputs)
        
        # OpenAI API Key
        openai_label = QLabel("OpenAI API Key:")
        self.openai_input = QLineEdit()
        self.openai_input.setEchoMode(QLineEdit.Password)
        self.registerField("openai_key", self.openai_input)
        
        # Suno Cookie
        suno_label = QLabel("Suno Cookie:")
        self.suno_input = QLineEdit()
        self.suno_input.setEchoMode(QLineEdit.Password)
        self.registerField("suno_cookie", self.suno_input)
        
        # Add widgets to layout
        layout.addWidget(QLabel(
            "These API keys are optional but enable additional features:\n"
            "- OpenAI API Key: Alternative for text generation\n"
            "- Suno Cookie: Required for music generation\n\n"
            "You can skip this step and configure these later in the preferences menu."
        ))
        layout.addSpacing(10)
        layout.addWidget(self.skip_checkbox)
        layout.addSpacing(10)
        layout.addWidget(openai_label)
        layout.addWidget(self.openai_input)
        layout.addSpacing(10)
        layout.addWidget(suno_label)
        layout.addWidget(self.suno_input)
        layout.addStretch()
        
        self.setLayout(layout)
        
    def toggle_inputs(self, state):
        enabled = not bool(state)
        self.openai_input.setEnabled(enabled)
        self.suno_input.setEnabled(enabled)

class CompletionPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Setup Complete")
        
        layout = QVBoxLayout()
        self.status_label = QLabel(
            "Configuration is complete!\n\n"
            "The application will now start with your configuration.\n\n"
            "You can modify these settings later through the application's "
            "preferences menu."
        )
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        
        # Warning label for skipped configuration
        self.warning_label = QLabel(
            "\nWARNING: You have skipped the optional API configuration. "
            "Some features will not be available until you configure these "
            "API keys in the preferences menu."
        )
        self.warning_label.setWordWrap(True)
        self.warning_label.setStyleSheet("color: #FFA500")  # Orange color
        self.warning_label.hide()
        layout.addWidget(self.warning_label)
        
        layout.addStretch()
        self.setLayout(layout)
        
    def initializePage(self):
        # Show warning if optional configuration was skipped
        if self.field("skip_optional"):
            self.warning_label.show()
        else:
            self.warning_label.hide()
