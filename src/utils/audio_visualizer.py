import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from pydub import AudioSegment

class AudioVisualizer:
    def __init__(self, master):
        self.master = master
        self.figure, self.ax = plt.subplots(figsize=(6, 0.75))
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.master)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.setup_plot()
        self.playhead = None
        self.audio_duration = 0

    def setup_plot(self):
        bg_color = '#2b2b2b'
        self.ax.set_facecolor(bg_color)
        self.figure.patch.set_facecolor(bg_color)
        self.ax.axis('off')
        self.canvas_widget.configure(bg=bg_color)

    def update_waveform(self, audio_file):
        try:
            audio = AudioSegment.from_file(audio_file)
            if audio.channels == 2:
                audio = audio.set_channels(1)
            
            samples = np.array(audio.get_array_of_samples()).astype(np.float32)
            samples = samples / np.max(np.abs(samples))
            
            self.audio_duration = audio.duration_seconds
            time = np.linspace(0, self.audio_duration, num=len(samples))

            self.ax.clear()
            self.setup_plot()
            
            self.ax.plot(time, samples, color='#00aaff', linewidth=0.5, alpha=0.7)
            self.ax.set_xlim(0, self.audio_duration)
            self.ax.set_ylim(-1, 1)
            
            self.update_playhead(0)  # Show playhead at start
            self.canvas.draw()
        except Exception as e:
            print(f"Error updating waveform: {str(e)}")

    def update_playhead(self, position):
        self.hide_playhead()  # Remove existing playhead if any
        self.playhead = self.ax.axvline(x=position, color='r', linewidth=0.5)
        self.canvas.draw()

    def clear(self, hide_playhead=False):
        self.ax.clear()
        self.setup_plot()
        self.hide_playhead()
        if not hide_playhead:
            self.update_playhead(0)
        self.canvas.draw()
        self.audio_duration = 0

    def hide_playhead(self):
        if self.playhead:
            self.playhead.remove()
            self.playhead = None
            self.canvas.draw()