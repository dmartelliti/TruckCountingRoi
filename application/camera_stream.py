import logging
from application.video_source import VideoSource


class CameraStream:

    def __init__(self, camera_id: str, source):

        self.camera_id = camera_id
        self.source = source
        self.video_source = None

        self.logger = logging.getLogger(f"CameraStream[{camera_id}]")

        self._open()

    # ==========================
    # PRIVATE
    # ==========================
    def _open(self):

        self.video_source = VideoSource(self.source)
        self.video_source.open()

        self.logger.info(
            f"Camera opened | id={self.camera_id} | source={self.source}"
        )

    # ==========================
    # PUBLIC
    # ==========================
    def read_frame(self):

        if self.video_source is None:
            raise RuntimeError("Camera not initialized")

        frame = self.video_source.read_frame()

        if frame is None:

            # todavía no hay frame, esperar
            if not hasattr(self, "_empty_reads"):
                self._empty_reads = 0

            self._empty_reads += 1

            # permitir algunos ciclos vacíos
            if self._empty_reads < 30:
                return None

            self.logger.warning(
                "Frame read failed. Attempting reconnect..."
            )

            self._reconnect()
            self._empty_reads = 0
            return None

        self._empty_reads = 0
        return frame

    def release(self):

        if self.video_source:

            self.video_source.release()
            self.video_source = None

            self.logger.info("Camera released.")

    def is_opened(self):

        return self.video_source is not None

    # ==========================
    # INTERNAL RESILIENCE
    # ==========================
    def _reconnect(self):

        self.release()

        try:
            self._open()

        except Exception as e:
            self.logger.error(f"Reconnect failed: {e}")