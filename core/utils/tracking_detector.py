import torch
import numpy as np
import logging

from ultralytics import YOLO
from ultralytics.engine.results import Results

from typing import Optional
from core.dtos.bbox_dto import BBoxDto
from core.dtos.detection_dto import DetectionDto
from core.dtos.detections_dto import DetectionsDto
from core.configs.detection_config import DetectionConfig

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class TrackingDetector(object):

    def __init__(
        self,
        object_classes: list[int] = (2, 3, 5, 7),
        model_name: str = "yolov8s.pt",
        tracker_cfg: str = "bytetrack.yaml",
        device: Optional[str] = None,
    ):
        self.logger = logging.getLogger(self.__class__.__name__)

        self.device = self._select_device(device)
        self.model = self._load_model(BASE_DIR / "models" / model_name)
        self.vehicle_classes = object_classes
        self.tracker_cfg = tracker_cfg

        # configuración interna
        self.detection_config = DetectionConfig()

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

    def update_config(self, configs):
        if configs is None or "detector" not in configs:
            return
        self.detection_config.conf = configs['detector'].get("conf", self.detection_config.conf)
        self.detection_config.iou = configs['detector'].get("iou", self.detection_config.iou)

        self.logger.info(
            f"Detector config updated | conf={self.detection_config.conf}, iou={self.detection_config.iou}"
        )

    # -------- PREDICT --------
    def predict(self, image: np.ndarray) -> Results:

        results = self.model.track(
            source=image,
            classes=self.vehicle_classes,
            tracker=self.tracker_cfg,
            persist=True,
            verbose=False,
            device=self.device,
            conf=self.detection_config.conf,
            iou=self.detection_config.iou
        )

        return results[0]

    def process(
        self,
        image: np.ndarray,
        offset: Optional[tuple] = None,
        frame_id: Optional[int] = None
    ) -> DetectionsDto:

        result = self.predict(image)
        detections = DetectionsDto(frame_id=frame_id)

        if result.boxes is None or len(result.boxes) == 0:
            return detections

        if result.boxes.id is None:
            return detections

        xyxy = result.boxes.xyxy.cpu().numpy()
        conf = result.boxes.conf.cpu().numpy()
        cls = result.boxes.cls.cpu().numpy().astype(int)
        ids = result.boxes.id.cpu().numpy().astype(int)

        if offset is not None:
            offset_y, offset_x = offset
            xyxy[:, [0, 2]] += offset_x
            xyxy[:, [1, 3]] += offset_y

        for box, c, k, t in zip(xyxy, conf, cls, ids):

            bbox = BBoxDto(
                x1=float(box[0]),
                y1=float(box[1]),
                x2=float(box[2]),
                y2=float(box[3]),
                img_shape=image.shape[:2]
            )

            label = self.model.names[k]

            detections.detections.append(
                DetectionDto(
                    bbox=bbox,
                    class_id=k,
                    label=label,
                    confidence=float(c),
                    track_id=int(t),
                    frame_id=frame_id,
                    model_version=self.model.ckpt_path,
                )
            )

        return detections