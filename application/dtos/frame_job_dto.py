from dataclasses import dataclass, field
from typing import Optional
import numpy as np
from core.dtos.roi_dto import RoiDTO
from core.pipelines.base_pipeline import BasePipeline


@dataclass
class FrameJob:

    job_id: str
    camera_id: str
    frame: np.ndarray
    rois: list[RoiDTO] = field(default_factory=list)
    pipeline: Optional[BasePipeline] = None