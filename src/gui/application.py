import customtkinter as ctk
import logging
import threading
from services.llama_service import LlamaService
from services.music_service import MusicService
from services.sfx_service import SFXService
from services.speech_service import SpeechService
from utils.file_utils import open_file
from utils.audio_utils import AudioPlayer

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

class Application(ctk.CTk):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.title(self.config['gui']['window_title'])
        self.geometry(self.config['gui']['window_size'])
        
        self.llama_service = LlamaService(self, config)
        self.music_service = MusicService(self, config)
        self.sfx_service = SFXService(self, config)
        self.speech_service = SpeechService(self, config)

        self.current_module = ctk.StringVar(value="Music")
        self.duration_var = ctk.StringVar(value="0")
        self.instrumental_var = ctk.BooleanVar(value=False)
        self.selected_voice = ctk.StringVar()

        self.voices = []
        self.output_text = None
        self.status_bar = None

        self.status_queue = []
        self.is_processing = False

        self.setup_logging()
        self.create_widgets()

        self.audio_player = AudioPlayer(self)

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
        self.create_output_display()
        self.load_voices()
        self.create_status_bar()

    def create_module_buttons(self):
        module_frame = ctk.CTkFrame(self)
        module_frame.pack(pady=10)

        for module in ["Music", "SFX", "Speech"]:
            ctk.CTkRadioButton(
                module_frame, 
                text=module, 
                variable=self.current_module, 
                value=module, 
                command=self.update_action_buttons
            ).pack(side="left", padx=5)

    def create_input_field(self):
        input_frame = ctk.CTkFrame(self)
        input_frame.pack(pady=10)

        ctk.CTkLabel(input_frame, text="Enter your text:").pack()
        self.user_input = ctk.CTkTextbox(input_frame, width=400, height=150)  # Increased height
        self.user_input.pack(pady=5)

        self.duration_label = ctk.CTkLabel(input_frame, text="Duration (0 = automatic, 0.5-22s):")
        self.duration_entry = ctk.CTkEntry(input_frame, textvariable=self.duration_var)
        self.instrumental_checkbox = ctk.CTkCheckBox(input_frame, text="Instrumental", variable=self.instrumental_var)
        self.voice_label = ctk.CTkLabel(input_frame, text="Select Voice:")
        self.voice_dropdown = ctk.CTkOptionMenu(input_frame, variable=self.selected_voice)

    def create_action_buttons(self):
        self.action_frame = ctk.CTkFrame(self)
        self.action_frame.pack(pady=10)

        self.llama_button = ctk.CTkButton(self.action_frame, text="Input to Llama3", command=self.process_llama_input)
        self.generate_button = ctk.CTkButton(self.action_frame, text="Generate", command=self.process_input)
        self.clear_button = ctk.CTkButton(self.action_frame, text="Clear", command=self.clear_input)

        self.update_action_buttons()

    def update_action_buttons(self):
        for widget in self.action_frame.winfo_children():
            widget.pack_forget()

        if self.current_module.get() in ["Music", "SFX"]:
            self.llama_button.pack(side="left", padx=5)
        self.generate_button.pack(side="left", padx=5)
        self.clear_button.pack(side="left", padx=5)

        if self.current_module.get() == "Music":
            self.instrumental_checkbox.pack()
            self.duration_label.pack_forget()
            self.duration_entry.pack_forget()
            self.voice_label.pack_forget()
            self.voice_dropdown.pack_forget()
        elif self.current_module.get() == "SFX":
            self.duration_label.pack()
            self.duration_entry.pack()
            self.instrumental_checkbox.pack_forget()
            self.voice_label.pack_forget()
            self.voice_dropdown.pack_forget()
        elif self.current_module.get() == "Speech":
            self.voice_label.pack()
            self.voice_dropdown.pack()
            self.instrumental_checkbox.pack_forget()
            self.duration_label.pack_forget()
            self.duration_entry.pack_forget()

    def create_output_display(self):
        output_frame = ctk.CTkFrame(self)
        output_frame.pack(pady=10)

        ctk.CTkLabel(output_frame, text="Output:").pack()
        self.output_text = ctk.CTkTextbox(output_frame, width=400, height=80, state="disabled")  # Decreased height and set state to "disabled"
        self.output_text.pack()
        self.output_text.bind("<Button-1>", self.open_audio_file)

    def create_status_bar(self):
        self.status_var = ctk.StringVar()
        self.status_var.set("Ready")
        self.status_bar = ctk.CTkLabel(self, textvariable=self.status_var, anchor="w", padx=10)  # Added padx for padding
        self.status_bar.pack(side="bottom", fill="x")

    def load_voices(self):
        try:
            self.logger.info("Loading available voices...")
            self.voices = self.speech_service.get_available_voices()
            if self.voices:
                voice_names = [voice[0] for voice in self.voices]
                self.voice_dropdown.configure(values=voice_names)
                self.voice_dropdown.set(voice_names[0])  # Set the first voice as default
                self.logger.info(f"Loaded {len(self.voices)} voices.")
            else:
                self.voice_dropdown.configure(values=["No voices available"])
                self.update_output("Warning: No voices available.")
        except Exception as e:
            error_message = f"Failed to load voices: {str(e)}"
            self.logger.error(error_message)
            self.update_output(f"Error: {error_message}")
            self.voice_dropdown.configure(values=["No voices available"])

    def process_llama_input(self):
        user_input = self.user_input.get("1.0", "end-1c").strip()
        if not user_input:
            self.update_output("Error: Please enter some text.")
            return

        self.logger.info(f"Processing Llama3 input for {self.current_module.get()} module...")
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
            self.logger.info("Llama3 processing complete. Result inserted in the input field.")
        else:
            self.update_output("Error: Failed to process input with Llama3.")

    def process_input(self):
        if self.current_module.get() == "Music":
            self.process_music_request()
        elif self.current_module.get() == "SFX":
            self.process_sfx_request()
        elif self.current_module.get() == "Speech":
            self.process_speech_request()

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

    def _process_request(self, service_method, args):
        if not args[0]:  # Check if user input is empty
            self.update_output("Error: Please enter some text.")
            return

        self.logger.info(f"Processing {service_method.__self__.__class__.__name__} request...")
        self.generate_button.configure(state="disabled")
        self.audio_player.clear()
        
        def process_thread():
            result = service_method(*args)
            if result:
                self.logger.info(f"Audio generated successfully. File saved to: {result}")
                self.after(0, lambda: self.update_output(f"Audio generated successfully. File saved to: {result}"))
                self.after(0, lambda: self.update_status("Ready"))
                self.after(0, lambda: self.audio_player.set_audio_file(result))
            else:
                self.after(0, lambda: self.update_output("Error: An error occurred during audio generation."))
            self.after(0, lambda: self.generate_button.configure(state="normal"))

        threading.Thread(target=process_thread, daemon=True).start()

    def update_status(self, message):
        self.status_queue.append(message)
        if not self.is_processing:
            self.process_status_queue()

    def process_status_queue(self):
        if self.status_queue:
            message = self.status_queue.pop(0)
            self.status_var.set(message)
            self.is_processing = True
            self.after(100, self.process_status_queue)
        else:
            self.is_processing = False

    def update_output(self, message):
        self.output_text.configure(state="normal")  # Temporarily enable writing
        self.output_text.insert("end", message + "\n")
        self.output_text.see("end")  # Scroll to the end
        self.output_text.configure(state="disabled")  # Disable writing again
        self.logger.info(message)

    def clear_input(self):
        self.user_input.delete("1.0", "end")
        self.output_text.delete("1.0", "end")
        self.duration_var.set("0")
        self.logger.info("Input and output cleared.")
        self.update_status("Ready")
        self.audio_player.clear()

    def open_audio_file(self, event):
        try:
            index = self.output_text.index(f"@{event.x},{event.y}")
            line = self.output_text.get(index + " linestart", index + " lineend")
            if "File saved to:" in line:
                file_path = line.split("File saved to:")[-1].strip()
                self.logger.info(f"Opening audio file: {file_path}")
                open_file(file_path)
        except Exception as e:
            error_message = f"Unable to open file: {str(e)}"
            self.logger.error(error_message)
            self.update_output(f"Error: {error_message}")

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