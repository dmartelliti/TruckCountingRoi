from application.handlers.base_handler import BaseHandler
from application.commands.load_camera_command import LoadCameraCommand


class LoadCameraHandler(BaseHandler[LoadCameraCommand]):

    def handle(self, command: LoadCameraCommand) -> None:
        print(f"Loading camera {command.camera_id}")