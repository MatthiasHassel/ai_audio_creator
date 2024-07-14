from controllers.audio_controller import AudioController
from controllers.script_editor_controller import ScriptEditorController
from models.audio_model import AudioModel
from models.script_model import ScriptModel

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

        script_model = self.model.get_script_model()
        script_view = self.view.get_script_editor_view()
        self.script_editor_controller = ScriptEditorController(script_model, script_view, self.config)

    def run(self):
        # Perform any necessary initialization
        self.audio_controller.load_voices()

        # Start the main event loop
        self.view.run()

    def quit(self):
        # Perform any necessary cleanup
        self.audio_controller.quit()
        self.view.quit()