import tkinter as tk
from tkinter import ttk, messagebox
import logging
import threading
from services import LlamaService, MusicService, SFXService, SpeechService
from utils.file_utils import open_file

class StatusHandler(logging.Handler):
    def __init__(self, status_bar):
        super().__init__()
        self.status_bar = status_bar

    def emit(self, record):
        log_entry = self.format(record)
        self.status_bar.config(text=log_entry)

class Application(tk.Tk):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.title(self.config['gui']['window_title'])
        self.geometry(self.config['gui']['window_size'])
        
        self.llama_service = LlamaService(self, config)
        self.music_service = MusicService(self, config)
        self.sfx_service = SFXService(self, config)
        self.speech_service = SpeechService(self, config)

        self.current_module = tk.StringVar(value="Music")
        self.duration_var = tk.StringVar(value="0")
        self.instrumental_var = tk.BooleanVar(value=False)
        self.selected_voice = tk.StringVar()

        self.voices = []
        self.output_text = None
        self.status_bar = None
        self.setup_logging()
        self.create_widgets()

        self.status_queue = []
        self.is_processing = False

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
        module_frame = ttk.Frame(self)
        module_frame.pack(pady=10)

        for module in ["Music", "SFX", "Speech"]:
            ttk.Radiobutton(
                module_frame, 
                text=module, 
                variable=self.current_module, 
                value=module, 
                command=self.update_action_buttons
            ).pack(side=tk.LEFT, padx=5)

    def create_input_field(self):
        input_frame = ttk.Frame(self)
        input_frame.pack(pady=10)

        ttk.Label(input_frame, text="Enter your text:").pack()
        self.user_input = tk.Text(input_frame, width=70, height=10)
        self.user_input.pack(pady=5)

        self.duration_label = ttk.Label(input_frame, text="Duration (0 = automatic, 0.5-22s):")
        self.duration_entry = ttk.Entry(input_frame, textvariable=self.duration_var)
        self.instrumental_checkbox = ttk.Checkbutton(input_frame, text="Instrumental", variable=self.instrumental_var)
        self.voice_label = ttk.Label(input_frame, text="Select Voice:")
        self.voice_dropdown = ttk.Combobox(input_frame, textvariable=self.selected_voice, state="readonly")

    def create_action_buttons(self):
        self.action_frame = ttk.Frame(self)
        self.action_frame.pack(pady=10)

        self.llama_button = ttk.Button(self.action_frame, text="Input to Llama3", command=self.process_llama_input)
        self.generate_button = ttk.Button(self.action_frame, text="Generate", command=self.process_input)
        self.clear_button = ttk.Button(self.action_frame, text="Clear", command=self.clear_input)

        self.update_action_buttons()

    def update_action_buttons(self):
        for widget in self.action_frame.winfo_children():
            widget.pack_forget()

        if self.current_module.get() in ["Music", "SFX"]:
            self.llama_button.pack(side=tk.LEFT, padx=5)
        self.generate_button.pack(side=tk.LEFT, padx=5)
        self.clear_button.pack(side=tk.LEFT, padx=5)

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
        output_frame = ttk.Frame(self)
        output_frame.pack(pady=10)

        ttk.Label(output_frame, text="Output:").pack()
        self.output_text = tk.Text(output_frame, height=10, width=70)
        self.output_text.pack()
        self.output_text.bind("<Button-1>", self.open_audio_file)

    def create_status_bar(self):
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        self.status_bar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def load_voices(self):
        try:
            self.logger.info("Loading available voices...")
            self.voices = self.speech_service.get_available_voices()
            if self.voices:
                self.voice_dropdown['values'] = [voice[0] for voice in self.voices]
                self.voice_dropdown.current(0)
                self.logger.info(f"Loaded {len(self.voices)} voices.")
            else:
                self.voice_dropdown['values'] = ["No voices available"]
                self.logger.warning("No voices available.")
        except Exception as e:
            self.logger.error(f"Failed to load voices: {str(e)}")
            messagebox.showerror("Error", f"Failed to load voices: {str(e)}")
            self.voice_dropdown['values'] = ["No voices available"]

    def process_llama_input(self):
        user_input = self.user_input.get("1.0", tk.END).strip()
        if not user_input:
            self.logger.error("Please enter some text.")
            messagebox.showerror("Error", "Please enter some text.")
            return

        self.logger.info(f"Processing Llama3 input for {self.current_module.get()} module...")
        if self.current_module.get() == "Music":
            result = self.llama_service.get_llama_musicprompt(user_input)
        elif self.current_module.get() == "SFX":
            result = self.llama_service.get_llama_sfx(user_input)
        else:
            self.logger.error("Llama3 input is only available for Music and SFX modules.")
            messagebox.showerror("Error", "Llama3 input is only available for Music and SFX modules.")
            return

        if result:
            self.user_input.delete("1.0", tk.END)
            self.user_input.insert(tk.END, result)
            self.logger.info("Llama3 processing complete. Result inserted in the input field.")
        else:
            self.logger.error("Failed to process input with Llama3.")

    def process_input(self):
        if self.current_module.get() == "Music":
            self.process_music_request()
        elif self.current_module.get() == "SFX":
            self.process_sfx_request()
        elif self.current_module.get() == "Speech":
            self.process_speech_request()

    def process_music_request(self):
        self._process_request(self.music_service.process_music_request, 
                              [self.user_input.get("1.0", tk.END).strip(), self.instrumental_var.get()])

    def process_sfx_request(self):
        self._process_request(self.sfx_service.process_sfx_request, 
                              [self.user_input.get("1.0", tk.END).strip(), self.duration_var.get()])

    def process_speech_request(self):
        selected_voice_name = self.selected_voice.get()
        voice_id = next((voice[1] for voice in self.voices if voice[0] == selected_voice_name), None)
        if voice_id:
            self._process_request(self.speech_service.process_speech_request, 
                                  [self.user_input.get("1.0", tk.END).strip(), voice_id])
        else:
            self.logger.error("Invalid voice selected.")
            messagebox.showerror("Error", "Invalid voice selected.")

    def _process_request(self, service_method, args):
        if not args[0]:  # Check if user input is empty
            self.logger.error("Please enter some text.")
            messagebox.showerror("Error", "Please enter some text.")
            return

        self.logger.info(f"Processing {service_method.__self__.__class__.__name__} request...")
        self.generate_button.config(state=tk.DISABLED)
        
        def process_thread():
            result = service_method(*args)
            if result:
                self.logger.info(f"Audio generated successfully. File saved to: {result}")
                self.after(0, lambda: self.update_status("Ready"))
            else:
                self.after(0, lambda: self.update_status("An error occurred"))
            self.after(0, lambda: self.generate_button.config(state=tk.NORMAL))

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
        self.output_text.insert(tk.END, message + "\n")
        self.output_text.see(tk.END)  # Scroll to the end
        self.logger.info(message)

        # If it's an error message, show it in a messagebox as well
        if message.startswith("Error:"):
            messagebox.showerror("Error", message)

    def clear_input(self):
        self.user_input.delete("1.0", tk.END)
        if self.output_text:
            self.output_text.delete("1.0", tk.END)
        self.duration_var.set("0")
        self.logger.info("Input and output cleared.")
        self.update_status("Ready")

    def open_audio_file(self, event):
        try:
            index = self.output_text.index(f"@{event.x},{event.y}")
            line = self.output_text.get(index + " linestart", index + " lineend")
            if "File saved to:" in line:
                file_path = line.split("File saved to:")[-1].strip()
                self.logger.info(f"Opening audio file: {file_path}")
                open_file(file_path)
        except Exception as e:
            self.logger.error(f"Unable to open file: {str(e)}")
            messagebox.showerror("Error", f"Unable to open file: {str(e)}")

if __name__ == "__main__":
    import yaml
    with open('config/config.yaml', 'r') as file:
        config = yaml.safe_load(file)
    app = Application(config)
    app.mainloop()