import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from pydub import AudioSegment
import threading
import queue

class AudioVisualizer:
    def __init__(self, master):
        self.master = master
        self.figure, self.ax = plt.subplots(figsize=(6, 0.75))
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.master)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.playhead_line = None
        self.audio_duration = 0
        self.waveform_data = None
        self.render_queue = queue.Queue()
        self.render_thread = threading.Thread(target=self.render_worker, daemon=True)
        self.render_thread.start()
        self.on_click_seek = None
        self.setup_plot()

    def setup_plot(self):
        bg_color = '#2b2b2b'
        self.ax.set_facecolor(bg_color)
        self.figure.patch.set_facecolor(bg_color)
        self.ax.axis('off')
        self.canvas_widget.configure(bg=bg_color)
        self.figure.subplots_adjust(left=0.01, right=1, top=1, bottom=0)
        self.playhead_line, = self.ax.plot([0, 0], [-1, 1], color='r', linewidth=1)
        self.canvas.mpl_connect('button_press_event', self._on_click)

    def update_waveform(self, audio_file):
        def process_audio():
            try:
                audio = AudioSegment.from_file(audio_file)
                if audio.channels == 2:
                    audio = audio.set_channels(1)
                
                samples = np.array(audio.get_array_of_samples()).astype(np.float32)
                samples = samples / np.max(np.abs(samples))
                
                self.audio_duration = audio.duration_seconds
                
                chunk_size = 1000
                num_chunks = len(samples) // chunk_size
                max_min = np.array([(np.max(samples[i:i+chunk_size]), np.min(samples[i:i+chunk_size])) 
                                    for i in range(0, len(samples), chunk_size)])
                
                time = np.linspace(0, self.audio_duration, num=len(max_min))
                
                self.render_queue.put((time, max_min))
            except Exception as e:
                print(f"Error processing audio: {str(e)}")

        threading.Thread(target=process_audio, daemon=True).start()

    def render_worker(self):
        while True:
            time, max_min = self.render_queue.get()
            if time is None and max_min is None:
                break
            
            self.ax.clear()
            self.setup_plot()
            
            self.ax.plot(time, max_min[:, 0], color='#00aaff', linewidth=0.5, alpha=0.7)
            self.ax.plot(time, max_min[:, 1], color='#00aaff', linewidth=0.5, alpha=0.7)
            self.ax.fill_between(time, max_min[:, 0], max_min[:, 1], color='#00aaff', alpha=0.3)
            
            self.ax.set_xlim(0, self.audio_duration)
            self.ax.set_ylim(-1, 1)
            
            self.waveform_data = (time, max_min)
            self.playhead_line.set_xdata([0, 0])
            
            self.master.after(0, self.canvas.draw)

    def update_playhead(self, position):
        if self.playhead_line:
            self.playhead_line.set_xdata([position, position])
            self.canvas.draw_idle()

    def set_on_click_seek(self, callback):
        self.on_click_seek = callback

    def _on_click(self, event):
        if event.xdata is not None and self.audio_duration > 0 and self.on_click_seek:
            click_time = event.xdata
            if 0 <= click_time <= self.audio_duration:
                self.on_click_seek(click_time)

    def clear(self):
        self.ax.clear()
        self.setup_plot()
        self.waveform_data = None
        self.audio_duration = 0
        self.canvas.draw()

    def quit(self):
        self.render_queue.put((None, None))
        self.render_thread.join()