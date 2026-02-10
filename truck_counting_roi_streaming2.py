import cv2
import supervision as sv

from video_source import VideoSource
from tracking_detector import TrackingDetector

# ==============================
# CONFIG
# ==============================
VIDEO_PATH = "https://www.youtube.com/watch?v=WPMgP2C3_co"
#VIDEO_PATH = "vehicle-counting.mp4"

tracking_detector = TrackingDetector(model_name="yolov8n.pt")

# -----------------------------
# Mouse callback
# -----------------------------

roi_start = None
roi_end = None
drawing = False
roi = None
def mouse_callback(event, x, y, flags, param):
    global roi_start, roi_end, drawing, roi

    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        roi_start = (x, y)
        roi_end = (x, y)

    elif event == cv2.EVENT_MOUSEMOVE:
        if drawing:
            roi_end = (x, y)

    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False
        roi_end = (x, y)

        x1, y1 = roi_start
        x2, y2 = roi_end

        roi = (min(x1, x2), min(y1, y2),
               abs(x2 - x1), abs(y2 - y1))
        print("ROI seleccionada:", roi)

# ==============================
# ANNOTATORS
# ==============================
box_annotator = sv.BoxAnnotator(thickness=5)
label_annotator = sv.LabelAnnotator(text_scale=0.8)


# ==============================
# STREAM + TRACKING
# ==============================

source = VideoSource(VIDEO_PATH)
cap = source.open()

cv2.namedWindow("Video")
cv2.setMouseCallback("Video", mouse_callback)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Dibujar ROI en tiempo real mientras arrastrás
    if drawing and roi_start and roi_end:
        cv2.rectangle(frame, roi_start, roi_end, (0, 255, 0), 2)

    # Dibujar ROI final
    if roi is None:
        cv2.imshow("Video", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
        continue

    x, y, w, h = roi
    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)

    roi_frame = frame[y:y+h, x:x+w]

    detections, labels = tracking_detector.process(roi_frame, offset=(y,x))

    if detections is None:
        cv2.imshow("Video", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
        continue

    frame = box_annotator.annotate(frame, detections)

    frame = label_annotator.annotate(frame, detections, labels)

    cv2.imshow("Video", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cv2.destroyAllWindows()
