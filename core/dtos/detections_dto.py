from dataclasses import dataclass, field
from typing import List
from .detection_dto import DetectionDto


@dataclass(slots=True)
class DetectionsDto:
    frame_id: int
    detections: List[DetectionDto] = field(default_factory=list)

    def __iter__(self):
        return iter(self.detections)

    def __len__(self):
        return len(self.detections)