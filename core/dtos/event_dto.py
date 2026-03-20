from dataclasses import dataclass
from typing import List, Optional
import numpy as np

from core.dtos.roi_dto import RoiDTO
from ..constants import FlowDirectionCode
from .detection_dto import DetectionDto

from dataclasses import asdict

@dataclass(slots=True)
class EventDto:

    id: int
    detections: List[DetectionDto]
    event_frame: int
    status: FlowDirectionCode

    camera_id: Optional[str] = None
    pipeline_name: Optional[str] = None
    roi: Optional[RoiDTO] = None
    frame: Optional[np.ndarray] = None

    def to_dict_without_frame(self):
        data = asdict(self)
        data.pop("frame", None)
        return data
