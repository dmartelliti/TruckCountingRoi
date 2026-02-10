import numpy as np
import supervision as sv
import torch
from ultralytics import YOLO
from ultralytics.engine.results import Results


class TrackingDetector(object):
    def __init__(
        self,
        object_classes: list[int] = (2, 3, 5, 7),
        model_name: str = "yolov8s.pt",
        tracker_cfg: str = "bytetrack.yaml",
        device: str | None = None,
    ):
        self.device = self._select_device(device)
        self.model = self._load_model(f"models/{model_name}")
        self.vehicle_classes = object_classes
        self.tracker_cfg = tracker_cfg

    @staticmethod
    def _select_device(device):
        if device is not None:
            print(f"[TrackingDetector] Using user-selected device: {device}")
            return device

        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            print(f"[TrackingDetector] CUDA available — using GPU: {gpu_name}")
            return "cuda"
        else:
            print("[TrackingDetector] CUDA NOT available — falling back to CPU")
            return "cpu"

    @staticmethod
    def _load_model(model_name):
        return YOLO(model_name)

    def predict(self, image: np.ndarray) -> Results:
        results = self.model.track(
            source=image,
            classes=self.vehicle_classes,
            tracker=self.tracker_cfg,
            persist=True,
            verbose=False,
            device=self.device,
        )

        return results[0]

    def process(self, image: np.ndarray, offset: tuple) -> tuple:
        result = self.predict(image)

        if result.boxes is None or len(result.boxes) == 0:
            return None, None

        if result.boxes.id is None:
            return None, None

        offset_y, offset_x = offset
        xyxy = result.boxes.xyxy.cpu().numpy()
        xyxy[:, [0, 2]] += offset_x
        xyxy[:, [1, 3]] += offset_y

        detections = sv.Detections(
            xyxy=xyxy,
            confidence=result.boxes.conf.cpu().numpy(),
            class_id=result.boxes.cls.cpu().numpy().astype(int),
            tracker_id=result.boxes.id.cpu().numpy().astype(int),
        )

        labels = [
            f"{self.model.names[class_id]} #{track_id}"
            for class_id, track_id in zip(
                detections.class_id,
                detections.tracker_id
            )
        ]

        return detections, labels
