import logging

class BaseService:
    def __init__(self, app, config):
        self.app = app
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)

    def update_status(self, message):
        self.logger.info(message)
        self.app.update_status(message)

    def update_output(self, message):
        self.logger.info(message)
        self.app.update_output(message)

    def handle_error(self, error):
        error_message = f"Error: {str(error)}"
        self.logger.error(error_message)
        self.app.update_output(error_message)
        self.app.update_status("An error occurred")