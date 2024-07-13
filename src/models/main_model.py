from models.audio_model import AudioModel

class MainModel:
    def __init__(self):
        self.audio_model = AudioModel()
        # Add other models here as needed, e.g.:
        # self.script_model = ScriptModel()

    def get_audio_model(self):
        return self.audio_model

    # Add other methods to interact with models as needed