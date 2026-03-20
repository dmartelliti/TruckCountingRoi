import logging
from application.video_source import VideoSource


class CameraStream:
    def __init__(self, camera_id: str, source):
        """
        camera_id: identificador lógico del sistema
        source:
            - int (webcam)
            - str (path)
            - str (rtsp/http/youtube)
        """
        self.camera_id = camera_id
        self.source = source
        self.cap = None

        self.logger = logging.getLogger(f"CameraStream[{camera_id}]")

        self._open()

    # ==========================
    # PRIVATE
    # ==========================
    def _open(self):
        video_source = VideoSource(self.source)
        self.cap = video_source.open()

        self.logger.info(
            f"Camera opened | id={self.camera_id} | source={self.source}"
        )

    # ==========================
    # PUBLIC
    # ==========================
    def read_frame(self):
        if self.cap is None:
            raise RuntimeError("Camera not initialized")

        ret, frame = self.cap.read()

        if not ret:
            self.logger.warning("Frame read failed. Attempting reopen...")
            self._reconnect()
            return None

        return frame

    def release(self):
        if self.cap:
            self.cap.release()
            self.cap = None
            self.logger.info("Camera released.")

    def is_opened(self):
        return self.cap is not None and self.cap.isOpened()

    # ==========================
    # INTERNAL RESILIENCE
    # ==========================
    def _reconnect(self):
        self.release()
        try:
            self._open()
        except Exception as e:
            self.logger.error(f"Reconnect failed: {e}")




if __name__ == "__main__":
    import cv2
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

    YOUTUBE_URL = "https://www.youtube.com/watch?v=WPMgP2C3_co"

    try:
        camera = CameraStream(
            camera_id="cam_youtube_test",
            source=YOUTUBE_URL
        )

        print("Press 'q' to exit...")

        while True:
            frame = camera.read_frame()

            if frame is None:
                continue

            cv2.imshow("Camera Stream", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except Exception as e:
        print(f"Error: {e}")

    finally:
        if "camera" in locals():
            camera.release()

        cv2.destroyAllWindows()
        print("Stream closed.")