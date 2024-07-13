from controllers.audio_controller import AudioController

class MainController:
    def __init__(self, model, view, config):
        self.model = model
        self.view = view
        self.config = config
        self.setup_controllers()

    def setup_controllers(self):
        audio_model = self.model.get_audio_model()
        audio_view = self.view.get_audio_generator_view()
        self.audio_controller = AudioController(audio_model, audio_view, self.config)

    def run(self):
        # Perform any necessary initialization
        self.audio_controller.load_voices()

        # Start the main event loop
        self.view.run()

    def quit(self):
        # Perform any necessary cleanup
        self.audio_controller.quit()
        self.view.quit()