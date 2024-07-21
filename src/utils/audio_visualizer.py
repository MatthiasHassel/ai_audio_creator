import tkinter as tk
from PIL import Image, ImageDraw, ImageTk
import numpy as np
import wave
import struct
from pydub import AudioSegment
import threading
import logging

class AudioVisualizer(tk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.canvas = tk.Canvas(self, bg='#2b2b2b', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        self.playhead_line = None
        self.waveform_image = None
        self.audio_duration = 0

    def update_waveform(self, audio_file):
        try:
            width = self.canvas.winfo_width()
            height = self.canvas.winfo_height()
            if width <= 1 or height <= 1:  # Canvas not properly sized yet
                self.master.after(100, lambda: self.update_waveform(audio_file))
                return
            thread = threading.Thread(target=self._process_audio, args=(audio_file, width, height))
            thread.start()
        except Exception as e:
            logging.error(f"Error updating waveform: {str(e)}", exc_info=True)

    def _process_audio(self, audio_file, width, height):
        try:
            audio = AudioSegment.from_file(audio_file)
            samples = np.array(audio.get_array_of_samples())
            
            # Downsample
            samples = samples[::max(1, len(samples) // width)]
            
            # Normalize
            if np.max(np.abs(samples)) > 0:
                samples = samples / np.max(np.abs(samples))
            
            # Create image
            img = Image.new('RGB', (width, height), color='#2b2b2b')
            draw = ImageDraw.Draw(img)
            
            for x, sample in enumerate(samples):
                y = int((1 - sample) * height / 2)
                draw.line((x, height // 2, x, y), fill=(0, 170, 255))  # Light blue color

            self.waveform_image = ImageTk.PhotoImage(img)
            self.audio_duration = len(audio) / 1000.0  # Duration in seconds
            
            self.master.after(0, self._draw_waveform)
        except Exception as e:
            logging.error(f"Error processing audio: {str(e)}", exc_info=True)

    def _draw_waveform(self):
        if self.waveform_image:
            self.canvas.delete("all")
            self.canvas.create_image(0, self.canvas.winfo_height() // 2, anchor="w", image=self.waveform_image)
            self.playhead_line = self.canvas.create_line(0, 0, 0, self.canvas.winfo_height(), fill='red', width=2)

    def update_playhead(self, position):
        if self.playhead_line and self.audio_duration > 0:
            x = position / self.audio_duration * self.canvas.winfo_width()
            self.canvas.coords(self.playhead_line, x, 0, x, self.canvas.winfo_height())

    def clear(self):
        self.canvas.delete("all")
        self.waveform_image = None
        self.audio_duration = 0
        self.playhead_line = None

    def set_on_click_seek(self, callback):
        def on_click(event):
            if self.audio_duration > 0:
                fraction = event.x / self.canvas.winfo_width()
                time = fraction * self.audio_duration
                callback(time)
        self.canvas.bind("<Button-1>", on_click)