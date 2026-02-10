import numpy as np
import supervision as sv
from ultralytics import YOLO
from ultralytics.engine.results import Results



class TrackingDetector(object):
    def __init__(
        self,
        object_classes: list[int] = (2, 3, 5, 7),
        model_name: str = "yolov8s.pt",
        tracker_cfg: str = "bytetrack.yaml"
    ):
        self.model = self._load_model(f"models/{model_name}")
        self.vehicle_classes = object_classes
        self.tracker_cfg = tracker_cfg

    @staticmethod
    def _load_model(model_name):
         return YOLO(model_name)

    def predict(self, image: np.ndarray) -> Results:
        results = self.model.track(
            source=image,
            classes=self.vehicle_classes,
            tracker=self.tracker_cfg,
            persist=True,
            verbose=False
        )

        return results[0]

    def process(self, image: np.ndarray, offset: tuple) -> tuple:
        """
        Process a single frame and return detections + labels.

        Returns
        -------
        detections : sv.Detections | None
        labels : list[str] | None
        """

        result = self.predict(image)

        # No detections at all
        if result.boxes is None or len(result.boxes) == 0:
            return None, None

        # No tracking IDs yet (ByteTrack warmup)
        if result.boxes.id is None:
            return None, None

        offset_y, offset_x = offset
        xyxy = result.boxes.xyxy.cpu().numpy()
        xyxy[:, [0, 2]] += offset_x  # x1, x2
        xyxy[:, [1, 3]] += offset_y  # y1, y2

        # Convert to Supervision Detections
        detections = sv.Detections(
            xyxy=xyxy,
            confidence=result.boxes.conf.cpu().numpy(),
            class_id=result.boxes.cls.cpu().numpy().astype(int),
            tracker_id=result.boxes.id.cpu().numpy().astype(int)
        )

        labels = [
            f"{self.model.names[class_id]} #{track_id}"
            for class_id, track_id
            in zip(detections.class_id, detections.tracker_id)
        ]

        return detections, labels
