import cv2
import supervision as sv
from flask import Flask, Response

from video_source import VideoSource
from tracking_detector import TrackingDetector

# ==============================
# CONFIG
# ==============================
VIDEO_PATH = "vehicle-counting.mp4"
tracking_detector = TrackingDetector(model_name="yolov8n.pt")

# ==============================
# ANNOTATORS
# ==============================
box_annotator = sv.BoxAnnotator(thickness=5)
label_annotator = sv.LabelAnnotator(text_scale=0.8)

# ==============================
# VIDEO SOURCE
# ==============================
source = VideoSource(VIDEO_PATH)
cap = source.open()

# ==============================
# FLASK APP
# ==============================
app = Flask(__name__)

def generate_frames():
    while True:
        ret, frame = cap.read()
        if not ret:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Reinicia el video si llega al final
            continue

        detections, labels = tracking_detector.process(frame)

        if detections is not None:
            frame = box_annotator.annotate(frame, detections)
            frame = label_annotator.annotate(frame, detections, labels)

        # Codifica la imagen a JPEG
        ret, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()

        # Devuelve el frame como un stream MJPEG
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=8000,
        debug=False,
        threaded=True,
        use_reloader=False
    )

