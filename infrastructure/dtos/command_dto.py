from pydantic import BaseModel
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from infrastructure.dtos.source_dto import Source
from infrastructure.dtos.metadata_dto import Metadata


class CommandDTO(BaseModel):
    eventId: UUID
    timestamp: datetime
    source: Source
    targetId: str
    priority: int
    type: str
    version: str
    payload: Dict[str, Any]
    metadata: Optional[Metadata] = None


if __name__ == '__main__':
    input_event_dto = CommandDTO(
        eventId=UUID(int=0),
        timestamp=datetime.now(),
        source=Source(clientId='test', topic='test'),
        targetId='test',
        priority=1,
        type='test',
        version='test',
        payload={},
        metadata=None)

    print(input_event_dto.model_dump())