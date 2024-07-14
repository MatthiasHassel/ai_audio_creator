from models.audio_model import AudioModel
from models.script_model import ScriptModel

class MainModel:
    def __init__(self):
        self.audio_model = AudioModel()
        self.script_model = ScriptModel()

    def get_audio_model(self):
        return self.audio_model

    def get_script_model(self):
        return self.script_model