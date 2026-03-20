from dataclasses import dataclass, field
from pydantic.dataclasses import dataclass as dataclass_typed_attributes_check
from typing import Dict
from .track_dto import TrackDto
from ..constants import GeneralStatusCode


@dataclass_typed_attributes_check()
@dataclass(slots=True)
class TrackHistoryDto:
    tracks: Dict[int, TrackDto] = field(default_factory=dict)
    status: Dict[int, GeneralStatusCode] = field(default_factory=dict)