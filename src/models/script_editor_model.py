class ScriptEditorModel:
    def __init__(self):
        self.content = ""

    def set_content(self, content):
        self.content = content

    def get_content(self):
        return self.content