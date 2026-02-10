import cv2
from ultralytics import YOLO
import supervision as sv
import numpy as np
import subprocess

import logging

from video_source import VideoSource

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger("yolo-track")

# Ejemplo de como usar un llm para detectar un perro usando sv y PaliGemma
# https://roboflow.github.io/cheatsheet-supervision/

# video streaming
# https://www.youtube.com/watch?v=OS5qI9YBkfk

# ==============================
# CONFIG
# ==============================
VIDEO_PATH = "https://www.youtube.com/watch?v=WPMgP2C3_co"
# MODEL_PATH = "yolov8n.pt"
MODEL_PATH = "models/yolov8s.pt"  ## Better for traffic
# MODEL_PATH = "yolov8m.pt"

VEHICLE_CLASSES = [2, 3, 5, 7]

# ==============================
# MODEL
# ==============================
model = YOLO(MODEL_PATH)

# ==============================
# ANNOTATORS
# ==============================
box_annotator = sv.BoxAnnotator(thickness=5)
label_annotator = sv.LabelAnnotator(text_scale=0.8)


# ==============================
# STREAM + TRACKING
# ==============================

print("[INFO] Procesando video. Presioná 'q' para salir.")
source = VideoSource("https://www.youtube.com/watch?v=WPMgP2C3_co")
cap = source.open()

print("▶️ Tracking iniciado (ESC para salir)")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    results = model.track(
        source=frame,
        classes=VEHICLE_CLASSES,  ## Optimization
        # imgsz=640,  # default  ## Optimization
        # imgsz=480,      # ⚡ más rápido
        # imgsz=320,      # ⚡⚡ ultra rápido (menos precisión)
        tracker="bytetrack.yaml",
        persist=True
    )

    result = results[0]

    if result.boxes.id is None:
        cv2.imshow("YOLO + ByteTrack (MP4)", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
        continue

    # Convertir a Supervision Detections
    detections = sv.Detections(
        xyxy=result.boxes.xyxy.cpu().numpy(),
        confidence=result.boxes.conf.cpu().numpy(),
        class_id=result.boxes.cls.cpu().numpy().astype(int),
        tracker_id=result.boxes.id.cpu().numpy().astype(int)
    )

    labels = [
        f"{model.names[class_id]} #{track_id}"
        for class_id, track_id
        in zip(detections.class_id, detections.tracker_id)
    ]

    frame = box_annotator.annotate(frame, detections)

    frame = label_annotator.annotate(frame, detections, labels)

    cv2.imshow("YOLO + ByteTrack (MP4)", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cv2.destroyAllWindows()
