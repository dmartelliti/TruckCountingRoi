from dataclasses import dataclass as dataclass
from pydantic.dataclasses import dataclass as dataclass_typed_attributes_check
from typing import List
from .detection_dto import DetectionDto


@dataclass_typed_attributes_check()
@dataclass(slots=True)
class TrackDto:
    id: int
    detections: List[DetectionDto]