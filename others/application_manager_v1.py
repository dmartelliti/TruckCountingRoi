import time
import logging
from application.camera_stream import CameraStream
from core.pipelines.truck_counter_pipeline import TruckCounterPipeline
from application.constants import AppState, CameraState

import os
import cv2
import base64
os.environ["OPENCV_FFMPEG_LOGLEVEL"] = "quiet"

from functools import wraps

def log_exceptions(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except Exception as e:
            self.logger.exception(f"Unhandled exception in {func.__name__}: {e}")
            raise
    return wrapper


class ApplicationManager:

    def __init__(self, config):
        self.config = config

        # Core components (v1: single instances)
        self.camera = None
        self.pipeline = None

        # State
        self.state = AppState.IDLE
        self.camera_state = CameraState.IDLE
        self.running = False

        # Logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s"
        )
        self.logger = logging.getLogger("ApplicationManager")

    # ==========================
    # MAIN LOOP
    # ==========================
    @log_exceptions
    def run(self, event_queue, instruction_queue, frame_queue):
        self.logger.info("ApplicationManager started.")

        while True:
            try:
                self._consume_instructions(instruction_queue)
                if self.camera_state == CameraState.IDLE:
                    continue

                frame = self._get_next_frame(frame_queue)

                if self.state == AppState.DETECTING:
                    self._process_frame(frame, event_queue)

                time.sleep(0.01)

            except Exception as e:
                self.logger.exception(f"Critical error in main loop: {e}")
                time.sleep(0.5)

    # ==========================
    # INSTRUCTION HANDLING
    # ==========================
    def _consume_instructions(self, queue):
        if not queue.empty():
            command = queue.get()
            self.logger.info(f"Received command: {command}")
            self._handle_command(command)

    def _handle_command(self, command):
        """
        command.name: str
        command.payload: dict
        """

        if command.type == "load_camera":
            self._load_camera(command.payload)

        elif command.type == "start_detection":
            self._start_detection(command.payload)

        elif command.type == "stop_detection":
            self._stop_detection()

        elif command.type == "update_config":
            self._update_config(command.payload)

        else:
            self.logger.warning(f"Unknown command: {command.type}")

    # ==========================
    # COMMAND IMPLEMENTATIONS
    # ==========================
    def _load_camera(self, payload):
        camera_ip = payload.get("camera_ip")
        source = payload.get("source")

        # Aquí iría tu implementación real
        self.camera = CameraStream(camera_ip, source)

        self.state = AppState.CAMERA_LOADED
        self.camera_state = CameraState.STREAMING
        self.logger.info(f"Camera loaded: {camera_ip}")

    def _start_detection(self, payload):
        if self.state != AppState.CAMERA_LOADED:
            self.logger.warning("Cannot start detection. Camera not loaded.")
            return

        self.pipeline = TruckCounterPipeline()
        self.state = AppState.DETECTING
        self.running = True

        self.logger.info("Detection started.")

    def _stop_detection(self):
        self.running = False
        self.state = AppState.STOPPED
        self.logger.info("Detection stopped.")

    def _update_config(self, payload):
        if self.pipeline:
            self.pipeline.update_config(payload)
            self.logger.info("Pipeline configuration updated.")
        else:
            self.logger.warning("No pipeline to update.")

    # ==========================
    # FRAME PROCESSING
    # ==========================

    def _get_next_frame(self, frame_queue):
        frame = self.camera.read_frame()
        frame_queue.put((frame, (500, 400), (3500, 400)))
        return frame

    def _process_frame(self, frame, event_queue):
        if frame is None:
            self.logger.warning("Empty frame received.")
            return

        events = self.pipeline.process(frame)

        if events:
            _, buffer = cv2.imencode('.jpg', frame)
            frame_base64 = base64.b64encode(buffer.tobytes()).decode('utf-8')
            self.logger.info(f"Processed frame: {frame_base64}")
            for event in events:
                event_queue.put(event)


