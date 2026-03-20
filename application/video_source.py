import cv2
import re
import subprocess
import threading
import time


class VideoSource:

    def __init__(self, source):

        self.source = source
        self.cap = None

        self.latest_frame = None
        self.lock = threading.Lock()

        self.running = False
        self.thread = None
        self.fps = 30

    # =========================
    # PUBLIC
    # =========================
    def open(self):

        if isinstance(self.source, int):
            self.cap = self._open_camera()

        elif isinstance(self.source, str):

            if self._is_youtube_url(self.source):
                self.cap = self._open_youtube()

            else:
                self.cap = self._open_generic()

        else:
            raise ValueError("Fuente de video no soportada")

        # evitar lag por buffer
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        fps = self.cap.get(cv2.CAP_PROP_FPS)
        if fps and fps > 1:
            self.fps = fps

        self.running = True

        self.thread = threading.Thread(
            target=self._reader_loop,
            daemon=True
        )

        self.thread.start()

    def read_frame(self):

        with self.lock:
            if self.latest_frame is None:
                return None

            return self.latest_frame.copy()

    def release(self):

        self.running = False

        if self.thread:
            self.thread.join(timeout=1)

        if self.cap:
            self.cap.release()

        self.cap = None

    # =========================
    # INTERNAL
    # =========================
    def _reader_loop(self):

        frame_interval = 1.0 / self.fps

        while self.running:

            start = time.time()

            ret, frame = self.cap.read()

            if not ret:
                continue

            with self.lock:
                self.latest_frame = frame

            elapsed = time.time() - start
            sleep_time = frame_interval - elapsed

            if sleep_time > 0:
                time.sleep(sleep_time)

    # =========================
    # SOURCE OPENERS
    # =========================
    def _open_camera(self):

        cap = cv2.VideoCapture(self.source)
        self._check_cap(cap)

        return cap

    def _open_generic(self):

        cap = cv2.VideoCapture(self.source)
        self._check_cap(cap)

        return cap

    def _open_youtube(self):

        stream_url = self._get_youtube_stream_url(self.source)

        cap = cv2.VideoCapture(stream_url)
        self._check_cap(cap)

        return cap

    # =========================
    # HELPERS
    # =========================
    @staticmethod
    def _check_cap(cap):

        if not cap.isOpened():
            raise RuntimeError("❌ No se pudo abrir la fuente de video")

    @staticmethod
    def _is_youtube_url(url):

        return bool(re.search(r"(youtube\.com|youtu\.be)", url))

    @staticmethod
    def _get_youtube_stream_url(url):

        command = [
            "yt-dlp",
            "-f", "best[ext=mp4]/best",
            "-g",
            url
        ]

        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        if result.returncode != 0:
            raise RuntimeError("❌ Error obteniendo stream de YouTube")

        return result.stdout.strip()

if __name__ == '__main__':
    # importa tu clase
    # from video_source import VideoSource

    def main():

        # ejemplos de fuentes
        # source = 0
        source = "video.mp4"
        # source = "https://www.youtube.com/watch?v=XXXXX"

        video = VideoSource(source)

        video.open()

        print("Video abierto. Presiona 'q' para salir.")

        last_time = time.time()
        frame_count = 0

        while True:

            frame = video.read_frame()

            if frame is None:
                continue

            cv2.imshow("VideoSource Test", frame)

            frame_count += 1

            # medir FPS real
            now = time.time()
            if now - last_time >= 1:
                print(f"FPS real: {frame_count}")
                frame_count = 0
                last_time = now

            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                break

        video.release()
        cv2.destroyAllWindows()


    if __name__ == "__main__":
        main()