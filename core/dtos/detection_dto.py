from dataclasses import dataclass as dataclass
from pydantic.dataclasses import dataclass as dataclass_typed_attributes_check
from typing import Optional
from .bbox_dto import BBoxDto


@dataclass_typed_attributes_check()
@dataclass(slots=True)
class DetectionDto:
    bbox: BBoxDto

    class_id: int
    label: str
    confidence: float
    track_id: Optional[int] = None

    frame_id: Optional[int] = None
    model_version: Optional[str] = None