import cv2
from ultralytics import YOLO
import supervision as sv
import os

# Ejemplo de como usar un llm para detectar un perro usando sv y PaliGemma
# https://roboflow.github.io/cheatsheet-supervision/

# video streaming
# https://www.youtube.com/watch?v=OS5qI9YBkfk

# ==============================
# CONFIG
# ==============================
VIDEO_PATH = "data/vehicle-counting.mp4"  # 👈 ruta a tu MP4
# MODEL_PATH = "yolov8n.pt"
MODEL_PATH = "models/yolov8s.pt"  ## Better for traffic
# MODEL_PATH = "yolov8m.pt"

VEHICLE_CLASSES = [2, 3, 5, 7]

assert os.path.exists(VIDEO_PATH), f"No existe el archivo: {VIDEO_PATH}"

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

results = model.track(
    source=VIDEO_PATH,
    classes=VEHICLE_CLASSES, ## Optimization
    # imgsz=640,  # default  ## Optimization
    # imgsz=480,      # ⚡ más rápido
    # imgsz=320,      # ⚡⚡ ultra rápido (menos precisión)
    tracker="bytetrack.yaml",
    persist=True,
    stream=True,
    verbose=False
)

print("[INFO] Procesando video. Presioná 'q' para salir.")

for i, result in enumerate(results):
    if i % 1 != 0: ## Optimization
        continue

    frame = result.orig_img

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
