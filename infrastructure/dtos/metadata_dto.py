from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID


class Metadata(BaseModel):
    correlationId: Optional[UUID] = None
    ttl: Optional[int] = None
    tags: Optional[List[str]] = None