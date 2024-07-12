class AudioController:
    def __init__(self, model, view):
        self.model = model
        self.view = view
        self.setup_view_commands()

    def setup_view_commands(self):
        self.view.set_play_command(self.play_audio)
        self.view.set_pause_resume_command(self.pause_resume_audio)
        self.view.set_stop_command(self.stop_audio)
        self.view.set_seek_command(self.seek_audio)

    def load_audio(self, file_path):
        self.model.load_audio(file_path)
        self.view.update_button_states(False, False)

    def play_audio(self):
        self.model.play()
        self.view.update_button_states(self.model.is_playing, self.model.is_paused)

    def pause_resume_audio(self):
        if self.model.is_playing and not self.model.is_paused:
            self.model.pause()
        elif self.model.is_paused:
            self.model.resume()
        self.view.update_button_states(self.model.is_playing, self.model.is_paused)

    def stop_audio(self):
        self.model.stop()
        self.view.update_button_states(self.model.is_playing, self.model.is_paused)
        self.view.update_playhead(0)

    def update_playhead(self):
        if self.model.is_playing and not self.model.is_paused:
            current_time = self.model.get_current_position()
            self.view.update_playhead(current_time)
        return self.model.is_playing

    def seek_audio(self, position):
        if self.model.seek(position):
            self.view.update_playhead(position)
            if not self.model.is_playing:
                self.play_audio()
                
    def clear(self):
        self.model.stop()
        self.view.clear()
        self.view.update_button_states(False, False)

    def quit(self):
        self.model.quit()