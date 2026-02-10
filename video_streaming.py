import cv2
import time
import atexit
from flask import Flask, Response

app = Flask(__name__)
camera = cv2.VideoCapture(0)

if not camera.isOpened():
    raise RuntimeError("Could not start camera")

def cleanup():
    camera.release()

atexit.register(cleanup)


def generate_frames():
    while True:
        success, frame = camera.read()
        if not success:
            continue

        ret, buffer = cv2.imencode('.jpg', frame)
        if not ret:
            continue

        frame_bytes = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' +
               frame_bytes + b'\r\n')

        time.sleep(0.03)


@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/')
def index():
    return "<h1>Video Streaming</h1><img src='/video_feed'>"


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, threaded=True)
