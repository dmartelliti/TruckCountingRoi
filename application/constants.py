from enum import Enum


class AppState(Enum):
    IDLE = "idle"
    CAMERA_LOADED = "camera_loaded"
    DETECTING = "detecting"
    STOPPED = "stopped"

class CameraState(Enum):
    IDLE = "idle"
    STREAMING = "streaming"