import customtkinter as ctk
import logging
import threading
from services.llama_service import LlamaService
from services.music_service import MusicService
from services.sfx_service import SFXService
from services.speech_service import SpeechService
from utils.file_utils import open_file
from utils.audio_utils import AudioPlayer
from .tab_widgets import TabWidgets
from utils.audio_visualizer import AudioVisualizer
from utils.audio_file_selector import AudioFileSelector

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

class Application(ctk.CTk):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.setup_window()
        self.setup_variables()
        self.setup_services()
        self.setup_logging()
        self.create_widgets()

    def setup_window(self):
        self.title(self.config['gui']['window_title'])
        self.geometry(self.config['gui']['window_size'])
        self.grid_columnconfigure(0, weight=1)

    def setup_variables(self):
        self.current_module = ctk.StringVar(value="Music")
        self.duration_var = ctk.StringVar(value="0")
        self.instrumental_var = ctk.BooleanVar(value=False)
        self.selected_voice = ctk.StringVar()
        self.voices = []
        self.status_queue = []
        self.is_processing = False

    def setup_services(self):
        self.llama_service = LlamaService(self, self.config)
        self.music_service = MusicService(self, self.config)
        self.sfx_service = SFXService(self, self.config)
        self.speech_service = SpeechService(self, self.config)

    def setup_logging(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)

    def create_widgets(self):
        self.create_module_buttons()
        self.create_input_field()
        self.create_action_buttons()
        self.create_tab_specific_options()
        self.create_status_bar()
        self.create_separator()
        self.create_output_display()
        self.create_audio_file_selector() 
        self.create_audio_visualizer()
        self.create_audio_controls()
        self.create_progress_bar()
        self.load_voices()
        self.update_tab_widgets()

    def create_module_buttons(self):
        module_frame = ctk.CTkFrame(self)
        module_frame.grid(row=0, column=0, pady=10, padx=10, sticky="ew")
        for i, module in enumerate(["Music", "SFX", "Speech"]):
            ctk.CTkRadioButton(
                module_frame, 
                text=module, 
                variable=self.current_module, 
                value=module, 
                command=self.update_tab_widgets
            ).grid(row=0, column=i, padx=5)

    def create_input_field(self):
        input_frame = ctk.CTkFrame(self)
        input_frame.grid(row=1, column=0, pady=10, padx=10, sticky="ew")
        input_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(input_frame, text="Enter your text:").grid(row=0, column=0, sticky="w")
        self.user_input = ctk.CTkTextbox(input_frame, height=150)
        self.user_input.grid(row=1, column=0, sticky="ew")

    def create_action_buttons(self):
        action_frame = ctk.CTkFrame(self)
        action_frame.grid(row=2, column=0, pady=10, padx=10, sticky="w")
        self.generate_button = ctk.CTkButton(action_frame, text="Generate", command=self.process_input)
        self.generate_button.pack(side="left", padx=(0, 5))
        self.clear_button = ctk.CTkButton(action_frame, text="Clear", command=self.clear_input)
        self.clear_button.pack(side="left", padx=(0, 5))
        self.llama_button = ctk.CTkButton(action_frame, text="Input to Llama3", command=self.process_llama_input)
        self.llama_button.pack(side="left")

    def create_tab_specific_options(self):
        tab_config = {
            'instrumental_var': self.instrumental_var,
            'duration_var': self.duration_var,
            'selected_voice': self.selected_voice
        }
        self.tab_widgets = TabWidgets(self, tab_config)
        self.tab_widgets.grid(row=3, column=0, pady=10, padx=10, sticky="w")

    def create_audio_file_selector(self):
        self.audio_file_selector = AudioFileSelector(
            self, 
            self.config, 
            self.current_module, 
            self.on_audio_file_select
        )
        self.audio_file_selector.grid(row=7, column=0, pady=10, padx=10, sticky="ew")

    def on_audio_file_select(self, file_path):
        if hasattr(self, 'audio_player'):
            self.audio_player.set_audio_file(file_path)

    def create_status_bar(self):
        self.status_var = ctk.StringVar()
        self.status_var.set("Ready")
        self.status_bar = ctk.CTkLabel(self, textvariable=self.status_var, anchor="w", padx=10)
        self.status_bar.grid(row=10, column=0, sticky="ew", padx=10, pady=(5, 0))

    def create_separator(self):
        separator = ctk.CTkFrame(self, height=2, fg_color="gray")
        separator.grid(row=4, column=0, sticky="ew", padx=10, pady=(5, 5))

    def create_output_display(self):
        output_frame = ctk.CTkFrame(self)
        output_frame.grid(row=5, column=0, pady=10, padx=10, sticky="ew")
        output_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(output_frame, text="Output:").grid(row=0, column=0, sticky="w")
        self.output_text = ctk.CTkTextbox(output_frame, height=80, state="disabled")
        self.output_text.grid(row=1, column=0, sticky="ew")
        self.output_text.bind("<Button-1>", self.open_audio_file)

    def create_audio_visualizer(self):
        self.audio_visualizer = AudioVisualizer(self)
        self.audio_visualizer.canvas_widget.grid(row=6, column=0, pady=(0, 10), padx=10, sticky="ew")

    def create_audio_controls(self):
        self.audio_player = AudioPlayer(self, self.audio_visualizer)
        
    def create_progress_bar(self):
        self.progress_bar = ctk.CTkProgressBar(self, width=380)
        self.progress_bar.grid(row=9, column=0, pady=10, padx=10, sticky="ew")
        self.progress_bar.grid_remove()

    def update_tab_widgets(self):
        current_tab = self.current_module.get()
        self.tab_widgets.update_widgets(current_tab)
        if current_tab in ["Music", "SFX"]:
            self.llama_button.pack(side="left", padx=(0, 5))
        else:
            self.llama_button.pack_forget()
        if hasattr(self, 'audio_file_selector'):
            self.audio_file_selector.refresh_files()
        if self.audio_file_selector.initial_state:
            self.audio_player.clear()
            self.audio_visualizer.hide_playhead()

    def process_llama_input(self):
        user_input = self.user_input.get("1.0", "end-1c").strip()
        if not user_input:
            self.update_output("Error: Please enter some text.")
            return

        if self.current_module.get() == "Music":
            result = self.llama_service.get_llama_musicprompt(user_input)
        elif self.current_module.get() == "SFX":
            result = self.llama_service.get_llama_sfx(user_input)
        else:
            self.update_output("Error: Llama3 input is only available for Music and SFX modules.")
            return

        if result:
            self.user_input.delete("1.0", "end")
            self.user_input.insert("1.0", result)
        else:
            self.update_output("Error: Failed to process input with Llama3.")

    def process_input(self):
        if self.current_module.get() == "Music":
            self.process_music_request()
        elif self.current_module.get() == "SFX":
            self.process_sfx_request()
        elif self.current_module.get() == "Speech":
            self.process_speech_request()
        self.audio_file_selector.initial_state = False

    def process_music_request(self):
        self._process_request(self.music_service.process_music_request, 
                              [self.user_input.get("1.0", "end-1c").strip(), self.instrumental_var.get()])

    def process_sfx_request(self):
        self._process_request(self.sfx_service.process_sfx_request, 
                              [self.user_input.get("1.0", "end-1c").strip(), self.duration_var.get()])

    def process_speech_request(self):
        selected_voice_name = self.selected_voice.get()
        voice_id = next((voice[1] for voice in self.voices if voice[0] == selected_voice_name), None)
        if voice_id:
            self._process_request(self.speech_service.process_speech_request, 
                                  [self.user_input.get("1.0", "end-1c").strip(), voice_id])
        else:
            self.update_output("Error: Invalid voice selected.")

    def load_voices(self):
        try:
            self.voices = self.speech_service.get_available_voices()
            if self.voices:
                voice_names = [voice[0] for voice in self.voices]
                self.selected_voice.set(voice_names[0])  # Set the first voice as default
                # Update the voice dropdown if it exists
                if self.current_module.get() == "Speech":
                    self.tab_widgets.configure_widget("Speech", "voice_dropdown", values=voice_names)
            else:
                self.update_output("Warning: No voices available.")
        except Exception as e:
            error_message = f"Failed to load voices: {str(e)}"
            self.update_output(f"Error: {error_message}")

    def _process_request(self, service_method, args):
        if not args[0]:  # Check if user input is empty
            self.update_output("Error: Please enter some text.")
            return

        self.generate_button.configure(state="disabled")
        self.audio_player.clear()
        
        self.show_progress_bar(determinate=False)  # Use indeterminate mode for unknown duration

        def process_thread():
            result = service_method(*args)
            if result:
                self.after(0, lambda: self.update_output(f"Audio generated successfully. File saved to: {result}"))
                self.after(0, lambda: self.update_status("Ready"))
                self.after(0, lambda: self.audio_file_selector.set_latest_file())
                self.after(0, lambda: self.audio_player.set_audio_file(result))
                self.after(0, lambda: setattr(self.audio_file_selector, 'initial_state', False))
            else:
                self.after(0, lambda: self.update_output("Error: An error occurred during audio generation."))
            self.after(0, lambda: self.generate_button.configure(state="normal"))
            self.after(0, self.hide_progress_bar)

        threading.Thread(target=process_thread, daemon=True).start()

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

    def update_output(self, message):
        self.output_text.configure(state="normal")
        self.output_text.insert("end", message + "\n")
        self.output_text.see("end")
        self.output_text.configure(state="disabled")

    def clear_input(self):
        self.user_input.delete("1.0", "end")
        self.output_text.configure(state="normal")
        self.output_text.delete("1.0", "end")
        self.output_text.configure(state="disabled")
        self.duration_var.set("0")
        self.update_status("Ready")
        self.audio_player.clear()
        self.audio_file_selector.reset_to_initial_state()
        self.audio_visualizer.hide_playhead()

    def open_audio_file(self, event):
        try:
            index = self.output_text.index(f"@{event.x},{event.y}")
            line = self.output_text.get(index + " linestart", index + " lineend")
            if "File saved to:" in line:
                file_path = line.split("File saved to:")[-1].strip()
                open_file(file_path)
        except Exception as e:
            self.update_output(f"Error: Unable to open file: {str(e)}")

    def on_closing(self):
        self.audio_player.quit()
        self.destroy()

if __name__ == "__main__":
    import yaml
    with open('config/config.yaml', 'r') as file:
        config = yaml.safe_load(file)
    app = Application(config)
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()