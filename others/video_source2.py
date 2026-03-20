import cv2
import re
import subprocess


class VideoSource(object):
    def __init__(self, source):
        """
        source puede ser:
        - int -> webcam (0, 1, ...)
        - str -> path local
        - str -> URL (rtsp, http, https, youtube)
        """
        self.source = source

    # =========================
    # PUBLIC
    # =========================
    def open(self):
        if isinstance(self.source, int):
            return self._open_camera()

        if isinstance(self.source, str):
            if self._is_youtube_url(self.source):
                return self._open_youtube()
            else:
                return self._open_generic()

        raise ValueError("Fuente de video no soportada")

    # =========================
    # PRIVATE
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
        """
        Usa yt-dlp para obtener el stream directo
        """
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
