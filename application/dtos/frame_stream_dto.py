from dataclasses import dataclass, field
import numpy as np

from core.dtos.roi_dto import RoiDTO


@dataclass(slots=True)
class FrameStreamDto:

    camera_id: str
    frame: np.ndarray
    rois: list[RoiDTO] = field(default_factory=list)