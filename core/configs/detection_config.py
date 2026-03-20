from dataclasses import dataclass

@dataclass
class DetectionConfig:
    conf: float = 0.25
    iou: float = 0.7